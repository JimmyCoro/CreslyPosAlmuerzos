import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Crea un superusuario automáticamente usando variables de entorno'

    def handle(self, *args, **options):
        # Obtener credenciales de variables de entorno
        username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', None)

        # Si no hay contraseña en variables de entorno, no crear superusuario
        if not password:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  No se encontró DJANGO_SUPERUSER_PASSWORD en variables de entorno. '
                    'El superusuario no se creará automáticamente.'
                )
            )
            return

        # Verificar si el superusuario ya existe
        try:
            user = User.objects.get(username=username)
            # Si existe, actualizar la contraseña
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ El superusuario "{username}" ya existe. Contraseña actualizada.'
                )
            )
            return
        except User.DoesNotExist:
            pass  # Continuar para crear el usuario

        # Crear el superusuario
        try:
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Superusuario "{username}" creado exitosamente.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error al crear superusuario: {e}')
            )

