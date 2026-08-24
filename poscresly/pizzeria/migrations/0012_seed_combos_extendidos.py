from django.db import migrations

SABORES_MICHELADA = ['Maracuyá', 'Limón']

# (nombre_viejo_producto_simple, nombre_nuevo_combo, precio, tamano_fijo_pizza, componentes)
# componentes: lista de (tipo, cantidad, detalle)
COMBOS = [
    (
        'Combo Tu y Yo', 'Combo Tu y Yo', '12.50', None,
        [('alitas', 8, ''), ('papas', 1, ''), ('michelada', 2, '')],
    ),
    (
        'Combo Cumpleañero', 'Combo Cumpleañero', '28.50', 'Familiar',
        [('alitas', 10, ''), ('papas', 1, ''), ('bebida', 1, ''), ('helado', 1, '')],
    ),
    (
        'Combo Cresly', 'Combo Cresly', '18.00', None,
        [('hamburguesa', 2, 'Clásica'), ('alitas', 10, ''), ('papas', 1, ''), ('bebida', 1, '')],
    ),
    (
        'Reto de Comelones', 'Reto de Comelones', '16.00', None,
        [('alitas', 15, ''), ('papas', 1, ''), ('bebida', 1, '')],
    ),
    (
        'Combo Personal', 'Combo Personal', '7.00', None,
        [('porcion_pizza', 1, ''), ('alitas', 4, ''), ('papas', 1, ''), ('bebida', 1, '')],
    ),
    (
        'Combo completo', 'Combo Completo', '4.00', None,
        [('porcion_pizza', 1, ''), ('papas', 1, ''), ('bebida', 1, '')],
    ),
    (
        'Combo Duo', 'Combo Duo', '11.00', None,
        [('porcion_pizza', 2, ''), ('alitas', 4, ''), ('bebida', 2, '')],
    ),
    (
        'Combo Wings y Burguer', 'Combo Wings & Burguer', '15.00', None,
        [('alitas', 6, ''), ('hamburguesa', 2, 'Clásica'), ('papas', 1, ''), ('bebida', 2, '')],
    ),
    (
        'Combo MicheBurguer', 'Combo MicheBurguer', '13.00', None,
        [('hamburguesa', 2, 'Clásica'), ('michelada', 2, ''), ('papas', 1, '')],
    ),
]


def crear_combos(apps, schema_editor):
    Sabor = apps.get_model('pizzeria', 'Sabor')
    TamanoPizza = apps.get_model('pizzeria', 'TamanoPizza')
    ProductoSimple = apps.get_model('pizzeria', 'ProductoSimple')
    ComboPizzeria = apps.get_model('pizzeria', 'ComboPizzeria')
    ComboComponente = apps.get_model('pizzeria', 'ComboComponente')

    for nombre in SABORES_MICHELADA:
        Sabor.objects.get_or_create(nombre=nombre, tipo='michelada')

    for nombre_viejo, nombre_nuevo, precio, tamano_fijo_nombre, componentes in COMBOS:
        tamano_fijo = (
            TamanoPizza.objects.filter(nombre=tamano_fijo_nombre).first()
            if tamano_fijo_nombre else None
        )
        combo, _ = ComboPizzeria.objects.get_or_create(
            nombre=nombre_nuevo,
            defaults={'precio_fijo': precio, 'pizza_tamano_fijo': tamano_fijo, 'activo': True},
        )
        if not combo.componentes.exists():
            for tipo, cantidad, detalle in componentes:
                ComboComponente.objects.create(
                    combo=combo, tipo=tipo, cantidad=cantidad, detalle=detalle,
                )

        ProductoSimple.objects.filter(nombre=nombre_viejo, categoria='otro').update(activo=False)


def revertir(apps, schema_editor):
    Sabor = apps.get_model('pizzeria', 'Sabor')
    ProductoSimple = apps.get_model('pizzeria', 'ProductoSimple')
    ComboPizzeria = apps.get_model('pizzeria', 'ComboPizzeria')

    nombres_nuevos = [c[1] for c in COMBOS]
    nombres_viejos = [c[0] for c in COMBOS]
    ComboPizzeria.objects.filter(nombre__in=nombres_nuevos).delete()
    ProductoSimple.objects.filter(nombre__in=nombres_viejos, categoria='otro').update(activo=True)
    Sabor.objects.filter(tipo='michelada', nombre__in=SABORES_MICHELADA).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0011_remove_pedidocombo_sabor_bebida_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_combos, revertir),
    ]
