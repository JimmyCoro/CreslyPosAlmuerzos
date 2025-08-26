from django.urls import path
from pedidos import views as pedidos_views
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('agregar-al-carrito/', pedidos_views.agregar_al_carrito, name='agregar_al_carrito'),
    path('guardar-pedido/', pedidos_views.guardar_pedido, name='guardar_pedido'),
    path('marcar-completado/', pedidos_views.marcar_pedido_completado, name='marcar_pedido_completado'),
    path('obtener-pedido/<int:pedido_id>/', pedidos_views.obtener_pedido, name='obtener_pedido'),
    path('obtener-pedidos-pendientes/', pedidos_views.obtener_pedidos_pendientes, name='obtener_pedidos_pendientes'),
    path('eliminar-pedido/', pedidos_views.eliminar_pedido, name='eliminar_pedido'),
    path('obtener-cantidades-actualizadas/', pedidos_views.obtener_cantidades_actualizadas, name='obtener_cantidades_actualizadas'),
    
    # Nuevas URLs para selección múltiple de pedidos
    path('marcar-pedidos-completados/', pedidos_views.marcar_pedidos_completados, name='marcar_pedidos_completados'),
    path('obtener-pedidos-por-tipo/', pedidos_views.obtener_pedidos_por_tipo, name='obtener_pedidos_por_tipo'),
]
