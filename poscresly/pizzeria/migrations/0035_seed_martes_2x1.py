from decimal import Decimal

from django.db import migrations

CATEGORIA = {'clave': 'martes-2x1', 'nombre': 'Martes 2X1'}

# 2x1: precio fijo por tamaño, dos pizzas; cada una paga su recargo premium.
DOS_POR_UNO = [
    ('2 Pizzas Familiares', 'Familiar', Decimal('18.00'), '2 pizzas familiares'),
    ('2 Pizzas Medianas', 'Mediana', Decimal('15.00'), '2 pizzas medianas'),
    ('2 Pizzas Pequeñas', 'Pequeña', Decimal('11.00'), '2 pizzas pequeñas'),
]

# Igual que los Mega Combos: precio por tamaño + recargo premium de la pizza.
# Los tamaños van de menor a mayor, en el orden en que se muestran.
COMBOS_MARTES = [
    ('Combo Martes #1', 6, {'Pequeña': '15.00', 'Mediana': '17.50', 'Familiar': '20.00'}),
    ('Combo Martes #2', 10, {'Pequeña': '18.00', 'Mediana': '20.00', 'Familiar': '22.00'}),
    ('Combo Martes #3', 16, {'Pequeña': '20.00', 'Mediana': '23.00', 'Familiar': '25.00'}),
]


def crear(apps, schema_editor):
    CategoriaProducto = apps.get_model('pizzeria', 'CategoriaProducto')
    ComboPizzeria = apps.get_model('pizzeria', 'ComboPizzeria')
    ComboTamano = apps.get_model('pizzeria', 'ComboTamano')
    ComboComponente = apps.get_model('pizzeria', 'ComboComponente')
    TamanoPizza = apps.get_model('pizzeria', 'TamanoPizza')

    tamanos = {t.nombre: t for t in TamanoPizza.objects.filter(nombre__in=['Familiar', 'Mediana', 'Pequeña'])}
    if len(tamanos) < 3:
        # Base sin catálogo de pizzas (ej. la de tests): no hay a qué colgar los combos.
        return

    categoria = (
        CategoriaProducto.objects.filter(clave=CATEGORIA['clave']).first()
        or CategoriaProducto.objects.filter(nombre__iexact=CATEGORIA['nombre']).first()
    )
    if categoria is None:
        ultima = CategoriaProducto.objects.order_by('-orden').first()
        categoria = CategoriaProducto.objects.create(
            clave=CATEGORIA['clave'], nombre=CATEGORIA['nombre'], orden=(ultima.orden + 1) if ultima else 1,
        )
    else:
        categoria.nombre = CATEGORIA['nombre']
        categoria.activa = True
        categoria.save(update_fields=['nombre', 'activa'])

    for nombre, tamano_nombre, precio, descripcion in DOS_POR_UNO:
        ComboPizzeria.objects.update_or_create(
            nombre=nombre,
            defaults={
                'descripcion': f'{descripcion} · cada una de un sabor o mitad y mitad',
                'activo': True, 'precio_fijo': precio, 'pizza_tamano_fijo': tamanos[tamano_nombre],
                'pizzas': 2, 'categoria': categoria,
            },
        )

    for nombre, alitas, precios in COMBOS_MARTES:
        combo, _ = ComboPizzeria.objects.update_or_create(
            nombre=nombre,
            defaults={
                'descripcion': f'pizza + {alitas} alitas + papas + bebida + fresas con crema',
                'activo': True, 'precio_fijo': None, 'pizza_tamano_fijo': None,
                'pizzas': 1, 'categoria': categoria,
            },
        )
        combo.tamanos.all().delete()
        ComboTamano.objects.bulk_create([
            ComboTamano(combo=combo, tamano=tamanos[tamano_nombre], precio=Decimal(precio))
            for tamano_nombre, precio in precios.items()
        ])
        combo.componentes.all().delete()
        ComboComponente.objects.bulk_create([
            ComboComponente(combo=combo, tipo='alitas', cantidad=alitas),
            ComboComponente(combo=combo, tipo='papas', cantidad=1),
            ComboComponente(combo=combo, tipo='bebida', cantidad=1),
            ComboComponente(combo=combo, tipo='postre', cantidad=1, detalle='Fresas con crema'),
        ])


def quitar(apps, schema_editor):
    ComboPizzeria = apps.get_model('pizzeria', 'ComboPizzeria')
    nombres = [c[0] for c in DOS_POR_UNO] + [c[0] for c in COMBOS_MARTES]
    # Los que ya se vendieron quedan protegidos por los pedidos: se desactivan.
    ComboPizzeria.objects.filter(nombre__in=nombres).update(activo=False)


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0034_combo_categoria_y_2x1'),
    ]

    operations = [
        migrations.RunPython(crear, quitar),
    ]
