from django.db import models
from django.utils import timezone

# Create your models here.

ESTADOS = [
    ('abierta', 'Abierta'),
    ('cerrada', 'Cerrada'),
]

class CajaDiaria(models.Model):
    fecha = models.DateField(unique=True)  # Una caja por día
    estado = models.CharField(max_length=20, choices=ESTADOS, default='abierta')
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Caja Diaria'
        verbose_name_plural = 'Cajas Diarias'
        ordering = ['-fecha']

    def __str__(self):
        return f"Caja {self.fecha} - {self.estado.title()}"

    def hora_apertura(self):
        """Retorna solo la hora de apertura"""
        return self.fecha_apertura.time() if self.fecha_apertura else None

    def hora_cierre(self):
        """Retorna solo la hora de cierre"""
        return self.fecha_cierre.time() if self.fecha_cierre else None

    def duracion_caja(self):
        """Calcula la duración que estuvo abierta la caja"""
        if self.fecha_cierre and self.fecha_apertura:
            return self.fecha_cierre - self.fecha_apertura
        return None

class CajaEfectivo(models.Model):
    caja_diaria = models.OneToOneField(CajaDiaria, on_delete=models.CASCADE, related_name='caja_efectivo')
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_gastos = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Caja Efectivo'
        verbose_name_plural = 'Cajas Efectivo'

    def __str__(self):
        return f"Efectivo {self.caja_diaria.fecha}"

class CajaTransferencia(models.Model):
    caja_diaria = models.OneToOneField(CajaDiaria, on_delete=models.CASCADE, related_name='caja_transferencia')
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Caja Transferencia'
        verbose_name_plural = 'Cajas Transferencia'

    def __str__(self):
        return f"Transferencia {self.caja_diaria.fecha}"

class Gasto(models.Model):
    caja_diaria = models.ForeignKey(CajaDiaria, on_delete=models.CASCADE, related_name='gastos')
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    categoria = models.CharField(max_length=50, choices=[
        ('insumos', 'Insumos'),
        ('servicios', 'Servicios'),
        ('otros', 'Otros')
    ], default='otros')

    class Meta:
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"

