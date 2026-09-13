from django.db import migrations, models

# "Por cobrar" deja de existir: una orden sigue abierta hasta que se cobra, y
# su avance lo dicen los estados de sus platillos (pendiente, en cocina,
# servido → completo). La mesa sigue ocupada hasta que se libera al cobrar.


def quitar_por_cobrar(apps, schema_editor):
    apps.get_model('pizzeria', 'PedidoPizzeria').objects.filter(estado='por_cobrar').update(estado='abierto')
    apps.get_model('pizzeria', 'Mesa').objects.filter(estado='por_cobrar').update(estado='ocupada')


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0026_item_preparacion_tres_estados'),
    ]

    operations = [
        # Sin reversa de datos: no se puede saber qué órdenes estaban por cobrar.
        migrations.RunPython(quitar_por_cobrar, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='mesa',
            name='estado',
            field=models.CharField(
                choices=[('libre', 'Libre'), ('reservada', 'Reservada'), ('ocupada', 'Ocupada')],
                default='libre', max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='pedidopizzeria',
            name='estado',
            field=models.CharField(
                choices=[('abierto', 'Abierto'), ('cobrado', 'Cobrado'), ('anulado', 'Anulado')],
                default='abierto', max_length=20,
            ),
        ),
    ]
