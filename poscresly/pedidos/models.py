from django.db import models
from menu.models import MenuDiaSopa, MenuDiaSegundo, MenuDiaJugo
from django.utils import timezone

class Pedido( models.Model):
    
    TIPO_CHOICES = [
        ('Servirse', 'Servirse'),
        ('Reservado', 'Reservado'),
        ('Llevar', 'Llevar'),
    ]

    FORMA_PAGO = [
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia')
    ]

    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
    ]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    forma_pago = models.CharField(max_length=15, choices=FORMA_PAGO, default='Efectivo')
    fecha = models.DateField(auto_now_add=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    numero_mesa = models.IntegerField(blank=True, null=True)
    contacto = models.CharField(max_length=100, blank=True, null=True)  # Puede ser nombre o teléfono
    subtipo_reservado = models.CharField(max_length=20, blank=True, null=True)  # Para pedidos reservados: 'servirse' o 'llevar'
    observaciones_generales = models.TextField(blank=True, null=True)  # Observaciones generales del pedido
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total del pedido
    numero_dia = models.PositiveIntegerField(default=1)  # Número de pedido del día (se reinicia cada día)

    def __str__(self):
        return f"{self.tipo} - {self.forma_pago} - {self.fecha} - {self.estado}"
    
    def save(self, *args, **kwargs):
        # Si es un nuevo pedido (no tiene ID), asignar el siguiente número del día
        if not self.pk:
            today = timezone.now().date()
            ultimo_pedido_hoy = Pedido.objects.filter(fecha=today).order_by('-numero_dia').first()
            
            if ultimo_pedido_hoy:
                self.numero_dia = ultimo_pedido_hoy.numero_dia + 1
            else:
                self.numero_dia = 1
        
        super().save(*args, **kwargs)
    
    @property
    def numero_pedido_completo(self):
        """Retorna el número de pedido del día formateado: 001, 002, 003..."""
        return f"{self.numero_dia:03d}"
    
class PedidoAlmuerzo(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='almuerzos')
    sopa = models.ForeignKey(MenuDiaSopa, on_delete=models.PROTECT)
    segundo = models.ForeignKey(MenuDiaSegundo, on_delete=models.PROTECT)
    jugo = models.ForeignKey(MenuDiaJugo, on_delete=models.PROTECT)
    postre = models.CharField(max_length=100)  
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacion = models.CharField(max_length=200, blank=True, null=True)

class PedidoSopa(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='sopas')
    sopa = models.ForeignKey(MenuDiaSopa, on_delete=models.PROTECT)
    jugo = models.ForeignKey(MenuDiaJugo, on_delete=models.PROTECT)
    postre = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacion = models.CharField(max_length=200, blank=True, null=True)

class PedidoSegundo(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='segundos')
    segundo = models.ForeignKey(MenuDiaSegundo, on_delete=models.PROTECT)
    jugo = models.ForeignKey(MenuDiaJugo, on_delete=models.PROTECT)
    postre = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observacion = models.CharField(max_length=200, blank=True, null=True)
