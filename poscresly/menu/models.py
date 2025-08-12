from django.db import models

TIPO_CHOICES = [
    ('sopa', 'Sopa'),
    ('segundo', 'Segundo'),
    ('jugo', 'Jugo'),
    ('postre', 'Postre'),
    ('extra', 'Extra'),
]

PRODUCTO_CHOICES = [
    ('sopa', 'Sopa'),
    ('segundo', 'Segundo'),
    ('almuerzo', 'Almuerzo'),
    ('jugo', 'Jugo'),
    ('postre', 'Postre'),
    ('extra', 'Extra'),
]

class Plato(models.Model):
    nombre_plato = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100, choices=TIPO_CHOICES)

    def __str__(self):
        return f"{self.nombre_plato}"

class Producto(models.Model):
    nombre_producto = models.CharField(max_length=100, choices=PRODUCTO_CHOICES, unique=True)
    precio_servirse = models.DecimalField(max_digits=6, decimal_places=2)
    precio_llevar = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.get_nombre_producto_display()} - Servirse: ${self.precio_servirse} / Llevar: ${self.precio_llevar}"

class MenuDia(models.Model):
    fecha = models.DateField(unique=True)
    postre = models.ForeignKey(
        Plato,
        on_delete=models.CASCADE,
        limit_choices_to={'tipo': 'postre'},
        related_name='menus_postre',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Menú del día {self.fecha}"

class MenuDiaSopa(models.Model):
    menu = models.ForeignKey(MenuDia, on_delete=models.CASCADE, related_name='sopas')
    sopa = models.ForeignKey(Plato, on_delete=models.CASCADE, limit_choices_to={'tipo': 'sopa'})
    nota = models.CharField(max_length=100, blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.sopa} para {self.menu.fecha}"

class MenuDiaSegundo(models.Model):
    menu = models.ForeignKey(MenuDia, on_delete=models.CASCADE, related_name='segundos')
    segundo = models.ForeignKey(Plato, on_delete=models.CASCADE, limit_choices_to={'tipo': 'segundo'})
    nota = models.CharField(max_length=100, blank=True, null=True)
    cantidad = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.segundo} para {self.menu.fecha}"

class MenuDiaJugo(models.Model):
    menu = models.ForeignKey(MenuDia, on_delete=models.CASCADE, related_name='jugos')
    jugo = models.ForeignKey(Plato, on_delete=models.CASCADE, limit_choices_to={'tipo': 'jugo'})
    nota = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.jugo} para {self.menu.fecha}"

class MenuDiaExtra(models.Model):
    menu = models.ForeignKey(MenuDia, on_delete=models.CASCADE, related_name='extras')
    extra = models.ForeignKey(Plato, on_delete=models.CASCADE, limit_choices_to={'tipo': 'extra'})
    nota = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.extra} para {self.menu.fecha}"
