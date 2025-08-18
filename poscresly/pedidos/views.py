from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import date
from decimal import Decimal
from .models import Pedido, CajaDiaria, PedidoAlmuerzo, PedidoSopa, PedidoSegundo

# ===== FUNCIONES AUXILIARES =====

def calcular_precio_producto(tipo):
    """Calcula el precio unitario de un producto según su tipo"""
    from menu.models import Producto
    
    producto = Producto.objects.get(nombre_producto__iexact=tipo)
    return Decimal(str(producto.precio_servirse))

def convertir_producto_a_dict(producto_obj, tipo):
    """Convierte un objeto de producto de BD a diccionario JSON"""
    if tipo == 'Almuerzo':
        return {
            'tipo': 'Almuerzo',
            'sopa_id': producto_obj.sopa.id,
            'segundo_id': producto_obj.segundo.id,
            'jugo_id': producto_obj.jugo.id,
            'cantidad': producto_obj.cantidad,
            'precio_unitario': float(producto_obj.precio_unitario),
            'observacion': producto_obj.observacion or '',
            'componentes': [
                producto_obj.sopa.sopa.nombre_plato,
                producto_obj.segundo.segundo.nombre_plato,
                producto_obj.jugo.jugo.nombre_plato
            ]
        }
    elif tipo == 'Sopa':
        return {
            'tipo': 'Sopa',
            'sopa_id': producto_obj.sopa.id,
            'jugo_id': producto_obj.jugo.id,
            'cantidad': producto_obj.cantidad,
            'precio_unitario': float(producto_obj.precio_unitario),
            'observacion': producto_obj.observacion or '',
            'componentes': [
                producto_obj.sopa.sopa.nombre_plato,
                producto_obj.jugo.jugo.nombre_plato
            ]
        }
    elif tipo == 'Segundo':
        return {
            'tipo': 'Segundo',
            'segundo_id': producto_obj.segundo.id,
            'jugo_id': producto_obj.jugo.id,
            'cantidad': producto_obj.cantidad,
            'precio_unitario': float(producto_obj.precio_unitario),
            'observacion': producto_obj.observacion or '',
            'componentes': [
                producto_obj.segundo.segundo.nombre_plato,
                producto_obj.jugo.jugo.nombre_plato
            ]
        }
    return None

def obtener_productos_pedido(pedido):
    """Obtiene todos los productos de un pedido en formato JSON"""
    productos = []
    
    # Almuerzos
    for almuerzo in pedido.almuerzos.all():
        productos.append(convertir_producto_a_dict(almuerzo, 'Almuerzo'))
    
    # Sopas
    for sopa in pedido.sopas.all():
        productos.append(convertir_producto_a_dict(sopa, 'Sopa'))
    
    # Segundos
    for segundo in pedido.segundos.all():
        productos.append(convertir_producto_a_dict(segundo, 'Segundo'))
    
    return productos

