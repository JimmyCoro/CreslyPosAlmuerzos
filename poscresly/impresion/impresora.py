from escpos.printer import Network
import socket

class ImpresoraTermica:
    def __init__(self, ip="192.168.1.100", puerto=9100):
        """
        Inicializa la conexión con la impresora térmica
        ip: Dirección IP de la impresora
        puerto: Puerto de comunicación (9100 es el estándar para impresoras térmicas)
        """
        self.ip = ip
        self.puerto = puerto
        self.printer = None
        
    def conectar(self):
        """
        Establece conexión con la impresora
        """
        try:
            # Crear objeto de impresora de red
            self.printer = Network(self.ip, port=self.puerto)
            print(f"[OK] Conectado a impresora en {self.ip}:{self.puerto}")
            return True
        except Exception as e:
            print(f"[ERROR] Error al conectar: {e}")
            return False
    
    def imprimir_ticket(self, contenido):
        """
        Imprime el contenido en la impresora térmica
        contenido: Lista de líneas a imprimir
        """
        if not self.printer:
            print("[ERROR] No hay conexión con la impresora")
            return False
            
        try:
            # Configurar impresora
            self.printer.set(align='left')  # Alinear a la izquierda
            self.printer.text("=" * 45 + "\n")  # Línea separadora
            
            # Imprimir cada línea del contenido
            for linea in contenido:
                self.printer.text(linea + "\n")
            
            # Línea final y cortar papel
            self.printer.text("=" * 45 )
            self.printer.cut()  # Cortar papel
            
            print("[OK] Ticket enviado a impresión")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error al imprimir: {e}")
            return False
    
    def desconectar(self):
        """
        Cierra la conexión con la impresora
        """
        if self.printer:
            self.printer.close()
            print("[INFO] Conexión cerrada")

# Función de prueba
def probar_impresora():
    """
    Función para probar la conexión con la impresora
    """
    impresora = ImpresoraTermica()
    
    if impresora.conectar():
        # Contenido de prueba
        ticket_prueba = [
            "RESTAURANTE CRESLY",
            "Pedido #001",
            "Fecha: 2024-01-15",
            "Hora: 14:30",
            "",
            "PRODUCTOS:",
            "1x Almuerzo - $15.00",
            "1x Sopa - $8.00",
            "",
            "TOTAL: $23.00",
            "Forma de pago: Efectivo"
        ]
        
        impresora.imprimir_ticket(ticket_prueba)
        impresora.desconectar()
    else:
        print("[ERROR] No se pudo conectar a la impresora")

if __name__ == "__main__":
    probar_impresora()
