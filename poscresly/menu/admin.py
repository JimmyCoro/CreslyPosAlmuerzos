from django.contrib import admin
from .models import (
    Plato, Producto, MenuDia, MenuDiaExtra, MenuDiaJugo,
    MenuDiaSegundo, MenuDiaSopa
)



# Puedes registrar los demás modelos de forma normal:
admin.site.register(MenuDia)
admin.site.register(Producto)
admin.site.register(Plato)
admin.site.register(MenuDiaExtra)
admin.site.register(MenuDiaJugo)
admin.site.register(MenuDiaSegundo)
admin.site.register(MenuDiaSopa)
