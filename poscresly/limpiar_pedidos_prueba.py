#!/usr/bin/env python3
"""
Script para limpiar pedidos de prueba
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poscresly.settings')
django.setup()

from pedidos.models import Pedido
from django.utils import timezone

def limpiar_pedidos_prueba():
    """
    Limpia los pedidos de prueba
    """
    print("=== LIMPIANDO PEDIDOS DE PRUEBA ===")
    
    today = timezone.now().date()
    pedidos_hoy = Pedido.objects.filter(fecha=today)
    
    print(f"Pedidos de hoy: {pedidos_hoy.count()}")
    
    # Eliminar todos los pedidos de hoy
    pedidos_hoy.delete()
    
    print("Pedidos de hoy eliminados")
    
    # Verificar que se eliminaron
    pedidos_restantes = Pedido.objects.filter(fecha=today)
    print(f"Pedidos restantes: {pedidos_restantes.count()}")

if __name__ == "__main__":
    limpiar_pedidos_prueba()


