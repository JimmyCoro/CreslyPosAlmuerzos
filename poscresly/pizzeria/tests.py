import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    CajaPizzeria, CajaPizzeriaEfectivo, CajaPizzeriaTarjeta, CajaPizzeriaTransferencia, CambioMetodoPago,
    CategoriaProducto, ItemPreparacion, Mesa,
    PagoPedido, PedidoPizzeria, PedidoProductoSimple, ProductoSimple,
)
from .views import _total_con_iva
from .views_caja import _resumen_turno


# Las plantillas piden estáticos con hash; en tests no hay collectstatic.
@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class CobroPorAdelantadoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'x')
        self.client.force_login(self.user)

        self.caja = CajaPizzeria.objects.create(fecha=timezone.localdate(), abierta_por=self.user)
        CajaPizzeriaEfectivo.objects.create(caja=self.caja, monto_inicial=Decimal('20.00'))
        CajaPizzeriaTransferencia.objects.create(caja=self.caja)

        self.mesa = Mesa.objects.create(numero=1, estado='ocupada')
        producto = ProductoSimple.objects.create(
            nombre='Agua', categoria=CategoriaProducto.objects.get(clave='bebida'), precio=Decimal('2.00'),
        )
        self.pedido = PedidoPizzeria.objects.create(tipo='mesa', mesa=self.mesa, mesero=self.user)
        linea = PedidoProductoSimple.objects.create(
            pedido=self.pedido, producto=producto, cantidad=2, precio_unitario=Decimal('2.00'),
        )
        self.item = ItemPreparacion.objects.create(
            pedido=self.pedido, producto_simple=linea, descripcion='Agua', cantidad=2,
        )
        self.pedido.total = Decimal('4.00')
        self.pedido.save()

    def cobrar(self, adelantado=True):
        monto = float(_total_con_iva(self.pedido.total))
        return self.client.post(
            reverse('pizzeria_procesar_cobro', args=[self.pedido.id]),
            data=json.dumps({'dividir': False, 'adelantado': adelantado,
                             'pagos': [{'metodo': 'Efectivo', 'monto': monto}]}),
            content_type='application/json',
        )

    def test_cobro_adelantado_deja_la_orden_abierta_y_suma_a_caja(self):
        respuesta = self.cobrar()
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        self.assertTrue(respuesta.json()['adelantado'])

        self.pedido.refresh_from_db()
        self.mesa.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'abierto')
        self.assertTrue(self.pedido.pagado_por_adelantado)
        self.assertEqual(self.mesa.estado, 'ocupada')
        self.assertEqual(PagoPedido.objects.contables().count(), 1)
        self.assertEqual(_resumen_turno(self.caja)['esperado_en_caja'], Decimal('20.00') + _total_con_iva(Decimal('4.00')))

    def test_no_se_cobra_dos_veces_ni_se_cambian_productos(self):
        self.cobrar()
        self.assertEqual(self.cobrar(adelantado=False).status_code, 400)
        quitar = self.client.post(reverse('pizzeria_quitar_item_preparacion', args=[self.item.id]))
        self.assertEqual(quitar.status_code, 400)
        cancelar = self.client.post(reverse('pizzeria_cancelar_pedido', args=[self.pedido.id]), {'motivo': 'x'})
        self.assertEqual(cancelar.status_code, 400)

    def test_cerrar_exige_todo_servido(self):
        self.cobrar()
        url = reverse('pizzeria_cerrar_orden_adelantada', args=[self.pedido.id])
        self.assertEqual(self.client.post(url).status_code, 400)

        self.item.estado = 'servido'
        self.item.save()
        self.assertEqual(self.client.post(url).status_code, 200)

        self.pedido.refresh_from_db()
        self.mesa.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'cobrado')
        self.assertEqual(self.mesa.estado, 'libre')
        # El pago no se cuenta dos veces al cerrar.
        self.assertEqual(PagoPedido.objects.contables().count(), 1)

    def test_tarjeta_muestra_leyenda_y_boton_cerrar_solo_con_todo_servido(self):
        self.cobrar()
        lista = self.client.get(reverse('pizzeria_ordenes') + '?canal=todas')
        self.assertContains(lista, 'Pagado por adelantado')
        self.assertNotContains(lista, 'data-cerrar-orden')

        self.item.estado = 'servido'
        self.item.save()
        lista = self.client.get(reverse('pizzeria_ordenes') + '?canal=todas')
        self.assertContains(lista, 'data-cerrar-orden')

    def test_con_todo_servido_es_cobro_normal(self):
        self.item.estado = 'servido'
        self.item.save()
        self.cobrar()
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.estado, 'cobrado')
        self.assertIsNone(self.pedido.pagado_adelantado_en)


