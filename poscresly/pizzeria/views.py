import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .impresion import generar_comanda_pizza
from .models import (
    CajaPizzeria,
    CajaPizzeriaEfectivo,
    CajaPizzeriaTransferencia,
    ComboPizzeria,
    ComboTamano,
    GastoPizzeria,
    Mesa,
    PedidoCombo,
    PedidoPizza,
    PedidoPizzeria,
    PedidoProductoSimple,
    ProductoSimple,
    Sabor,
    TamanoPizza,
)
from .pricing import calcular_precio_combo, calcular_precio_pizza

LOGIN_URL = 'pizzeria_login'


# ===== AUTENTICACIÓN =====

def pizzeria_login(request):
    if request.user.is_authenticated:
        return redirect('pizzeria_mapa_mesas')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('pizzeria_mapa_mesas')
        error = 'Usuario o contraseña incorrectos'

    return render(request, 'pizzeria/login.html', {'error': error})


def pizzeria_logout(request):
    logout(request)
    return redirect('pizzeria_login')


# ===== MAPA DE MESAS =====

@login_required(login_url=LOGIN_URL)
def mapa_mesas(request):
    mesas = list(Mesa.objects.filter(activa=True).order_by('numero'))
    pedidos_abiertos = {
        p.mesa_id: p
        for p in PedidoPizzeria.objects.filter(estado__in=['abierto', 'por_cobrar'], mesa__isnull=False)
    }
    for mesa in mesas:
        mesa.pedido_abierto = pedidos_abiertos.get(mesa.id)

    pedidos_llevar_abiertos = PedidoPizzeria.objects.filter(
        estado__in=['abierto', 'por_cobrar'], tipo='llevar'
    ).order_by('-fecha_creacion')

    return render(request, 'pizzeria/mapa_mesas.html', {
        'mesas': mesas,
        'pedidos_llevar_abiertos': pedidos_llevar_abiertos,
    })


# ===== TOMA DE PEDIDO =====

