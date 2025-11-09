#!/usr/bin/env python3
"""
Script de diagnóstico completo para el problema de numeración
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

def diagnostico_completo():
    """
    Diagnóstico completo del problema de numeración
    """
    print("=== DIAGNOSTICO COMPLETO DE NUMERACION ===")
    
    # Obtener todos los pedidos de hoy
    today = timezone.now().date()
    pedidos_hoy = Pedido.objects.filter(fecha=today).order_by('fecha_creacion')
    
    print(f"Pedidos de hoy ({today}): {pedidos_hoy.count()}")
    print()
    
    if pedidos_hoy.count() == 0:
        print("No hay pedidos de hoy. Creando pedidos de prueba...")
        crear_pedidos_prueba()
        pedidos_hoy = Pedido.objects.filter(fecha=today).order_by('fecha_creacion')
    
    print("=== DETALLES DE CADA PEDIDO ===")
    for i, pedido in enumerate(pedidos_hoy, 1):
        print(f"Pedido {i}:")
        print(f"  - ID: {pedido.id}")
        print(f"  - numero_dia: {pedido.numero_dia}")
        print(f"  - numero_pedido_completo: {pedido.numero_pedido_completo}")
        print(f"  - Tipo: {pedido.tipo}")
        print(f"  - Contacto: {pedido.contacto}")
        print(f"  - Fecha creación: {pedido.fecha_creacion}")
        print(f"  - Estado: {pedido.estado}")
        print()
    
    # Verificar duplicados
    numeros_dia = [p.numero_dia for p in pedidos_hoy]
    duplicados = [num for num in set(numeros_dia) if numeros_dia.count(num) > 1]
    
    if duplicados:
        print(f"PROBLEMA: Numeros duplicados en numero_dia: {duplicados}")
        print("Esto explica por que todos aparecen como #001")
    else:
        print("OK - No hay numeros duplicados en numero_dia")
    
    # Verificar si todos tienen el mismo numero_pedido_completo
    numeros_completos = [p.numero_pedido_completo for p in pedidos_hoy]
    duplicados_completos = [num for num in set(numeros_completos) if numeros_completos.count(num) > 1]
    
    if duplicados_completos:
        print(f"PROBLEMA: Numeros duplicados en numero_pedido_completo: {duplicados_completos}")
    else:
        print("OK - No hay numeros duplicados en numero_pedido_completo")
    
    # Verificar la secuencia
    print("\n=== VERIFICANDO SECUENCIA ===")
    numeros_ordenados = sorted([p.numero_dia for p in pedidos_hoy])
    print(f"Numeros ordenados: {numeros_ordenados}")
    
    # Verificar si la secuencia es correcta
    secuencia_correcta = True
    for i in range(len(numeros_ordenados)):
        if numeros_ordenados[i] != i + 1:
            secuencia_correcta = False
            break
    
    if secuencia_correcta:
        print("OK - La secuencia es correcta")
    else:
        print("PROBLEMA - La secuencia no es correcta")
    
    # Verificar el último número
    ultimo_pedido = pedidos_hoy.order_by('-numero_dia').first()
    if ultimo_pedido:
        print(f"Ultimo numero del dia: {ultimo_pedido.numero_dia}")
        print(f"Proximo numero deberia ser: {ultimo_pedido.numero_dia + 1}")
    
    print("\n=== SIMULANDO SERIALIZACION ===")
    for pedido in pedidos_hoy:
        print(f"Pedido ID {pedido.id}:")
        print(f"  - numero_dia: {pedido.numero_dia}")
        print(f"  - numero_pedido_completo: {pedido.numero_pedido_completo}")
        print(f"  - Serializado: {{'id': {pedido.id}, 'numero_dia': {pedido.numero_dia}, 'numero_pedido_completo': '{pedido.numero_pedido_completo}'}}")
        print()

def crear_pedidos_prueba():
    """
    Crea pedidos de prueba
    """
    print("Creando pedidos de prueba...")
    
    # Limpiar pedidos existentes de hoy
    today = timezone.now().date()
    Pedido.objects.filter(fecha=today).delete()
    
    # Crear 3 pedidos de prueba
    for i in range(3):
        pedido = Pedido.objects.create(
            tipo='Llevar',
            forma_pago='Efectivo',
            contacto=f'Cliente {i+1}',
            total=10.50 + i,
            estado='pendiente'
        )
        print(f"  - Creado pedido {i+1}: ID={pedido.id}, numero_dia={pedido.numero_dia}")

if __name__ == "__main__":
    diagnostico_completo()