@override_settings(STORAGES={
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class OrdenesDelTurnoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'x')
        self.client.force_login(self.user)
        self.caja = CajaPizzeria.objects.create(fecha=timezone.localdate(), abierta_por=self.user)
        CajaPizzeriaEfectivo.objects.create(caja=self.caja, monto_inicial=Decimal('20.00'))
        CajaPizzeriaTransferencia.objects.create(caja=self.caja)
        CajaPizzeriaTarjeta.objects.create(caja=self.caja)
        self.producto = ProductoSimple.objects.create(
            nombre='Agua', categoria=CategoriaProducto.objects.get(clave='bebida'), precio=Decimal('5.00'),
        )

    def pedido_cobrado(self, pagos, recibido=None):
        """Crea una orden de $total y la cobra por la vista real, como en el POS."""
        total = sum(Decimal(str(m)) for _, m in pagos)
        pedido = PedidoPizzeria.objects.create(tipo='llevar', mesero=self.user, total=total)
        PedidoProductoSimple.objects.create(
            pedido=pedido, producto=self.producto, cantidad=1, precio_unitario=total,
        )
        respuesta = self.client.post(
            reverse('pizzeria_procesar_cobro', args=[pedido.id]),
            data=json.dumps({'dividir': False, 'recibido': recibido,
                             'pagos': [{'metodo': m, 'monto': float(v)} for m, v in pagos]}),
            content_type='application/json',
        )
        self.assertEqual(respuesta.status_code, 200, respuesta.content)
        pedido.refresh_from_db()
        return pedido

    def corregir(self, pedido, metodo, motivo='Se marcó mal', turno_id=None):
        return self.client.post(
            reverse('pizzeria_caja_corregir_metodo', args=[pedido.id]),
            data=json.dumps({'turno_id': turno_id or self.caja.id, 'metodo': metodo, 'motivo': motivo}),
            content_type='application/json',
        )

    def test_agrupa_por_metodo_y_el_total_coincide_con_caja(self):
        efectivo = self.pedido_cobrado([('Efectivo', '10.00')], recibido=20)
        self.pedido_cobrado([('Tarjeta', '7.50')])
        self.pedido_cobrado([('Efectivo', '4.00'), ('Tarjeta', '6.00')])

        self.assertEqual(efectivo.cobrado_por, self.user)
        self.assertEqual(efectivo.recibido, Decimal('20.00'))

        respuesta = self.client.get(reverse('pizzeria_caja_ordenes_turno'))
        self.assertEqual(respuesta.status_code, 200)
        grupos = {g['clave']: g['subtotal'] for g in respuesta.context['grupos']}
        self.assertEqual(grupos, {'efectivo': Decimal('10.00'), 'tarjeta': Decimal('7.50'), 'mixto': Decimal('10.00')})
        self.assertEqual(respuesta.context['efectivo_en_mixtas'], Decimal('4.00'))
        self.assertEqual(respuesta.context['total_turno'], _resumen_turno(self.caja)['total_vendido'])
        self.assertContains(respuesta, '$10.00')  # cambio de lo recibido: 20 - 10

    def test_corregir_mueve_el_dinero_entre_metodos_y_deja_historial(self):
        pedido = self.pedido_cobrado([('Tarjeta', '8.00')])
        antes = _resumen_turno(self.caja)

        respuesta = self.corregir(pedido, 'Efectivo', motivo='El cliente pagó en efectivo')
        self.assertEqual(respuesta.status_code, 200, respuesta.content)

        despues = _resumen_turno(self.caja)
        self.assertEqual(despues['ventas_efectivo'], antes['ventas_efectivo'] + Decimal('8.00'))
        self.assertEqual(despues['ventas_tarjeta'], antes['ventas_tarjeta'] - Decimal('8.00'))
        self.assertEqual(despues['total_vendido'], antes['total_vendido'])
        self.caja.caja_tarjeta.refresh_from_db()
        self.assertEqual(self.caja.caja_tarjeta.total_ventas, Decimal('0.00'))

        cambio = CambioMetodoPago.objects.get(pedido=pedido)
        self.assertEqual((cambio.de, cambio.a, cambio.autor), ('Tarjeta', 'Efectivo', self.user))
        lista = self.client.get(reverse('pizzeria_caja_ordenes_turno') + '?filtro=editadas')
        self.assertEqual(len(lista.context['grupos']), 1)
        self.assertContains(lista, 'EDITADA')

    def test_corregir_exige_motivo_y_metodo_distinto(self):
        pedido = self.pedido_cobrado([('Efectivo', '5.00')])
        self.assertEqual(self.corregir(pedido, 'Tarjeta', motivo='  ').json()['message'], 'Falta escribir el motivo')
        self.assertEqual(self.corregir(pedido, 'Efectivo').json()['message'], 'Elige un método distinto al actual')
        self.assertEqual(self.corregir(pedido, 'Mixto').status_code, 400)
        self.assertFalse(CambioMetodoPago.objects.exists())

    def test_no_corrige_con_el_turno_cerrado(self):
        pedido = self.pedido_cobrado([('Efectivo', '5.00')])
        self.caja.estado = 'cerrada'
        self.caja.save()
        self.assertEqual(self.corregir(pedido, 'Tarjeta').status_code, 409)

    def test_caja_muestra_la_fila_de_entrada(self):
        self.pedido_cobrado([('Efectivo', '5.00')])
        respuesta = self.client.get(reverse('pizzeria_caja'))
        self.assertContains(respuesta, 'Órdenes del turno')
        self.assertContains(respuesta, '1 pagada · $5.00')