def crear_producto_pedido(pedido, producto_data):
    """Crea un producto de pedido según su tipo"""
    from menu.models import MenuDiaSopa, MenuDiaSegundo, MenuDiaJugo
    
    tipo = producto_data['tipo']
    
    if tipo == 'Almuerzo':
        sopa_menu = MenuDiaSopa.objects.filter(sopa_id=producto_data['sopa_id']).first()
        segundo_menu = MenuDiaSegundo.objects.filter(segundo_id=producto_data['segundo_id']).first()
        jugo_menu = MenuDiaJugo.objects.filter(jugo_id=producto_data['jugo_id']).first()
        
        if sopa_menu and segundo_menu and jugo_menu:
            return PedidoAlmuerzo.objects.create(
                pedido=pedido,
                sopa=sopa_menu,
                segundo=segundo_menu,
                jugo=jugo_menu,
                cantidad=producto_data['cantidad'],
                precio_unitario=producto_data['precio_unitario'],
                observacion=producto_data.get('observacion', '')
            )
    
    elif tipo == 'Sopa':
        sopa_menu = MenuDiaSopa.objects.filter(sopa_id=producto_data['sopa_id']).first()
        jugo_menu = MenuDiaJugo.objects.filter(jugo_id=producto_data['jugo_id']).first()
        
        if sopa_menu and jugo_menu:
            return PedidoSopa.objects.create(
                pedido=pedido,
                sopa=sopa_menu,
                jugo=jugo_menu,
                cantidad=producto_data['cantidad'],
                precio_unitario=producto_data['precio_unitario'],
                observacion=producto_data.get('observacion', '')
            )
    
    elif tipo == 'Segundo':
        segundo_menu = MenuDiaSegundo.objects.filter(segundo_id=producto_data['segundo_id']).first()
        jugo_menu = MenuDiaJugo.objects.filter(jugo_id=producto_data['jugo_id']).first()
        
        if segundo_menu and jugo_menu:
            return PedidoSegundo.objects.create(
                pedido=pedido,
                segundo=segundo_menu,
                jugo=jugo_menu,
                cantidad=producto_data['cantidad'],
                precio_unitario=producto_data['precio_unitario'],
                observacion=producto_data.get('observacion', '')
            )
    
    return None

def generar_clave_producto(producto):
    """Genera una clave única para identificar un producto"""
    if producto['tipo'] == 'Almuerzo':
        return f"almuerzo_{producto['sopa_id']}_{producto['segundo_id']}_{producto['jugo_id']}"
    elif producto['tipo'] == 'Sopa':
        return f"sopa_{producto['sopa_id']}_{producto['jugo_id']}"
    elif producto['tipo'] == 'Segundo':
        return f"segundo_{producto['segundo_id']}_{producto['jugo_id']}"
    return None

def calcular_total_pedido(pedido):
    """Calcula el total de un pedido sumando todos sus productos"""
    total = Decimal('0.00')
    for almuerzo in pedido.almuerzos.all():
        total += Decimal(str(almuerzo.precio_unitario)) * Decimal(str(almuerzo.cantidad))
    for sopa in pedido.sopas.all():
        total += Decimal(str(sopa.precio_unitario)) * Decimal(str(sopa.cantidad))
    for segundo in pedido.segundos.all():
        total += Decimal(str(segundo.precio_unitario)) * Decimal(str(segundo.cantidad))
    return total

# ===== VISTAS PRINCIPALES =====

