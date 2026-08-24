import json
import re
from datetime import date
from decimal import Decimal

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError, transaction
from django.db.models import Sum

from .impresion import generar_comanda_pizza
from .models import (
    AsignacionItemCobro,
    CajaPizzeria,
    CajaPizzeriaEfectivo,
    CajaPizzeriaTarjeta,
    CajaPizzeriaTransferencia,
    ComboPizzeria,
    ComboTamano,
    GastoPizzeria,
    ItemPreparacion,
    Mesa,
    PagoPedido,
    PedidoCombo,
    PedidoComboSaborAlitas,
    PedidoComboSaborBebida,
    PedidoComboSaborMichelada,
    PedidoComboSaborPorcion,
    PedidoPizza,
    PedidoPizzeria,
    PedidoProductoSimple,
    PedidoProductoSimpleSaborAlitas,
    PersonaCobro,
    ProductoSimple,
    Sabor,
    TamanoPizza,
)
from .pricing import calcular_precio_combo, calcular_precio_pizza, calcular_recargo_premium

LOGIN_URL = 'pizzeria_login'


def _alitas_cantidad_producto(nombre):
    """Extrae la cantidad de alitas del nombre del producto (ej: '14 alitas' -> 14)."""
    match = re.match(r'\s*(\d+)', nombre)
    return int(match.group(1)) if match else 0


def _tipo_sabor_bebida_producto(producto):
    """Los productos de bebida tipo "Cola" (ej. Cola Mediana, Cola Grande) piden
    elegir el sabor (Coca-Cola, Fanta, etc) y las Micheladas piden sabor (Maracuyá,
    Limón). El resto de bebidas (agua, cuba libre, jugos) quedan igual, sin
    selección. Devuelve el `tipo` de Sabor que aplica ('bebida', 'michelada') o
    None si el producto no necesita selección de sabor."""
    if producto.categoria != 'bebida':
        return None
    nombre = producto.nombre.lower()
    if 'cola' in nombre:
        return 'bebida'
    if 'michelada' in nombre:
        return 'michelada'
    return None


def _cantidad_componente(componentes, tipo):
    return next((c.cantidad for c in componentes if c.tipo == tipo), 0)


TAMANO_REFERENCIA_PORCION_NOMBRE = 'Pequeña'


def _tamano_referencia_porcion():
    """Las porciones de pizza no tienen un tamaño propio, pero si se elige un sabor
    premium igual debe sumar un recargo: se usa el recargo del tamaño más pequeño
    como referencia."""
    return TamanoPizza.objects.filter(nombre=TAMANO_REFERENCIA_PORCION_NOMBRE).first() or TamanoPizza.objects.order_by('orden').first()


def _serializar_combo_catalogo(c):
    """Arma el dict de catálogo de un combo para el frontend. Cubre tanto los
    Mega Combos (con tamaños/precio variable) como los combos de precio fijo
    (sin ComboTamano), y expone cuántas unidades de cada componente interactivo
    trae (alitas, bebida, michelada, porción de pizza)."""
    componentes = list(c.componentes.all())
    tamanos = list(c.tamanos.all())
    return {
        'id': c.id,
        'nombre': c.nombre,
        'descripcion': c.descripcion,
        'tamanos': [
            {'tamano_id': ct.tamano_id, 'tamano_nombre': ct.tamano.nombre, 'precio': str(ct.precio)}
            for ct in tamanos
        ],
        'componentes': [
            {'tipo': cc.tipo, 'tipo_display': cc.get_tipo_display(), 'cantidad': cc.cantidad, 'detalle': cc.detalle}
            for cc in componentes
        ],
        'alitas_cantidad': _cantidad_componente(componentes, 'alitas'),
        'bebida_cantidad': _cantidad_componente(componentes, 'bebida'),
        'michelada_cantidad': _cantidad_componente(componentes, 'michelada'),
        'porcion_pizza_cantidad': _cantidad_componente(componentes, 'porcion_pizza'),
        'hamburguesa_cantidad': _cantidad_componente(componentes, 'hamburguesa'),
        'precio_fijo': str(c.precio_fijo) if c.precio_fijo is not None else None,
        'pizza_tamano_fijo_id': c.pizza_tamano_fijo_id,
        'pizza_tamano_fijo_nombre': c.pizza_tamano_fijo.nombre if c.pizza_tamano_fijo_id else None,
        'precio_desde': str(min((ct.precio for ct in tamanos), default=(c.precio_fijo or 0))),
    }


# ===== AUTENTICACIÓN =====

def pizzeria_login(request):
    if request.user.is_authenticated:
        return redirect('pizzeria_inicio')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('pizzeria_inicio')
        error = 'Usuario o contraseña incorrectos'

    return render(request, 'pizzeria/login.html', {'error': error})


def pizzeria_logout(request):
    logout(request)
    return redirect('pizzeria_login')


# ===== MAPA DE MESAS =====

