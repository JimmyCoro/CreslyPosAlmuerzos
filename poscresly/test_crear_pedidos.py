#!/usr/bin/env python3
"""
Script para crear pedidos de prueba y verificar la numeración
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

def crear_pedidos_prueba():
    """
    Crea pedidos de prueba para verificar la numeración
    """
    print("=== CREANDO PEDIDOS DE PRUEBA ===")
    
    # Limpiar pedidos existentes de hoy
    today = timezone.now().date()
    Pedido.objects.filter(fecha=today).delete()
    print(f"Pedidos de hoy eliminados")
    
    # Crear 3 pedidos de prueba
    for i in range(3):
        print(f"\nCreando pedido {i+1}...")
        
        pedido = Pedido.objects.create(
            tipo='Llevar',
            forma_pago='Efectivo',
            contacto=f'Cliente {i+1}',
            total=10.50 + i,
            estado='pendiente'
        )
        
        print(f"  - ID: {pedido.id}")
        print(f"  - numero_dia: {pedido.numero_dia}")
        print(f"  - numero_pedido_completo: {pedido.numero_pedido_completo}")
        print(f"  - Tipo: {pedido.tipo}")
        print(f"  - Contacto: {pedido.contacto}")
    
    print("\n=== VERIFICANDO RESULTADOS ===")
    pedidos_creados = Pedido.objects.filter(fecha=today).order_by('fecha_creacion')
    
    for i, pedido in enumerate(pedidos_creados, 1):
        print(f"Pedido {i}:")
        print(f"  - numero_dia: {pedido.numero_dia}")
        print(f"  - numero_pedido_completo: {pedido.numero_pedido_completo}")
        print(f"  - Contacto: {pedido.contacto}")
        print()
    
    # Verificar si hay duplicados
    numeros_dia = [p.numero_dia for p in pedidos_creados]
    duplicados = [num for num in set(numeros_dia) if numeros_dia.count(num) > 1]
    
    if duplicados:
        print(f"PROBLEMA: Numeros duplicados: {duplicados}")
    else:
        print("OK - No hay numeros duplicados")

if __name__ == "__main__":
    crear_pedidos_prueba()

