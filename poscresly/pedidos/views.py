from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import logging
from datetime import date
from decimal import Decimal
from .models import Pedido, CajaDiaria, PedidoAlmuerzo, PedidoSopa, PedidoSegundo

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def agregar_al_carrito(request):
    try:
        logger.info(f"Recibida petición POST a agregar_al_carrito")
        logger.info(f"Datos POST: {request.POST}")

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

        # Importar Producto al inicio para que esté disponible en todos los bloques
        from menu.models import Producto

        # Calcular precio unitario según el tipo de producto
        precio_unitario = Decimal('0.00')
        if tipo == 'almuerzo':
            # Buscar precio de almuerzo en la BD
            try:
                producto = Producto.objects.get(nombre_producto__iexact='almuerzo')
                precio_unitario = Decimal(str(producto.precio_servirse))  # Convertir a Decimal
            except Producto.DoesNotExist:
                precio_unitario = Decimal('8.00')  # Precio por defecto
        elif tipo == 'sopa':
            try:
                producto = Producto.objects.get(nombre_producto__iexact='sopa')
                precio_unitario = Decimal(str(producto.precio_servirse))
            except Producto.DoesNotExist:
                precio_unitario = Decimal('4.00')
        elif tipo == 'segundo':
            try:
                producto = Producto.objects.get(nombre_producto__iexact='segundo')
                precio_unitario = Decimal(str(producto.precio_servirse))
            except Producto.DoesNotExist:
                precio_unitario = Decimal('6.00')

        # Ya no usamos el carrito de sesión, solo devolvemos el precio
        logger.info(f"Precio calculado para {tipo}: {precio_unitario}")
        
        return JsonResponse({
            'status': 'ok', 
            'precio_unitario': float(precio_unitario),
            'message': 'Producto agregado exitosamente'
        })

    except Exception as e:
        logger.error(f"Error interno en agregar_al_carrito: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def guardar_pedido(request):
    caja, created = CajaDiaria.objects.get_or_create(fecha=date.today())

    try:
        logger.info("=== INICIO DE GUARDAR PEDIDO ===")
        logger.info(f"Datos POST: {request.POST}")
        
        tipo_pedido = request.POST.get('tipo_pedido')
        forma_pago = request.POST.get('forma_pago')
        mesa = request.POST.get('mesa')
        contacto = request.POST.get('cliente')  # Viene del frontend como 'cliente'
        pedido_id_editar = request.POST.get('pedido_id')

        logger.info(f"Tipo pedido: {tipo_pedido}")
        logger.info(f"Forma pago: {forma_pago}")
        logger.info(f"Mesa: {mesa}")
        logger.info(f"Contacto: {contacto}")

        total_pedido = Decimal('0.00')
        productos_carrito = []
        
        # Intentar obtener productos del frontend primero
        productos_frontend = request.POST.get('productos_carrito')
        logger.info(f"Productos del frontend (raw): {productos_frontend}")
        
        if productos_frontend:
            try:
                import json
                productos_carrito = json.loads(productos_frontend)
                logger.info(f"Productos parseados del frontend: {productos_carrito}")
                logger.info(f"Cantidad de productos parseados: {len(productos_carrito)}")
                
                for i, producto in enumerate(productos_carrito):
                    logger.info(f"Procesando producto {i+1}: {producto}")
                    precio_unitario = Decimal(str(producto.get('precio_unitario', 0)))
                    cantidad = int(producto.get('cantidad', 1))
                    total_pedido += precio_unitario * Decimal(str(cantidad))
                    logger.info(f"Producto {i+1} procesado - Tipo: {producto.get('tipo')}, Precio: {precio_unitario}, Cantidad: {cantidad}")
                    
            except Exception as e:
                logger.error(f"Error al parsear productos del frontend: {e}")
                productos_carrito = []
        
        # Si no hay productos del frontend, mostrar error
        if not productos_carrito:
            logger.error("No se recibieron productos del frontend")
            return JsonResponse({'status': 'error', 'message': 'No se recibieron productos del pedido'}, status=400)

        logger.info(f"Total del pedido: {total_pedido}")
        logger.info(f"Cantidad de productos: {len(productos_carrito)}")
        logger.info(f"Productos del carrito: {productos_carrito}")

        # Si viene un ID, actualizar el pedido existente; si no, crear uno nuevo
        if pedido_id_editar:
            logger.info(f"Actualizando pedido existente ID: {pedido_id_editar}")
            pedido = Pedido.objects.get(id=pedido_id_editar, estado='pendiente')

            # Calcular total anterior del pedido para ajustar caja diaria
            total_anterior = Decimal('0.00')
            for a in pedido.almuerzos.all():
                total_anterior += Decimal(str(a.precio_unitario)) * Decimal(str(a.cantidad))
            for s in pedido.sopas.all():
                total_anterior += Decimal(str(s.precio_unitario)) * Decimal(str(s.cantidad))
            for sg in pedido.segundos.all():
                total_anterior += Decimal(str(sg.precio_unitario)) * Decimal(str(sg.cantidad))

            # NO limpiar productos anteriores - solo actualizar campos del pedido
            pedido.tipo = tipo_pedido
            pedido.forma_pago = forma_pago
            pedido.numero_mesa = mesa if mesa else None
            pedido.contacto = contacto
            pedido.total = total_pedido
            pedido.save()
            
            logger.info("Productos anteriores preservados - solo se actualizaron los campos del pedido")
        else:
            # Crear el pedido principal
            pedido = Pedido.objects.create(
                tipo=tipo_pedido,
                forma_pago=forma_pago,
                numero_mesa=mesa if mesa else None,
                contacto=contacto,
                estado='pendiente',  # Guardar como pendiente
                total=total_pedido  # Guardar el total del pedido
            )
        
        logger.info(f"Pedido creado con ID: {pedido.id}")

        # Guardar productos del carrito en BD
        productos_guardados = []
        logger.info("=== GUARDANDO PRODUCTOS EN BD ===")
        logger.info(f"Total de productos a guardar: {len(productos_carrito)}")
        
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
            logger.info(f"Productos existentes: {list(productos_existentes.keys())}")
        
        for i, producto in enumerate(productos_carrito):
            logger.info(f"Guardando producto {i+1}: {producto}")
            logger.info(f"Procesando producto: {producto}")
            
            # Generar clave del producto
            if producto['tipo'] == 'Almuerzo':
                producto_key = f"almuerzo_{producto['sopa_id']}_{producto['segundo_id']}_{producto['jugo_id']}"
            elif producto['tipo'] == 'Sopa':
                producto_key = f"sopa_{producto['sopa_id']}_{producto['jugo_id']}"
            elif producto['tipo'] == 'Segundo':
                producto_key = f"segundo_{producto['segundo_id']}_{producto['jugo_id']}"
            
            # Si es edición y el producto existe, actualizar cantidad
            if pedido_id_editar and producto_key in productos_existentes:
                logger.info(f"Actualizando cantidad de producto existente: {producto_key}")
                producto_existente = productos_existentes[producto_key]['objeto']
                productos_procesados.add(producto_key)  # Marcar como procesado
                
                # Si la cantidad es 0, eliminar el producto
                if producto['cantidad'] <= 0:
                    producto_existente.delete()
                    logger.info(f"Producto eliminado por cantidad 0: {producto_key}")
                else:
                    producto_existente.cantidad = producto['cantidad']
                    producto_existente.observacion = producto.get('observacion', '')
                    producto_existente.save()
                    logger.info(f"Cantidad actualizada: {producto_existente.cantidad}")
                continue
            
            if producto['tipo'] == 'Almuerzo':
                logger.info("Creando PedidoAlmuerzo...")
                # Buscar los registros del menú del día correspondientes
                from menu.models import MenuDiaSopa, MenuDiaSegundo, MenuDiaJugo
                from django.utils import timezone
                
                try:
                    # Buscar el registro de sopa del menú del día
                    sopa_menu = MenuDiaSopa.objects.filter(sopa_id=producto['sopa_id']).first()
                    segundo_menu = MenuDiaSegundo.objects.filter(segundo_id=producto['segundo_id']).first()
                    jugo_menu = MenuDiaJugo.objects.filter(jugo_id=producto['jugo_id']).first()
                    
                    if sopa_menu and segundo_menu and jugo_menu:
                        pedido_almuerzo = PedidoAlmuerzo.objects.create(
                            pedido=pedido,
                            sopa=sopa_menu,
                            segundo=segundo_menu,
                            jugo=jugo_menu,
                            cantidad=producto['cantidad'],
                            precio_unitario=producto['precio_unitario'],
                            observacion=producto.get('observacion', '')
                        )
                        logger.info(f"PedidoAlmuerzo creado: {pedido_almuerzo}")
                        productos_guardados.append({
                            'tipo': 'Almuerzo',
                            'cantidad': producto['cantidad'],
                            'precio_unitario': float(producto['precio_unitario']),
                            'observacion': producto['observacion'],
                            'componentes': [
                                sopa_menu.sopa.nombre_plato,
                                segundo_menu.segundo.nombre_plato,
                                jugo_menu.jugo.nombre_plato
                            ]
                        })
                    else:
                        logger.error(f"No se encontraron registros del menú del día para: sopa_id={producto['sopa_id']}, segundo_id={producto['segundo_id']}, jugo_id={producto['jugo_id']}")
                        
                except Exception as e:
                    logger.error(f"Error al crear PedidoAlmuerzo: {e}")
                    
            elif producto['tipo'] == 'Sopa':
                logger.info("Creando PedidoSopa...")
                from menu.models import MenuDiaSopa, MenuDiaJugo
                
                try:
                    sopa_menu = MenuDiaSopa.objects.filter(sopa_id=producto['sopa_id']).first()
                    jugo_menu = MenuDiaJugo.objects.filter(jugo_id=producto['jugo_id']).first()
                    
                    if sopa_menu and jugo_menu:
                        pedido_sopa = PedidoSopa.objects.create(
                            pedido=pedido,
                            sopa=sopa_menu,
                            jugo=jugo_menu,
                            cantidad=producto['cantidad'],
                            precio_unitario=producto['precio_unitario'],
                            observacion=producto.get('observacion', '')
                        )
                        logger.info(f"PedidoSopa creado: {pedido_sopa}")
                        productos_guardados.append({
                            'tipo': 'Sopa',
                            'cantidad': producto['cantidad'],
                            'precio_unitario': float(producto['precio_unitario']),
                            'observacion': producto['observacion'],
                            'componentes': [
                                sopa_menu.sopa.nombre_plato,
                                jugo_menu.jugo.nombre_plato
                            ]
                        })
                    else:
                        logger.error(f"No se encontraron registros del menú del día para: sopa_id={producto['sopa_id']}, jugo_id={producto['jugo_id']}")
                        
                except Exception as e:
                    logger.error(f"Error al crear PedidoSopa: {e}")
                    
            elif producto['tipo'] == 'Segundo':
                logger.info("Creando PedidoSegundo...")
                from menu.models import MenuDiaSegundo, MenuDiaJugo
                
                try:
                    segundo_menu = MenuDiaSegundo.objects.filter(segundo_id=producto['segundo_id']).first()
                    jugo_menu = MenuDiaJugo.objects.filter(jugo_id=producto['jugo_id']).first()
                    
                    if segundo_menu and jugo_menu:
                        pedido_segundo = PedidoSegundo.objects.create(
                            pedido=pedido,
                            segundo=segundo_menu,
                            jugo=jugo_menu,
                            cantidad=producto['cantidad'],
                            precio_unitario=producto['precio_unitario'],
                            observacion=producto.get('observacion', '')
                        )
                        logger.info(f"PedidoSegundo creado: {pedido_segundo}")
                        productos_guardados.append({
                            'tipo': 'Segundo',
                            'cantidad': producto['cantidad'],
                            'precio_unitario': float(producto['precio_unitario']),
                            'observacion': producto['observacion'],
                            'componentes': [
                                segundo_menu.segundo.nombre_plato,
                                jugo_menu.jugo.nombre_plato
                            ]
                        })
                    else:
                        logger.error(f"No se encontraron registros del menú del día para: segundo_id={producto['segundo_id']}, jugo_id={producto['jugo_id']}")
                        
                except Exception as e:
                    logger.error(f"Error al crear PedidoSegundo: {e}")
            else:
                logger.warning(f"Tipo de producto desconocido: {producto['tipo']}")

        logger.info(f"Productos guardados: {len(productos_guardados)}")

        # Actualizar caja diaria según forma de pago
        if pedido_id_editar:
            # Ajustar por diferencia respecto al total anterior
            diferencia = total_pedido - total_anterior
            logger.info(f"Ajustando caja por diferencia: {diferencia}")
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

        # Reconstruir productos desde la BD para asegurar que se devuelvan todos
        logger.info("=== RECONSTRUYENDO PRODUCTOS DESDE BD ===")
        logger.info(f"Pedido ID: {pedido.id}")
        logger.info(f"Almuerzos en BD: {pedido.almuerzos.count()}")
        logger.info(f"Sopas en BD: {pedido.sopas.count()}")
        logger.info(f"Segundos en BD: {pedido.segundos.count()}")
        productos_reconstruidos = []
        
        # Almuerzos
        for almuerzo in pedido.almuerzos.all():
            productos_reconstruidos.append({
                'tipo': 'Almuerzo',
                'sopa_id': almuerzo.sopa.id,
                'segundo_id': almuerzo.segundo.id,
                'jugo_id': almuerzo.jugo.id,
                'cantidad': almuerzo.cantidad,
                'precio_unitario': float(almuerzo.precio_unitario),
                'observacion': almuerzo.observacion or '',
                'componentes': [
                    almuerzo.sopa.sopa.nombre_plato,
                    almuerzo.segundo.segundo.nombre_plato,
                    almuerzo.jugo.jugo.nombre_plato
                ]
            })
        
        # Sopas
        for sopa in pedido.sopas.all():
            productos_reconstruidos.append({
                'tipo': 'Sopa',
                'sopa_id': sopa.sopa.id,
                'jugo_id': sopa.jugo.id,
                'cantidad': sopa.cantidad,
                'precio_unitario': float(sopa.precio_unitario),
                'observacion': sopa.observacion or '',
                'componentes': [
                    sopa.sopa.sopa.nombre_plato,
                    sopa.jugo.jugo.nombre_plato
                ]
            })
        
        # Segundos
        for segundo in pedido.segundos.all():
            productos_reconstruidos.append({
                'tipo': 'Segundo',
                'segundo_id': segundo.segundo.id,
                'jugo_id': segundo.jugo.id,
                'cantidad': segundo.cantidad,
                'precio_unitario': float(segundo.precio_unitario),
                'observacion': segundo.observacion or '',
                'componentes': [
                    segundo.segundo.segundo.nombre_plato,
                    segundo.jugo.jugo.nombre_plato
                ]
            })
        
        # Si es edición, eliminar productos que ya no están en el carrito
        if pedido_id_editar:
            productos_a_eliminar = set(productos_existentes.keys()) - productos_procesados
            for producto_key in productos_a_eliminar:
                producto_existente = productos_existentes[producto_key]['objeto']
                producto_existente.delete()
                logger.info(f"Producto eliminado por no estar en carrito: {producto_key}")
        
        logger.info(f"Productos reconstruidos desde BD: {len(productos_reconstruidos)}")
        logger.info("Pedido guardado exitosamente")
        
        # Recalcular el total real desde la BD
        total_real = Decimal('0.00')
        for producto in productos_reconstruidos:
            total_real += Decimal(str(producto['precio_unitario'])) * Decimal(str(producto['cantidad']))
        
        # Actualizar el total del pedido si es diferente
        if pedido.total != total_real:
            pedido.total = total_real
            pedido.save()
            logger.info(f"Total actualizado: {pedido.total} -> {total_real}")

        return JsonResponse({
            'status': 'ok', 
            'pedido_id': pedido.id,
            'pedido_data': {
                'id': pedido.id,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
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
        logger.error(f"Error al marcar pedido como completado: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_pedido(request, pedido_id):
    try:
        pedido = Pedido.objects.get(id=pedido_id, estado='pendiente')
        
        # Obtener productos del pedido
        productos = []
        
        # Almuerzos
        for almuerzo in pedido.almuerzos.all():
            productos.append({
                'tipo': 'Almuerzo',
                'sopa_id': almuerzo.sopa.id,
                'segundo_id': almuerzo.segundo.id,
                'jugo_id': almuerzo.jugo.id,
                'cantidad': almuerzo.cantidad,
                'precio_unitario': float(almuerzo.precio_unitario),
                'observacion': almuerzo.observacion or '',
                'componentes': [
                    almuerzo.sopa.sopa.nombre_plato,
                    almuerzo.segundo.segundo.nombre_plato,
                    almuerzo.jugo.jugo.nombre_plato
                ]
            })
        
        # Sopas
        for sopa in pedido.sopas.all():
            productos.append({
                'tipo': 'Sopa',
                'sopa_id': sopa.sopa.id,
                'jugo_id': sopa.jugo.id,
                'cantidad': sopa.cantidad,
                'precio_unitario': float(sopa.precio_unitario),
                'observacion': sopa.observacion or '',
                'componentes': [
                    sopa.sopa.sopa.nombre_plato,
                    sopa.jugo.jugo.nombre_plato
                ]
            })
        
        # Segundos
        for segundo in pedido.segundos.all():
            productos.append({
                'tipo': 'Segundo',
                'segundo_id': segundo.segundo.id,
                'jugo_id': segundo.jugo.id,
                'cantidad': segundo.cantidad,
                'precio_unitario': float(segundo.precio_unitario),
                'observacion': segundo.observacion or '',
                'componentes': [
                    segundo.segundo.segundo.nombre_plato,
                    segundo.jugo.jugo.nombre_plato
                ]
            })
        
        return JsonResponse({
            'status': 'ok',
            'pedido': {
                'id': pedido.id,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
                'productos': productos
            }
        })
        
    except Pedido.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Pedido no encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Error al obtener pedido: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def obtener_pedidos_pendientes(request):
    try:
        # Obtener todos los pedidos pendientes
        pedidos = Pedido.objects.filter(estado='pendiente').order_by('-fecha_creacion')
        
        pedidos_data = []
        for pedido in pedidos:
            # Obtener productos del pedido
            productos = []
            
            # Almuerzos
            for almuerzo in pedido.almuerzos.all():
                productos.append({
                    'tipo': 'Almuerzo',
                    'sopa_id': almuerzo.sopa.id,
                    'segundo_id': almuerzo.segundo.id,
                    'jugo_id': almuerzo.jugo.id,
                    'cantidad': almuerzo.cantidad,
                    'precio_unitario': float(almuerzo.precio_unitario),
                    'observacion': almuerzo.observacion or '',
                    'componentes': [
                        almuerzo.sopa.sopa.nombre_plato,
                        almuerzo.segundo.segundo.nombre_plato,
                        almuerzo.jugo.jugo.nombre_plato
                    ]
                })
            
            # Sopas
            for sopa in pedido.sopas.all():
                productos.append({
                    'tipo': 'Sopa',
                    'sopa_id': sopa.sopa.id,
                    'jugo_id': sopa.jugo.id,
                    'cantidad': sopa.cantidad,
                    'precio_unitario': float(sopa.precio_unitario),
                    'observacion': sopa.observacion or '',
                    'componentes': [
                        sopa.sopa.sopa.nombre_plato,
                        sopa.jugo.jugo.nombre_plato
                    ]
                })
            
            # Segundos
            for segundo in pedido.segundos.all():
                productos.append({
                    'tipo': 'Segundo',
                    'segundo_id': segundo.segundo.id,
                    'jugo_id': segundo.jugo.id,
                    'cantidad': segundo.cantidad,
                    'precio_unitario': float(segundo.precio_unitario),
                    'observacion': segundo.observacion or '',
                    'componentes': [
                        segundo.segundo.segundo.nombre_plato,
                        segundo.jugo.jugo.nombre_plato
                    ]
                })
            
            pedidos_data.append({
                'id': pedido.id,
                'tipo': pedido.tipo,
                'forma_pago': pedido.forma_pago,
                'mesa': pedido.numero_mesa,
                'contacto': pedido.contacto,
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
        logger.error(f"Error al obtener pedidos pendientes: {str(e)}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f'Error interno: {str(e)}'}, status=500)