@login_required(login_url=LOGIN_URL)
def tomar_pedido_pizzeria(request, mesa_id=None):
    mesa = get_object_or_404(Mesa, pk=mesa_id) if mesa_id else None
    tipo = 'mesa' if mesa else 'llevar'

    pedido_id_param = request.GET.get('pedido_id')
    if pedido_id_param:
        pedido_abierto = get_object_or_404(PedidoPizzeria, pk=pedido_id_param)
    elif mesa:
        pedido_abierto = PedidoPizzeria.objects.filter(
            mesa=mesa, estado__in=['abierto', 'por_cobrar']
        ).first()
    else:
        pedido_abierto = None

    tamanos = list(TamanoPizza.objects.order_by('orden'))
    sabores_pizza = list(Sabor.objects.filter(tipo='pizza').order_by('-es_premium', 'nombre'))
    combos = ComboPizzeria.objects.filter(activo=True).prefetch_related('tamanos__tamano', 'componentes')
    productos = ProductoSimple.objects.filter(activo=True).order_by('categoria', 'nombre')

    catalogo = {
        'tamanos': [
            {'id': t.id, 'nombre': t.nombre, 'precio_base': str(t.precio_base)} for t in tamanos
        ],
        'sabores': [
            {'id': s.id, 'nombre': s.nombre, 'es_premium': s.es_premium} for s in sabores_pizza
        ],
        'combos': [
            {
                'id': c.id,
                'nombre': c.nombre,
                'tamanos': [
                    {'tamano_id': ct.tamano_id, 'tamano_nombre': ct.tamano.nombre, 'precio': str(ct.precio)}
                    for ct in c.tamanos.all()
                ],
                'componentes': [
                    {'tipo': cc.get_tipo_display(), 'cantidad': cc.cantidad, 'detalle': cc.detalle}
                    for cc in c.componentes.all()
                ],
            }
            for c in combos
        ],
        'productos': [
            {
                'id': p.id, 'nombre': p.nombre, 'categoria': p.get_categoria_display(),
                'precio': str(p.precio),
            }
            for p in productos
        ],
    }

    return render(request, 'pizzeria/tomar_pedido_mobile.html', {
        'mesa': mesa,
        'tipo': tipo,
        'pedido_abierto': pedido_abierto,
        'catalogo_json': json.dumps(catalogo),
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def calcular_precio_pizza_ajax(request):
    try:
        tamano = get_object_or_404(TamanoPizza, pk=request.POST.get('tamano_id'))
        sabor_1 = get_object_or_404(Sabor, pk=request.POST.get('sabor_1_id'))
        sabor_2_id = request.POST.get('sabor_2_id') or None
        sabor_2 = get_object_or_404(Sabor, pk=sabor_2_id) if sabor_2_id else None
        combo_id = request.POST.get('combo_id') or None

        if combo_id:
            combo_tamano = get_object_or_404(ComboTamano, combo_id=combo_id, tamano=tamano)
            precio = calcular_precio_combo(combo_tamano, sabor_1, sabor_2)
        else:
            precio = calcular_precio_pizza(tamano, sabor_1, sabor_2)

        return JsonResponse({'status': 'ok', 'precio': str(precio)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def guardar_pedido_pizzeria(request):
    try:
        tipo = request.POST.get('tipo')
        mesa_id = request.POST.get('mesa_id') or None
        contacto = (request.POST.get('contacto') or '').strip()
        observaciones = request.POST.get('observaciones', '')
        pedido_id = request.POST.get('pedido_id') or None
        carrito = json.loads(request.POST.get('carrito', '[]'))

        if not carrito:
            return JsonResponse({'status': 'error', 'message': 'El carrito está vacío'}, status=400)

        nuevos_items_ticket = []

        with transaction.atomic():
            if pedido_id:
                pedido = get_object_or_404(PedidoPizzeria, pk=pedido_id)
            else:
                mesa = get_object_or_404(Mesa, pk=mesa_id) if tipo == 'mesa' else None
                pedido = PedidoPizzeria.objects.create(
                    tipo=tipo,
                    mesa=mesa,
                    contacto=contacto or None,
                    mesero=request.user,
                    observaciones=observaciones,
                )

            for item in carrito:
                kind = item.get('kind')
                cantidad = int(item.get('cantidad', 1))
                observacion_item = item.get('observacion', '')

                if kind == 'pizza':
                    tamano = TamanoPizza.objects.get(pk=item['tamano_id'])
                    sabor_1 = Sabor.objects.get(pk=item['sabor_1_id'])
                    sabor_2_id = item.get('sabor_2_id')
                    sabor_2 = Sabor.objects.get(pk=sabor_2_id) if sabor_2_id else None
                    precio_unitario = calcular_precio_pizza(tamano, sabor_1, sabor_2)

                    PedidoPizza.objects.create(
                        pedido=pedido, tamano=tamano, sabor_1=sabor_1, sabor_2=sabor_2,
                        cantidad=cantidad, precio_unitario=precio_unitario, observacion=observacion_item,
                    )
                    linea_sabor = sabor_1.nombre if not sabor_2 else f"1/2 {sabor_1.nombre} / 1/2 {sabor_2.nombre}"
                    nuevos_items_ticket.append(f"{cantidad}x Pizza {tamano.nombre}")
                    nuevos_items_ticket.append(f"   - {linea_sabor}")
                    if observacion_item:
                        nuevos_items_ticket.append(f"   Obs: {observacion_item}")

                elif kind == 'combo':
                    combo = ComboPizzeria.objects.get(pk=item['combo_id'])
                    tamano = TamanoPizza.objects.get(pk=item['tamano_id'])
                    combo_tamano = ComboTamano.objects.get(combo=combo, tamano=tamano)
                    sabor_1 = Sabor.objects.get(pk=item['sabor_1_id'])
                    sabor_2_id = item.get('sabor_2_id')
                    sabor_2 = Sabor.objects.get(pk=sabor_2_id) if sabor_2_id else None
                    precio_unitario = calcular_precio_combo(combo_tamano, sabor_1, sabor_2)

                    PedidoCombo.objects.create(
                        pedido=pedido, combo=combo, tamano=tamano, sabor_1=sabor_1, sabor_2=sabor_2,
                        cantidad=cantidad, precio_unitario=precio_unitario, observacion=observacion_item,
                    )
                    linea_sabor = sabor_1.nombre if not sabor_2 else f"1/2 {sabor_1.nombre} / 1/2 {sabor_2.nombre}"
                    nuevos_items_ticket.append(f"{cantidad}x {combo.nombre} ({tamano.nombre})")
                    nuevos_items_ticket.append(f"   - Pizza: {linea_sabor}")
                    for comp in combo.componentes.all():
                        detalle = f" {comp.detalle}" if comp.detalle else ''
                        nuevos_items_ticket.append(f"   - {comp.cantidad}x {comp.get_tipo_display()}{detalle}")
                    if observacion_item:
                        nuevos_items_ticket.append(f"   Obs: {observacion_item}")

                elif kind == 'producto':
                    producto = ProductoSimple.objects.get(pk=item['producto_id'])
                    PedidoProductoSimple.objects.create(
                        pedido=pedido, producto=producto, cantidad=cantidad,
                        precio_unitario=producto.precio, observacion=observacion_item,
                    )
                    nuevos_items_ticket.append(f"{cantidad}x {producto.nombre}")
                    if observacion_item:
                        nuevos_items_ticket.append(f"   Obs: {observacion_item}")

            pedido.total = _calcular_total_pedido(pedido)
            pedido.save()

            if pedido.tipo == 'mesa' and pedido.mesa:
                pedido.mesa.estado = 'ocupada'
                pedido.mesa.save()

        _enviar_mensaje_websocket_pizzeria('pedido_pizzeria_actualizado', _serializar_pedido(pedido))
        if pedido.mesa:
            _enviar_mensaje_websocket_pizzeria('mesa_actualizada', {
                'mesa_id': pedido.mesa.id, 'estado': pedido.mesa.estado, 'pedido_id': pedido.id,
            })

        if nuevos_items_ticket:
            comanda = generar_comanda_pizza(pedido, nuevos_items_ticket)
            _enviar_trabajo_impresion_pizzeria(pedido, comanda)

        return JsonResponse({'status': 'ok', 'pedido': _serializar_pedido(pedido)})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def cerrar_y_cobrar_pedido(request):
    try:
        pedido_id = request.POST.get('pedido_id')
        forma_pago = request.POST.get('forma_pago')
        if forma_pago not in ('Efectivo', 'Transferencia'):
            return JsonResponse({'status': 'error', 'message': 'Forma de pago inválida'}, status=400)

        pedido = get_object_or_404(PedidoPizzeria, pk=pedido_id)
        if pedido.estado == 'cobrado':
            return JsonResponse({'status': 'error', 'message': 'El pedido ya fue cobrado'}, status=400)

        caja = CajaPizzeria.objects.filter(estado='abierta').first()
        if not caja:
            caja = CajaPizzeria.objects.create(fecha=date.today(), estado='abierta')
            CajaPizzeriaEfectivo.objects.create(caja=caja, monto_inicial=0)
            CajaPizzeriaTransferencia.objects.create(caja=caja, monto_inicial=0)

        with transaction.atomic():
            pedido.forma_pago = forma_pago
            pedido.estado = 'cobrado'
            pedido.save()

            if forma_pago == 'Efectivo':
                caja.caja_efectivo.total_ventas += pedido.total
                caja.caja_efectivo.save()
            else:
                caja.caja_transferencia.total_ventas += pedido.total
                caja.caja_transferencia.save()

            if pedido.mesa:
                pedido.mesa.estado = 'libre'
                pedido.mesa.save()

        if pedido.mesa:
            _enviar_mensaje_websocket_pizzeria('mesa_actualizada', {
                'mesa_id': pedido.mesa.id, 'estado': 'libre', 'pedido_id': None,
            })
        _enviar_mensaje_websocket_pizzeria('pedido_pizzeria_actualizado', _serializar_pedido(pedido))

        return JsonResponse({'status': 'ok', 'pedido': _serializar_pedido(pedido)})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url=LOGIN_URL)
def obtener_pedido_pizzeria(request, pedido_id):
    pedido = get_object_or_404(PedidoPizzeria, pk=pedido_id)
    data = _serializar_pedido(pedido)
    data['pizzas'] = [
        {
            'id': p.id, 'tamano': p.tamano.nombre, 'sabor_1': p.sabor_1.nombre,
            'sabor_2': p.sabor_2.nombre if p.sabor_2 else None, 'cantidad': p.cantidad,
            'precio_unitario': float(p.precio_unitario), 'observacion': p.observacion,
        }
        for p in pedido.pizzas.select_related('tamano', 'sabor_1', 'sabor_2').all()
    ]
    data['combos'] = [
        {
            'id': c.id, 'combo': c.combo.nombre, 'tamano': c.tamano.nombre, 'sabor_1': c.sabor_1.nombre,
            'sabor_2': c.sabor_2.nombre if c.sabor_2 else None, 'cantidad': c.cantidad,
            'precio_unitario': float(c.precio_unitario), 'observacion': c.observacion,
        }
        for c in pedido.combos.select_related('combo', 'tamano', 'sabor_1', 'sabor_2').all()
    ]
    data['productos_simples'] = [
        {
            'id': ps.id, 'producto': ps.producto.nombre, 'cantidad': ps.cantidad,
            'precio_unitario': float(ps.precio_unitario), 'observacion': ps.observacion,
        }
        for ps in pedido.productos_simples.select_related('producto').all()
    ]
    return JsonResponse({'status': 'ok', 'pedido': data})


@login_required(login_url=LOGIN_URL)
def obtener_pedidos_abiertos_pizzeria(request):
    pedidos = PedidoPizzeria.objects.filter(
        estado__in=['abierto', 'por_cobrar']
    ).select_related('mesa', 'mesero')
    return JsonResponse({'status': 'ok', 'pedidos': [_serializar_pedido(p) for p in pedidos]})


# ===== CAJA PIZZERÍA =====

@login_required(login_url=LOGIN_URL)
def dashboard_caja_pizzeria(request):
    caja_abierta = CajaPizzeria.objects.filter(estado='abierta').first()

    if not caja_abierta:
        pedidos_cobrados = PedidoPizzeria.objects.none()
        total_efectivo = Decimal('0')
        total_transferencia = Decimal('0')
        monto_inicial_efectivo = monto_inicial_transferencia = Decimal('0')
        gastos = GastoPizzeria.objects.none()
    else:
        pedidos_cobrados = PedidoPizzeria.objects.filter(
            estado='cobrado', fecha_creacion__gte=caja_abierta.fecha_apertura
        ).order_by('-fecha_creacion')
        total_efectivo = sum((p.total for p in pedidos_cobrados if p.forma_pago == 'Efectivo'), Decimal('0'))
        total_transferencia = sum((p.total for p in pedidos_cobrados if p.forma_pago == 'Transferencia'), Decimal('0'))
        monto_inicial_efectivo = caja_abierta.caja_efectivo.monto_inicial
        monto_inicial_transferencia = caja_abierta.caja_transferencia.monto_inicial
        gastos = caja_abierta.gastos.all()

    total_ventas = total_efectivo + total_transferencia
    total_gastos = sum((g.monto for g in gastos), Decimal('0'))

    return render(request, 'pizzeria/caja_pizzeria.html', {
        'caja_hoy': caja_abierta,
        'pedidos_cobrados': pedidos_cobrados,
        'gastos': gastos,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_ventas': total_ventas,
        'total_gastos': total_gastos,
        'balance_neto': total_ventas - total_gastos,
        'monto_inicial_efectivo': monto_inicial_efectivo,
        'monto_inicial_transferencia': monto_inicial_transferencia,
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def abrir_caja_pizzeria(request):
    if CajaPizzeria.objects.filter(estado='abierta').exists():
        return JsonResponse({'success': False, 'message': 'Ya existe una caja de pizzería abierta.'})

    try:
        monto_inicial_efectivo = float(request.POST.get('monto_inicial_efectivo', 0))
        monto_inicial_transferencia = float(request.POST.get('monto_inicial_transferencia', 0))
        observaciones = request.POST.get('observaciones', '')

        caja = CajaPizzeria.objects.create(fecha=date.today(), estado='abierta', observaciones=observaciones)
        CajaPizzeriaEfectivo.objects.create(caja=caja, monto_inicial=monto_inicial_efectivo)
        CajaPizzeriaTransferencia.objects.create(caja=caja, monto_inicial=monto_inicial_transferencia)

        return JsonResponse({'success': True, 'message': 'Caja de pizzería abierta exitosamente', 'caja_id': caja.id})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al abrir caja: {e}'})


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def cerrar_caja_pizzeria(request):
    try:
        caja_abierta = CajaPizzeria.objects.filter(estado='abierta').first()
        if not caja_abierta:
            return JsonResponse({'success': False, 'message': 'No hay caja de pizzería abierta para cerrar'})

        monto_final_efectivo = float(request.POST.get('monto_final_efectivo') or 0)
        monto_final_transferencia = float(request.POST.get('monto_final_transferencia') or 0)
        observaciones_cierre = request.POST.get('observaciones_cierre', '')

        caja_abierta.caja_efectivo.monto_final = monto_final_efectivo
        caja_abierta.caja_efectivo.save()
        caja_abierta.caja_transferencia.monto_final = monto_final_transferencia
        caja_abierta.caja_transferencia.save()

        caja_abierta.estado = 'cerrada'
        caja_abierta.fecha_cierre = timezone.now()
        if observaciones_cierre:
            caja_abierta.observaciones += f"\nCierre: {observaciones_cierre}"
        caja_abierta.save()

        return JsonResponse({'success': True, 'message': 'Caja de pizzería cerrada exitosamente'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al cerrar caja: {e}'})


# ===== HELPERS INTERNOS =====

def _calcular_total_pedido(pedido):
    total = Decimal('0.00')
    for p in pedido.pizzas.all():
        total += p.precio_unitario * p.cantidad
    for c in pedido.combos.all():
        total += c.precio_unitario * c.cantidad
    for ps in pedido.productos_simples.all():
        total += ps.precio_unitario * ps.cantidad
    return total


def _serializar_pedido(pedido):
    return {
        'id': pedido.id,
        'numero_dia': pedido.numero_dia,
        'numero_pedido_completo': pedido.numero_pedido_completo,
        'tipo': pedido.tipo,
        'mesa_id': pedido.mesa_id,
        'mesa_numero': pedido.mesa.numero if pedido.mesa else None,
        'contacto': pedido.contacto,
        'mesero': pedido.mesero.get_username(),
        'estado': pedido.estado,
        'forma_pago': pedido.forma_pago,
        'total': float(pedido.total),
        'fecha_creacion': pedido.fecha_creacion.isoformat(),
    }


def _enviar_mensaje_websocket_pizzeria(tipo_mensaje, payload):
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync

    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "pizzeria_mesas",
                {"type": tipo_mensaje, "payload": payload},
            )
    except Exception as e:
        print(f"[WEBSOCKET PIZZERIA] Error al enviar mensaje: {e}")


def _enviar_trabajo_impresion_pizzeria(pedido, contenido):
    import os

    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    try:
        payload = {
            "type": "print_job",
            "pedido": _serializar_pedido(pedido),
            "contenido": contenido,
        }
        ips_impresoras_str = os.getenv('IMPRESORAS_IPS', '').strip()
        if ips_impresoras_str:
            payload["impresoras"] = [ip.strip() for ip in ips_impresoras_str.split(',') if ip.strip()]

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "impresion",
                {"type": "print_job", "payload": payload},
            )
    except Exception as e:
        print(f"[WEBSOCKET PIZZERIA] Error al enviar trabajo de impresión: {e}")
