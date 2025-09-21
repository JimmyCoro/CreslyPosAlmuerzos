from django.urls import path
from . import views

urlpatterns = [
    # Dashboard principal de caja
    path('', views.dashboard_caja, name='dashboard_caja'),
    
    # Operaciones de caja
    path('abrir/', views.abrir_caja, name='abrir_caja'),
    path('cerrar/', views.cerrar_caja, name='cerrar_caja'),
]
