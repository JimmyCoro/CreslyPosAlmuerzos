from django.db import migrations

TEMPERATURA_TEXTO = {'helada': 'helada', 'ambiente': 'al ambiente'}


def agregar_temperatura(apps, schema_editor):
    """Las bebidas de combo pasaban a cocina solo con el sabor ("Bebida:
    Coca-Cola"). Se reescriben con la temperatura que se eligió en el combo,
    emparejando cada ítem con su bebida en el orden en que se crearon."""
    ItemPreparacion = apps.get_model('pizzeria', 'ItemPreparacion')
    PedidoComboSaborBebida = apps.get_model('pizzeria', 'PedidoComboSaborBebida')

    items = (
        ItemPreparacion.objects
        .filter(combo__isnull=False, descripcion__startswith='Bebida')
        .order_by('combo_id', 'id')
    )
    por_combo = {}
    for item in items:
        por_combo.setdefault(item.combo_id, []).append(item)

    for combo_id, items_combo in por_combo.items():
        bebidas = list(
            PedidoComboSaborBebida.objects.filter(pedido_combo_id=combo_id).select_related('sabor').order_by('id')
        )
        for item, bebida in zip(items_combo, bebidas):
            temperatura = TEMPERATURA_TEXTO.get(bebida.temperatura)
            if not temperatura or item.descripcion.endswith(')'):
                continue
            sufijo = bebida.sabor.nombre
            if item.descripcion.endswith(sufijo):
                item.descripcion = f'{item.descripcion} ({temperatura})'
                item.save(update_fields=['descripcion'])


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0028_caja_cierre_y_anulacion'),
    ]

    operations = [
        migrations.RunPython(agregar_temperatura, migrations.RunPython.noop),
    ]
