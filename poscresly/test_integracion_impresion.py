#!/usr/bin/env python3
"""
Script para probar la integración de impresión múltiple
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poscresly.settings')
django.setup()

from pedidos.models import Pedido
from impresion.impresora import ImpresoraMultiple
from datetime import datetime

def probar_integracion():
    """
    Prueba la integración de impresión múltiple con un pedido real
    """
    print("=== PRUEBA DE INTEGRACIÓN DE IMPRESIÓN MÚLTIPLE ===")
    
    # Obtener el último pedido de la base de datos
    try:
        ultimo_pedido = Pedido.objects.last()
        if ultimo_pedido:
            print(f"Usando pedido real: #{ultimo_pedido.numero_pedido_completo}")
            print(f"Tipo: {ultimo_pedido.tipo}")
            print(f"Total: ${ultimo_pedido.total}")
        else:
            print("No hay pedidos en la base de datos")
            return
    except Exception as e:
        print(f"Error al obtener pedido: {e}")
        return
    
    # Simular el comando de cocina como lo hace la aplicación
    try:
        from datetime import datetime
        
        # Crear línea dinámica según el tipo de pedido
        linea_info = f"{ultimo_pedido.tipo.upper()}"
        
        if ultimo_pedido.tipo == 'Servirse' and ultimo_pedido.numero_mesa:
            espacios = 45 - len(f"{ultimo_pedido.tipo.upper()}.") - len(f"MESA: {ultimo_pedido.numero_mesa}")
            linea_info += " " * espacios + f"MESA: {ultimo_pedido.numero_mesa}"
        elif ultimo_pedido.tipo == 'Llevar' and ultimo_pedido.contacto:
            espacios = 45 - len(f"{ultimo_pedido.tipo.upper()}.") - len(f"{ultimo_pedido.contacto}")
            linea_info += " " * espacios + f"{ultimo_pedido.contacto.upper()}"
        elif ultimo_pedido.tipo == 'Reservado' and ultimo_pedido.contacto:
            subtipo_texto = f" ({ultimo_pedido.subtipo_reservado})" if ultimo_pedido.subtipo_reservado else ""
            espacios = 45 - len(f"{ultimo_pedido.tipo.upper()}.") - len(f"{ultimo_pedido.contacto}{subtipo_texto}")
            linea_info += " " * espacios + f"{ultimo_pedido.contacto.upper()}{subtipo_texto.upper()}"
        
        # Calcular espacios para la segunda línea
        espacios_segunda = 45 - len(f"Pedido #{ultimo_pedido.numero_pedido_completo}") - len(f"Hora: {datetime.now().strftime('%H:%M')}")
        
        comando_cocina = [
            linea_info,
            f"Pedido #{ultimo_pedido.numero_pedido_completo}" + " " * espacios_segunda + f"Hora: {datetime.now().strftime('%H:%M')}",
            "-" * 45,
            ""
        ]
        
        # Agregar observaciones generales si existen
        if ultimo_pedido.observaciones_generales:
            comando_cocina.append(f"  {ultimo_pedido.observaciones_generales}")
            comando_cocina.append("-" * 45)
        
        # Simular productos (en la aplicación real esto viene de la base de datos)
        comando_cocina.extend([
            "PRODUCTOS:",
            "1x Almuerzo",
            "  - Sopa del día",
            "  - Segundo del día", 
            "  - Jugo del día",
            "",
            "TOTAL: $" + str(ultimo_pedido.total),
            "Forma de pago: " + ultimo_pedido.forma_pago
        ])
        
        print("Contenido del comando de cocina:")
        for linea in comando_cocina:
            print(f"  {linea}")
        
        # Probar impresión múltiple
        print("\n=== PROBANDO IMPRESIÓN MÚLTIPLE ===")
        ips_impresoras = ["192.168.1.100", "192.168.1.110"]
        
        impresoras = ImpresoraMultiple(ips_impresoras)
        if impresoras.conectar_todas():
            impresoras.imprimir_en_todas(comando_cocina)
            impresoras.desconectar_todas()
            print("OK - Comando impreso en múltiples impresoras")
        else:
            print("ERROR - No se pudo conectar a ninguna impresora")
            
    except Exception as e:
        print(f"Error al procesar pedido: {e}")

if __name__ == "__main__":
    probar_integracion()

