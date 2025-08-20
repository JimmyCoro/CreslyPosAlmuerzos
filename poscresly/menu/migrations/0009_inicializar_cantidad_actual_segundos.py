from django.db import migrations

def inicializar_cantidad_actual(apps, schema_editor):
    """Inicializa cantidad_actual con el valor de cantidad para todos los registros"""
    MenuDiaSopa = apps.get_model('menu', 'MenuDiaSopa')
    MenuDiaSegundo = apps.get_model('menu', 'MenuDiaSegundo')
    
    # Inicializar sopas
    for sopa in MenuDiaSopa.objects.all():
        if sopa.cantidad_actual == 0:
            sopa.cantidad_actual = sopa.cantidad
            sopa.save()
    
    # Inicializar segundos
    for segundo in MenuDiaSegundo.objects.all():
        if segundo.cantidad_actual == 0:
            segundo.cantidad_actual = segundo.cantidad
            segundo.save()

def reverse_inicializar_cantidad_actual(apps, schema_editor):
    """Revierte la inicialización (pone cantidad_actual en 0)"""
    MenuDiaSopa = apps.get_model('menu', 'MenuDiaSopa')
    MenuDiaSegundo = apps.get_model('menu', 'MenuDiaSegundo')
    
    MenuDiaSopa.objects.all().update(cantidad_actual=0)
    MenuDiaSegundo.objects.all().update(cantidad_actual=0)

class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0008_menudiasegundo_cantidad_actual_and_more'),
    ]

    operations = [
        migrations.RunPython(inicializar_cantidad_actual, reverse_inicializar_cantidad_actual),
    ]
