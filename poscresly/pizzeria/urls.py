from django.urls import path

from . import views, views_caja

urlpatterns = [
    path('login/', views.pizzeria_login, name='pizzeria_login'),
    path('logout/', views.pizzeria_logout, name='pizzeria_logout'),

    path('', views.inicio_pizzeria, name='pizzeria_inicio'),
    path('movil/', views.inicio_movil, name='pizzeria_inicio_movil'),
    path('mesas/', views.mapa_mesas, name='pizzeria_mapa_mesas'),
    path('mesas/gestionar/', views.gestionar_mesas, name='pizzeria_gestionar_mesas'),
    path('ordenes/', views.ordenes_en_curso, name='pizzeria_ordenes'),
    path('delivery/', views.ordenes_delivery, name='pizzeria_delivery'),
    path('ordenes/<int:pedido_id>/', views.detalle_orden_pizzeria, name='pizzeria_detalle_orden'),
    path('ordenes/<int:pedido_id>/cobrar/', views.cobrar_orden_pizzeria, name='pizzeria_cobrar_orden'),
    path('ordenes/<int:pedido_id>/cobrar/dividir/', views.cobrar_dividir_pizzeria, name='pizzeria_cobrar_dividir'),
    path('ordenes/<int:pedido_id>/cobrar/dividir/persona/agregar/', views.cobrar_dividir_agregar_persona, name='pizzeria_cobrar_dividir_agregar'),
    path('ordenes/<int:pedido_id>/cobrar/dividir/persona/<int:indice>/quitar/', views.cobrar_dividir_quitar_persona, name='pizzeria_cobrar_dividir_quitar'),
    path('ordenes/<int:pedido_id>/cobrar/dividir/persona/<int:indice>/activar/', views.cobrar_dividir_activar_persona, name='pizzeria_cobrar_dividir_activar'),
    path('ordenes/<int:pedido_id>/cobrar/dividir/asignar/', views.cobrar_dividir_asignar, name='pizzeria_cobrar_dividir_asignar'),
    path('ordenes/<int:pedido_id>/cobrar/dividir/repartir-igual/', views.cobrar_dividir_repartir_igual, name='pizzeria_cobrar_dividir_repartir_igual'),
    path('ordenes/<int:pedido_id>/cobrar/persona/<int:numero>/', views.cobrar_persona_pizzeria, name='pizzeria_cobrar_persona'),
    path('nueva-orden/', views.nueva_orden, name='pizzeria_nueva_orden'),

    path('pedido/mesa/<int:mesa_id>/', views.tomar_pedido_pizzeria, name='pizzeria_tomar_pedido_mesa'),

    path('ajax/mesas/crear/', views.crear_mesa_pizzeria, name='pizzeria_crear_mesa'),
    path('ajax/mesas/<int:mesa_id>/actualizar/', views.actualizar_mesa_pizzeria, name='pizzeria_actualizar_mesa'),
    path('ajax/mesas/<int:mesa_id>/mover/', views.mover_mesa_pizzeria, name='pizzeria_mover_mesa'),
    path('ajax/mesas/<int:mesa_id>/estado/', views.cambiar_estado_mesa_pizzeria, name='pizzeria_cambiar_estado_mesa'),

    path('ajax/calcular-precio/', views.calcular_precio_pizza_ajax, name='pizzeria_calcular_precio'),
    path('ajax/guardar-pedido/', views.guardar_pedido_pizzeria, name='pizzeria_guardar_pedido'),
    path('ajax/pedido/<int:pedido_id>/procesar-cobro/', views.procesar_cobro_pedido, name='pizzeria_procesar_cobro'),
    path('ajax/pedido/<int:pedido_id>/cancelar/', views.cancelar_pedido_pizzeria, name='pizzeria_cancelar_pedido'),
    path('ajax/pedido/<int:pedido_id>/reimprimir-comanda/', views.reimprimir_comanda_pizzeria, name='pizzeria_reimprimir_comanda'),
    path('ajax/pedido/<int:pedido_id>/precuenta/', views.imprimir_precuenta_pizzeria, name='pizzeria_imprimir_precuenta'),
    path('ajax/pedido/<int:pedido_id>/', views.obtener_pedido_pizzeria, name='pizzeria_obtener_pedido'),
    path('ajax/pedidos-abiertos/', views.obtener_pedidos_abiertos_pizzeria, name='pizzeria_pedidos_abiertos'),
    path('ajax/item-preparacion/<int:item_id>/avanzar/', views.avanzar_estado_item_preparacion, name='pizzeria_avanzar_item_preparacion'),
    path('ajax/item-preparacion/<int:item_id>/estado/', views.establecer_estado_item_preparacion, name='pizzeria_establecer_estado_item_preparacion'),
    path('ajax/item-preparacion/<int:item_id>/detalle/', views.detalle_item_preparacion, name='pizzeria_detalle_item_preparacion'),
    path('ajax/item-preparacion/<int:item_id>/editar/', views.editar_item_preparacion, name='pizzeria_editar_item_preparacion'),
    path('ajax/item-preparacion/<int:item_id>/duplicar/', views.duplicar_item_preparacion, name='pizzeria_duplicar_item_preparacion'),
    path('ajax/item-preparacion/<int:item_id>/reimprimir/', views.reimprimir_item_preparacion, name='pizzeria_reimprimir_item_preparacion'),
    path('ajax/item-preparacion/<int:item_id>/quitar/', views.quitar_item_preparacion, name='pizzeria_quitar_item_preparacion'),

    path('caja/', views.dashboard_caja_pizzeria, name='pizzeria_dashboard_caja'),
    path('caja/abrir/', views.abrir_caja_pizzeria, name='pizzeria_abrir_caja'),
    path('caja/cerrar/', views.cerrar_caja_pizzeria, name='pizzeria_cerrar_caja'),

    path('caja/turno/', views_caja.estado_caja, name='pizzeria_caja'),
    path('caja/turno/abrir/', views_caja.abrir_caja, name='pizzeria_caja_abrir'),
    path('caja/turno/movimientos/', views_caja.movimientos_caja, name='pizzeria_caja_movimientos'),
    path('caja/turno/cortes/', views_caja.cortes_caja, name='pizzeria_caja_cortes'),
    path('caja/turno/retiro/', views_caja.registrar_retiro, name='pizzeria_caja_retiro'),
    path('caja/turno/movimiento/', views_caja.registrar_movimiento, name='pizzeria_caja_movimiento'),
]
