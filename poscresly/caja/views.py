from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date
from .models import CajaDiaria, CajaEfectivo, CajaTransferencia, Gasto
from pedidos.models import Pedido, PedidoAlmuerzo, PedidoSopa, PedidoSegundo
from menu.models import MenuDia
from collections import defaultdict

def dashboard_caja(request):
    """Vista principal de caja - Dashboard"""
    hoy = date.today()
    
    # Obtener la caja abierta actual (cualquier fecha) o la última caja del día
    caja_abierta = CajaDiaria.objects.filter(estado='abierta').first()
    caja_hoy = CajaDiaria.objects.filter(fecha=hoy).order_by('-fecha_apertura').first()
    
    # Solo usar datos si hay caja abierta; si está cerrada, mostrar ceros
    caja_actual = caja_abierta if caja_abierta else None
    
    # Si NO hay caja abierta, mostrar todo en ceros
    if not caja_actual:
        pedidos_hoy = Pedido.objects.none()
        total_efectivo = 0
        total_transferencia = 0
        pedidos_efectivo = 0
        pedidos_transferencia = 0
    else:
        # Solo calcular si hay caja abierta
        # Obtener pedidos completados DESDE QUE SE ABRIÓ LA CAJA (no todo el día)
        pedidos_hoy = Pedido.objects.filter(
            fecha_creacion__gte=caja_actual.fecha_apertura,
            estado='completado'
        ).order_by('-fecha_creacion')
        
        # Calcular totales REALES desde los pedidos completados del día
        total_efectivo = 0
        total_transferencia = 0
        pedidos_efectivo = 0
        pedidos_transferencia = 0
        
        for pedido in pedidos_hoy:
            # Calcular el total del pedido sumando todos sus items
            total_pedido = 0
            
            # Sumar almuerzos
            for almuerzo in pedido.almuerzos.all():
                total_pedido += almuerzo.precio_unitario * almuerzo.cantidad
            
            # Sumar sopas
            for sopa in pedido.sopas.all():
                total_pedido += sopa.precio_unitario * sopa.cantidad
            
            # Sumar segundos
            for segundo in pedido.segundos.all():
                total_pedido += segundo.precio_unitario * segundo.cantidad
            
            # Agregar al total según forma de pago
            if pedido.forma_pago == 'Efectivo':
                total_efectivo += total_pedido
                pedidos_efectivo += 1
            elif pedido.forma_pago == 'Transferencia':
                total_transferencia += total_pedido
                pedidos_transferencia += 1
    
    # Obtener montos iniciales y finales de la caja si existe
    if caja_actual:
        monto_inicial_efectivo = caja_actual.caja_efectivo.monto_inicial
        monto_inicial_transferencia = caja_actual.caja_transferencia.monto_inicial
        monto_final_efectivo = caja_actual.caja_efectivo.monto_final
        monto_final_transferencia = caja_actual.caja_transferencia.monto_final
    else:
        # Si no hay caja abierta, mostrar ceros
        monto_inicial_efectivo = 0
        monto_inicial_transferencia = 0
        monto_final_efectivo = 0
        monto_final_transferencia = 0
    
    # Obtener gastos del día si existe caja
    gastos_hoy = []
    if caja_actual:
        gastos_hoy = caja_actual.gastos.all()
    
    # Total de pedidos
    total_pedidos_caja = pedidos_efectivo + pedidos_transferencia
    
    # Análisis de productos vendidos del día (solo si hay caja abierta)
    productos_vendidos = defaultdict(lambda: {'cantidad': 0, 'total_ventas': 0, 'tipo': ''})
    
    # Obtener menú del día
    try:
        menu_hoy = MenuDia.objects.get(fecha=hoy)
    except MenuDia.DoesNotExist:
        menu_hoy = None
    
    # Solo analizar productos si hay caja abierta
    if caja_actual and menu_hoy:
        # Analizar almuerzos vendidos
        for pedido in pedidos_hoy:
            for almuerzo in pedido.almuerzos.all():
                sopa_nombre = almuerzo.sopa.sopa.nombre_plato
                segundo_nombre = almuerzo.segundo.segundo.nombre_plato
                
                # Contar sopa
                productos_vendidos[sopa_nombre]['cantidad'] += almuerzo.cantidad
                productos_vendidos[sopa_nombre]['total_ventas'] += almuerzo.precio_unitario * almuerzo.cantidad
                productos_vendidos[sopa_nombre]['tipo'] = 'Sopa'
                
                # Contar segundo
                productos_vendidos[segundo_nombre]['cantidad'] += almuerzo.cantidad
                productos_vendidos[segundo_nombre]['total_ventas'] += almuerzo.precio_unitario * almuerzo.cantidad
                productos_vendidos[segundo_nombre]['tipo'] = 'Segundo'
            
            # Analizar sopas vendidas individualmente
            for sopa in pedido.sopas.all():
                sopa_nombre = sopa.sopa.sopa.nombre_plato
                productos_vendidos[sopa_nombre]['cantidad'] += sopa.cantidad
                productos_vendidos[sopa_nombre]['total_ventas'] += sopa.precio_unitario * sopa.cantidad
                productos_vendidos[sopa_nombre]['tipo'] = 'Sopa'
            
            # Analizar segundos vendidos individualmente
            for segundo in pedido.segundos.all():
                segundo_nombre = segundo.segundo.segundo.nombre_plato
                productos_vendidos[segundo_nombre]['cantidad'] += segundo.cantidad
                productos_vendidos[segundo_nombre]['total_ventas'] += segundo.precio_unitario * segundo.cantidad
                productos_vendidos[segundo_nombre]['tipo'] = 'Segundo'
    
    # Convertir a lista ordenada por cantidad vendida
    productos_ordenados = sorted(
        productos_vendidos.items(), 
        key=lambda x: x[1]['cantidad'], 
        reverse=True
    )
    
    # Obtener datos semanales para el gráfico (lunes a viernes)
    from datetime import timedelta
    datos_semana = []
    dias_semana = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie']
    
    # Calcular el lunes de esta semana
    hoy_weekday = hoy.weekday()  # 0=lunes, 6=domingo
    lunes_semana = hoy - timedelta(days=hoy_weekday)
    
    for i in range(5):  # Lunes a viernes
        fecha_dia = lunes_semana + timedelta(days=i)
        
        # Si es hoy y no hay caja abierta, mostrar ceros
        if fecha_dia == hoy and not caja_actual:
            datos_semana.append({
                'dia': dias_semana[i],
                'ventas': 0,
                'pedidos': 0
            })
        else:
            # Obtener pedidos del día (SOLO COMPLETADOS)
            pedidos_dia = Pedido.objects.filter(fecha_creacion__date=fecha_dia, estado='completado')
            
            # Calcular ventas del día
            ventas_dia = 0
            for pedido in pedidos_dia:
                for almuerzo in pedido.almuerzos.all():
                    ventas_dia += almuerzo.precio_unitario * almuerzo.cantidad
                for sopa in pedido.sopas.all():
                    ventas_dia += sopa.precio_unitario * sopa.cantidad
                for segundo in pedido.segundos.all():
                    ventas_dia += segundo.precio_unitario * segundo.cantidad
            
            datos_semana.append({
                'dia': dias_semana[i],
                'ventas': round(ventas_dia, 2),
                'pedidos': pedidos_dia.count()
            })
       
    context = {
        'caja_hoy': caja_actual,  # Caja actual (abierta o última del día)
        'caja_abierta': caja_abierta,  # Caja abierta (si existe)
        'pedidos_hoy': pedidos_hoy,
        'gastos_hoy': gastos_hoy,
        'total_efectivo': total_efectivo,
        'total_transferencia': total_transferencia,
        'total_ventas': total_efectivo + total_transferencia,
        'total_gastos': sum(g.monto for g in gastos_hoy),
        'monto_inicial_efectivo': monto_inicial_efectivo,
        'monto_inicial_transferencia': monto_inicial_transferencia,
        'monto_final_efectivo': monto_final_efectivo,
        'monto_final_transferencia': monto_final_transferencia,
        'pedidos_efectivo': pedidos_efectivo,
        'pedidos_transferencia': pedidos_transferencia,
        'total_pedidos_caja': total_pedidos_caja,
        'productos_vendidos': productos_ordenados,
        'menu_hoy': menu_hoy,
        'datos_semana': datos_semana,
    }
    
    return render(request, 'caja/caja.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def abrir_caja(request):
    """Abrir caja del día"""
    hoy = date.today()
    
    # Verificar si ya existe una caja abierta (cualquier fecha)
    if CajaDiaria.objects.filter(estado='abierta').exists():
        return JsonResponse({
            'success': False,
            'message': 'Ya existe una caja abierta. Debe cerrar la caja actual antes de abrir una nueva.'
        })
    
    try:
        # Obtener datos del formulario
        monto_inicial_efectivo = float(request.POST.get('monto_inicial_efectivo', 0))
        monto_inicial_transferencia = float(request.POST.get('monto_inicial_transferencia', 0))
        observaciones = request.POST.get('observaciones', '')
        
        # Crear caja diaria
        caja = CajaDiaria.objects.create(
            fecha=hoy,
            estado='abierta',
            observaciones=observaciones
        )
        
        # Crear caja efectivo
        CajaEfectivo.objects.create(
            caja_diaria=caja,
            monto_inicial=monto_inicial_efectivo
        )
        
        # Crear caja transferencia
        CajaTransferencia.objects.create(
            caja_diaria=caja,
            monto_inicial=monto_inicial_transferencia
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Caja abierta exitosamente',
            'caja_id': caja.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al abrir caja: {str(e)}'
        })

