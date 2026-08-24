from django.db import migrations

DESCRIPCIONES = {
    'Combo Tu y Yo': '8 alitas + papas + 2 micheladas',
    'Combo Cumpleañero': 'pizza familiar + 10 alitas + papas + bebida grande + helado',
    'Combo Cresly': '2 hamburguesas clásicas + 10 alitas + papas + bebida grande',
    'Reto de Comelones': '15 alitas + papas + bebida grande',
    'Combo Personal': 'porción de pizza + 4 alitas + papas + bebida pequeña',
    'Combo Completo': 'porción de pizza + papas + bebida pequeña',
    'Combo Duo': '2 porciones de pizza + 4 alitas + 2 bebidas pequeñas',
    'Combo Wings & Burguer': '6 alitas + 2 hamburguesas clásicas + papas + 2 bebidas pequeñas',
    'Combo MicheBurguer': '2 hamburguesas clásicas + 2 micheladas + papas',
}


def set_descripciones(apps, schema_editor):
    ComboPizzeria = apps.get_model('pizzeria', 'ComboPizzeria')
    for nombre, descripcion in DESCRIPCIONES.items():
        ComboPizzeria.objects.filter(nombre=nombre).update(descripcion=descripcion)


def revertir(apps, schema_editor):
    ComboPizzeria = apps.get_model('pizzeria', 'ComboPizzeria')
    ComboPizzeria.objects.filter(nombre__in=DESCRIPCIONES.keys()).update(descripcion='')


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0012_seed_combos_extendidos'),
    ]

    operations = [
        migrations.RunPython(set_descripciones, revertir),
    ]
