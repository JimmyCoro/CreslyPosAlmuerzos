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

class ImpresoraMultiple:
    def __init__(self, ips_impresoras=None):
        """
        Inicializa múltiples impresoras térmicas
        ips_impresoras: Lista de IPs de las impresoras
        """
        if ips_impresoras is None:
            ips_impresoras = ["192.168.1.100", "192.168.1.110"]  # IPs por defecto
        
        self.impresoras = []
        for ip in ips_impresoras:
            self.impresoras.append(ImpresoraTermica(ip))
        
    def conectar_todas(self):
        """
        Establece conexión con todas las impresoras
        """
        conexiones_exitosas = 0
        for impresora in self.impresoras:
            if impresora.conectar():
                conexiones_exitosas += 1
        
        print(f"[INFO] {conexiones_exitosas}/{len(self.impresoras)} impresoras conectadas")
        return conexiones_exitosas > 0
    
    def imprimir_en_todas(self, contenido):
        """
        Imprime el contenido en todas las impresoras conectadas
        contenido: Lista de líneas a imprimir
        """
        impresiones_exitosas = 0
        
        for i, impresora in enumerate(self.impresoras):
            if impresora.printer:
                try:
                    print(f"[INFO] Imprimiendo en impresora {i+1} ({impresora.ip})")
                    impresora.imprimir_ticket(contenido)
                    impresiones_exitosas += 1
                except Exception as e:
                    print(f"[ERROR] Error al imprimir en {impresora.ip}: {e}")
        
        print(f"[INFO] {impresiones_exitosas}/{len(self.impresoras)} impresiones exitosas")
        return impresiones_exitosas > 0
    
    def desconectar_todas(self):
        """
        Cierra la conexión con todas las impresoras
        """
        for impresora in self.impresoras:
            impresora.desconectar()

# Función de prueba para una impresora
def probar_impresora():
    """
    Función para probar la conexión con una impresora
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

# Función de prueba para múltiples impresoras
def probar_impresoras_multiples():
    """
    Función para probar la conexión con múltiples impresoras
    """
    # Lista de IPs de las impresoras
    ips_impresoras = ["192.168.1.100", "192.168.1.110"]
    
    impresoras = ImpresoraMultiple(ips_impresoras)
    
    if impresoras.conectar_todas():
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
        
        impresoras.imprimir_en_todas(ticket_prueba)
        impresoras.desconectar_todas()
    else:
        print("[ERROR] No se pudo conectar a ninguna impresora")

if __name__ == "__main__":
    print("=== PRUEBA DE MÚLTIPLES IMPRESORAS ===")
    probar_impresoras_multiples()
