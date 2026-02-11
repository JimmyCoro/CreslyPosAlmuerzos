import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from datetime import date
from decimal import Decimal
from .models import Pedido, PedidoAlmuerzo, PedidoSopa, PedidoSegundo, PedidoExtra
from caja.models import CajaDiaria, CajaEfectivo, CajaTransferencia
from menu.models import MenuDia, MenuDiaSopa, MenuDiaSegundo, MenuDiaJugo, Plato
import json

# Configurar logger
logger = logging.getLogger(__name__)


# ===== FUNCIONES AUXILIARES =====

def actualizar_cantidades_menu(productos_carrito, operacion='restar'):
    """
    Actualiza las cantidades del menú del día según los productos vendidos.
    
    Args:
        productos_carrito: Lista de productos del pedido
        operacion: 'restar' para crear pedido, 'sumar' para eliminar pedido
    """
    from datetime import date
    from menu.models import MenuDia, MenuDiaSopa, MenuDiaSegundo, Plato
    import logging
    
    logger = logging.getLogger(__name__)
    
    hoy = date.today()
    logger.info(f"Actualizando cantidades para {hoy}, operación: {operacion}")
    logger.info(f"Productos a procesar: {productos_carrito}")
    
    try:
        menu = MenuDia.objects.get(fecha=hoy)
        logger.info(f"Menú encontrado: {menu}")
    except MenuDia.DoesNotExist:
        logger.warning("No hay menú configurado para hoy")
        return  # No hay menú configurado para hoy
    
    for producto in productos_carrito:
        cantidad = producto.get('cantidad', 1)
        tipo = producto.get('tipo', '').lower()
        
        logger.info(f"Procesando producto: tipo={tipo}, cantidad={cantidad}")
        
        if operacion == 'restar':
            cantidad = -cantidad  # Restar
        # Si es 'sumar', cantidad ya es positiva
        
        if tipo == 'almuerzo':
            # Almuerzo consume 1 sopa + 1 segundo
            sopa_id = producto.get('sopa_id')
            segundo_id = producto.get('segundo_id')
            
            logger.info(f"Almuerzo - sopa_id: {sopa_id}, segundo_id: {segundo_id}")
            
            if sopa_id:
                try:
                    # Buscar directamente por Plato ID en el menú actual
                    sopa_actual = MenuDiaSopa.objects.get(menu=menu, sopa_id=sopa_id)
                    cantidad_anterior = sopa_actual.cantidad_actual
                    sopa_actual.cantidad_actual = max(0, sopa_actual.cantidad_actual + cantidad)
                    sopa_actual.save()
                    logger.info(f"Sopa actualizada: {sopa_actual.sopa} - {cantidad_anterior} → {sopa_actual.cantidad_actual}")
                except MenuDiaSopa.DoesNotExist:
                    logger.warning(f"No se encontró sopa con Plato ID {sopa_id} en el menú actual")
            
            if segundo_id:
                try:
                    # Buscar directamente por Plato ID en el menú actual
                    segundo_actual = MenuDiaSegundo.objects.filter(menu=menu, segundo_id=segundo_id).first()
                    cantidad_anterior = segundo_actual.cantidad_actual
                    segundo_actual.cantidad_actual = max(0, segundo_actual.cantidad_actual + cantidad)
                    segundo_actual.save()
                    logger.info(f"Segundo actualizado: {segundo_actual.segundo} - {cantidad_anterior} → {segundo_actual.cantidad_actual}")
                except MenuDiaSegundo.DoesNotExist:
                    logger.warning(f"No se encontró segundo con Plato ID {segundo_id} en el menú actual")
        
        elif tipo == 'sopa':
            # Sopa individual
            sopa_id = producto.get('sopa_id')
            logger.info(f"Sopa individual - sopa_id: {sopa_id}")
            if sopa_id:
                try:
                    # Buscar directamente por Plato ID en el menú actual
                    sopa_actual = MenuDiaSopa.objects.get(menu=menu, sopa_id=sopa_id)
                    cantidad_anterior = sopa_actual.cantidad_actual
                    sopa_actual.cantidad_actual = max(0, sopa_actual.cantidad_actual + cantidad)
                    sopa_actual.save()
                    logger.info(f"Sopa individual actualizada: {sopa_actual.sopa} - {cantidad_anterior} → {sopa_actual.cantidad_actual}")
                except MenuDiaSopa.DoesNotExist:
                    logger.warning(f"No se encontró sopa con Plato ID {sopa_id} en el menú actual")
        
        elif tipo == 'segundo':
            # Segundo individual
            segundo_id = producto.get('segundo_id')
            logger.info(f"Segundo individual - segundo_id: {segundo_id}")
            if segundo_id:
                try:
                    # Buscar directamente por Plato ID en el menú actual
                    segundo_actual = MenuDiaSegundo.objects.filter(menu=menu, segundo_id=segundo_id).first()
                    cantidad_anterior = segundo_actual.cantidad_actual
                    segundo_actual.cantidad_actual = max(0, segundo_actual.cantidad_actual + cantidad)
                    segundo_actual.save()
                    logger.info(f"Segundo individual actualizada: {segundo_actual.segundo} - {cantidad_anterior} → {segundo_actual.cantidad_actual}")
                except MenuDiaSegundo.DoesNotExist:
                    logger.warning(f"No se encontró segundo con Plato ID {segundo_id} en el menú actual")
        
        elif tipo == 'extra':
            # Los extras no consumen cantidades del menú, solo se registran
            logger.info(f"Extra procesado - no requiere actualización de cantidades")
        
        logger.info(f"Producto procesado exitosamente: {tipo}")

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
            'sopa_id': producto_obj.sopa.sopa.id,  # Plato ID
            'segundo_id': producto_obj.segundo.segundo.id,  # Plato ID
            'jugo_id': producto_obj.jugo.jugo.id,  # Plato ID
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
            'sopa_id': producto_obj.sopa.sopa.id,  # Plato ID
            'jugo_id': producto_obj.jugo.jugo.id,  # Plato ID
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
            'segundo_id': producto_obj.segundo.segundo.id,  # Plato ID
            'jugo_id': producto_obj.jugo.jugo.id,  # Plato ID
            'cantidad': producto_obj.cantidad,
            'precio_unitario': float(producto_obj.precio_unitario),
            'observacion': producto_obj.observacion or '',
            'componentes': [
                producto_obj.segundo.segundo.nombre_plato,
                producto_obj.jugo.jugo.nombre_plato
            ]
        }
    elif tipo == 'Extra':
        return {
            'tipo': 'Extra',
            'extra_id': producto_obj.extra.id,  # Plato ID
            'cantidad': producto_obj.cantidad,
            'precio_unitario': float(producto_obj.precio_unitario),
            'observacion': producto_obj.observacion or '',
            'componentes': [
                producto_obj.extra.nombre_plato
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
    
    # Extras
    for extra in pedido.extras.all():
        productos.append(convertir_producto_a_dict(extra, 'Extra'))
    
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
    
    elif tipo == 'Extra':
        # Para extras, crear múltiples registros si hay múltiples extras
        extras_ids = producto_data.get('extras_ids', '').split(',')
        extras_creados = []
        
        for extra_id in extras_ids:
            if extra_id.strip():
                try:
                    extra_plato = Plato.objects.get(id=int(extra_id.strip()), tipo='extra')
                    extra_creado = PedidoExtra.objects.create(
                        pedido=pedido,
                        extra=extra_plato,
                        cantidad=producto_data['cantidad'],
                        precio_unitario=extra_plato.precio,  # Usar precio del plato
                        observacion=producto_data.get('observacion', '')
                    )
                    extras_creados.append(extra_creado)
                except Plato.DoesNotExist:
                    continue
        
        return extras_creados[0] if extras_creados else None
    
    return None

def generar_clave_producto(producto):
    """Genera una clave única para identificar un producto"""
    if producto['tipo'] == 'Almuerzo':
        return f"almuerzo_{producto['sopa_id']}_{producto['segundo_id']}_{producto['jugo_id']}"
    elif producto['tipo'] == 'Sopa':
        return f"sopa_{producto['sopa_id']}_{producto['jugo_id']}"
    elif producto['tipo'] == 'Segundo':
        return f"segundo_{producto['segundo_id']}_{producto['jugo_id']}"
    elif producto['tipo'] == 'Extra':
        return f"extra_{producto.get('extras_ids', '')}"
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
    
    for extra in pedido.extras.all():
        total += Decimal(str(extra.precio_unitario)) * Decimal(str(extra.cantidad))
    
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
        extras_ids_raw = request.POST.get('extras_ids', '')
        
        # Manejar valores None para cantidad
        cantidad_str = request.POST.get('cantidad', '1')
        try:
            cantidad = int(cantidad_str) if cantidad_str else 1
        except (ValueError, TypeError):
            cantidad = 1
            
        observacion = request.POST.get('observacion', '')

        if not tipo:
            return JsonResponse({'status': 'error', 'message': 'Tipo de producto requerido'}, status=400)

        # Calcular precio unitario
        if tipo and tipo.lower() == 'extra':
            # Para extras: sumar precios de todos los extras seleccionados
            ids = [int(x) for x in extras_ids_raw.split(',') if x.strip().isdigit()]
            from menu.models import Plato
            precios = list(Plato.objects.filter(id__in=ids, tipo='extra').values_list('precio', flat=True))
            precio_unitario = sum(Decimal(str(p)) for p in precios) if precios else Decimal('0.00')
        else:
            # Productos normales (almuerzo/sopa/segundo)
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
    # Buscar caja abierta actual o crear una nueva para hoy
    caja = CajaDiaria.objects.filter(estado='abierta').first()
    
    if not caja:
        # No hay caja abierta, crear una nueva para hoy
        caja = CajaDiaria.objects.create(
            fecha=date.today(),
            estado='abierta'
        )
        CajaEfectivo.objects.create(caja_diaria=caja, monto_inicial=0)
        CajaTransferencia.objects.create(caja_diaria=caja, monto_inicial=0)

    try:
        tipo_pedido = request.POST.get('tipo_pedido')
        forma_pago = request.POST.get('forma_pago')
        mesa = request.POST.get('mesa')
        contacto = request.POST.get('cliente')  # Viene del frontend como 'cliente'
        subtipo_reservado = request.POST.get('subtipo_reservado')  # Para pedidos reservados
        print(f"[DEBUG] Subtipo recibido del frontend: {subtipo_reservado}")
        observaciones_generales = request.POST.get('observaciones_generales')
        pedido_id_editar = request.POST.get('pedido_id')
        es_agregar_productos = request.POST.get('es_agregar_productos') == 'true'

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

            if es_agregar_productos:
                # Solo agregar productos, no modificar campos del pedido
                total_anterior = pedido.total
                pedido.total = total_anterior + total_pedido  # Sumar al total existente
                pedido.save()
            else:
                # Edición normal - actualizar campos del pedido
                total_anterior = pedido.total
                pedido.tipo = tipo_pedido
                pedido.forma_pago = forma_pago
                pedido.numero_mesa = mesa if mesa else None
                pedido.contacto = contacto
                pedido.subtipo_reservado = (
                    subtipo_reservado
                    if (tipo_pedido or '').lower() == 'reservado'
                    else None
                )
                pedido.observaciones_generales = observaciones_generales
                pedido.total = total_pedido
                pedido.save()
        else:
            # Crear el pedido principal
            pedido = Pedido.objects.create(
                tipo=tipo_pedido,
                forma_pago=forma_pago,
                numero_mesa=mesa if mesa else None,
                contacto=contacto,
                subtipo_reservado=subtipo_reservado if tipo_pedido.lower() == 'reservado' else None,
                observaciones_generales=observaciones_generales,
                estado='pendiente',  # Guardar como pendiente
                total=total_pedido  # Guardar el total del pedido
            )
            
            # Debug: verificar que se guardó correctamente
            print(f"[DEBUG] Pedido creado - ID: {pedido.id}, Subtipo guardado: {pedido.subtipo_reservado}")
            print(f"[DEBUG] Tipo pedido: '{tipo_pedido}', Comparación: {tipo_pedido.lower() == 'reservado'}")

        # Guardar productos del carrito en BD
        productos_guardados = []
        
        # Si es edición, manejar productos existentes y nuevos
        productos_existentes = {}  # Cambiar a diccionario para mantener referencias
        productos_procesados = set()  # Para rastrear qué productos se procesaron
        productos_originales = []  # Para devolver cantidades originales
        
        if pedido_id_editar:
            # Obtener productos existentes con sus referencias
            for almuerzo in pedido.almuerzos.all():
                key = f"almuerzo_{almuerzo.sopa.id}_{almuerzo.segundo.id}_{almuerzo.jugo.id}"
                productos_existentes[key] = {'tipo': 'almuerzo', 'objeto': almuerzo}
                # Agregar a productos originales para devolver cantidades
                productos_originales.append({
                    'tipo': 'almuerzo',
                    'cantidad': almuerzo.cantidad,
                    'sopa_id': almuerzo.sopa.sopa.id,  # Plato ID
                    'segundo_id': almuerzo.segundo.segundo.id  # Plato ID
                })
            for sopa in pedido.sopas.all():
                key = f"sopa_{sopa.sopa.id}_{sopa.jugo.id}"
                productos_existentes[key] = {'tipo': 'sopa', 'objeto': sopa}
                # Agregar a productos originales para devolver cantidades
                productos_originales.append({
                    'tipo': 'sopa',
                    'cantidad': sopa.cantidad,
                    'sopa_id': sopa.sopa.sopa.id  # Plato ID
                })
            for segundo in pedido.segundos.all():
                key = f"segundo_{segundo.segundo.id}_{segundo.jugo.id}"
                productos_existentes[key] = {'tipo': 'segundo', 'objeto': segundo}
                # Agregar a productos originales para devolver cantidades
                productos_originales.append({
                    'tipo': 'segundo',
                    'cantidad': segundo.cantidad,
                    'segundo_id': segundo.segundo.segundo.id  # Plato ID
                })
            # Agregar extras existentes
            for extra in pedido.extras.all():
                key = f"extra_{extra.extra.id}"
                productos_existentes[key] = {'tipo': 'extra', 'objeto': extra}
                # Agregar a productos originales para devolver cantidades
                productos_originales.append({
                    'tipo': 'extra',
                    'cantidad': extra.cantidad,
                    'extra_id': extra.extra.id  # Plato ID
                })
        
        for producto in productos_carrito:
            # Para extras, procesar cada extra individualmente
            if producto['tipo'] == 'Extra':
                # Los extras se procesan individualmente ya que cada uno es un registro separado
                extras_ids = producto.get('extras_ids', '').split(',')
                extras_a_crear = []  # Lista de IDs de extras que necesitan ser creados
                
                # Si es edición, verificar qué extras ya existen
                if pedido_id_editar:
                    for extra_id in extras_ids:
                        if extra_id.strip():
                            extra_key = f"extra_{extra_id.strip()}"
                            if extra_key in productos_existentes:
                                # El extra existe, actualizar cantidad
                                extra_existente = productos_existentes[extra_key]['objeto']
                                productos_procesados.add(extra_key)  # Marcar como procesado
                                
                                # Si la cantidad es 0, eliminar el extra
                                if producto['cantidad'] <= 0:
                                    extra_existente.delete()
                                else:
                                    extra_existente.cantidad = producto['cantidad']
                                    extra_existente.observacion = producto.get('observacion', '')
                                    extra_existente.save()
                            else:
                                # El extra no existe, agregarlo a la lista para crearlo
                                extras_a_crear.append(extra_id.strip())
                else:
                    # Pedido nuevo, todos los extras deben crearse
                    extras_a_crear = [eid.strip() for eid in extras_ids if eid.strip()]
                
                # Si hay extras a crear, crear el producto (que creará todos los extras)
                if extras_a_crear:
                    producto_creado = crear_producto_pedido(pedido, producto)
                    if producto_creado:
                        # Agregar todos los extras creados a productos_guardados
                        for extra_id in extras_a_crear:
                            if extra_id.strip():
                                try:
                                    from menu.models import Plato
                                    extra_plato = Plato.objects.get(id=int(extra_id.strip()), tipo='extra')
                                    extra_obj = PedidoExtra.objects.filter(
                                        pedido=pedido,
                                        extra=extra_plato
                                    ).order_by('-id').first()
                                    if extra_obj:
                                        producto_dict = convertir_producto_a_dict(extra_obj, 'Extra')
                                        if producto_dict:
                                            extra_id_existente = producto_dict.get('extra_id')
                                            if not any(p.get('extra_id') == extra_id_existente and p.get('tipo') == 'Extra' 
                                                       for p in productos_guardados):
                                                productos_guardados.append(producto_dict)
                                except (Plato.DoesNotExist, ValueError):
                                    continue
                # Continuar al siguiente producto
                continue
            
            # Generar clave del producto usando función auxiliar (para productos normales)
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
                # Para extras, crear_producto_pedido puede crear múltiples registros
                # Necesitamos agregar todos los extras creados
                if producto['tipo'] == 'Extra':
                    # Obtener todos los extras recién creados para este pedido
                    # Usar el ID del pedido y los extras_ids para encontrar los extras creados
                    extras_ids = producto.get('extras_ids', '').split(',')
                    for extra_id in extras_ids:
                        if extra_id.strip():
                            try:
                                from menu.models import Plato
                                extra_plato = Plato.objects.get(id=int(extra_id.strip()), tipo='extra')
                                # Buscar el extra más reciente creado para este pedido y este plato
                                extra_obj = PedidoExtra.objects.filter(
                                    pedido=pedido,
                                    extra=extra_plato
                                ).order_by('-id').first()
                                if extra_obj:
                                    producto_dict = convertir_producto_a_dict(extra_obj, 'Extra')
                                    if producto_dict:
                                        # Verificar que no esté ya en productos_guardados
                                        extra_id_existente = producto_dict.get('extra_id')
                                        if not any(p.get('extra_id') == extra_id_existente and p.get('tipo') == 'Extra' 
                                                   for p in productos_guardados):
                                            productos_guardados.append(producto_dict)
                            except (Plato.DoesNotExist, ValueError):
                                continue
                else:
                    # Para otros tipos de productos, usar el método normal
                    producto_dict = convertir_producto_a_dict(producto_creado, producto['tipo'])
                    if producto_dict:
                        productos_guardados.append(producto_dict)

        # NOTA: No se actualiza caja automáticamente aquí
        # Las ventas solo se suman cuando el pedido se marca como 'completado'

        # Si es edición, devolver cantidades originales antes de restar las nuevas
        if pedido_id_editar and productos_originales:
            print(f"=== EDITANDO PEDIDO {pedido_id_editar} ===")
            print(f"Productos originales: {productos_originales}")
            actualizar_cantidades_menu(productos_originales, 'sumar')
            print("✅ Cantidades originales devueltas")
        
        # Actualizar cantidades del menú del día
        print(f"Productos nuevos: {productos_carrito}")
        actualizar_cantidades_menu(productos_carrito, 'restar')
        print("✅ Cantidades nuevas restadas")

        # Si es edición, eliminar productos que ya no están en el carrito
        if pedido_id_editar and not es_agregar_productos:
            # Solo eliminar productos si NO estamos agregando productos
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

        # Enviar mensaje WebSocket
        try:
            pedido_data = serializar_pedido_para_websocket(pedido)
            if pedido_data:
                if pedido_id_editar:
                    # Pedido actualizado
                    enviar_mensaje_websocket('pedido_actualizado', pedido_data)
                else:
                    # Pedido creado
                    enviar_mensaje_websocket('pedido_creado', pedido_data)
        except Exception as e:
            print(f"[WEBSOCKET] Error al enviar mensaje: {e}")

        # Imprimir comando para cocina
        try:
            from impresion.impresora import ImpresoraTermica
            from datetime import datetime
            
            # Crear comando para cocina
            # Crear línea dinámica según el tipo de pedido
            linea_info = f"{pedido.tipo.upper()}"
            
            if pedido.tipo == 'Servirse' and pedido.numero_mesa:
                # Para servirse: mostrar mesa
                espacios = 45 - len(f"{pedido.tipo.upper()}.") - len(f"MESA: {pedido.numero_mesa}")
                linea_info += " " * espacios + f"MESA: {pedido.numero_mesa}"
            elif pedido.tipo == 'Llevar' and pedido.contacto:
                # Para llevar: mostrar cliente
                espacios = 45 - len(f"{pedido.tipo.upper()}.") - len(f"{pedido.contacto}")
                linea_info += " " * espacios + f"{pedido.contacto.upper()}"
            elif pedido.tipo == 'Reservado' and pedido.contacto:
                # Para reservado: mostrar cliente y subtipo
                print(f"[DEBUG] Pedido Reservado - Contacto: {pedido.contacto}, Subtipo: {pedido.subtipo_reservado}")
                print(f"[DEBUG] Tipo de pedido: {pedido.tipo}, Subtipo_reservado: {pedido.subtipo_reservado}")
                subtipo_texto = f" ({pedido.subtipo_reservado})" if pedido.subtipo_reservado else ""
                espacios = 45 - len(f"{pedido.tipo.upper()}.") - len(f"{pedido.contacto}{subtipo_texto}")
                linea_info += " " * espacios + f"{pedido.contacto.upper()}{subtipo_texto.upper()}"
            
            # Calcular espacios para la segunda línea
            espacios_segunda = 45 - len(f"Pedido #{pedido.numero_pedido_completo}") - len(f"Hora: {datetime.now().strftime('%H:%M')}")
            
            comando_cocina = [
                linea_info,
                f"Pedido #{pedido.numero_pedido_completo}" + " " * espacios_segunda + f"Hora: {datetime.now().strftime('%H:%M')}"
            ]
            
            # Agregar observaciones generales si existen
            if pedido.observaciones_generales:
                comando_cocina.append(f"  {pedido.observaciones_generales}")

            comando_cocina.append("-" * 45)
                        

            
            # Agregar productos con componentes verticales
            productos_a_imprimir = productos_carrito if es_agregar_productos else productos_reconstruidos
            
            print(f"[DEBUG IMPRESIÓN] Productos a imprimir: {len(productos_a_imprimir)}")
            print(f"[DEBUG IMPRESIÓN] Es agregar productos: {es_agregar_productos}")
            
            # Asegurar que todos los productos tengan componentes formateados
            productos_formateados = []
            for producto in productos_a_imprimir:
                try:
                    producto_formateado = producto.copy()
                    
                    # Si es un extra y no tiene componentes, formatearlo
                    if producto.get('tipo') == 'Extra':
                        # Si viene de productos_carrito, puede no tener componentes formateados
                        if not producto.get('componentes') or len(producto.get('componentes', [])) == 0:
                            # Intentar obtener el nombre del extra desde extras_ids
                            extras_ids = producto.get('extras_ids', '')
                            if extras_ids:
                                try:
                                    from menu.models import Plato
                                    nombres_extras = []
                                    for extra_id in extras_ids.split(','):
                                        if extra_id.strip():
                                            try:
                                                extra_plato = Plato.objects.get(id=int(extra_id.strip()), tipo='extra')
                                                nombres_extras.append(extra_plato.nombre_plato)
                                            except Plato.DoesNotExist:
                                                continue
                                    if nombres_extras:
                                        producto_formateado['componentes'] = nombres_extras
                                except Exception as e:
                                    print(f"[ERROR] Error al formatear extras para impresión: {e}")
                    
                    productos_formateados.append(producto_formateado)
                except Exception as e:
                    print(f"[ERROR] Error al formatear producto para impresión: {e}")
                    print(f"[ERROR] Producto problemático: {producto}")
                    continue
            
            print(f"[DEBUG IMPRESIÓN] Productos formateados: {len(productos_formateados)}")
            
            for producto in productos_formateados:
                try:
                    # Línea principal con cantidad y tipo
                    comando_cocina.append(f"{producto['cantidad']}x {producto['tipo']}")
                    
                    # Componentes en forma vertical (uno debajo del otro)
                    if producto.get('componentes'):
                        for componente in producto['componentes']:
                            comando_cocina.append(f"  - {componente}")
                    
                    # Observación en línea separada si existe
                    if producto.get('observacion'):
                        comando_cocina.append(f"  Obs: {producto['observacion']}")
                    
                    comando_cocina.append("")
                except Exception as e:
                    print(f"[ERROR] Error al agregar producto al comando: {e}")
                    print(f"[ERROR] Producto: {producto}")
                    continue
            
            print(f"[DEBUG IMPRESIÓN] Comando cocina generado: {len(comando_cocina)} líneas")


            
            # Imprimir vía WebSocket (tablet conectada a Railway)
            try:
                enviar_trabajo_impresion(pedido, comando_cocina, es_agregar_productos)
            except Exception as e:
                print(f"[WARNING] Error al enviar trabajo de impresión: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"[ERROR] Error general al imprimir: {e}")
            import traceback
            traceback.print_exc()

        # Mensaje diferente según la acción
        if es_agregar_productos:
            mensaje = 'Productos agregados al pedido correctamente'
        elif pedido_id_editar:
            mensaje = 'Pedido actualizado correctamente'
        else:
            mensaje = 'Pedido creado correctamente'
        
        return JsonResponse({
            'status': 'ok', 
            'message': mensaje,
            'pedido_id': pedido.id,
            'pedido_data': {
                'id': pedido.id,
                'numero_dia': pedido.numero_dia,
                'numero_pedido_completo': pedido.numero_pedido_completo,
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
        
        # Enviar mensaje WebSocket
        try:
            pedido_data = serializar_pedido_para_websocket(pedido)
            if pedido_data:
                enviar_mensaje_websocket('pedido_actualizado', pedido_data)
        except Exception as e:
            print(f"[WEBSOCKET] Error al enviar mensaje: {e}")
        
        # Sumar a caja cuando se marca como completado
        from caja.models import CajaDiaria
        from datetime import date
        
        try:
            # Buscar caja abierta actual
            caja = CajaDiaria.objects.filter(estado='abierta').first()
            if caja:
                if pedido.forma_pago == 'Efectivo':
                    caja.caja_efectivo.total_ventas += pedido.total
                    caja.caja_efectivo.save()
                elif pedido.forma_pago == 'Transferencia':
                    caja.caja_transferencia.total_ventas += pedido.total
                    caja.caja_transferencia.save()
        except Exception:
            pass  # No hay caja abierta, no se suma
        
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
                'numero_dia': pedido.numero_dia,
                'numero_pedido_completo': pedido.numero_pedido_completo,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
                'subtipo_reservado': pedido.subtipo_reservado,
                'observaciones_generales': pedido.observaciones_generales,
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
                'numero_dia': pedido.numero_dia,
                'numero_pedido_completo': pedido.numero_pedido_completo,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
                'subtipo_reservado': pedido.subtipo_reservado,
                'observaciones_generales': pedido.observaciones_generales,
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


@csrf_exempt
@require_http_methods(["POST"])
def eliminar_pedido(request):
    """Elimina un pedido y actualiza las cantidades del menú"""
    try:
        pedido_id = request.POST.get('pedido_id')
        if not pedido_id:
            return JsonResponse({'status': 'error', 'message': 'ID de pedido requerido'}, status=400)
        
        pedido = Pedido.objects.get(id=pedido_id, estado='pendiente')
        
        # Obtener productos del pedido antes de eliminarlo
        productos_pedido = []
        
        # Obtener almuerzos
        for almuerzo in pedido.almuerzos.all():
            productos_pedido.append({
                'tipo': 'almuerzo',
                'cantidad': almuerzo.cantidad,
                'sopa_id': almuerzo.sopa.sopa.id,      # Plato.id
                'segundo_id': almuerzo.segundo.segundo.id  # Plato.id
            })
        
        # Obtener sopas individuales
        for sopa in pedido.sopas.all():
            productos_pedido.append({
                'tipo': 'sopa',
                'cantidad': sopa.cantidad,
                'sopa_id': sopa.sopa.sopa.id           # Plato.id
            })
        
        # Obtener segundos individuales
        for segundo in pedido.segundos.all():
            productos_pedido.append({
                'tipo': 'segundo',
                'cantidad': segundo.cantidad,
                'segundo_id': segundo.segundo.segundo.id  # Plato.id
            })
        
        # Actualizar cantidades del menú (sumar de vuelta)
        actualizar_cantidades_menu(productos_pedido, 'sumar')
        
        # Enviar mensaje WebSocket antes de eliminar
        try:
            pedido_data = serializar_pedido_para_websocket(pedido)
            if pedido_data:
                enviar_mensaje_websocket('pedido_eliminado', pedido_data)
        except Exception as e:
            print(f"[WEBSOCKET] Error al enviar mensaje: {e}")
        
        # Eliminar el pedido
        pedido.delete()
        
        return JsonResponse({'status': 'ok', 'message': 'Pedido eliminado correctamente'})
        
    except Pedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_cantidades_actualizadas(request):
    """Obtiene las cantidades actualizadas del menú del día"""
    try:
        from datetime import date
        from menu.models import MenuDia, MenuDiaSopa, MenuDiaSegundo
        
        hoy = date.today()
        
        try:
            menu = MenuDia.objects.get(fecha=hoy)
        except MenuDia.DoesNotExist:
            return JsonResponse({
                'status': 'ok',
                'sopas': [],
                'segundos': []
            })
        
        # Obtener sopas con cantidades actuales
        sopas_data = []
        for sopa in MenuDiaSopa.objects.filter(menu=menu):
            sopas_data.append({
                'id': sopa.id,
                'nombre': str(sopa.sopa),
                'cantidad_configurada': sopa.cantidad,
                'cantidad_actual': sopa.cantidad_actual,
                'cantidad_vendida': sopa.cantidad - sopa.cantidad_actual
            })
        
        # Obtener segundos con cantidades actuales
        segundos_data = []
        for segundo in MenuDiaSegundo.objects.filter(menu=menu):
            segundos_data.append({
                'id': segundo.id,
                'nombre': str(segundo.segundo),
                'cantidad_configurada': segundo.cantidad,
                'cantidad_actual': segundo.cantidad_actual,
                'cantidad_vendida': segundo.cantidad - segundo.cantidad_actual
            })
        
        return JsonResponse({
            'status': 'ok',
            'sopas': sopas_data,
            'segundos': segundos_data
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def marcar_pedidos_completados(request):
    """Marcar múltiples pedidos como completados"""
    try:
        data = json.loads(request.body)
        pedido_ids = data.get('pedido_ids', [])
        
        if not pedido_ids:
            return JsonResponse({'status': 'error', 'message': 'No se proporcionaron IDs de pedidos'})
        
        # Actualizar pedidos
        pedidos_actualizados = Pedido.objects.filter(id__in=pedido_ids, estado='pendiente')
        cantidad_actualizada = pedidos_actualizados.update(estado='completado')
        
        # Sumar a caja los pedidos que se marcaron como completados
        from caja.models import CajaDiaria
        from datetime import date
        
        try:
            # Buscar caja abierta actual
            caja = CajaDiaria.objects.filter(estado='abierta').first()
            if caja:
                total_efectivo = 0
                total_transferencia = 0
                
                for pedido in pedidos_actualizados:
                    if pedido.forma_pago == 'Efectivo':
                        total_efectivo += pedido.total
                    elif pedido.forma_pago == 'Transferencia':
                        total_transferencia += pedido.total
                
                # Actualizar totales en caja
                if total_efectivo > 0:
                    caja.caja_efectivo.total_ventas += total_efectivo
                    caja.caja_efectivo.save()
                if total_transferencia > 0:
                    caja.caja_transferencia.total_ventas += total_transferencia
                    caja.caja_transferencia.save()
                
        except Exception:
            pass  # No hay caja abierta, no se suma
        
        # Enviar mensaje WebSocket para notificar a otros dispositivos
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    "pedidos",
                    {
                        "type": "pedidos_marcados_completados",
                        "pedidos_ids": pedido_ids,
                        "cantidad": cantidad_actualizada
                    }
                )
                print(f"[WEBSOCKET] Notificación enviada: {cantidad_actualizada} pedidos marcados como completados")
            else:
                print("[WEBSOCKET] No hay channel layer configurado")
        except Exception as e:
            print(f"[WEBSOCKET] Error al enviar notificación: {e}")
        
        return JsonResponse({
            'status': 'ok',
            'message': f'{cantidad_actualizada} pedidos marcados como completados',
            'pedidos_actualizados': cantidad_actualizada
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})



@require_http_methods(["GET"])
def obtener_pedidos_por_tipo(request):
    """Obtener pedidos filtrados por tipo"""
    try:
        tipo = request.GET.get('tipo', 'todos')
        
        pedidos = Pedido.objects.filter(estado='pendiente').prefetch_related(
            'almuerzos__sopa', 'almuerzos__segundo', 'almuerzos__jugo',
            'sopas__sopa', 'sopas__jugo',
            'segundos__segundo', 'segundos__jugo',
            'extras__extra'  # Incluir extras
        ).order_by('-fecha_creacion')
        
        if tipo == 'servirse':
            pedidos = pedidos.filter(tipo='Servirse')
        elif tipo == 'llevar':
            pedidos = pedidos.filter(tipo='Llevar')
        elif tipo == 'reservados':
            pedidos = pedidos.filter(tipo='Reservado')
        
        # Calcular totales para cada pedido
        for pedido in pedidos:
            total_calculado = Decimal('0.00')
            
            for almuerzo in pedido.almuerzos.all():
                total_calculado += almuerzo.precio_unitario * Decimal(str(almuerzo.cantidad))
            
            for sopa in pedido.sopas.all():
                total_calculado += sopa.precio_unitario * Decimal(str(sopa.cantidad))
            
            for segundo in pedido.segundos.all():
                total_calculado += segundo.precio_unitario * Decimal(str(segundo.cantidad))
            
            # Agregar extras al total
            for extra in pedido.extras.all():
                total_calculado += extra.precio_unitario * Decimal(str(extra.cantidad))
            
            pedido.total_calculado = total_calculado
        
        # Serializar pedidos
        pedidos_data = []
        for pedido in pedidos:
            productos = []
            
            for almuerzo in pedido.almuerzos.all():
                productos.append({
                    'tipo': 'Almuerzo',
                    'componentes': [
                        almuerzo.sopa.sopa.nombre_plato,
                        almuerzo.segundo.segundo.nombre_plato,
                        almuerzo.jugo.jugo.nombre_plato
                    ],
                    'cantidad': almuerzo.cantidad,
                    'precio_unitario': float(almuerzo.precio_unitario),
                    'observacion': almuerzo.observacion or ''
                })
            
            for sopa in pedido.sopas.all():
                productos.append({
                    'tipo': 'Sopa',
                    'componentes': [
                        sopa.sopa.sopa.nombre_plato,
                        sopa.jugo.jugo.nombre_plato
                    ],
                    'cantidad': sopa.cantidad,
                    'precio_unitario': float(sopa.precio_unitario),
                    'observacion': sopa.observacion or ''
                })
            
            for segundo in pedido.segundos.all():
                productos.append({
                    'tipo': 'Segundo',
                    'componentes': [
                        segundo.segundo.segundo.nombre_plato,
                        segundo.jugo.jugo.nombre_plato
                    ],
                    'cantidad': segundo.cantidad,
                    'precio_unitario': float(segundo.precio_unitario),
                    'observacion': segundo.observacion or ''
                })
            
            # Agregar extras
            for extra in pedido.extras.all():
                productos.append({
                    'tipo': 'Extra',
                    'componentes': [
                        extra.extra.nombre_plato
                    ],
                    'cantidad': extra.cantidad,
                    'precio_unitario': float(extra.precio_unitario),
                    'observacion': extra.observacion or ''
                })
            
            pedidos_data.append({
                'id': pedido.id,
                'numero_dia': pedido.numero_dia,
                'numero_pedido_completo': pedido.numero_pedido_completo,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'fecha_creacion': pedido.fecha_creacion.isoformat(),
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
                'subtipo_reservado': pedido.subtipo_reservado,
                'observaciones_generales': pedido.observaciones_generales,
                'total': float(pedido.total_calculado),  # Usar total calculado que incluye extras
                'productos': productos
            })
        
        return JsonResponse({
            'status': 'ok',
            'pedidos': pedidos_data,
            'cantidad': len(pedidos_data)
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_http_methods(["GET"])
def obtener_contadores_tabs(request):
    """Obtener contadores de pedidos para cada tab"""
    try:
        # Obtener pedidos pendientes
        pedidos = Pedido.objects.filter(estado='pendiente')
        
        # Contar por tipo
        contadores = {
            'todos': pedidos.count(),
            'servirse': pedidos.filter(tipo='Servirse').count(),
            'llevar': pedidos.filter(tipo='Llevar').count(),
            'reservados': pedidos.filter(tipo='Reservado').count()
        }
        
        return JsonResponse({
            'status': 'ok',
            'contadores': contadores
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@require_http_methods(["GET"])
def obtener_cantidades_modal(request):
    """Obtener cantidades actualizadas para el modal de agregar productos"""
    try:
        hoy = date.today()
        menu = MenuDia.objects.get(fecha=hoy)
        
        # Obtener sopas con cantidades
        sopas = []
        for sopa_dia in MenuDiaSopa.objects.filter(menu=menu):
            sopas.append({
                'id': sopa_dia.id,
                'sopa_id': sopa_dia.sopa.id,
                'nombre': sopa_dia.sopa.nombre_plato,
                'cantidad_actual': sopa_dia.cantidad_actual,
                'cantidad_configurada': sopa_dia.cantidad
            })
        
        # Obtener segundos con cantidades
        segundos = []
        for segundo_dia in MenuDiaSegundo.objects.filter(menu=menu):
            segundos.append({
                'id': segundo_dia.id,
                'segundo_id': segundo_dia.segundo.id,
                'nombre': segundo_dia.segundo.nombre_plato,
                'cantidad_actual': segundo_dia.cantidad_actual,
                'cantidad_configurada': segundo_dia.cantidad
            })
        
        return JsonResponse({
            'status': 'ok',
            'sopas': sopas,
            'segundos': segundos
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ===== FUNCIONES WEBSOCKET =====

def enviar_mensaje_websocket(tipo_mensaje, pedido_data):
    """
    Envía un mensaje WebSocket al grupo 'pedidos' para notificar cambios
    
    Args:
        tipo_mensaje: 'pedido_creado' o 'pedido_actualizado'
        pedido_data: Datos del pedido en formato JSON
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "pedidos",
                {
                    "type": tipo_mensaje,
                    "pedido": pedido_data
                }
            )
            print(f"[WEBSOCKET] Mensaje enviado: {tipo_mensaje}")
        else:
            print("[WEBSOCKET] No hay channel layer configurado")
    except Exception as e:
        print(f"[WEBSOCKET] Error al enviar mensaje: {e}")


def enviar_trabajo_impresion(pedido, contenido, es_agregar_productos):
    """
    Envía un trabajo de impresión al grupo 'impresion' para la tablet
    
    Args:
        pedido: Instancia del modelo Pedido
        contenido: Lista de líneas para imprimir
        es_agregar_productos: bool indicando si son productos adicionales
    """
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    import os

    try:
        payload = {
            "type": "print_job",
            "pedido": serializar_pedido_para_websocket(pedido),
            "contenido": contenido,
            "es_agregar_productos": es_agregar_productos,
        }

        ips_impresoras_str = os.getenv('IMPRESORAS_IPS', '').strip()
        if ips_impresoras_str:
            payload["impresoras"] = [ip.strip() for ip in ips_impresoras_str.split(',') if ip.strip()]

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                "impresion",
                {
                    "type": "print_job",
                    "payload": payload
                }
            )
            print("[WEBSOCKET] Trabajo de impresión enviado")
        else:
            print("[WEBSOCKET] No hay channel layer configurado para impresión")
    except Exception as e:
        print(f"[WEBSOCKET] Error al enviar trabajo de impresión: {e}")


def serializar_pedido_para_websocket(pedido):
    """
    Serializa un pedido para enviarlo por WebSocket
    
    Args:
        pedido: Instancia del modelo Pedido
        
    Returns:
        dict: Datos del pedido en formato JSON
    """
    try:
        # Obtener productos del pedido
        productos = obtener_productos_pedido(pedido)
        
        return {
            'id': pedido.id,
            'numero_dia': pedido.numero_dia,
            'numero_pedido_completo': pedido.numero_pedido_completo,
            'tipo': pedido.tipo,
            'subtipo': pedido.subtipo_reservado,
            'forma_pago': pedido.forma_pago,
            'total': float(pedido.total),
            'estado_pedido': pedido.estado,
            'fecha_creacion': pedido.fecha_creacion.isoformat(),
            'contacto': pedido.contacto,
            'observaciones_generales': pedido.observaciones_generales,
            'mesa': pedido.numero_mesa,
            'productos': productos
        }
    except Exception as e:
        print(f"[WEBSOCKET] Error al serializar pedido: {e}")
        return None