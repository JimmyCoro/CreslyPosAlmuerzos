from django.urls import path

from . import views

urlpatterns = [
    path('', views.menu_dia, name='menu'),
    path('configurar/', views.configurar_menu, name='menu_configurar'),
    path('publicar/', views.publicar_menu, name='menu_publicar'),
    path('platos/crear/', views.crear_plato, name='menu_crear_plato'),
]
