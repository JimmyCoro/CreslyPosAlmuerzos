"""
Módulo para imprimir pedidos en múltiples impresoras
"""
from impresora import ImpresoraMultiple
from datetime import datetime

def imprimir_pedido(pedido):
    """
    Imprime un pedido en todas las impresoras configuradas
    pedido: Objeto Pedido de Django
    """
    # Lista de IPs de las impresoras
    ips_impresoras = ["192.168.1.100", "192.168.1.110"]
    
    # Crear instancia de múltiples impresoras
    impresoras = ImpresoraMultiple(ips_impresoras)
    
    # Conectar a todas las impresoras
    if impresoras.conectar_todas():
        # Generar contenido del ticket
        contenido_ticket = generar_contenido_ticket(pedido)
        
        # Imprimir en todas las impresoras
        impresoras.imprimir_en_todas(contenido_ticket)
        
        # Desconectar todas las impresoras
        impresoras.desconectar_todas()
        
        return True
    else:
        print("[ERROR] No se pudo conectar a ninguna impresora")
        return False

def generar_contenido_ticket(pedido):
    """
    Genera el contenido del ticket basado en el pedido
    pedido: Objeto Pedido de Django
    """
    contenido = []
    
    # Encabezado
    contenido.append("RESTAURANTE CRESLY")
    contenido.append(f"Pedido #{pedido.numero_pedido_completo}")
    contenido.append(f"Fecha: {pedido.fecha_creacion.strftime('%Y-%m-%d')}")
    contenido.append(f"Hora: {pedido.fecha_creacion.strftime('%H:%M')}")
    contenido.append("")
    
    # Información del pedido
    if pedido.tipo == "Servirse":
        contenido.append(f"Mesa: {pedido.numero_mesa}")
    elif pedido.tipo == "Llevar":
        contenido.append("Tipo: Llevar")
    elif pedido.tipo == "Reservado":
        contenido.append("Tipo: Reservado")
    
    contenido.append("")
    
    # Productos del pedido
    contenido.append("PRODUCTOS:")
    
    # Aquí puedes agregar la lógica para obtener los productos del pedido
    # Por ahora, agregamos información básica
    contenido.append(f"Tipo: {pedido.tipo}")
    if pedido.contacto:
        contenido.append(f"Contacto: {pedido.contacto}")
    
    contenido.append("")
    
    # Total y forma de pago
    contenido.append(f"TOTAL: ${pedido.total:.2f}")
    contenido.append(f"Forma de pago: {pedido.forma_pago}")
    
    if pedido.observaciones_generales:
        contenido.append("")
        contenido.append("OBSERVACIONES:")
        contenido.append(pedido.observaciones_generales)
    
    return contenido

def probar_impresion_pedido():
    """
    Función para probar la impresión de un pedido simulado
    """
    # Simular un pedido (en la aplicación real, esto vendría de la base de datos)
    class PedidoSimulado:
        def __init__(self):
            self.numero_pedido_completo = "001"
            self.fecha_creacion = datetime.now()
            self.tipo = "Servirse"
            self.numero_mesa = "7"
            self.contacto = "Juan Pérez"
            self.total = 15.50
            self.forma_pago = "Efectivo"
            self.observaciones_generales = "Sin cebolla"
    
    pedido_simulado = PedidoSimulado()
    
    print("=== PRUEBA DE IMPRESIÓN DE PEDIDO ===")
    if imprimir_pedido(pedido_simulado):
        print("OK - Pedido impreso exitosamente en todas las impresoras")
    else:
        print("ERROR - Error al imprimir el pedido")

if __name__ == "__main__":
    probar_impresion_pedido()
