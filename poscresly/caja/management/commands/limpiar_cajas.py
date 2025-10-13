from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from caja.models import CajaDiaria

class Command(BaseCommand):
    help = 'Elimina todas las cajas anteriores al lunes de esta semana'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma la eliminación (sin esto solo muestra qué se eliminaría)',
        )

    def handle(self, *args, **options):
        # Calcular el lunes de esta semana
        hoy = date.today()
        # Lunes = 0, Martes = 1, ..., Domingo = 6
        dias_desde_lunes = hoy.weekday()
        lunes_esta_semana = hoy - timedelta(days=dias_desde_lunes)
        
        self.stdout.write(f"Fecha de hoy: {hoy}")
        self.stdout.write(f"Lunes de esta semana: {lunes_esta_semana}")
        
        # Buscar cajas anteriores al lunes
        cajas_a_eliminar = CajaDiaria.objects.filter(fecha__lt=lunes_esta_semana)
        
        if not cajas_a_eliminar.exists():
            self.stdout.write(
                self.style.SUCCESS('No hay cajas anteriores al lunes para eliminar.')
            )
            return
        
        self.stdout.write(f"\nCajas encontradas anteriores al lunes ({lunes_esta_semana}):")
        for caja in cajas_a_eliminar:
            estado = "ABIERTA" if caja.estado == 'abierta' else "CERRADA"
            self.stdout.write(f"  - {caja.fecha} - {estado} (ID: {caja.id})")
        
        if not options['confirmar']:
            self.stdout.write(
                self.style.WARNING(
                    f'\nSe encontraron {cajas_a_eliminar.count()} cajas para eliminar.\n'
                    'Para confirmar la eliminación, ejecuta el comando con --confirmar'
                )
            )
            return
        
        # Eliminar las cajas
        cantidad_eliminadas = cajas_a_eliminar.count()
        cajas_a_eliminar.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Se eliminaron {cantidad_eliminadas} cajas anteriores al lunes.'
            )
        )
