from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.pizzeria_login, name='pizzeria_login'),
    path('logout/', views.pizzeria_logout, name='pizzeria_logout'),

    path('', views.inicio_pizzeria, name='pizzeria_inicio'),
    path('mesas/', views.mapa_mesas, name='pizzeria_mapa_mesas'),
    path('mesas/gestionar/', views.gestionar_mesas, name='pizzeria_gestionar_mesas'),
    path('ordenes/', views.ordenes_en_curso, name='pizzeria_ordenes'),
    path('delivery/', views.ordenes_delivery, name='pizzeria_delivery'),
    path('ordenes/<int:pedido_id>/', views.detalle_orden_pizzeria, name='pizzeria_detalle_orden'),
    path('ordenes/<int:pedido_id>/cobrar/', views.cobrar_orden_pizzeria, name='pizzeria_cobrar_orden'),
    path('nueva-orden/', views.nueva_orden, name='pizzeria_nueva_orden'),

    path('pedido/mesa/<int:mesa_id>/', views.tomar_pedido_pizzeria, name='pizzeria_tomar_pedido_mesa'),
    path('pedido/llevar/', views.tomar_pedido_pizzeria, name='pizzeria_tomar_pedido_llevar'),

    path('ajax/mesas/crear/', views.crear_mesa_pizzeria, name='pizzeria_crear_mesa'),
    path('ajax/mesas/<int:mesa_id>/actualizar/', views.actualizar_mesa_pizzeria, name='pizzeria_actualizar_mesa'),
    path('ajax/mesas/<int:mesa_id>/mover/', views.mover_mesa_pizzeria, name='pizzeria_mover_mesa'),
    path('ajax/mesas/<int:mesa_id>/estado/', views.cambiar_estado_mesa_pizzeria, name='pizzeria_cambiar_estado_mesa'),

    path('ajax/calcular-precio/', views.calcular_precio_pizza_ajax, name='pizzeria_calcular_precio'),
    path('ajax/guardar-pedido/', views.guardar_pedido_pizzeria, name='pizzeria_guardar_pedido'),
    path('ajax/pedido/<int:pedido_id>/procesar-cobro/', views.procesar_cobro_pedido, name='pizzeria_procesar_cobro'),
    path('ajax/pedido/<int:pedido_id>/cancelar/', views.cancelar_pedido_pizzeria, name='pizzeria_cancelar_pedido'),
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
]
