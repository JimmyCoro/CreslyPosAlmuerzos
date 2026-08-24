from django.db import migrations


class Migration(migrations.Migration):
    """Esta base de datos tiene pizzeria_mesa con columnas de una versión
    anterior del modelo (area_id NOT NULL -> pizzeria_areamesas, capacidad_min,
    capacidad_max, reservable) y 'numero' quedó como character varying en vez
    de integer, aunque el modelo/0001_initial ya lo definen como
    PositiveIntegerField sin esas columnas. Esto rompe cualquier INSERT hecho
    por el ORM (viola el NOT NULL de area_id). Se reconcilia el esquema real
    con el modelo, sin state_operations porque el estado de Django ya coincide
    con el modelo actual. Es idempotente: no hace nada si el esquema ya está
    limpio (por ejemplo en producción, si nunca tuvo este drift)."""

    dependencies = [
        ('pizzeria', '0015_fix_mesa_columns_faltantes'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'pizzeria_mesa' AND column_name = 'numero'
                          AND data_type = 'character varying'
                    ) THEN
                        WITH numeric_max AS (
                            SELECT COALESCE(MAX(numero::integer), 0) AS m
                            FROM pizzeria_mesa WHERE numero ~ '^[0-9]+$'
                        ), reasignadas AS (
                            SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS rn
                            FROM pizzeria_mesa
                            WHERE numero !~ '^[0-9]+$' AND (nombre IS NULL OR nombre = '')
                        )
                        UPDATE pizzeria_mesa m
                        SET nombre = m.numero,
                            numero = (numeric_max.m + reasignadas.rn)::text
                        FROM reasignadas, numeric_max
                        WHERE m.id = reasignadas.id;

                        ALTER TABLE pizzeria_mesa ALTER COLUMN numero TYPE integer USING numero::integer;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'pizzeria_mesa' AND column_name = 'area_id'
                    ) THEN
                        ALTER TABLE pizzeria_mesa DROP CONSTRAINT IF EXISTS pizzeria_mesa_area_id_fb5de3e8_fk_pizzeria_areamesas_id;
                        ALTER TABLE pizzeria_mesa DROP COLUMN area_id;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'pizzeria_mesa' AND column_name = 'capacidad_min'
                    ) THEN
                        ALTER TABLE pizzeria_mesa DROP COLUMN capacidad_min;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'pizzeria_mesa' AND column_name = 'capacidad_max'
                    ) THEN
                        ALTER TABLE pizzeria_mesa DROP COLUMN capacidad_max;
                    END IF;

                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'pizzeria_mesa' AND column_name = 'reservable'
                    ) THEN
                        ALTER TABLE pizzeria_mesa DROP COLUMN reservable;
                    END IF;
                END $$;
            """,
            reverse_sql=migrations.RunSQL.noop,
            state_operations=[],
        ),
    ]