@csrf_exempt
@require_http_methods(["POST"])
def cerrar_caja(request):
    """Cerrar caja del día"""
    hoy = date.today()
    
    try:
        # Obtener la caja abierta actual (cualquier fecha)
        caja_abierta = CajaDiaria.objects.filter(estado='abierta').first()
        
        if not caja_abierta:
            return JsonResponse({
                'success': False,
                'message': 'No hay caja abierta para cerrar'
            })
        
        # Obtener datos del formulario
        monto_final_efectivo_str = request.POST.get('monto_final_efectivo', '0')
        monto_final_transferencia_str = request.POST.get('monto_final_transferencia', '0')
        
        # Convertir a float, manejando cadenas vacías
        monto_final_efectivo = float(monto_final_efectivo_str) if monto_final_efectivo_str else 0
        monto_final_transferencia = float(monto_final_transferencia_str) if monto_final_transferencia_str else 0
        observaciones_cierre = request.POST.get('observaciones_cierre', '')
        
        # Calcular totales de ventas del día (SOLO PEDIDOS COMPLETADOS)
        pedidos_caja = Pedido.objects.filter(
            fecha_creacion__date=caja_abierta.fecha,
            estado='completado'
        )
        
        # Calcular totales reales sumando los items de cada pedido
        total_efectivo = 0
        total_transferencia = 0
        
        for pedido in pedidos_caja:
            total_pedido = 0
            
            # Sumar almuerzos
            for almuerzo in pedido.almuerzos.all():
                total_pedido += almuerzo.precio_unitario * almuerzo.cantidad
            
            # Sumar sopas
            for sopa in pedido.sopas.all():
                total_pedido += sopa.precio_unitario * sopa.cantidad
            
            # Sumar segundos
            for segundo in pedido.segundos.all():
                total_pedido += segundo.precio_unitario * segundo.cantidad
            
            # Agregar al total según forma de pago
            if pedido.forma_pago == 'Efectivo':
                total_efectivo += total_pedido
            elif pedido.forma_pago == 'Transferencia':
                total_transferencia += total_pedido
        
        # Actualizar caja efectivo
        caja_efectivo = caja_abierta.caja_efectivo
        caja_efectivo.monto_final = monto_final_efectivo
        caja_efectivo.total_ventas = total_efectivo
        caja_efectivo.save()
        
        # Actualizar caja transferencia
        caja_transferencia = caja_abierta.caja_transferencia
        caja_transferencia.monto_final = monto_final_transferencia
        caja_transferencia.total_ventas = total_transferencia
        caja_transferencia.save()
        
        # Cerrar caja
        caja_abierta.estado = 'cerrada'
        caja_abierta.fecha_cierre = timezone.now()
        if observaciones_cierre:
            caja_abierta.observaciones += f"\nCierre: {observaciones_cierre}"
        caja_abierta.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Caja cerrada exitosamente',
            'resumen': {
                'total_efectivo': total_efectivo,
                'total_transferencia': total_transferencia,
                'total_ventas': total_efectivo + total_transferencia
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cerrar caja: {str(e)}'
        })
