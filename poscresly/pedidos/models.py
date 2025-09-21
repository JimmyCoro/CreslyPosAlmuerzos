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
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total del pedido

    def __str__(self):
        return f"{self.tipo} - {self.forma_pago} - {self.fecha} - {self.estado}"
    
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
