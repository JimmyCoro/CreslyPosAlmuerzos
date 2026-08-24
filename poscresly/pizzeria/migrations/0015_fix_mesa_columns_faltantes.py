from django.db import migrations


class Migration(migrations.Migration):
    """La tabla pizzeria_mesa en esta base de datos quedó desactualizada
    respecto al modelo (le faltan pos_x, pos_y y capacidad), pero Django ya
    tiene 0001_initial marcada como aplicada -> no la vuelve a correr sola.
    Se agregan las columnas directamente por SQL, sin tocar datos existentes
    (hay pedidos abiertos ligados a estas mesas)."""

    dependencies = [
        ('pizzeria', '0014_alter_pedidopizzeria_forma_pago_cajapizzeriatarjeta_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE pizzeria_mesa ADD COLUMN IF NOT EXISTS pos_x double precision NOT NULL DEFAULT 0;
                ALTER TABLE pizzeria_mesa ADD COLUMN IF NOT EXISTS pos_y double precision NOT NULL DEFAULT 0;
                ALTER TABLE pizzeria_mesa ADD COLUMN IF NOT EXISTS capacidad integer NOT NULL DEFAULT 4;
            """,
            reverse_sql="""
                ALTER TABLE pizzeria_mesa DROP COLUMN IF EXISTS pos_x;
                ALTER TABLE pizzeria_mesa DROP COLUMN IF EXISTS pos_y;
                ALTER TABLE pizzeria_mesa DROP COLUMN IF EXISTS capacidad;
            """,
            state_operations=[],
        ),
    ]
