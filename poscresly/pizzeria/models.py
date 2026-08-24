from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Mesa(models.Model):
    ESTADOS = [
        ('libre', 'Libre'),
        ('reservada', 'Reservada'),
        ('ocupada', 'Ocupada'),
        ('por_cobrar', 'Por cobrar'),
    ]
    FORMAS = [
        ('redonda', 'Redonda'),
        ('cuadrada', 'Cuadrada'),
    ]

    numero = models.PositiveIntegerField(unique=True)
    nombre = models.CharField(max_length=50, blank=True)
    zona = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='libre')
    pos_x = models.FloatField(default=0)
    pos_y = models.FloatField(default=0)
    forma = models.CharField(max_length=10, choices=FORMAS, default='cuadrada')
    capacidad = models.PositiveIntegerField(default=4)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Mesa'
        verbose_name_plural = 'Mesas'
        ordering = ['numero']

    def __str__(self):
        return self.nombre or f"Mesa {self.numero}"


class Sabor(models.Model):
    TIPOS = [
        ('pizza', 'Pizza'),
        ('alitas', 'Alitas'),
        ('bebida', 'Bebida'),
        ('michelada', 'Michelada'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    es_premium = models.BooleanField(default=False)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'Sabor'
        verbose_name_plural = 'Sabores'
        ordering = ['tipo', '-es_premium', 'nombre']

    def __str__(self):
        return f"{self.nombre} ({'Premium' if self.es_premium else self.get_tipo_display()})"


class TamanoPizza(models.Model):
    nombre = models.CharField(max_length=20, unique=True)
    precio_base = models.DecimalField(max_digits=6, decimal_places=2)
    recargo_premium_completo = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    recargo_premium_mitad = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Tamaño de pizza'
        verbose_name_plural = 'Tamaños de pizza'
        ordering = ['orden']

    def __str__(self):
        return self.nombre


class ProductoSimple(models.Model):
    CATEGORIAS = [
        ('bebida', 'Bebida'),
        ('alitas', 'Alitas'),
        ('hamburguesa', 'Hamburguesa'),
        ('para_picar', 'Para picar'),
        ('otro', 'Otro'),
    ]

    nombre = models.CharField(max_length=150)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    descripcion = models.CharField(max_length=255, blank=True)
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Producto simple'
        verbose_name_plural = 'Productos simples'
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return self.nombre


class ComboPizzeria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)
    activo = models.BooleanField(default=True)
    precio_fijo = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text='Precio único del combo cuando no tiene tamaños (ComboTamano). '
                   'Si el combo sí tiene tamaños, el precio se calcula por tamaño y este campo se ignora.',
    )
    pizza_tamano_fijo = models.ForeignKey(
        TamanoPizza, on_delete=models.PROTECT, null=True, blank=True, related_name='+',
        help_text='Tamaño predeterminado (no seleccionable) de la pizza completa de este combo, '
                   'ej. "Pizza Familiar" en un combo de precio fijo. Vacío si el combo no incluye pizza completa.',
    )

    class Meta:
        verbose_name = 'Combo'
        verbose_name_plural = 'Combos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ComboTamano(models.Model):
    combo = models.ForeignKey(ComboPizzeria, on_delete=models.CASCADE, related_name='tamanos')
    tamano = models.ForeignKey(TamanoPizza, on_delete=models.PROTECT)
    precio = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        verbose_name = 'Tamaño de combo'
        verbose_name_plural = 'Tamaños de combo'
        unique_together = ('combo', 'tamano')

    def __str__(self):
        return f"{self.combo.nombre} - {self.tamano.nombre}"


class ComboComponente(models.Model):
    TIPOS = [
        ('papas', 'Papas'),
        ('alitas', 'Alitas'),
        ('bebida', 'Bebida'),
        ('postre', 'Postre'),
        ('helado', 'Helado'),
        ('hamburguesa', 'Hamburguesa'),
        ('michelada', 'Michelada'),
        ('porcion_pizza', 'Porción de pizza'),
    ]

    combo = models.ForeignKey(ComboPizzeria, on_delete=models.CASCADE, related_name='componentes')
    tipo = models.CharField(max_length=15, choices=TIPOS)
    cantidad = models.PositiveIntegerField(default=1)
    detalle = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Componente de combo'
        verbose_name_plural = 'Componentes de combo'

    def __str__(self):
        return f"{self.combo.nombre} - {self.cantidad}x {self.get_tipo_display()}"


