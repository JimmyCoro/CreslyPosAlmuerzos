from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.pizzeria_login, name='pizzeria_login'),
    path('logout/', views.pizzeria_logout, name='pizzeria_logout'),

    path('', views.mapa_mesas, name='pizzeria_mapa_mesas'),

    path('pedido/mesa/<int:mesa_id>/', views.tomar_pedido_pizzeria, name='pizzeria_tomar_pedido_mesa'),
    path('pedido/llevar/', views.tomar_pedido_pizzeria, name='pizzeria_tomar_pedido_llevar'),

    path('ajax/calcular-precio/', views.calcular_precio_pizza_ajax, name='pizzeria_calcular_precio'),
    path('ajax/guardar-pedido/', views.guardar_pedido_pizzeria, name='pizzeria_guardar_pedido'),
    path('ajax/cerrar-cobrar/', views.cerrar_y_cobrar_pedido, name='pizzeria_cerrar_cobrar'),
    path('ajax/pedido/<int:pedido_id>/', views.obtener_pedido_pizzeria, name='pizzeria_obtener_pedido'),
    path('ajax/pedidos-abiertos/', views.obtener_pedidos_abiertos_pizzeria, name='pizzeria_pedidos_abiertos'),

    path('caja/', views.dashboard_caja_pizzeria, name='pizzeria_dashboard_caja'),
    path('caja/abrir/', views.abrir_caja_pizzeria, name='pizzeria_abrir_caja'),
    path('caja/cerrar/', views.cerrar_caja_pizzeria, name='pizzeria_cerrar_caja'),
]
