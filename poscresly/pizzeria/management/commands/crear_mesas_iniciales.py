from django.core.management.base import BaseCommand

from pizzeria.models import Mesa

# Grid inicial 4x3 (12 mesas), posiciones en % dentro del floor plan.
FILAS = 3
COLUMNAS = 4


class Command(BaseCommand):
    help = 'Crea un set inicial de mesas distribuidas en grid para el mapa gráfico de pizzería'

    def add_arguments(self, parser):
        parser.add_argument('--cantidad', type=int, default=FILAS * COLUMNAS)

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        creadas = 0
        numero = 1
        for fila in range(FILAS):
            for col in range(COLUMNAS):
                if numero > cantidad:
                    break
                pos_x = 10 + col * (80 / max(COLUMNAS - 1, 1))
                pos_y = 15 + fila * (70 / max(FILAS - 1, 1))
                _, created = Mesa.objects.get_or_create(
                    numero=numero,
                    defaults={'pos_x': pos_x, 'pos_y': pos_y, 'capacidad': 4},
                )
                if created:
                    creadas += 1
                numero += 1

        self.stdout.write(self.style.SUCCESS(f"{creadas} mesas nuevas creadas (de {cantidad} solicitadas)."))
