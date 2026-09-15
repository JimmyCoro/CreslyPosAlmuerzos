import django.db.models.deletion
from django.db import migrations, models

# Las categorías que antes estaban fijas en ProductoSimple.CATEGORIAS.
CATEGORIAS_INICIALES = [
    ('bebida', 'Bebida'),
    ('alitas', 'Alitas'),
    ('hamburguesa', 'Hamburguesa'),
    ('para_picar', 'Para picar'),
    ('otro', 'Otro'),
]


def crear_categorias_y_asignar(apps, schema_editor):
    CategoriaProducto = apps.get_model('pizzeria', 'CategoriaProducto')
    ProductoSimple = apps.get_model('pizzeria', 'ProductoSimple')

    por_clave = {}
    for orden, (clave, nombre) in enumerate(CATEGORIAS_INICIALES, start=1):
        por_clave[clave], _ = CategoriaProducto.objects.get_or_create(
            clave=clave, defaults={'nombre': nombre, 'orden': orden},
        )

    for producto in ProductoSimple.objects.all():
        categoria = por_clave.get(producto.categoria) or por_clave['otro']
        producto.categoria_nueva = categoria
        producto.save(update_fields=['categoria_nueva'])


def devolver_claves(apps, schema_editor):
    ProductoSimple = apps.get_model('pizzeria', 'ProductoSimple')
    for producto in ProductoSimple.objects.select_related('categoria_nueva'):
        producto.categoria = producto.categoria_nueva.clave[:20] if producto.categoria_nueva else 'otro'
        producto.save(update_fields=['categoria'])


class Migration(migrations.Migration):

    dependencies = [
        ('pizzeria', '0031_ordenes_turno_cobro'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoriaProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50, unique=True)),
                ('clave', models.SlugField(help_text='Identificador interno. "alitas" y "bebida" activan la elección de sabores; no las cambies.', unique=True)),
                ('orden', models.PositiveIntegerField(default=0, help_text='Posición en el menú (menor va primero).')),
                ('activa', models.BooleanField(default=True, help_text='Si se desactiva, sus productos no salen en el menú.')),
            ],
            options={
                'verbose_name': 'Categoría de producto',
                'verbose_name_plural': 'Categorías de producto',
                'ordering': ['orden', 'nombre'],
            },
        ),
        migrations.AddField(
            model_name='productosimple',
            name='categoria_nueva',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='pizzeria.categoriaproducto'),
        ),
        migrations.RunPython(crear_categorias_y_asignar, devolver_claves),
    ]
