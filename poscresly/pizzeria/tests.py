import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    CajaPizzeria, CajaPizzeriaEfectivo, CajaPizzeriaTransferencia, ItemPreparacion, Mesa,
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
        producto = ProductoSimple.objects.create(nombre='Agua', categoria='bebida', precio=Decimal('2.00'))
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
