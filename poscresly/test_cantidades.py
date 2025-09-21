#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poscresly.settings')
django.setup()

from menu.models import MenuDia, MenuDiaSopa, MenuDiaSegundo
from datetime import date

def verificar_cantidades():
    """Verificar las cantidades del menú del día"""
    hoy = date.today()
    
    try:
        menu = MenuDia.objects.get(fecha=hoy)
        print(f"=== MENÚ DEL DÍA: {hoy} ===")
        
        # Verificar sopas
        print("\n--- SOPAS ---")
        sopas = MenuDiaSopa.objects.filter(menu=menu)
        for sopa in sopas:
            print(f"  {sopa.sopa.nombre_plato}:")
            print(f"    Cantidad configurada: {sopa.cantidad}")
            print(f"    Cantidad actual: {sopa.cantidad_actual}")
            print(f"    Diferencia: {sopa.cantidad - sopa.cantidad_actual}")
        
        # Verificar segundos
        print("\n--- SEGUNDOS ---")
        segundos = MenuDiaSegundo.objects.filter(menu=menu)
        for segundo in segundos:
            print(f"  {segundo.segundo.nombre_plato}:")
            print(f"    Cantidad configurada: {segundo.cantidad}")
            print(f"    Cantidad actual: {segundo.cantidad_actual}")
            print(f"    Diferencia: {segundo.cantidad - segundo.cantidad_actual}")
            
    except MenuDia.DoesNotExist:
        print(f"No hay menú configurado para {hoy}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verificar_cantidades()

