from django.db import migrations, models

# Los cuatro estados anteriores se reducen a tres. "listo" (terminado pero aún
# no llevado a la mesa) queda en cocina: todavía no está servido.
A_NUEVO = {
    'en_proceso': 'pendiente',
    'cocinando': 'cocina',
    'listo': 'cocina',
    'completo': 'servido',
}
A_ANTERIOR = {
    'pendiente': 'en_proceso',
    'cocina': 'cocinando',
    'servido': 'completo',
}


def convertir(mapa):
    def _convertir(apps, schema_editor):
        ItemPreparacion = apps.get_model('pizzeria', 'ItemPreparacion')
        for anterior, nuevo in mapa.items():
            ItemPreparacion.objects.filter(estado=anterior).update(estado=nuevo)
    return _convertir


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0025_caja_turno_movimientos'),
    ]

    operations = [
        migrations.AddField(
            model_name='itempreparacion',
            name='enviado_en',
            field=models.DateTimeField(
                blank=True, null=True,
                help_text='Cuándo pasó a cocina. El tiempo en cocina de la lista de Órdenes corre desde aquí.',
            ),
        ),
        migrations.RunPython(convertir(A_NUEVO), convertir(A_ANTERIOR)),
        migrations.AlterField(
            model_name='itempreparacion',
            name='estado',
            field=models.CharField(
                choices=[('pendiente', 'Pendiente'), ('cocina', 'En cocina'), ('servido', 'Servido')],
                default='pendiente', max_length=20,
            ),
        ),
    ]
