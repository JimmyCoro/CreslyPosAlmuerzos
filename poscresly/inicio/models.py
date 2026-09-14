from django.conf import settings
from django.db import models


class PerfilUsuario(models.Model):
    """Datos de la cuenta que no caben en auth.User. El rol vive en los grupos
    de Django (ver inicio/permisos.py), no aquí."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    # El admin entrega una contraseña temporal; hasta cambiarla, el empleado
    # solo puede entrar a /cambiar-password/.
    debe_cambiar_password = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return f'Perfil de {self.user}'