class PedidoPizzeria(models.Model):
    TIPOS = [
        ('mesa', 'En mesa'),
        ('llevar', 'Para llevar'),
        ('delivery', 'Domicilio'),
    ]
    FORMA_PAGO = [
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Tarjeta', 'Tarjeta'),
    ]
    ESTADOS = [
        ('abierto', 'Abierto'),
        ('por_cobrar', 'Por cobrar'),
        ('cobrado', 'Cobrado'),
        ('anulado', 'Anulado'),
    ]

    tipo = models.CharField(max_length=10, choices=TIPOS)
    mesa = models.ForeignKey(Mesa, null=True, blank=True, on_delete=models.PROTECT)
    contacto = models.CharField(max_length=100, blank=True, null=True)
    mesero = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='pedidos_pizzeria'
    )
    estado = models.CharField(max_length=20, choices=ESTADOS, default='abierto')
    forma_pago = models.CharField(max_length=15, choices=FORMA_PAGO, blank=True, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)
    numero_dia = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, null=True)
    valor_moto = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Pedido de pizzería'
        verbose_name_plural = 'Pedidos de pizzería'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Pedido pizzería #{self.numero_dia:03d} - {self.get_tipo_display()}"

    def save(self, *args, **kwargs):
        if not self.pk:
            today = timezone.localdate()
            with transaction.atomic():
                ultimo_pedido_hoy = (
                    PedidoPizzeria.objects.select_for_update()
                    .filter(fecha_creacion__date=today)
                    .order_by('-numero_dia')
                    .first()
                )
                self.numero_dia = (ultimo_pedido_hoy.numero_dia + 1) if ultimo_pedido_hoy else 1
                super().save(*args, **kwargs)
            return

        super().save(*args, **kwargs)

    @property
    def numero_pedido_completo(self):
        return f"{self.numero_dia:03d}"

    @property
    def resumen_forma_pago(self):
        if self.personas_cobro.exists():
            return f"Dividido ({self.personas_cobro.count()})"
        metodos = sorted(set(self.pagos.values_list('metodo', flat=True)))
        if not metodos:
            return self.forma_pago or '—'
        return metodos[0] if len(metodos) == 1 else 'Mixto (' + ' + '.join(metodos) + ')'


class PedidoPizza(models.Model):
    pedido = models.ForeignKey(PedidoPizzeria, on_delete=models.CASCADE, related_name='pizzas')
    tamano = models.ForeignKey(TamanoPizza, on_delete=models.PROTECT)
    sabor_1 = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+')
    sabor_2 = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=6, decimal_places=2)
    observacion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Pizza de pedido'
        verbose_name_plural = 'Pizzas de pedido'


class PedidoCombo(models.Model):
    pedido = models.ForeignKey(PedidoPizzeria, on_delete=models.CASCADE, related_name='combos')
    combo = models.ForeignKey(ComboPizzeria, on_delete=models.PROTECT)
    tamano = models.ForeignKey(TamanoPizza, on_delete=models.PROTECT, null=True, blank=True)
    sabor_1 = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    sabor_2 = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=6, decimal_places=2)
    observacion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Combo de pedido'
        verbose_name_plural = 'Combos de pedido'


class PedidoComboSaborAlitas(models.Model):
    pedido_combo = models.ForeignKey(PedidoCombo, on_delete=models.CASCADE, related_name='sabores_alitas')
    sabor = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+')
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Sabor de alitas de combo'
        verbose_name_plural = 'Sabores de alitas de combo'

    def __str__(self):
        return f"{self.pedido_combo} - {self.cantidad}x {self.sabor.nombre}"


class PedidoComboSaborBebida(models.Model):
    """Un registro por cada bebida (cola) incluida en el combo, para permitir
    sabor independiente cuando el combo trae más de una (ej. Combo Duo)."""
    pedido_combo = models.ForeignKey(PedidoCombo, on_delete=models.CASCADE, related_name='sabores_bebida')
    sabor = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+')

    class Meta:
        verbose_name = 'Sabor de bebida de combo'
        verbose_name_plural = 'Sabores de bebida de combo'

    def __str__(self):
        return f"{self.pedido_combo} - {self.sabor.nombre}"