@csrf_exempt
@require_http_methods(["POST"])
def agregar_al_carrito(request):
    try:
        tipo = request.POST.get('tipo')
        sopa_id = request.POST.get('sopa_id')
        segundo_id = request.POST.get('segundo_id')
        jugo_id = request.POST.get('jugo_id')
        
        # Manejar valores None para cantidad
        cantidad_str = request.POST.get('cantidad', '1')
        try:
            cantidad = int(cantidad_str) if cantidad_str else 1
        except (ValueError, TypeError):
            cantidad = 1
            
        observacion = request.POST.get('observacion', '')

        if not tipo:
            return JsonResponse({'status': 'error', 'message': 'Tipo de producto requerido'}, status=400)

        # Calcular precio unitario usando función auxiliar
        precio_unitario = calcular_precio_producto(tipo)
        
        return JsonResponse({
            'status': 'ok', 
            'precio_unitario': float(precio_unitario),
            'message': 'Producto agregado exitosamente'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def guardar_pedido(request):
    caja, created = CajaDiaria.objects.get_or_create(fecha=date.today())

    try:
        tipo_pedido = request.POST.get('tipo_pedido')
        forma_pago = request.POST.get('forma_pago')
        mesa = request.POST.get('mesa')
        contacto = request.POST.get('cliente')  # Viene del frontend como 'cliente'
        subtipo_reservado = request.POST.get('subtipo_reservado')  # Para pedidos reservados
        pedido_id_editar = request.POST.get('pedido_id')

        total_pedido = Decimal('0.00')
        productos_carrito = []
        
        # Intentar obtener productos del frontend primero
        productos_frontend = request.POST.get('productos_carrito')
        
        if productos_frontend:
            try:
                import json
                productos_carrito = json.loads(productos_frontend)
                
                for producto in productos_carrito:
                    precio_unitario = Decimal(str(producto.get('precio_unitario', 0)))
                    cantidad = int(producto.get('cantidad', 1))
                    total_pedido += precio_unitario * Decimal(str(cantidad))
                    
            except Exception as e:
                productos_carrito = []
        
        # Si no hay productos del frontend, mostrar error
        if not productos_carrito:
            return JsonResponse({'status': 'error', 'message': 'No se recibieron productos del pedido'}, status=400)

        # Si viene un ID, actualizar el pedido existente; si no, crear uno nuevo
        if pedido_id_editar:
            pedido = Pedido.objects.get(id=pedido_id_editar, estado='pendiente')

            # Usar el total guardado en la BD (más eficiente)
            total_anterior = pedido.total

            # NO limpiar productos anteriores - solo actualizar campos del pedido
            pedido.tipo = tipo_pedido
            pedido.forma_pago = forma_pago
            pedido.numero_mesa = mesa if mesa else None
            pedido.contacto = contacto
            pedido.subtipo_reservado = subtipo_reservado if tipo_pedido == 'reservado' else None
            pedido.total = total_pedido
            pedido.save()
        else:
            # Crear el pedido principal
            pedido = Pedido.objects.create(
                tipo=tipo_pedido,
                forma_pago=forma_pago,
                numero_mesa=mesa if mesa else None,
                contacto=contacto,
                subtipo_reservado=subtipo_reservado if tipo_pedido == 'reservado' else None,
                estado='pendiente',  # Guardar como pendiente
                total=total_pedido  # Guardar el total del pedido
            )

        # Guardar productos del carrito en BD
        productos_guardados = []
        
        # Si es edición, manejar productos existentes y nuevos
        productos_existentes = {}  # Cambiar a diccionario para mantener referencias
        productos_procesados = set()  # Para rastrear qué productos se procesaron
        if pedido_id_editar:
            # Obtener productos existentes con sus referencias
            for almuerzo in pedido.almuerzos.all():
                key = f"almuerzo_{almuerzo.sopa.id}_{almuerzo.segundo.id}_{almuerzo.jugo.id}"
                productos_existentes[key] = {'tipo': 'almuerzo', 'objeto': almuerzo}
            for sopa in pedido.sopas.all():
                key = f"sopa_{sopa.sopa.id}_{sopa.jugo.id}"
                productos_existentes[key] = {'tipo': 'sopa', 'objeto': sopa}
            for segundo in pedido.segundos.all():
                key = f"segundo_{segundo.segundo.id}_{segundo.jugo.id}"
                productos_existentes[key] = {'tipo': 'segundo', 'objeto': segundo}
        
        for producto in productos_carrito:
            # Generar clave del producto usando función auxiliar
            producto_key = generar_clave_producto(producto)
            
            # Si es edición y el producto existe, actualizar cantidad
            if pedido_id_editar and producto_key in productos_existentes:
                producto_existente = productos_existentes[producto_key]['objeto']
                productos_procesados.add(producto_key)  # Marcar como procesado
                
                # Si la cantidad es 0, eliminar el producto
                if producto['cantidad'] <= 0:
                    producto_existente.delete()
                else:
                    producto_existente.cantidad = producto['cantidad']
                    producto_existente.observacion = producto.get('observacion', '')
                    producto_existente.save()
                continue
            
            # Crear producto usando función auxiliar
            producto_creado = crear_producto_pedido(pedido, producto)
            if producto_creado:
                # Agregar a productos guardados usando función auxiliar
                producto_dict = convertir_producto_a_dict(producto_creado, producto['tipo'])
                if producto_dict:
                    productos_guardados.append(producto_dict)

        # Actualizar caja diaria según forma de pago
        if pedido_id_editar:
            # Ajustar por diferencia respecto al total anterior
            diferencia = total_pedido - total_anterior
            if forma_pago == 'Efectivo':
                caja.total_efectivo += diferencia
            elif forma_pago == 'Transferencia':
                caja.total_transferencia += diferencia
        else:
            if forma_pago == 'Efectivo':
                caja.total_efectivo += total_pedido
            elif forma_pago == 'Transferencia':
                caja.total_transferencia += total_pedido
        caja.save()

        # Si es edición, eliminar productos que ya no están en el carrito
        if pedido_id_editar:
            # Encontrar productos que no fueron procesados (eliminados del carrito)
            productos_a_eliminar = set(productos_existentes.keys()) - productos_procesados
            print(f"DEBUG: Productos a eliminar: {productos_a_eliminar}")
            print(f"DEBUG: Productos existentes: {set(productos_existentes.keys())}")
            print(f"DEBUG: Productos procesados: {productos_procesados}")
            for producto_key in productos_a_eliminar:
                producto_existente = productos_existentes[producto_key]['objeto']
                producto_existente.delete()
                print(f"DEBUG: Producto eliminado: {producto_key}")
        
        # Reconstruir productos desde la BD usando función auxiliar (después de eliminar)
        productos_reconstruidos = obtener_productos_pedido(pedido)
        
        # Recalcular el total real desde la BD
        total_real = Decimal('0.00')
        for producto in productos_reconstruidos:
            total_real += Decimal(str(producto['precio_unitario'])) * Decimal(str(producto['cantidad']))
        
        # Actualizar el total del pedido si es diferente
        if pedido.total != total_real:
            pedido.total = total_real
            pedido.save()

        return JsonResponse({
            'status': 'ok', 
            'pedido_id': pedido.id,
            'pedido_data': {
                'id': pedido.id,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
                'subtipo_reservado': pedido.subtipo_reservado,
                'fecha_creacion': pedido.fecha_creacion.isoformat(),
                'estado': pedido.estado,
                'productos': productos_reconstruidos,  # Usar productos reconstruidos
                'total': float(total_real)  # Usar total real recalculado
            }
        })

    except Exception as e:
        logger.error(f"Error al guardar pedido: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def marcar_pedido_completado(request):
    try:
        pedido_id = request.POST.get('pedido_id')
        if not pedido_id:
            return JsonResponse({'status': 'error', 'message': 'ID de pedido requerido'}, status=400)
        
        pedido = Pedido.objects.get(id=pedido_id)
        pedido.estado = 'completado'
        pedido.save()
        
        return JsonResponse({'status': 'ok', 'message': 'Pedido marcado como completado'})
        
    except Pedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_pedido(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id, estado='pendiente')
        
        # Obtener productos del pedido usando función auxiliar 
        productos = obtener_productos_pedido(pedido)
        
        return JsonResponse({
            'status': 'ok',
            'pedido': {
                'id': pedido.id,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
                'subtipo_reservado': pedido.subtipo_reservado,
                'productos': productos
            }
        })
        
    except Pedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_pedidos_pendientes(request):
    try:
        # Obtener todos los pedidos pendientes
        pedidos = Pedido.objects.filter(estado='pendiente').order_by('-fecha_creacion')
        
        pedidos_data = []
        for pedido in pedidos:
            # Obtener productos del pedido usando función auxiliar
            productos = obtener_productos_pedido(pedido)
            
            pedidos_data.append({
                'id': pedido.id,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
                'subtipo_reservado': pedido.subtipo_reservado,
                'fecha_creacion': pedido.fecha_creacion.isoformat(),
                'estado': pedido.estado,
                'productos': productos,
                'total': float(pedido.total) if pedido.total else 0.0
            })
        
        return JsonResponse({
            'status': 'ok',
            'pedidos': pedidos_data
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)
