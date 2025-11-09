from django.contrib import admin
from .models import (
    Plato, Producto, MenuDia, MenuDiaExtra, MenuDiaJugo,
    MenuDiaSegundo, MenuDiaSopa
)


@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre_plato', 'tipo', 'precio')
    list_filter = ('tipo',)
    search_fields = ('nombre_plato',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_plato', 'tipo')
        }),
        ('Precio (Solo para Extras)', {
            'fields': ('precio',),
            'description': 'El precio solo se usa para platos de tipo "Extra"'
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.tipo != 'extra':
            # Ocultar el campo precio para tipos que no son extra
            fieldsets = (
                ('Información Básica', {
                    'fields': ('nombre_plato', 'tipo')
                }),
            )
        return fieldsets


# Puedes registrar los demás modelos de forma normal:
admin.site.register(MenuDia)
admin.site.register(Producto)
admin.site.register(MenuDiaExtra)
admin.site.register(MenuDiaJugo)
admin.site.register(MenuDiaSegundo)
admin.site.register(MenuDiaSopa)