class PedidoComboSaborMichelada(models.Model):
    """Un registro por cada michelada incluida en el combo, con sabor independiente."""
    pedido_combo = models.ForeignKey(PedidoCombo, on_delete=models.CASCADE, related_name='sabores_michelada')
    sabor = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+')

    class Meta:
        verbose_name = 'Sabor de michelada de combo'
        verbose_name_plural = 'Sabores de michelada de combo'

    def __str__(self):
        return f"{self.pedido_combo} - {self.sabor.nombre}"


class PedidoComboSaborPorcion(models.Model):
    """Un registro por cada porción de pizza incluida en el combo (ej. Combo Duo
    trae 2), cada una con un solo sabor (sin mitad y mitad)."""
    pedido_combo = models.ForeignKey(PedidoCombo, on_delete=models.CASCADE, related_name='sabores_porcion')
    sabor = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+')

    class Meta:
        verbose_name = 'Sabor de porción de combo'
        verbose_name_plural = 'Sabores de porción de combo'

    def __str__(self):
        return f"{self.pedido_combo} - {self.sabor.nombre}"


class PedidoProductoSimple(models.Model):
    pedido = models.ForeignKey(PedidoPizzeria, on_delete=models.CASCADE, related_name='productos_simples')
    producto = models.ForeignKey(ProductoSimple, on_delete=models.PROTECT)
    sabor_bebida = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=6, decimal_places=2)
    observacion = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Producto simple de pedido'
        verbose_name_plural = 'Productos simples de pedido'


class PedidoProductoSimpleSaborAlitas(models.Model):
    pedido_producto = models.ForeignKey(PedidoProductoSimple, on_delete=models.CASCADE, related_name='sabores_alitas')
    sabor = models.ForeignKey(Sabor, on_delete=models.PROTECT, related_name='+')
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Sabor de alitas de producto'
        verbose_name_plural = 'Sabores de alitas de producto'

    def __str__(self):
        return f"{self.pedido_producto} - {self.cantidad}x {self.sabor.nombre}"


class PersonaCobro(models.Model):
    """Una 'parte' del pedido cuando se divide la cuenta por productos."""
    pedido = models.ForeignKey(PedidoPizzeria, on_delete=models.CASCADE, related_name='personas_cobro')
    nombre = models.CharField(max_length=50)
    orden = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Persona de cobro'
        verbose_name_plural = 'Personas de cobro'
        ordering = ['orden']

    def __str__(self):
        return f"{self.pedido} - {self.nombre}"


class AsignacionItemCobro(models.Model):
    """Cuántas unidades de una línea del pedido (pizza/combo/producto) le
    corresponden a una PersonaCobro. Mismo patrón de FKs nullable que
    ItemPreparacion (pizza/combo/producto_simple): solo una se llena."""
    persona = models.ForeignKey(PersonaCobro, on_delete=models.CASCADE, related_name='asignaciones')
    pizza = models.ForeignKey(
        PedidoPizza, null=True, blank=True, on_delete=models.CASCADE, related_name='asignaciones_cobro',
    )
    combo = models.ForeignKey(
        PedidoCombo, null=True, blank=True, on_delete=models.CASCADE, related_name='asignaciones_cobro',
    )
    producto_simple = models.ForeignKey(
        PedidoProductoSimple, null=True, blank=True, on_delete=models.CASCADE, related_name='asignaciones_cobro',
    )
    cantidad = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Asignación de ítem a persona'
        verbose_name_plural = 'Asignaciones de ítems a personas'

    def __str__(self):
        linea = self.pizza or self.combo or self.producto_simple
        return f"{self.persona} - {self.cantidad}x {linea}"


class PagoPedido(models.Model):
    """Una línea de pago (método + monto) contra un pedido, opcionalmente
    ligada a una PersonaCobro cuando la cuenta está dividida. Un pedido puede
    tener varias filas (pago mixto) con o sin persona asociada."""
    METODOS = [
        ('Efectivo', 'Efectivo'),
        ('Transferencia', 'Transferencia'),
        ('Tarjeta', 'Tarjeta'),
    ]

    pedido = models.ForeignKey(PedidoPizzeria, on_delete=models.CASCADE, related_name='pagos')
    persona = models.ForeignKey(
        PersonaCobro, null=True, blank=True, on_delete=models.CASCADE, related_name='pagos',
    )
    metodo = models.CharField(max_length=15, choices=METODOS)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago de pedido'
        verbose_name_plural = 'Pagos de pedido'
        ordering = ['id']

    def __str__(self):
        return f"{self.pedido} - {self.metodo} ${self.monto}"


