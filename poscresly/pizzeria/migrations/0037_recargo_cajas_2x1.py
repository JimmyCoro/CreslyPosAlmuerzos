from decimal import Decimal

from django.db import migrations

RECARGOS = {
    '2 Pizzas Familiares': Decimal('1.00'),
    '2 Pizzas Medianas': Decimal('0.75'),
    '2 Pizzas Pequeñas': Decimal('0.50'),
}


def poner(apps, schema_editor):
    ComboPizzeria = apps.get_model('pizzeria', 'ComboPizzeria')
    for nombre, recargo in RECARGOS.items():
        ComboPizzeria.objects.filter(nombre=nombre).update(recargo_cajas=recargo)


def quitar(apps, schema_editor):
    ComboPizzeria = apps.get_model('pizzeria', 'ComboPizzeria')
    ComboPizzeria.objects.filter(nombre__in=RECARGOS).update(recargo_cajas=None)


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0036_recargo_cajas'),
    ]

    operations = [
        migrations.RunPython(poner, quitar),
    ]
