from django.db import migrations

ROLES = ['Administrador', 'Empleado']


def crear_grupos(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    User = apps.get_model('auth', 'User')
    empleado = None
    for nombre in ROLES:
        grupo, _ = Group.objects.get_or_create(name=nombre)
        if nombre == 'Empleado':
            empleado = grupo
    # Las cuentas que ya existían (meseros de la pizzería) quedan como Empleado;
    # los superusuarios ya cuentan como Administrador sin grupo.
    for user in User.objects.filter(is_superuser=False, groups__isnull=True):
        user.groups.add(empleado)


def borrar_grupos(apps, schema_editor):
    apps.get_model('auth', 'Group').objects.filter(name__in=ROLES).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inicio', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(crear_grupos, borrar_grupos),
    ]