class ItemPreparacion(models.Model):
    """Ítem de cocina rastreable dentro de un pedido (ej: la pizza de un combo,
    las papas+alitas de un combo, una bebida suelta). No es 1:1 con las líneas
    de PedidoPizza/PedidoCombo/PedidoProductoSimple: un combo puede generar
    varios ItemPreparacion (uno por estación de cocina)."""

    ESTADOS = [
        ('en_proceso', 'En proceso'),
        ('cocinando', 'Cocinando'),
        ('listo', 'Listo'),
        ('completo', 'Completo'),
    ]

    pedido = models.ForeignKey(PedidoPizzeria, on_delete=models.CASCADE, related_name='items_preparacion')
    descripcion = models.CharField(max_length=200)
    cantidad = models.PositiveIntegerField(default=1)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='en_proceso')
    grupo = models.CharField(
        max_length=200, blank=True, default='',
        help_text='Nombre del combo al que pertenece este ítem (ej: "Mega Combo 1"), vacío si es un ítem suelto.',
    )
    pizza = models.ForeignKey(
        'PedidoPizza', null=True, blank=True, on_delete=models.CASCADE, related_name='items_preparacion',
    )
    combo = models.ForeignKey(
        'PedidoCombo', null=True, blank=True, on_delete=models.CASCADE, related_name='items_preparacion',
    )
    producto_simple = models.ForeignKey(
        'PedidoProductoSimple', null=True, blank=True, on_delete=models.CASCADE, related_name='items_preparacion',
    )

    class Meta:
        verbose_name = 'Ítem de preparación'
        verbose_name_plural = 'Ítems de preparación'
        ordering = ['id']

    def __str__(self):
        return f"{self.pedido} - {self.descripcion}"

    @property
    def linea(self):
        """La línea de pedido (PedidoPizza/PedidoCombo/PedidoProductoSimple) que originó
        este ítem de cocina, o None si no se pudo asociar (datos legacy)."""
        return self.pizza or self.combo or self.producto_simple


class CajaPizzeria(models.Model):
    ESTADOS = [
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    ]

    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='abierta')
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Caja pizzería'
        verbose_name_plural = 'Cajas pizzería'
        ordering = ['-fecha']

    def __str__(self):
        return f"Caja pizzería {self.fecha} - {self.estado.title()}"

    def hora_apertura(self):
        return self.fecha_apertura.time() if self.fecha_apertura else None

    def hora_cierre(self):
        return self.fecha_cierre.time() if self.fecha_cierre else None

    def duracion_caja(self):
        if self.fecha_cierre and self.fecha_apertura:
            return self.fecha_cierre - self.fecha_apertura
        return None


class CajaPizzeriaEfectivo(models.Model):
    caja = models.OneToOneField(CajaPizzeria, on_delete=models.CASCADE, related_name='caja_efectivo')
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_gastos = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Caja pizzería - Efectivo'
        verbose_name_plural = 'Cajas pizzería - Efectivo'

    def __str__(self):
        return f"Efectivo pizzería {self.caja.fecha}"


class CajaPizzeriaTransferencia(models.Model):
    caja = models.OneToOneField(CajaPizzeria, on_delete=models.CASCADE, related_name='caja_transferencia')
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Caja pizzería - Transferencia'
        verbose_name_plural = 'Cajas pizzería - Transferencia'

    def __str__(self):
        return f"Transferencia pizzería {self.caja.fecha}"


class CajaPizzeriaTarjeta(models.Model):
    caja = models.OneToOneField(CajaPizzeria, on_delete=models.CASCADE, related_name='caja_tarjeta')
    monto_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monto_final = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Caja pizzería - Tarjeta'
        verbose_name_plural = 'Cajas pizzería - Tarjeta'

    def __str__(self):
        return f"Tarjeta pizzería {self.caja.fecha}"


class GastoPizzeria(models.Model):
    CATEGORIAS = [
        ('insumos', 'Insumos'),
        ('servicios', 'Servicios'),
        ('otros', 'Otros'),
    ]

    caja = models.ForeignKey(CajaPizzeria, on_delete=models.CASCADE, related_name='gastos')
    descripcion = models.CharField(max_length=200)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='otros')

    class Meta:
        verbose_name = 'Gasto pizzería'
        verbose_name_plural = 'Gastos pizzería'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.descripcion} - ${self.monto}"
