from django.urls import path
from pedidos import views as pedidos_views
from . import views, views_auth, views_usuarios

urlpatterns = [
    path('', views.inicio, name='inicio'),

    # Cuenta
    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('cambiar-password/', views_auth.cambiar_password, name='cambiar_password'),

    # Configuración → Usuarios (solo administradores)
    path('configuracion/usuarios/', views_usuarios.usuarios_lista, name='usuarios'),
    path('configuracion/usuarios/nuevo/', views_usuarios.usuario_crear, name='usuario_crear'),
    path('configuracion/usuarios/<int:user_id>/', views_usuarios.usuario_editar, name='usuario_editar'),
    path('configuracion/usuarios/<int:user_id>/password/', views_usuarios.usuario_password, name='usuario_password'),

    path('agregar-al-carrito/', pedidos_views.agregar_al_carrito, name='agregar_al_carrito'),
    path('guardar-pedido/', pedidos_views.guardar_pedido, name='guardar_pedido'),
    path('marcar-completado/', pedidos_views.marcar_pedido_completado, name='marcar_pedido_completado'),
    path('obtener-pedido/<int:pedido_id>/', pedidos_views.obtener_pedido, name='obtener_pedido'),
    path('obtener-pedidos-pendientes/', pedidos_views.obtener_pedidos_pendientes, name='obtener_pedidos_pendientes'),
    path('eliminar-pedido/', pedidos_views.eliminar_pedido, name='eliminar_pedido'),
    path('obtener-cantidades-actualizadas/', pedidos_views.obtener_cantidades_actualizadas, name='obtener_cantidades_actualizadas'),
    path('obtener-cantidades-modal/', pedidos_views.obtener_cantidades_modal, name='obtener_cantidades_modal'),

    # Nuevas URLs para selección múltiple de pedidos
    path('marcar-pedidos-completados/', pedidos_views.marcar_pedidos_completados, name='marcar_pedidos_completados'),
    path('obtener-pedidos-por-tipo/', pedidos_views.obtener_pedidos_por_tipo, name='obtener_pedidos_por_tipo'),

    # URL para obtener contadores de tabs
    path('obtener-contadores-tabs/', pedidos_views.obtener_contadores_tabs, name='obtener_contadores_tabs'),
]
