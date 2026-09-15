import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0032_categoriaproducto'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productosimple',
            name='categoria',
        ),
        migrations.RenameField(
            model_name='productosimple',
            old_name='categoria_nueva',
            new_name='categoria',
        ),
        migrations.AlterField(
            model_name='productosimple',
            name='categoria',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='productos', to='pizzeria.categoriaproducto'),
        ),
        migrations.AlterModelOptions(
            name='productosimple',
            options={
                'ordering': ['categoria__orden', 'categoria__nombre', 'nombre'],
                'verbose_name': 'Producto simple',
                'verbose_name_plural': 'Productos simples',
            },
        ),
    ]
