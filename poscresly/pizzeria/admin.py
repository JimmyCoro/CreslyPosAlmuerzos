from django.contrib import admin

from .models import (
    AsignacionItemCobro,
    CajaPizzeria,
    CajaPizzeriaEfectivo,
    CajaPizzeriaTarjeta,
    CajaPizzeriaTransferencia,
    ComboComponente,
    ComboPizzeria,
    ComboTamano,
    GastoPizzeria,
    ItemPreparacion,
    Mesa,
    PagoPedido,
    PedidoCombo,
    PedidoComboSaborAlitas,
    PedidoPizza,
    PedidoPizzeria,
    PedidoProductoSimple,
    PedidoProductoSimpleSaborAlitas,
    PersonaCobro,
    ProductoSimple,
    Sabor,
    TamanoPizza,
)


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'zona', 'estado', 'capacidad', 'activa')
    list_filter = ('zona', 'estado', 'activa')
    list_editable = ('estado', 'activa')


@admin.register(Sabor)
class SaborAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'es_premium')
    list_filter = ('tipo', 'es_premium')
    list_editable = ('es_premium',)


@admin.register(TamanoPizza)
class TamanoPizzaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_base', 'recargo_premium_completo', 'recargo_premium_mitad', 'orden')
    list_editable = ('precio_base', 'recargo_premium_completo', 'recargo_premium_mitad', 'orden')


@admin.register(ProductoSimple)
class ProductoSimpleAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'activo')
    list_filter = ('categoria', 'activo')
    list_editable = ('precio', 'activo')


class ComboTamanoInline(admin.TabularInline):
    model = ComboTamano
    extra = 1


class ComboComponenteInline(admin.TabularInline):
    model = ComboComponente
    extra = 1


@admin.register(ComboPizzeria)
class ComboPizzeriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_editable = ('activo',)
    inlines = [ComboTamanoInline, ComboComponenteInline]


class ItemPreparacionInline(admin.TabularInline):
    model = ItemPreparacion
    extra = 0


class PagoPedidoInline(admin.TabularInline):
    model = PagoPedido
    extra = 0


@admin.register(PedidoPizzeria)
class PedidoPizzeriaAdmin(admin.ModelAdmin):
    list_display = ('numero_pedido_completo', 'tipo', 'mesa', 'mesero', 'estado', 'total', 'fecha_creacion')
    list_filter = ('tipo', 'estado', 'forma_pago')
    inlines = [ItemPreparacionInline, PagoPedidoInline]


class PedidoComboSaborAlitasInline(admin.TabularInline):
    model = PedidoComboSaborAlitas
    extra = 0


@admin.register(PedidoCombo)
class PedidoComboAdmin(admin.ModelAdmin):
    list_display = ('combo', 'pedido', 'tamano', 'cantidad', 'precio_unitario')
    inlines = [PedidoComboSaborAlitasInline]


class PedidoProductoSimpleSaborAlitasInline(admin.TabularInline):
    model = PedidoProductoSimpleSaborAlitas
    extra = 0


@admin.register(PedidoProductoSimple)
class PedidoProductoSimpleAdmin(admin.ModelAdmin):
    list_display = ('producto', 'pedido', 'cantidad', 'precio_unitario')
    inlines = [PedidoProductoSimpleSaborAlitasInline]


admin.site.register(PedidoPizza)
admin.site.register(CajaPizzeria)
admin.site.register(CajaPizzeriaEfectivo)
admin.site.register(CajaPizzeriaTransferencia)
admin.site.register(CajaPizzeriaTarjeta)
admin.site.register(GastoPizzeria)
admin.site.register(PersonaCobro)
admin.site.register(AsignacionItemCobro)
admin.site.register(PagoPedido)
