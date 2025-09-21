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
    
    # Obtener caja del día actual
    try:
        caja_hoy = CajaDiaria.objects.get(fecha=hoy)
    except CajaDiaria.DoesNotExist:
        caja_hoy = None
    
    # Obtener pedidos del día ordenados por fecha de creación (más recientes primero)
    pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=hoy).order_by('-fecha_creacion')
    
    # Obtener totales desde los modelos de caja si existe, sino calcular desde pedidos
    if caja_hoy:
        total_efectivo = caja_hoy.caja_efectivo.total_ventas
        total_transferencia = caja_hoy.caja_transferencia.total_ventas
        monto_inicial_efectivo = caja_hoy.caja_efectivo.monto_inicial
        monto_inicial_transferencia = caja_hoy.caja_transferencia.monto_inicial
        monto_final_efectivo = caja_hoy.caja_efectivo.monto_final
        monto_final_transferencia = caja_hoy.caja_transferencia.monto_final
    else:
        # Si no hay caja, calcular desde pedidos
        total_efectivo = sum(p.total for p in pedidos_hoy if p.forma_pago == 'Efectivo')
        total_transferencia = sum(p.total for p in pedidos_hoy if p.forma_pago == 'Transferencia')
        monto_inicial_efectivo = 0
        monto_inicial_transferencia = 0
        monto_final_efectivo = 0
        monto_final_transferencia = 0
    
    # Obtener gastos del día si existe caja
    gastos_hoy = []
    if caja_hoy:
        gastos_hoy = caja_hoy.gastos.all()
    
    # Contar pedidos por forma de pago
    pedidos_efectivo = pedidos_hoy.filter(forma_pago='Efectivo').count()
    pedidos_transferencia = pedidos_hoy.filter(forma_pago='Transferencia').count()
    
    # Análisis de productos vendidos del día
    productos_vendidos = defaultdict(lambda: {'cantidad': 0, 'total_ventas': 0, 'tipo': ''})
    
    # Obtener menú del día
    try:
        menu_hoy = MenuDia.objects.get(fecha=hoy)
    except MenuDia.DoesNotExist:
        menu_hoy = None
    
    if menu_hoy:
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
        
        # Obtener pedidos del día
        pedidos_dia = Pedido.objects.filter(fecha_creacion__date=fecha_dia)
        
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
        'caja_hoy': caja_hoy,
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
    
    # Verificar si ya existe caja abierta
    
    if CajaDiaria.objects.filter(fecha=hoy).exists():
        return JsonResponse({
            'success': False,
            'message': 'Ya existe una caja abierta para hoy'
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
        # Obtener caja del día
        caja = get_object_or_404(CajaDiaria, fecha=hoy, estado='abierta')
        
        # Obtener datos del formulario
        monto_final_efectivo = float(request.POST.get('monto_final_efectivo', 0))
        monto_final_transferencia = float(request.POST.get('monto_final_transferencia', 0))
        observaciones_cierre = request.POST.get('observaciones_cierre', '')
        
        # Calcular totales de ventas del día
        pedidos_hoy = Pedido.objects.filter(fecha_creacion__date=hoy)
        total_efectivo = sum(p.total for p in pedidos_hoy if p.forma_pago == 'Efectivo')
        total_transferencia = sum(p.total for p in pedidos_hoy if p.forma_pago == 'Transferencia')
        
        # Actualizar caja efectivo
        caja_efectivo = caja.caja_efectivo
        caja_efectivo.monto_final = monto_final_efectivo
        caja_efectivo.total_ventas = total_efectivo
        caja_efectivo.save()
        
        # Actualizar caja transferencia
        caja_transferencia = caja.caja_transferencia
        caja_transferencia.monto_final = monto_final_transferencia
        caja_transferencia.total_ventas = total_transferencia
        caja_transferencia.save()
        
        # Cerrar caja
        caja.estado = 'cerrada'
        caja.fecha_cierre = timezone.now()
        if observaciones_cierre:
            caja.observaciones += f"\nCierre: {observaciones_cierre}"
        caja.save()
        
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
