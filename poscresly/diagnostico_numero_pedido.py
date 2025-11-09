#!/usr/bin/env python3
"""
Script para diagnosticar el problema de numeración de pedidos
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

def diagnosticar_numeracion():
    """
    Diagnostica el problema de numeración de pedidos
    """
    print("=== DIAGNÓSTICO DE NUMERACIÓN DE PEDIDOS ===")
    
    # Obtener todos los pedidos de hoy
    today = timezone.now().date()
    pedidos_hoy = Pedido.objects.filter(fecha=today).order_by('fecha_creacion')
    
    print(f"Pedidos de hoy ({today}): {pedidos_hoy.count()}")
    print()
    
    for i, pedido in enumerate(pedidos_hoy, 1):
        print(f"Pedido {i}:")
        print(f"  - ID: {pedido.id}")
        print(f"  - numero_dia: {pedido.numero_dia}")
        print(f"  - numero_pedido_completo: {pedido.numero_pedido_completo}")
        print(f"  - Tipo: {pedido.tipo}")
        print(f"  - Fecha creación: {pedido.fecha_creacion}")
        print(f"  - Estado: {pedido.estado}")
        print()
    
    # Verificar si hay duplicados en numero_dia
    numeros_dia = [p.numero_dia for p in pedidos_hoy]
    duplicados = [num for num in set(numeros_dia) if numeros_dia.count(num) > 1]
    
    if duplicados:
        print(f"PROBLEMA DETECTADO: Numeros duplicados: {duplicados}")
        print("Esto explica por que todos aparecen como #001")
    else:
        print("OK - No hay numeros duplicados en numero_dia")
    
    # Verificar el último número del día
    ultimo_pedido = pedidos_hoy.order_by('-numero_dia').first()
    if ultimo_pedido:
        print(f"Último número del día: {ultimo_pedido.numero_dia}")
        print(f"Próximo número debería ser: {ultimo_pedido.numero_dia + 1}")
    
    print("\n=== VERIFICANDO MIGRACIONES ===")
    from django.db import connection
    with connection.cursor() as cursor:
        # Para PostgreSQL
        cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'pedidos_pedido';")
        columns = cursor.fetchall()
        print("Columnas de la tabla pedidos_pedido:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
    
    # Verificar si numero_dia está en la tabla
    numero_dia_exists = any(col[0] == 'numero_dia' for col in columns)
    if numero_dia_exists:
        print("OK - Campo numero_dia existe en la base de datos")
    else:
        print("PROBLEMA: Campo numero_dia NO existe en la base de datos")
        print("Necesitas ejecutar: python manage.py makemigrations && python manage.py migrate")

if __name__ == "__main__":
    diagnosticar_numeracion()