def _formatear_tiempo_transcurrido(fecha):
    minutos = int((timezone.now() - fecha).total_seconds() // 60)
    if minutos < 60:
        return f"{minutos} min"
    horas, resto = divmod(minutos, 60)
    return f"{horas} h {resto:02d}"


@login_required(login_url=LOGIN_URL)
def mapa_mesas(request):
    mesas = list(Mesa.objects.filter(activa=True).order_by('numero'))
    pedidos_abiertos = {
        p.mesa_id: p
        for p in PedidoPizzeria.objects.filter(estado__in=['abierto', 'por_cobrar'], mesa__isnull=False)
    }

    zonas = {}
    count_free = count_busy = count_bill = 0
    total_open = Decimal('0')

    for mesa in mesas:
        pedido = pedidos_abiertos.get(mesa.id)
        mesa.pedido_abierto = pedido
        mesa.tiempo_transcurrido = _formatear_tiempo_transcurrido(pedido.fecha_creacion) if pedido else None
        if pedido:
            total_open += pedido.total

        if mesa.estado == 'libre':
            count_free += 1
        elif mesa.estado == 'ocupada':
            count_busy += 1
        elif mesa.estado == 'por_cobrar':
            count_bill += 1

        zonas.setdefault(mesa.zona or 'Mesas', []).append(mesa)

    zonas_lista = [
        {
            'nombre': nombre,
            'mesas': mesas_zona,
            'total': len(mesas_zona),
            'libres': sum(1 for m in mesas_zona if m.estado == 'libre'),
        }
        for nombre, mesas_zona in zonas.items()
    ]

    pedidos_llevar_abiertos = list(PedidoPizzeria.objects.filter(
        estado__in=['abierto', 'por_cobrar'], tipo='llevar'
    ).order_by('-fecha_creacion'))
    total_llevar = sum((p.total for p in pedidos_llevar_abiertos), Decimal('0'))

    return render(request, 'pizzeria/mapa_mesas.html', {
        'zonas': zonas_lista,
        'count_all': len(mesas),
        'count_free': count_free,
        'count_busy': count_busy,
        'count_bill': count_bill,
        'total_open': total_open,
        'pedidos_llevar_abiertos': pedidos_llevar_abiertos,
        'total_llevar': total_llevar,
        'breadcrumbs': [{'label': 'Mesas', 'url': None}],
    })


# ===== GESTIÓN DE MESAS =====

def _serializar_mesa(mesa):
    return {
        'id': mesa.id,
        'numero': mesa.numero,
        'nombre': mesa.nombre,
        'zona': mesa.zona,
        'estado': mesa.estado,
        'pos_x': mesa.pos_x,
        'pos_y': mesa.pos_y,
        'forma': mesa.forma,
        'capacidad': mesa.capacidad,
        'activa': mesa.activa,
    }


@login_required(login_url=LOGIN_URL)
def gestionar_mesas(request):
    mesas = Mesa.objects.all().order_by('numero')
    zonas_existentes = sorted({m.zona for m in mesas if m.zona})
    return render(request, 'pizzeria/gestionar_mesas.html', {
        'mesas': mesas,
        'formas': Mesa.FORMAS,
        'zonas_existentes': zonas_existentes,
        'breadcrumbs': [
            {'label': 'Mesas', 'url': reverse('pizzeria_mapa_mesas')},
            {'label': 'Gestionar', 'url': None},
        ],
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def crear_mesa_pizzeria(request):
    try:
        numero = request.POST.get('numero')
        if not numero:
            return JsonResponse({'status': 'error', 'message': 'El número de mesa es obligatorio'}, status=400)

        mesa = Mesa.objects.create(
            numero=int(numero),
            nombre=(request.POST.get('nombre') or '').strip(),
            zona=(request.POST.get('zona') or '').strip(),
            forma=request.POST.get('forma') or 'cuadrada',
            capacidad=int(request.POST.get('capacidad') or 4),
            pos_x=float(request.POST.get('pos_x') or 50),
            pos_y=float(request.POST.get('pos_y') or 50),
        )
        return JsonResponse({'status': 'ok', 'mesa': _serializar_mesa(mesa)})
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Datos inválidos'}, status=400)
    except IntegrityError:
        return JsonResponse({'status': 'error', 'message': 'Ya existe una mesa con ese número'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def actualizar_mesa_pizzeria(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    try:
        if 'numero' in request.POST:
            mesa.numero = int(request.POST.get('numero'))
        if 'nombre' in request.POST:
            mesa.nombre = (request.POST.get('nombre') or '').strip()
        if 'zona' in request.POST:
            mesa.zona = (request.POST.get('zona') or '').strip()
        if 'forma' in request.POST:
            mesa.forma = request.POST.get('forma')
        if 'capacidad' in request.POST:
            mesa.capacidad = int(request.POST.get('capacidad'))
        if 'activa' in request.POST:
            mesa.activa = request.POST.get('activa') in ('true', '1', 'on')
        mesa.full_clean()
        mesa.save()
        return JsonResponse({'status': 'ok', 'mesa': _serializar_mesa(mesa)})
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Datos inválidos'}, status=400)
    except (IntegrityError, ValidationError):
        return JsonResponse({'status': 'error', 'message': 'Ya existe una mesa con ese número'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def mover_mesa_pizzeria(request, mesa_id):
    try:
        mesa = get_object_or_404(Mesa, pk=mesa_id)
        pos_x = max(0.0, min(100.0, float(request.POST.get('pos_x'))))
        pos_y = max(0.0, min(100.0, float(request.POST.get('pos_y'))))
        mesa.pos_x = pos_x
        mesa.pos_y = pos_y
        mesa.save(update_fields=['pos_x', 'pos_y'])
        return JsonResponse({'status': 'ok', 'mesa': _serializar_mesa(mesa)})
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Coordenadas inválidas'}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def cambiar_estado_mesa_pizzeria(request, mesa_id):
    estado = request.POST.get('estado')
    if estado not in ('libre', 'reservada', 'ocupada'):
        return JsonResponse({'status': 'error', 'message': 'Estado inválido'}, status=400)

    mesa = get_object_or_404(Mesa, pk=mesa_id)
    if PedidoPizzeria.objects.filter(mesa_id=mesa_id, estado__in=['abierto', 'por_cobrar']).exists():
        return JsonResponse({'status': 'error', 'message': 'Esta mesa tiene un pedido abierto, no se puede cambiar el estado manualmente'}, status=400)

    mesa.estado = estado
    mesa.save(update_fields=['estado'])

    _enviar_mensaje_websocket_pizzeria('mesa_actualizada', {
        'mesa_id': mesa.id, 'estado': mesa.estado, 'pedido_id': None,
    })
    return JsonResponse({'status': 'ok', 'mesa': _serializar_mesa(mesa)})


# ===== ÓRDENES EN CURSO =====

def _describir_pizza(p):
    sabor = p.sabor_1.nombre if not p.sabor_2 else f"1/2 {p.sabor_1.nombre} / 1/2 {p.sabor_2.nombre}"
    return f"Pizza {p.tamano.nombre} - {sabor}"


def _describir_combo(c):
    linea = c.combo.nombre + (f" ({c.tamano.nombre})" if c.tamano else '')
    if c.sabor_1:
        sabor = c.sabor_1.nombre if not c.sabor_2 else f"1/2 {c.sabor_1.nombre} / 1/2 {c.sabor_2.nombre}"
        linea += f" - {sabor}"
    porciones = c.sabores_porcion.all()
    if porciones:
        linea += ' | Porciones: ' + ', '.join(sp.sabor.nombre for sp in porciones)
    alitas = c.sabores_alitas.all()
    if alitas:
        linea += ' | Alitas: ' + ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas)
    bebidas = c.sabores_bebida.all()
    if bebidas:
        linea += ' | Bebida: ' + ', '.join(sb.sabor.nombre for sb in bebidas)
    micheladas = c.sabores_michelada.all()
    if micheladas:
        linea += ' | Michelada: ' + ', '.join(sm.sabor.nombre for sm in micheladas)
    return linea


def _describir_producto_simple(ps):
    linea_ps = ps.producto.nombre
    alitas_ps = ps.sabores_alitas.all()
    if alitas_ps:
        linea_ps += ': ' + ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas_ps)
    elif ps.sabor_bebida_id:
        linea_ps += f' - {ps.sabor_bebida.nombre}'
    return linea_ps


def _pedido_combos_qs(pedido):
    return pedido.combos.select_related('combo', 'tamano', 'sabor_1', 'sabor_2').prefetch_related(
        'sabores_alitas__sabor', 'sabores_bebida__sabor', 'sabores_michelada__sabor', 'sabores_porcion__sabor',
    ).all()


def _pedido_productos_simples_qs(pedido):
    return pedido.productos_simples.select_related('producto', 'sabor_bebida').prefetch_related(
        'sabores_alitas__sabor',
    ).all()


def _construir_items_pedido(pedido):
    """Arma la lista de líneas legibles de un pedido y sus ítems de preparación de cocina."""
    items_preparacion = list(pedido.items_preparacion.all())
    items = []
    for p in pedido.pizzas.select_related('tamano', 'sabor_1', 'sabor_2').all():
        items.append(f"{p.cantidad}x {_describir_pizza(p)}")
    for c in _pedido_combos_qs(pedido):
        items.append(f"{c.cantidad}x {_describir_combo(c)}")
    for ps in _pedido_productos_simples_qs(pedido):
        items.append(f"{ps.cantidad}x {_describir_producto_simple(ps)}")

    return items, items_preparacion, (len(items_preparacion) or len(items))


def _construir_items_cobro(pedido):
    """Versión estructurada (id/tipo/cantidad/precio) de las líneas del pedido,
    usada por la pantalla de cobro para armar la división por productos."""
    items = []
    for p in pedido.pizzas.select_related('tamano', 'sabor_1', 'sabor_2').all():
        items.append({
            'tipo': 'pizza', 'id': p.id, 'descripcion': _describir_pizza(p),
            'cantidad': p.cantidad, 'precio_unitario': float(p.precio_unitario),
        })
    for c in _pedido_combos_qs(pedido):
        items.append({
            'tipo': 'combo', 'id': c.id, 'descripcion': _describir_combo(c),
            'cantidad': c.cantidad, 'precio_unitario': float(c.precio_unitario),
        })
    for ps in _pedido_productos_simples_qs(pedido):
        items.append({
            'tipo': 'producto_simple', 'id': ps.id, 'descripcion': _describir_producto_simple(ps),
            'cantidad': ps.cantidad, 'precio_unitario': float(ps.precio_unitario),
        })
    return items


def _agrupar_items_preparacion(items_preparacion):
    """Agrupa ítems de preparación consecutivos que pertenecen al mismo combo
    (ej. la pizza y las alitas de "Mega Combo 1") bajo un mismo bloque, para
    poder mostrar el nombre del combo como encabezado y cada sub-ítem con su
    propio estado. Los ítems sueltos (grupo vacío) quedan cada uno en su
    propio bloque, sin encabezado."""
    bloques = []
    for item in items_preparacion:
        linea = f"{item.cantidad}x {item.descripcion}"
        if item.grupo and bloques and bloques[-1]['grupo'] == item.grupo:
            bloques[-1]['items'].append(item)
            bloques[-1]['lineas'].append(linea)
        else:
            bloques.append({'grupo': item.grupo or None, 'items': [item], 'lineas': [linea]})
    return bloques


def _listar_ordenes_en_curso(pedidos_qs):
    ordenes = []
    for pedido in pedidos_qs:
        items, items_preparacion, total_items = _construir_items_pedido(pedido)
        bloques = _agrupar_items_preparacion(items_preparacion)
        ordenes.append({
            'pedido': pedido,
            'items': items,
            'bloques': bloques,
            'total_items': total_items,
        })
    return ordenes


def _lista_padre_pedido(pedido):
    if pedido.tipo == 'delivery':
        return {'label': 'Delivery', 'url': reverse('pizzeria_delivery')}
    return {'label': 'Órdenes', 'url': reverse('pizzeria_ordenes')}


@login_required(login_url=LOGIN_URL)
def ordenes_en_curso(request):
    pedidos = PedidoPizzeria.objects.filter(
        estado__in=['abierto', 'por_cobrar']
    ).select_related('mesa').prefetch_related('items_preparacion').order_by('-fecha_creacion')

    return render(request, 'pizzeria/ordenes.html', {
        'ordenes': _listar_ordenes_en_curso(pedidos),
        'es_delivery': False,
        'breadcrumbs': [{'label': 'Órdenes', 'url': None}],
    })


@login_required(login_url=LOGIN_URL)
def ordenes_delivery(request):
    pedidos = PedidoPizzeria.objects.filter(
        estado__in=['abierto', 'por_cobrar'], tipo='delivery'
    ).select_related('mesa').prefetch_related('items_preparacion').order_by('-fecha_creacion')

    return render(request, 'pizzeria/ordenes.html', {
        'ordenes': _listar_ordenes_en_curso(pedidos),
        'es_delivery': True,
        'breadcrumbs': [{'label': 'Delivery', 'url': None}],
    })


@login_required(login_url=LOGIN_URL)
def inicio_pizzeria(request):
    pedidos_abiertos = PedidoPizzeria.objects.filter(estado__in=['abierto', 'por_cobrar'])
    ventas_hoy = PagoPedido.objects.filter(
        pedido__estado='cobrado', creado_en__date=timezone.localdate()
    ).aggregate(total=Sum('monto'))['total'] or Decimal('0')

    return render(request, 'pizzeria/inicio.html', {
        'total_pedidos_abiertos': pedidos_abiertos.count(),
        'total_delivery_abiertos': pedidos_abiertos.filter(tipo='delivery').count(),
        'total_mesas_ocupadas': Mesa.objects.filter(estado__in=['ocupada', 'por_cobrar']).count(),
        'ventas_hoy': ventas_hoy,
        'breadcrumbs': [{'label': 'Inicio', 'url': None}],
    })


@login_required(login_url=LOGIN_URL)
def detalle_orden_pizzeria(request, pedido_id):
    pedido = get_object_or_404(
        PedidoPizzeria.objects.select_related('mesa', 'mesero').prefetch_related('items_preparacion'),
        pk=pedido_id,
    )
    items, items_preparacion, total_items = _construir_items_pedido(pedido)
    bloques = _agrupar_items_preparacion(items_preparacion)

    return render(request, 'pizzeria/detalle_orden.html', {
        'pedido': pedido,
        'items': items,
        'bloques': bloques,
        'total_items': total_items,
        'breadcrumbs': [
            _lista_padre_pedido(pedido),
            {'label': f'Pedido #{pedido.numero_pedido_completo}', 'url': None},
        ],
    })


@login_required(login_url=LOGIN_URL)
def cobrar_orden_pizzeria(request, pedido_id):
    pedido = get_object_or_404(PedidoPizzeria.objects.select_related('mesa', 'mesero'), pk=pedido_id)
    if pedido.estado not in ('abierto', 'por_cobrar'):
        return redirect('pizzeria_detalle_orden', pedido_id=pedido.id)

    if pedido.estado == 'abierto':
        pedido.estado = 'por_cobrar'
        pedido.save()
        if pedido.mesa:
            pedido.mesa.estado = 'por_cobrar'
            pedido.mesa.save()
            _enviar_mensaje_websocket_pizzeria('mesa_actualizada', {
                'mesa_id': pedido.mesa.id, 'estado': 'por_cobrar', 'pedido_id': pedido.id,
            })
        _enviar_mensaje_websocket_pizzeria('pedido_pizzeria_actualizado', _serializar_pedido(pedido))

    items_cobro = _construir_items_cobro(pedido)
    total_items = sum(item['cantidad'] for item in items_cobro)

    return render(request, 'pizzeria/cobrar_orden.html', {
        'pedido': pedido,
        'items_cobro_json': json.dumps(items_cobro),
        'total_items': total_items,
        'breadcrumbs': [
            _lista_padre_pedido(pedido),
            {'label': f'Pedido #{pedido.numero_pedido_completo}', 'url': reverse('pizzeria_detalle_orden', args=[pedido.id])},
            {'label': 'Cobrar', 'url': None},
        ],
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def avanzar_estado_item_preparacion(request, item_id):
    try:
        item = get_object_or_404(ItemPreparacion, pk=item_id)
        secuencia = [estado for estado, _ in ItemPreparacion.ESTADOS]
        siguiente_idx = (secuencia.index(item.estado) + 1) % len(secuencia)
        item.estado = secuencia[siguiente_idx]
        item.save()

        return JsonResponse({
            'status': 'ok',
            'estado': item.estado,
            'estado_display': item.get_estado_display(),
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def establecer_estado_item_preparacion(request, item_id):
    try:
        item = get_object_or_404(ItemPreparacion, pk=item_id)
        estado = request.POST.get('estado', '')
        if estado not in dict(ItemPreparacion.ESTADOS):
            return JsonResponse({'status': 'error', 'message': 'Estado inválido'}, status=400)

        item.estado = estado
        item.save()

        return JsonResponse({
            'status': 'ok',
            'estado': item.estado,
            'estado_display': item.get_estado_display(),
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def _hermanos_item_preparacion(item):
    """Ítems de cocina que comparten la misma línea de pedido que `item`
    (para un combo, la pizza/alitas/bebida generadas juntas)."""
    return ItemPreparacion.objects.filter(
        pizza=item.pizza, combo=item.combo, producto_simple=item.producto_simple,
    )


@login_required(login_url=LOGIN_URL)
def detalle_item_preparacion(request, item_id):
    item = get_object_or_404(ItemPreparacion, pk=item_id)
    linea = item.linea

    if item.pizza_id:
        tipo = 'pizza'
    elif item.combo_id:
        tipo = 'combo'
    elif item.producto_simple_id:
        tipo = 'producto'
    else:
        tipo = None

    puede_quitar = False
    if linea is not None:
        puede_quitar = all(h.estado == 'en_proceso' for h in _hermanos_item_preparacion(item))

    return JsonResponse({
        'status': 'ok',
        'item': {
            'id': item.id,
            'descripcion': item.descripcion,
            'cantidad': item.cantidad,
            'estado': item.estado,
            'estado_display': item.get_estado_display(),
            'estados': [{'value': v, 'display': d} for v, d in ItemPreparacion.ESTADOS],
            'tipo': tipo,
            'observacion': getattr(linea, 'observacion', ''),
            'puede_gestionar': linea is not None,
            'puede_quitar': puede_quitar,
        },
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def editar_item_preparacion(request, item_id):
    try:
        item = get_object_or_404(ItemPreparacion, pk=item_id)
        linea = item.linea
        if linea is None:
            return JsonResponse({'status': 'error', 'message': 'Este platillo no se puede editar'}, status=400)

        try:
            cantidad = int(request.POST.get('cantidad', linea.cantidad))
        except (TypeError, ValueError):
            return JsonResponse({'status': 'error', 'message': 'Cantidad inválida'}, status=400)
        if cantidad < 1:
            return JsonResponse({'status': 'error', 'message': 'La cantidad debe ser al menos 1'}, status=400)

        observacion = request.POST.get('observacion', '').strip()

        pedido = item.pedido
        with transaction.atomic():
            linea.cantidad = cantidad
            linea.observacion = observacion
            linea.save()

            _hermanos_item_preparacion(item).update(cantidad=cantidad)

            pedido.total = _calcular_total_pedido(pedido)
            pedido.save()

        _enviar_mensaje_websocket_pizzeria('pedido_pizzeria_actualizado', _serializar_pedido(pedido))

        return JsonResponse({'status': 'ok', 'total': float(pedido.total)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def duplicar_item_preparacion(request, item_id):
    try:
        item = get_object_or_404(ItemPreparacion, pk=item_id)
        pedido = item.pedido
        nuevas_lineas_ticket = []

        with transaction.atomic():
            if item.pizza_id:
                original = item.pizza
                linea_sabor = (
                    original.sabor_1.nombre if not original.sabor_2
                    else f"1/2 {original.sabor_1.nombre} / 1/2 {original.sabor_2.nombre}"
                )
                nueva_pizza = PedidoPizza.objects.create(
                    pedido=pedido, tamano=original.tamano, sabor_1=original.sabor_1, sabor_2=original.sabor_2,
                    cantidad=1, precio_unitario=original.precio_unitario, observacion=original.observacion,
                )
                nuevas_lineas_ticket.append(f"1x Pizza {original.tamano.nombre}")
                nuevas_lineas_ticket.append(f"   - {linea_sabor}")
                if original.observacion:
                    nuevas_lineas_ticket.append(f"   Obs: {original.observacion}")

                ItemPreparacion.objects.create(
                    pedido=pedido, pizza=nueva_pizza, cantidad=1,
                    descripcion=f"Pizza {original.tamano.nombre} - {linea_sabor}",
                )

            elif item.combo_id:
                original = item.combo
                combo = original.combo
                tamano = original.tamano
                linea_sabor = None
                if original.sabor_1:
                    linea_sabor = (
                        original.sabor_1.nombre if not original.sabor_2
                        else f"1/2 {original.sabor_1.nombre} / 1/2 {original.sabor_2.nombre}"
                    )

                nuevo_combo = PedidoCombo.objects.create(
                    pedido=pedido, combo=combo, tamano=tamano, sabor_1=original.sabor_1, sabor_2=original.sabor_2,
                    cantidad=1, precio_unitario=original.precio_unitario, observacion=original.observacion,
                )
                alitas_originales = list(original.sabores_alitas.select_related('sabor').all())
                if alitas_originales:
                    PedidoComboSaborAlitas.objects.bulk_create([
                        PedidoComboSaborAlitas(pedido_combo=nuevo_combo, sabor=sa.sabor, cantidad=sa.cantidad)
                        for sa in alitas_originales
                    ])
                bebida_originales = [sb.sabor for sb in original.sabores_bebida.select_related('sabor').all()]
                if bebida_originales:
                    PedidoComboSaborBebida.objects.bulk_create([
                        PedidoComboSaborBebida(pedido_combo=nuevo_combo, sabor=s) for s in bebida_originales
                    ])
                michelada_originales = [sm.sabor for sm in original.sabores_michelada.select_related('sabor').all()]
                if michelada_originales:
                    PedidoComboSaborMichelada.objects.bulk_create([
                        PedidoComboSaborMichelada(pedido_combo=nuevo_combo, sabor=s) for s in michelada_originales
                    ])
                porcion_originales = [sp.sabor for sp in original.sabores_porcion.select_related('sabor').all()]
                if porcion_originales:
                    PedidoComboSaborPorcion.objects.bulk_create([
                        PedidoComboSaborPorcion(pedido_combo=nuevo_combo, sabor=s) for s in porcion_originales
                    ])

                nombre_combo_ticket = combo.nombre + (f" ({tamano.nombre})" if tamano else '')
                nuevas_lineas_ticket.append(f"1x {nombre_combo_ticket}")
                if linea_sabor:
                    nuevas_lineas_ticket.append(f"   - Pizza: {linea_sabor}")
                for idx, sabor_p in enumerate(porcion_originales, start=1):
                    nuevas_lineas_ticket.append(f"   - Porción {idx}: {sabor_p.nombre}")

                componentes = list(combo.componentes.all())
                for comp in componentes:
                    if comp.tipo == 'alitas' and alitas_originales:
                        detalle_alitas = ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas_originales)
                        nuevas_lineas_ticket.append(f"   - {comp.cantidad}x Alitas: {detalle_alitas}")
                    elif comp.tipo == 'bebida' and bebida_originales:
                        nuevas_lineas_ticket.append(f"   - {comp.cantidad}x Bebida: {', '.join(s.nombre for s in bebida_originales)}")
                    elif comp.tipo == 'michelada' and michelada_originales:
                        nuevas_lineas_ticket.append(f"   - {comp.cantidad}x Michelada: {', '.join(s.nombre for s in michelada_originales)}")
                    elif comp.tipo == 'porcion_pizza':
                        continue
                    else:
                        detalle = f" {comp.detalle}" if comp.detalle else ''
                        nuevas_lineas_ticket.append(f"   - {comp.cantidad}x {comp.get_tipo_display()}{detalle}")
                if original.observacion:
                    nuevas_lineas_ticket.append(f"   Obs: {original.observacion}")

                grupo_combo = f"{combo.nombre} {tamano.nombre}" if tamano else combo.nombre
                if linea_sabor:
                    ItemPreparacion.objects.create(
                        pedido=pedido, combo=nuevo_combo, cantidad=1, grupo=grupo_combo,
                        descripcion=f"Pizza {tamano.nombre} - {linea_sabor}",
                    )
                for idx, sabor_p in enumerate(porcion_originales, start=1):
                    etiqueta = f"Porción de pizza {idx} - {sabor_p.nombre}" if len(porcion_originales) > 1 else f"Porción de pizza - {sabor_p.nombre}"
                    ItemPreparacion.objects.create(
                        pedido=pedido, combo=nuevo_combo, cantidad=1, grupo=grupo_combo, descripcion=etiqueta,
                    )
                if alitas_originales:
                    detalle_alitas_item = ': ' + ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas_originales)
                    ItemPreparacion.objects.create(
                        pedido=pedido, combo=nuevo_combo, cantidad=1, grupo=grupo_combo,
                        descripcion=f"Alitas{detalle_alitas_item}",
                    )
                for idx, sabor_b in enumerate(bebida_originales, start=1):
                    etiqueta = f"Bebida {idx} - {sabor_b.nombre}" if len(bebida_originales) > 1 else f"Bebida: {sabor_b.nombre}"
                    ItemPreparacion.objects.create(
                        pedido=pedido, combo=nuevo_combo, cantidad=1, grupo=grupo_combo, descripcion=etiqueta,
                    )
                for idx, sabor_m in enumerate(michelada_originales, start=1):
                    etiqueta = f"Michelada {idx} - {sabor_m.nombre}" if len(michelada_originales) > 1 else f"Michelada: {sabor_m.nombre}"
                    ItemPreparacion.objects.create(
                        pedido=pedido, combo=nuevo_combo, cantidad=1, grupo=grupo_combo, descripcion=etiqueta,
                    )

            elif item.producto_simple_id:
                original = item.producto_simple
                nuevo_producto = PedidoProductoSimple.objects.create(
                    pedido=pedido, producto=original.producto, sabor_bebida=original.sabor_bebida, cantidad=1,
                    precio_unitario=original.precio_unitario, observacion=original.observacion,
                )
                alitas_originales_prod = list(original.sabores_alitas.select_related('sabor').all())
                if alitas_originales_prod:
                    PedidoProductoSimpleSaborAlitas.objects.bulk_create([
                        PedidoProductoSimpleSaborAlitas(pedido_producto=nuevo_producto, sabor=sa.sabor, cantidad=sa.cantidad)
                        for sa in alitas_originales_prod
                    ])
                    detalle_alitas_prod = ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas_originales_prod)
                    descripcion_producto = f"{original.producto.nombre}: {detalle_alitas_prod}"
                    nuevas_lineas_ticket.append(f"1x {original.producto.nombre}: {detalle_alitas_prod}")
                elif original.sabor_bebida:
                    descripcion_producto = f"{original.producto.nombre} - {original.sabor_bebida.nombre}"
                    nuevas_lineas_ticket.append(f"1x {original.producto.nombre} - {original.sabor_bebida.nombre}")
                else:
                    descripcion_producto = original.producto.nombre
                    nuevas_lineas_ticket.append(f"1x {original.producto.nombre}")
                if original.observacion:
                    nuevas_lineas_ticket.append(f"   Obs: {original.observacion}")

                ItemPreparacion.objects.create(
                    pedido=pedido, producto_simple=nuevo_producto, cantidad=1, descripcion=descripcion_producto,
                )
            else:
                return JsonResponse({'status': 'error', 'message': 'Este platillo no se puede duplicar'}, status=400)

            pedido.total = _calcular_total_pedido(pedido)
            pedido.save()

        _enviar_mensaje_websocket_pizzeria('pedido_pizzeria_actualizado', _serializar_pedido(pedido))

        if nuevas_lineas_ticket:
            comanda = generar_comanda_pizza(pedido, nuevas_lineas_ticket)
            _enviar_trabajo_impresion_pizzeria(pedido, comanda)

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def reimprimir_item_preparacion(request, item_id):
    try:
        item = get_object_or_404(ItemPreparacion, pk=item_id)
        pedido = item.pedido
        lineas_ticket = []

        if item.pizza_id:
            p = item.pizza
            linea_sabor = p.sabor_1.nombre if not p.sabor_2 else f"1/2 {p.sabor_1.nombre} / 1/2 {p.sabor_2.nombre}"
            lineas_ticket.append(f"{p.cantidad}x Pizza {p.tamano.nombre}")
            lineas_ticket.append(f"   - {linea_sabor}")
            if p.observacion:
                lineas_ticket.append(f"   Obs: {p.observacion}")

        elif item.combo_id:
            c = item.combo
            combo = c.combo
            nombre_combo_ticket = combo.nombre + (f" ({c.tamano.nombre})" if c.tamano else '')
            lineas_ticket.append(f"{c.cantidad}x {nombre_combo_ticket}")
            if c.sabor_1:
                linea_sabor = c.sabor_1.nombre if not c.sabor_2 else f"1/2 {c.sabor_1.nombre} / 1/2 {c.sabor_2.nombre}"
                lineas_ticket.append(f"   - Pizza: {linea_sabor}")
            porciones = list(c.sabores_porcion.select_related('sabor').all())
            for idx, sp in enumerate(porciones, start=1):
                lineas_ticket.append(f"   - Porción {idx}: {sp.sabor.nombre}")
            alitas = list(c.sabores_alitas.select_related('sabor').all())
            bebidas = list(c.sabores_bebida.select_related('sabor').all())
            micheladas = list(c.sabores_michelada.select_related('sabor').all())
            for comp in combo.componentes.all():
                if comp.tipo == 'alitas' and alitas:
                    detalle_alitas = ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas)
                    lineas_ticket.append(f"   - {comp.cantidad}x Alitas: {detalle_alitas}")
                elif comp.tipo == 'bebida' and bebidas:
                    lineas_ticket.append(f"   - {comp.cantidad}x Bebida: {', '.join(sb.sabor.nombre for sb in bebidas)}")
                elif comp.tipo == 'michelada' and micheladas:
                    lineas_ticket.append(f"   - {comp.cantidad}x Michelada: {', '.join(sm.sabor.nombre for sm in micheladas)}")
                elif comp.tipo == 'porcion_pizza':
                    continue
                else:
                    detalle = f" {comp.detalle}" if comp.detalle else ''
                    lineas_ticket.append(f"   - {comp.cantidad}x {comp.get_tipo_display()}{detalle}")
            if c.observacion:
                lineas_ticket.append(f"   Obs: {c.observacion}")

        elif item.producto_simple_id:
            ps = item.producto_simple
            alitas_prod = list(ps.sabores_alitas.select_related('sabor').all())
            if alitas_prod:
                detalle_alitas_prod = ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas_prod)
                lineas_ticket.append(f"{ps.cantidad}x {ps.producto.nombre}: {detalle_alitas_prod}")
            elif ps.sabor_bebida:
                lineas_ticket.append(f"{ps.cantidad}x {ps.producto.nombre} - {ps.sabor_bebida.nombre}")
            else:
                lineas_ticket.append(f"{ps.cantidad}x {ps.producto.nombre}")
            if ps.observacion:
                lineas_ticket.append(f"   Obs: {ps.observacion}")
        else:
            return JsonResponse({'status': 'error', 'message': 'Este platillo no se puede reimprimir'}, status=400)

        lineas_ticket.insert(0, "*** REIMPRESION DE PLATILLO ***")
        comanda = generar_comanda_pizza(pedido, lineas_ticket)
        _enviar_trabajo_impresion_pizzeria(pedido, comanda)

        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def quitar_item_preparacion(request, item_id):
    try:
        item = get_object_or_404(ItemPreparacion, pk=item_id)
        linea = item.linea
        if linea is None:
            return JsonResponse({'status': 'error', 'message': 'Este platillo no se puede quitar'}, status=400)

        if any(h.estado != 'en_proceso' for h in _hermanos_item_preparacion(item)):
            return JsonResponse(
                {'status': 'error', 'message': 'Ya se empezó a preparar este platillo, no se puede quitar'},
                status=400,
            )

        pedido = item.pedido
        with transaction.atomic():
            linea.delete()
            pedido.total = _calcular_total_pedido(pedido)
            pedido.save()

        _enviar_mensaje_websocket_pizzeria('pedido_pizzeria_actualizado', _serializar_pedido(pedido))

        return JsonResponse({'status': 'ok', 'total': float(pedido.total)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ===== VENTA RÁPIDA (NUEVA ORDEN) =====

@login_required(login_url=LOGIN_URL)
def nueva_orden(request):
    pedido_id_param = request.GET.get('pedido_id')
    pedido_abierto = None
    items_pedido_abierto = []
    if pedido_id_param:
        pedido_abierto = get_object_or_404(
            PedidoPizzeria.objects.select_related('mesa'), pk=pedido_id_param
        )
        items_pedido_abierto, _, _ = _construir_items_pedido(pedido_abierto)

    tamanos = list(TamanoPizza.objects.order_by('orden'))
    tamano_menor = tamanos[0] if tamanos else None
    sabores_pizza = list(Sabor.objects.filter(tipo='pizza').order_by('-es_premium', 'nombre'))
    sabores_alitas = list(Sabor.objects.filter(tipo='alitas').order_by('nombre'))
    sabores_bebida = list(Sabor.objects.filter(tipo='bebida').order_by('nombre'))
    sabores_michelada = list(Sabor.objects.filter(tipo='michelada').order_by('nombre'))
    combos = ComboPizzeria.objects.filter(activo=True).select_related('pizza_tamano_fijo').prefetch_related('tamanos__tamano', 'componentes')
    productos = ProductoSimple.objects.filter(activo=True).order_by('categoria', 'nombre')
    mesas_libres = list(Mesa.objects.filter(activa=True, estado='libre').order_by('numero'))

    mesa_preseleccionada_id = request.GET.get('mesa_id')
    if mesa_preseleccionada_id:
        mesa_preseleccionada = get_object_or_404(Mesa, pk=mesa_preseleccionada_id, activa=True)
        if mesa_preseleccionada not in mesas_libres:
            mesas_libres = [mesa_preseleccionada] + mesas_libres

    catalogo = {
        'mesas': [
            {'id': m.id, 'numero': m.numero, 'nombre': m.nombre}
            for m in mesas_libres
        ],
        'mesa_preseleccionada': int(mesa_preseleccionada_id) if mesa_preseleccionada_id else None,
        'tamanos': [
            {
                'id': t.id, 'nombre': t.nombre, 'precio_base': str(t.precio_base),
                'recargo_premium_completo': str(t.recargo_premium_completo),
                'recargo_premium_mitad': str(t.recargo_premium_mitad),
            }
            for t in tamanos
        ],
        'sabores': [
            {
                'id': s.id, 'nombre': s.nombre, 'es_premium': s.es_premium,
                'descripcion': s.descripcion,
                'precio_desde': str(tamano_menor.precio_base + (tamano_menor.recargo_premium_completo if s.es_premium else 0)) if tamano_menor else '0',
            }
            for s in sabores_pizza
        ],
        'sabores_alitas': [
            {'id': s.id, 'nombre': s.nombre, 'es_premium': s.es_premium}
            for s in sabores_alitas
        ],
        'sabores_bebida': [
            {'id': s.id, 'nombre': s.nombre}
            for s in sabores_bebida
        ],
        'sabores_michelada': [
            {'id': s.id, 'nombre': s.nombre}
            for s in sabores_michelada
        ],
        'combos': [_serializar_combo_catalogo(c) for c in combos],
        'productos': [
            {
                'id': p.id, 'nombre': p.nombre, 'categoria': p.categoria,
                'categoria_display': p.get_categoria_display(),
                'descripcion': p.descripcion, 'precio': str(p.precio),
                'es_porcion_individual': p.nombre.strip().lower() == 'porción individual',
                'alitas_cantidad': _alitas_cantidad_producto(p.nombre) if p.categoria == 'alitas' else 0,
                'tipo_sabor_bebida': _tipo_sabor_bebida_producto(p),
            }
            for p in productos
        ],
    }

    ultimo_pedido_hoy = (
        PedidoPizzeria.objects.filter(fecha_creacion__date=timezone.localdate())
        .order_by('-numero_dia')
        .first()
    )
    proximo_numero = (ultimo_pedido_hoy.numero_dia + 1) if ultimo_pedido_hoy else 1

    if pedido_abierto:
        breadcrumbs = [
            _lista_padre_pedido(pedido_abierto),
            {'label': f'Pedido #{pedido_abierto.numero_pedido_completo}', 'url': reverse('pizzeria_detalle_orden', args=[pedido_abierto.id])},
            {'label': 'Agregar', 'url': None},
        ]
    else:
        breadcrumbs = [{'label': 'Punto de venta', 'url': None}]

    return render(request, 'pizzeria/nueva_orden.html', {
        'catalogo_json': json.dumps(catalogo),
        'proximo_numero': proximo_numero,
        'pedido_abierto': pedido_abierto,
        'items_pedido_abierto': items_pedido_abierto,
        'breadcrumbs': breadcrumbs,
    })


# ===== TOMA DE PEDIDO =====

@login_required(login_url=LOGIN_URL)
def tomar_pedido_pizzeria(request, mesa_id=None):
    mesa = get_object_or_404(Mesa, pk=mesa_id) if mesa_id else None
    tipo = 'mesa' if mesa else 'llevar'

    pedido_id_param = request.GET.get('pedido_id')
    items_pedido_abierto = []
    if pedido_id_param:
        pedido_abierto = get_object_or_404(PedidoPizzeria, pk=pedido_id_param)
        items_pedido_abierto, _, _ = _construir_items_pedido(pedido_abierto)
    elif mesa:
        pedido_abierto = PedidoPizzeria.objects.filter(
            mesa=mesa, estado__in=['abierto', 'por_cobrar']
        ).first()
    else:
        pedido_abierto = None

    tamanos = list(TamanoPizza.objects.order_by('orden'))
    sabores_pizza = list(Sabor.objects.filter(tipo='pizza').order_by('-es_premium', 'nombre'))
    sabores_alitas = list(Sabor.objects.filter(tipo='alitas').order_by('nombre'))
    sabores_bebida = list(Sabor.objects.filter(tipo='bebida').order_by('nombre'))
    sabores_michelada = list(Sabor.objects.filter(tipo='michelada').order_by('nombre'))
    combos = ComboPizzeria.objects.filter(activo=True).select_related('pizza_tamano_fijo').prefetch_related('tamanos__tamano', 'componentes')
    productos = ProductoSimple.objects.filter(activo=True).order_by('categoria', 'nombre')

    catalogo = {
        'tamanos': [
            {'id': t.id, 'nombre': t.nombre, 'precio_base': str(t.precio_base)} for t in tamanos
        ],
        'sabores': [
            {'id': s.id, 'nombre': s.nombre, 'es_premium': s.es_premium} for s in sabores_pizza
        ],
        'sabores_alitas': [
            {'id': s.id, 'nombre': s.nombre, 'es_premium': s.es_premium} for s in sabores_alitas
        ],
        'sabores_bebida': [
            {'id': s.id, 'nombre': s.nombre} for s in sabores_bebida
        ],
        'sabores_michelada': [
            {'id': s.id, 'nombre': s.nombre} for s in sabores_michelada
        ],
        'combos': [_serializar_combo_catalogo(c) for c in combos],
        'productos': [
            {
                'id': p.id, 'nombre': p.nombre, 'categoria': p.get_categoria_display(),
                'precio': str(p.precio),
                'alitas_cantidad': _alitas_cantidad_producto(p.nombre) if p.categoria == 'alitas' else 0,
                'tipo_sabor_bebida': _tipo_sabor_bebida_producto(p),
            }
            for p in productos
        ],
    }

    if mesa:
        breadcrumbs = [
            {'label': 'Mesas', 'url': reverse('pizzeria_mapa_mesas')},
            {'label': f'Mesa {mesa.nombre or mesa.numero}', 'url': None},
        ]
    else:
        breadcrumbs = [{'label': 'Pedido para llevar', 'url': None}]

    return render(request, 'pizzeria/tomar_pedido_mobile.html', {
        'mesa': mesa,
        'tipo': tipo,
        'pedido_abierto': pedido_abierto,
        'items_pedido_abierto': items_pedido_abierto,
        'catalogo_json': json.dumps(catalogo),
        'breadcrumbs': breadcrumbs,
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
        contacto_directo = (request.POST.get('contacto') or '').strip()
        nombre = (request.POST.get('nombre') or '').strip()
        telefono = (request.POST.get('telefono') or '').strip()
        valor_moto_raw = (request.POST.get('valor_moto') or '').strip()
        observaciones = request.POST.get('observaciones', '')
        pedido_id = request.POST.get('pedido_id') or None
        carrito = json.loads(request.POST.get('carrito', '[]'))
        imprimir_pedido = request.POST.get('imprimir', 'true') != 'false'

        if not carrito:
            return JsonResponse({'status': 'error', 'message': 'El carrito está vacío'}, status=400)

        if not pedido_id:
            if tipo == 'mesa' and not mesa_id:
                return JsonResponse({'status': 'error', 'message': 'Selecciona el número de mesa'}, status=400)
            if tipo == 'delivery' and not telefono:
                return JsonResponse({'status': 'error', 'message': 'Ingresa el teléfono del cliente'}, status=400)

        if contacto_directo:
            # Compatibilidad con el flujo de toma de pedido desde tablet/móvil,
            # que envía un único campo "contacto" en vez de nombre/teléfono separados.
            contacto = contacto_directo
        elif tipo == 'delivery':
            contacto = f"{telefono} - {nombre}" if nombre else telefono
        else:
            contacto = nombre

        valor_moto = None
        if tipo == 'delivery' and valor_moto_raw:
            try:
                valor_moto = Decimal(valor_moto_raw)
            except Exception:
                valor_moto = None

        nuevos_items_ticket = []

        with transaction.atomic():
            if pedido_id:
                pedido = get_object_or_404(PedidoPizzeria, pk=pedido_id)
            else:
                mesa = None
                if tipo == 'mesa' and mesa_id:
                    mesa = get_object_or_404(Mesa.objects.select_for_update(), pk=mesa_id)
                    if PedidoPizzeria.objects.filter(mesa_id=mesa_id, estado__in=['abierto', 'por_cobrar']).exists():
                        return JsonResponse({'status': 'error', 'message': 'Esta mesa ya tiene un pedido abierto'}, status=400)
                pedido = PedidoPizzeria.objects.create(
                    tipo=tipo,
                    mesa=mesa,
                    contacto=contacto or None,
                    valor_moto=valor_moto,
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

                    pedido_pizza = PedidoPizza.objects.create(
                        pedido=pedido, tamano=tamano, sabor_1=sabor_1, sabor_2=sabor_2,
                        cantidad=cantidad, precio_unitario=precio_unitario, observacion=observacion_item,
                    )
                    linea_sabor = sabor_1.nombre if not sabor_2 else f"1/2 {sabor_1.nombre} / 1/2 {sabor_2.nombre}"
                    nuevos_items_ticket.append(f"{cantidad}x Pizza {tamano.nombre}")
                    nuevos_items_ticket.append(f"   - {linea_sabor}")
                    if observacion_item:
                        nuevos_items_ticket.append(f"   Obs: {observacion_item}")

                    ItemPreparacion.objects.create(
                        pedido=pedido, pizza=pedido_pizza,
                        descripcion=f"Pizza {tamano.nombre} - {linea_sabor}", cantidad=cantidad,
                    )

                elif kind == 'combo':
                    combo = ComboPizzeria.objects.get(pk=item['combo_id'])
                    componentes = list(combo.componentes.all())
                    tamanos_combo = list(combo.tamanos.all())

                    alitas_requeridas = _cantidad_componente(componentes, 'alitas')
                    bebida_requerida = _cantidad_componente(componentes, 'bebida')
                    michelada_requerida = _cantidad_componente(componentes, 'michelada')
                    porcion_requerida = _cantidad_componente(componentes, 'porcion_pizza')

                    tamano = None
                    sabor_1 = None
                    sabor_2 = None
                    linea_sabor = None

                    if tamanos_combo:
                        # Mega Combo: tamaño seleccionable, con pizza completa y precio por tamaño.
                        tamano = TamanoPizza.objects.get(pk=item['tamano_id'])
                        combo_tamano = ComboTamano.objects.get(combo=combo, tamano=tamano)
                        sabor_1 = Sabor.objects.get(pk=item['sabor_1_id'])
                        sabor_2_id = item.get('sabor_2_id')
                        sabor_2 = Sabor.objects.get(pk=sabor_2_id) if sabor_2_id else None
                        precio_unitario = calcular_precio_combo(combo_tamano, sabor_1, sabor_2)
                        linea_sabor = sabor_1.nombre if not sabor_2 else f"1/2 {sabor_1.nombre} / 1/2 {sabor_2.nombre}"
                    else:
                        precio_unitario = combo.precio_fijo or Decimal('0')
                        if combo.pizza_tamano_fijo_id:
                            # Combo de precio fijo con pizza completa de tamaño predeterminado (ej. Cumpleañero).
                            tamano = combo.pizza_tamano_fijo
                            sabor_1 = Sabor.objects.get(pk=item['sabor_1_id'])
                            sabor_2_id = item.get('sabor_2_id')
                            sabor_2 = Sabor.objects.get(pk=sabor_2_id) if sabor_2_id else None
                            precio_unitario += calcular_recargo_premium(tamano, sabor_1, sabor_2)
                            linea_sabor = sabor_1.nombre if not sabor_2 else f"1/2 {sabor_1.nombre} / 1/2 {sabor_2.nombre}"

                    alitas_sabores_data = item.get('alitas_sabores') or []
                    if alitas_requeridas > 0:
                        if not alitas_sabores_data or len(alitas_sabores_data) > 3:
                            raise ValueError(f'Selecciona entre 1 y 3 sabores de alitas para {combo.nombre}')
                        suma_alitas = sum(int(a.get('cantidad', 0)) for a in alitas_sabores_data)
                        if suma_alitas != alitas_requeridas:
                            raise ValueError(f'Las alitas de {combo.nombre} deben sumar {alitas_requeridas} unidades')

                    sabores_bebida_ids = item.get('sabores_bebida_ids') or []
                    if bebida_requerida > 0 and len(sabores_bebida_ids) != bebida_requerida:
                        raise ValueError(f'Selecciona el sabor de cada bebida para {combo.nombre}')

                    sabores_michelada_ids = item.get('sabores_michelada_ids') or []
                    if michelada_requerida > 0 and len(sabores_michelada_ids) != michelada_requerida:
                        raise ValueError(f'Selecciona el sabor de cada michelada para {combo.nombre}')

                    sabores_porcion_ids = item.get('sabores_porcion_ids') or []
                    if porcion_requerida > 0 and len(sabores_porcion_ids) != porcion_requerida:
                        raise ValueError(f'Selecciona el sabor de cada porción de pizza para {combo.nombre}')

                    porcion_sabores_objs = []
                    if porcion_requerida > 0:
                        tamano_ref_porcion = _tamano_referencia_porcion()
                        for sid in sabores_porcion_ids:
                            sabor_p = Sabor.objects.get(pk=sid, tipo='pizza')
                            porcion_sabores_objs.append(sabor_p)
                            precio_unitario += calcular_recargo_premium(tamano_ref_porcion, sabor_p)

                    pedido_combo = PedidoCombo.objects.create(
                        pedido=pedido, combo=combo, tamano=tamano, sabor_1=sabor_1, sabor_2=sabor_2,
                        cantidad=cantidad, precio_unitario=precio_unitario, observacion=observacion_item,
                    )

                    alitas_sabores_objs = []
                    if alitas_requeridas > 0:
                        for a in alitas_sabores_data:
                            sabor_alitas = Sabor.objects.get(pk=a['sabor_id'], tipo='alitas')
                            alitas_sabores_objs.append(
                                PedidoComboSaborAlitas(
                                    pedido_combo=pedido_combo, sabor=sabor_alitas, cantidad=int(a['cantidad']),
                                )
                            )
                        PedidoComboSaborAlitas.objects.bulk_create(alitas_sabores_objs)

                    bebida_sabores_objs = []
                    if bebida_requerida > 0:
                        for sid in sabores_bebida_ids:
                            bebida_sabores_objs.append(Sabor.objects.get(pk=sid, tipo='bebida'))
                        PedidoComboSaborBebida.objects.bulk_create([
                            PedidoComboSaborBebida(pedido_combo=pedido_combo, sabor=s) for s in bebida_sabores_objs
                        ])

                    michelada_sabores_objs = []
                    if michelada_requerida > 0:
                        for sid in sabores_michelada_ids:
                            michelada_sabores_objs.append(Sabor.objects.get(pk=sid, tipo='michelada'))
                        PedidoComboSaborMichelada.objects.bulk_create([
                            PedidoComboSaborMichelada(pedido_combo=pedido_combo, sabor=s) for s in michelada_sabores_objs
                        ])

                    if porcion_requerida > 0:
                        PedidoComboSaborPorcion.objects.bulk_create([
                            PedidoComboSaborPorcion(pedido_combo=pedido_combo, sabor=s) for s in porcion_sabores_objs
                        ])

                    nombre_combo_ticket = combo.nombre + (f" ({tamano.nombre})" if tamano else '')
                    nuevos_items_ticket.append(f"{cantidad}x {nombre_combo_ticket}")
                    if linea_sabor:
                        nuevos_items_ticket.append(f"   - Pizza: {linea_sabor}")
                    for idx, sabor_p in enumerate(porcion_sabores_objs, start=1):
                        nuevos_items_ticket.append(f"   - Porción {idx}: {sabor_p.nombre}")

                    for comp in componentes:
                        if comp.tipo == 'alitas' and alitas_sabores_objs:
                            detalle_alitas = ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas_sabores_objs)
                            nuevos_items_ticket.append(f"   - {comp.cantidad}x Alitas: {detalle_alitas}")
                        elif comp.tipo == 'bebida' and bebida_sabores_objs:
                            detalle_bebida = ', '.join(s.nombre for s in bebida_sabores_objs)
                            nuevos_items_ticket.append(f"   - {comp.cantidad}x Bebida: {detalle_bebida}")
                        elif comp.tipo == 'michelada' and michelada_sabores_objs:
                            detalle_michelada = ', '.join(s.nombre for s in michelada_sabores_objs)
                            nuevos_items_ticket.append(f"   - {comp.cantidad}x Michelada: {detalle_michelada}")
                        elif comp.tipo == 'porcion_pizza':
                            continue
                        else:
                            detalle = f" {comp.detalle}" if comp.detalle else ''
                            nuevos_items_ticket.append(f"   - {comp.cantidad}x {comp.get_tipo_display()}{detalle}")
                    if observacion_item:
                        nuevos_items_ticket.append(f"   Obs: {observacion_item}")

                    # Cada combo se agrupa bajo su nombre (+ tamaño, si tiene pizza completa) en la
                    # pantalla de cocina, con cada componente interactivo (pizza/porciones, alitas,
                    # bebidas, micheladas) como sub-ítems que se pueden marcar como listos por
                    # separado. El resto de componentes (papas, hamburguesa, postre, helado) no se
                    # rastrean individualmente, solo aparecen en el ticket impreso.
                    grupo_combo = f"{combo.nombre} {tamano.nombre}" if tamano else combo.nombre
                    if linea_sabor:
                        ItemPreparacion.objects.create(
                            pedido=pedido, combo=pedido_combo,
                            descripcion=f"Pizza {tamano.nombre} - {linea_sabor}", cantidad=cantidad,
                            grupo=grupo_combo,
                        )

                    for idx, sabor_p in enumerate(porcion_sabores_objs, start=1):
                        etiqueta = f"Porción de pizza {idx} - {sabor_p.nombre}" if porcion_requerida > 1 else f"Porción de pizza - {sabor_p.nombre}"
                        ItemPreparacion.objects.create(
                            pedido=pedido, combo=pedido_combo,
                            descripcion=etiqueta, cantidad=cantidad,
                            grupo=grupo_combo,
                        )

                    if alitas_requeridas > 0:
                        detalle_alitas_item = (
                            ': ' + ', '.join(f"{sa.cantidad} {sa.sabor.nombre}" for sa in alitas_sabores_objs)
                            if alitas_sabores_objs else ''
                        )
                        ItemPreparacion.objects.create(
                            pedido=pedido, combo=pedido_combo,
                            descripcion=f"Alitas{detalle_alitas_item}", cantidad=cantidad,
                            grupo=grupo_combo,
                        )

                    for idx, sabor_b in enumerate(bebida_sabores_objs, start=1):
                        etiqueta = f"Bebida {idx} - {sabor_b.nombre}" if bebida_requerida > 1 else f"Bebida: {sabor_b.nombre}"
                        ItemPreparacion.objects.create(
                            pedido=pedido, combo=pedido_combo,
                            descripcion=etiqueta, cantidad=cantidad,
                            grupo=grupo_combo,
                        )

                    for idx, sabor_m in enumerate(michelada_sabores_objs, start=1):
                        etiqueta = f"Michelada {idx} - {sabor_m.nombre}" if michelada_requerida > 1 else f"Michelada: {sabor_m.nombre}"
                        ItemPreparacion.objects.create(
                            pedido=pedido, combo=pedido_combo,
                            descripcion=etiqueta, cantidad=cantidad,
                            grupo=grupo_combo,
                        )

                elif kind == 'producto':
                    producto = ProductoSimple.objects.get(pk=item['producto_id'])

                    alitas_requeridas_prod = (
                        _alitas_cantidad_producto(producto.nombre) if producto.categoria == 'alitas' else 0
                    )
                    alitas_sabores_data_prod = item.get('alitas_sabores') or []
                    if alitas_requeridas_prod > 0:
                        if not alitas_sabores_data_prod or len(alitas_sabores_data_prod) > 3:
                            raise ValueError(f'Selecciona entre 1 y 3 sabores de alitas para {producto.nombre}')
                        suma_alitas_prod = sum(int(a.get('cantidad', 0)) for a in alitas_sabores_data_prod)
                        if suma_alitas_prod != alitas_requeridas_prod:
                            raise ValueError(f'Las alitas de {producto.nombre} deben sumar {alitas_requeridas_prod} unidades')

                    sabor_bebida_prod = None
                    tipo_sabor_bebida_prod = _tipo_sabor_bebida_producto(producto)
                    if tipo_sabor_bebida_prod:
                        sabor_bebida_prod_id = item.get('sabor_bebida_id')
                        if not sabor_bebida_prod_id:
                            raise ValueError(f'Selecciona el sabor de la bebida para {producto.nombre}')
                        sabor_bebida_prod = Sabor.objects.get(pk=sabor_bebida_prod_id, tipo=tipo_sabor_bebida_prod)

                    pedido_producto = PedidoProductoSimple.objects.create(
                        pedido=pedido, producto=producto, sabor_bebida=sabor_bebida_prod, cantidad=cantidad,
                        precio_unitario=producto.precio, observacion=observacion_item,
                    )

                    if alitas_requeridas_prod > 0:
                        alitas_prod_objs = [
                            PedidoProductoSimpleSaborAlitas(
                                pedido_producto=pedido_producto,
                                sabor=Sabor.objects.get(pk=a['sabor_id'], tipo='alitas'),
                                cantidad=int(a['cantidad']),
                            )
                            for a in alitas_sabores_data_prod
                        ]
                        PedidoProductoSimpleSaborAlitas.objects.bulk_create(alitas_prod_objs)
                        detalle_alitas_prod = ', '.join(f"{o.cantidad} {o.sabor.nombre}" for o in alitas_prod_objs)
                        descripcion_producto = f"{producto.nombre}: {detalle_alitas_prod}"
                        nuevos_items_ticket.append(f"{cantidad}x {producto.nombre}: {detalle_alitas_prod}")
                    elif sabor_bebida_prod:
                        descripcion_producto = f"{producto.nombre} - {sabor_bebida_prod.nombre}"
                        nuevos_items_ticket.append(f"{cantidad}x {producto.nombre} - {sabor_bebida_prod.nombre}")
                    else:
                        descripcion_producto = producto.nombre
                        nuevos_items_ticket.append(f"{cantidad}x {producto.nombre}")
                    if observacion_item:
                        nuevos_items_ticket.append(f"   Obs: {observacion_item}")

                    ItemPreparacion.objects.create(
                        pedido=pedido, producto_simple=pedido_producto,
                        descripcion=descripcion_producto, cantidad=cantidad,
                    )

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

        if imprimir_pedido and nuevos_items_ticket:
            comanda = generar_comanda_pizza(pedido, nuevos_items_ticket)
            _enviar_trabajo_impresion_pizzeria(pedido, comanda)

        return JsonResponse({'status': 'ok', 'pedido': _serializar_pedido(pedido)})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


METODOS_PAGO_VALIDOS = {'Efectivo', 'Transferencia', 'Tarjeta'}
TOLERANCIA_MONTO = Decimal('0.01')


def _caja_tarjeta(caja):
    """Devuelve el bucket de tarjeta de una caja, creándolo si la caja se
    abrió antes de que existiera este método de pago."""
    tarjeta = getattr(caja, 'caja_tarjeta', None)
    if tarjeta is None:
        tarjeta, _ = CajaPizzeriaTarjeta.objects.get_or_create(caja=caja, defaults={'monto_inicial': 0})
    return tarjeta


def _asegurar_caja_abierta_pizzeria():
    caja = CajaPizzeria.objects.filter(estado='abierta').first()
    if not caja:
        caja = CajaPizzeria.objects.create(fecha=date.today(), estado='abierta')
        CajaPizzeriaEfectivo.objects.create(caja=caja, monto_inicial=0)
        CajaPizzeriaTransferencia.objects.create(caja=caja, monto_inicial=0)
        CajaPizzeriaTarjeta.objects.create(caja=caja, monto_inicial=0)
    return caja


def _monto_decimal(valor):
    try:
        return Decimal(str(valor))
    except Exception:
        raise ValueError('Monto inválido')


def _validar_pagos(pagos_data, objetivo, etiqueta):
    """Valida una lista de {'metodo', 'monto'} y que sumen `objetivo`.
    Devuelve la lista normalizada [(metodo, monto), ...]."""
    if not pagos_data:
        raise ValueError(f'{etiqueta}: debes registrar al menos un pago')

    pagos = []
    total = Decimal('0.00')
    for p in pagos_data:
        metodo = p.get('metodo')
        if metodo not in METODOS_PAGO_VALIDOS:
            raise ValueError(f'{etiqueta}: método de pago inválido')
        monto = _monto_decimal(p.get('monto'))
        if monto <= 0:
            raise ValueError(f'{etiqueta}: el monto debe ser mayor a cero')
        pagos.append((metodo, monto))
        total += monto

    if abs(total - objetivo) > TOLERANCIA_MONTO:
        raise ValueError(f'{etiqueta}: los pagos (${total}) no coinciden con lo que corresponde pagar (${objetivo})')

    return pagos


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def procesar_cobro_pedido(request, pedido_id):
    pedido = get_object_or_404(PedidoPizzeria, pk=pedido_id)
    if pedido.estado == 'cobrado':
        return JsonResponse({'status': 'error', 'message': 'El pedido ya fue cobrado'}, status=400)
    if pedido.estado == 'anulado':
        return JsonResponse({'status': 'error', 'message': 'El pedido está anulado'}, status=400)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Datos inválidos'}, status=400)

    items_map = {}
    for p in pedido.pizzas.all():
        items_map[('pizza', p.id)] = p
    for c in pedido.combos.all():
        items_map[('combo', c.id)] = c
    for ps in pedido.productos_simples.all():
        items_map[('producto_simple', ps.id)] = ps

    campo_fk = {'pizza': 'pizza', 'combo': 'combo', 'producto_simple': 'producto_simple'}

    try:
        with transaction.atomic():
            pagos_a_crear = []  # [(persona_o_None, metodo, monto)]

            if data.get('dividir'):
                personas_data = data.get('personas') or []
                if len(personas_data) < 2:
                    raise ValueError('Se necesitan al menos 2 personas para dividir la cuenta')

                asignado_acumulado = {}
                for idx, pdata in enumerate(personas_data, start=1):
                    nombre = (pdata.get('nombre') or f'Persona {idx}').strip()[:50] or f'Persona {idx}'
                    asignaciones = pdata.get('asignaciones') or []
                    if not asignaciones:
                        raise ValueError(f'{nombre}: debes asignarle al menos un producto')

                    persona = PersonaCobro.objects.create(pedido=pedido, nombre=nombre, orden=idx)
                    subtotal_persona = Decimal('0.00')

                    for a in asignaciones:
                        clave = (a.get('tipo'), a.get('id'))
                        try:
                            cantidad = int(a.get('cantidad') or 0)
                        except (TypeError, ValueError):
                            cantidad = 0
                        item = items_map.get(clave)
                        if not item or cantidad <= 0:
                            raise ValueError(f'{nombre}: producto asignado inválido')

                        asignado_acumulado[clave] = asignado_acumulado.get(clave, 0) + cantidad
                        if asignado_acumulado[clave] > item.cantidad:
                            raise ValueError(f'"{item}" fue asignado más veces de las que hay en el pedido')

                        subtotal_persona += item.precio_unitario * cantidad
                        AsignacionItemCobro.objects.create(
                            persona=persona, cantidad=cantidad, **{campo_fk[clave[0]]: item},
                        )

                    pagos_persona = _validar_pagos(pdata.get('pagos'), subtotal_persona, nombre)
                    for metodo, monto in pagos_persona:
                        pagos_a_crear.append((persona, metodo, monto))

                for clave, item in items_map.items():
                    if asignado_acumulado.get(clave, 0) != item.cantidad:
                        raise ValueError(f'"{item}" quedó sin asignar por completo a ninguna persona')

            else:
                pagos = _validar_pagos(data.get('pagos'), pedido.total, 'Pedido')
                for metodo, monto in pagos:
                    pagos_a_crear.append((None, metodo, monto))

            caja = _asegurar_caja_abierta_pizzeria()
            totales_metodo = {'Efectivo': Decimal('0.00'), 'Transferencia': Decimal('0.00'), 'Tarjeta': Decimal('0.00')}
            for persona, metodo, monto in pagos_a_crear:
                PagoPedido.objects.create(pedido=pedido, persona=persona, metodo=metodo, monto=monto)
                totales_metodo[metodo] += monto

            caja.caja_efectivo.total_ventas += totales_metodo['Efectivo']
            caja.caja_efectivo.save()
            caja.caja_transferencia.total_ventas += totales_metodo['Transferencia']
            caja.caja_transferencia.save()
            caja_tarjeta = _caja_tarjeta(caja)
            caja_tarjeta.total_ventas += totales_metodo['Tarjeta']
            caja_tarjeta.save()

            metodos_usados = {metodo for _, metodo, _ in pagos_a_crear}
            pedido.forma_pago = metodos_usados.pop() if (not data.get('dividir') and len(metodos_usados) == 1) else None
            pedido.estado = 'cobrado'
            pedido.save()

            if pedido.mesa:
                pedido.mesa.estado = 'libre'
                pedido.mesa.save()

    except ValueError as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    if pedido.mesa:
        _enviar_mensaje_websocket_pizzeria('mesa_actualizada', {
            'mesa_id': pedido.mesa.id, 'estado': 'libre', 'pedido_id': None,
        })
    _enviar_mensaje_websocket_pizzeria('pedido_pizzeria_actualizado', _serializar_pedido(pedido))

    return JsonResponse({'status': 'ok', 'pedido': _serializar_pedido(pedido)})


@csrf_exempt
@require_http_methods(["POST"])
@login_required(login_url=LOGIN_URL)
def cancelar_pedido_pizzeria(request, pedido_id):
    pedido = get_object_or_404(PedidoPizzeria, pk=pedido_id)
    if pedido.estado == 'cobrado':
        return JsonResponse({'status': 'error', 'message': 'El pedido ya fue cobrado, no se puede cancelar'}, status=400)
    if pedido.estado == 'anulado':
        return JsonResponse({'status': 'error', 'message': 'El pedido ya está anulado'}, status=400)

    with transaction.atomic():
        pedido.estado = 'anulado'
        pedido.save()

        if pedido.mesa:
            pedido.mesa.estado = 'libre'
            pedido.mesa.save()

    if pedido.mesa:
        _enviar_mensaje_websocket_pizzeria('mesa_actualizada', {
            'mesa_id': pedido.mesa.id, 'estado': 'libre', 'pedido_id': None,
        })
    _enviar_mensaje_websocket_pizzeria('pedido_pizzeria_actualizado', _serializar_pedido(pedido))

    return JsonResponse({'status': 'ok'})


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
            'id': c.id, 'combo': c.combo.nombre,
            'tamano': c.tamano.nombre if c.tamano else None,
            'sabor_1': c.sabor_1.nombre if c.sabor_1 else None,
            'sabor_2': c.sabor_2.nombre if c.sabor_2 else None, 'cantidad': c.cantidad,
            'precio_unitario': float(c.precio_unitario), 'observacion': c.observacion,
            'sabores_porcion': [sp.sabor.nombre for sp in c.sabores_porcion.all()],
            'sabores_bebida': [sb.sabor.nombre for sb in c.sabores_bebida.all()],
            'sabores_michelada': [sm.sabor.nombre for sm in c.sabores_michelada.all()],
            'sabores_alitas': [
                {'sabor': sa.sabor.nombre, 'cantidad': sa.cantidad} for sa in c.sabores_alitas.all()
            ],
        }
        for c in pedido.combos.select_related('combo', 'tamano', 'sabor_1', 'sabor_2').prefetch_related(
            'sabores_alitas__sabor', 'sabores_bebida__sabor', 'sabores_michelada__sabor', 'sabores_porcion__sabor',
        ).all()
    ]
    data['productos_simples'] = [
        {
            'id': ps.id, 'producto': ps.producto.nombre, 'cantidad': ps.cantidad,
            'precio_unitario': float(ps.precio_unitario), 'observacion': ps.observacion,
            'sabor_bebida': ps.sabor_bebida.nombre if ps.sabor_bebida_id else None,
            'sabores_alitas': [
                {'sabor': sa.sabor.nombre, 'cantidad': sa.cantidad} for sa in ps.sabores_alitas.all()
            ],
        }
        for ps in pedido.productos_simples.select_related('producto', 'sabor_bebida').prefetch_related('sabores_alitas__sabor').all()
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
        total_efectivo = total_transferencia = total_tarjeta = Decimal('0')
        monto_inicial_efectivo = monto_inicial_transferencia = monto_inicial_tarjeta = Decimal('0')
        gastos = GastoPizzeria.objects.none()
    else:
        pedidos_cobrados = PedidoPizzeria.objects.filter(
            estado='cobrado', fecha_creacion__gte=caja_abierta.fecha_apertura
        ).order_by('-fecha_creacion')
        totales = {
            row['metodo']: row['total'] for row in PagoPedido.objects.filter(
                pedido__estado='cobrado', creado_en__gte=caja_abierta.fecha_apertura,
            ).values('metodo').annotate(total=Sum('monto'))
        }
        total_efectivo = totales.get('Efectivo', Decimal('0'))
        total_transferencia = totales.get('Transferencia', Decimal('0'))
        total_tarjeta = totales.get('Tarjeta', Decimal('0'))
        monto_inicial_efectivo = caja_abierta.caja_efectivo.monto_inicial
        monto_inicial_transferencia = caja_abierta.caja_transferencia.monto_inicial
        monto_inicial_tarjeta = _caja_tarjeta(caja_abierta).monto_inicial
        gastos = caja_abierta.gastos.all()

    total_ventas = total_efectivo + total_transferencia + total_tarjeta
    total_gastos = sum((g.monto for g in gastos), Decimal('0'))

    return render(request, 'pizzeria/caja_pizzeria.html', {
        'caja_hoy': caja_abierta,
        'pedidos_cobrados': pedidos_cobrados,
        'gastos': gastos,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_tarjeta': total_tarjeta,
        'total_ventas': total_ventas,
        'total_gastos': total_gastos,
        'balance_neto': total_ventas - total_gastos,
        'monto_inicial_efectivo': monto_inicial_efectivo,
        'monto_inicial_transferencia': monto_inicial_transferencia,
        'monto_inicial_tarjeta': monto_inicial_tarjeta,
        'breadcrumbs': [{'label': 'Caja', 'url': None}],
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
        monto_inicial_tarjeta = float(request.POST.get('monto_inicial_tarjeta', 0))
        observaciones = request.POST.get('observaciones', '')

        caja = CajaPizzeria.objects.create(fecha=date.today(), estado='abierta', observaciones=observaciones)
        CajaPizzeriaEfectivo.objects.create(caja=caja, monto_inicial=monto_inicial_efectivo)
        CajaPizzeriaTransferencia.objects.create(caja=caja, monto_inicial=monto_inicial_transferencia)
        CajaPizzeriaTarjeta.objects.create(caja=caja, monto_inicial=monto_inicial_tarjeta)

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
        monto_final_tarjeta = float(request.POST.get('monto_final_tarjeta') or 0)
        observaciones_cierre = request.POST.get('observaciones_cierre', '')

        caja_abierta.caja_efectivo.monto_final = monto_final_efectivo
        caja_abierta.caja_efectivo.save()
        caja_abierta.caja_transferencia.monto_final = monto_final_transferencia
        caja_abierta.caja_transferencia.save()
        caja_tarjeta = _caja_tarjeta(caja_abierta)
        caja_tarjeta.monto_final = monto_final_tarjeta
        caja_tarjeta.save()

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
        'valor_moto': float(pedido.valor_moto) if pedido.valor_moto is not None else None,
        'mesero': pedido.mesero.get_username(),
        'estado': pedido.estado,
        'forma_pago': pedido.forma_pago,
        'forma_pago_resumen': pedido.resumen_forma_pago,
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
