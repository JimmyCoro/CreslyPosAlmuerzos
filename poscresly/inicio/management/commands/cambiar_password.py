import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Cambia la contraseña de un usuario usando variables de entorno'

    def handle(self, *args, **options):
        # Obtener credenciales de variables de entorno
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'cresly')
        new_password = os.getenv('DJANGO_SUPERUSER_PASSWORD', None)

        # Si no hay contraseña en variables de entorno, no hacer nada
        if not new_password:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  No se encontró DJANGO_SUPERUSER_PASSWORD en variables de entorno. '
                    'La contraseña no se cambiará.'
                )
            )
            return

        # Buscar el usuario
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ El usuario "{username}" no existe.')
            )
            return

        # Cambiar la contraseña
        try:
            user.set_password(new_password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Contraseña del usuario "{username}" actualizada exitosamente.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al cambiar contraseña: {e}')
            )

