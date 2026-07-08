from django.contrib import admin

from .models import (
    CajaPizzeria,
    CajaPizzeriaEfectivo,
    CajaPizzeriaTransferencia,
    ComboComponente,
    ComboPizzeria,
    ComboTamano,
    GastoPizzeria,
    Mesa,
    PedidoCombo,
    PedidoPizza,
    PedidoPizzeria,
    PedidoProductoSimple,
    ProductoSimple,
    Sabor,
    TamanoPizza,
)


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'estado', 'capacidad', 'activa')
    list_filter = ('estado', 'activa')
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


@admin.register(PedidoPizzeria)
class PedidoPizzeriaAdmin(admin.ModelAdmin):
    list_display = ('numero_pedido_completo', 'tipo', 'mesa', 'mesero', 'estado', 'total', 'fecha_creacion')
    list_filter = ('tipo', 'estado', 'forma_pago')


admin.site.register(PedidoPizza)
admin.site.register(PedidoCombo)
admin.site.register(PedidoProductoSimple)
admin.site.register(CajaPizzeria)
admin.site.register(CajaPizzeriaEfectivo)
admin.site.register(CajaPizzeriaTransferencia)
admin.site.register(GastoPizzeria)
