from urllib.parse import urlencode

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from .permisos import es_peticion_ajax

# Claves de sesión que escribe inicio/views_auth.py al entrar.
SESION_DEBE_CAMBIAR = 'debe_cambiar_password'


class LoginObligatorioMiddleware:
    """Toda la app pide sesión. Las únicas rutas abiertas son el login, los
    estáticos y /admin/ (que trae su propio login)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ruta = request.path
        publicas = (
            reverse('login'), reverse('logout'), '/pizzeria/login/', '/admin/',
            settings.STATIC_URL, '/favicon.ico',
        )
        if ruta.startswith(publicas):
            return self.get_response(request)

        login_url = reverse('login')
        if not request.user.is_authenticated:
            if es_peticion_ajax(request):
                return JsonResponse(
                    {'status': 'error', 'success': False, 'error': 'Tu sesión expiró. Vuelve a ingresar.',
                     'login_url': login_url},
                    status=401,
                )
            return redirect(f'{login_url}?{urlencode({"next": request.get_full_path()})}')

        if request.session.get(SESION_DEBE_CAMBIAR) and ruta != reverse('cambiar_password'):
            if es_peticion_ajax(request):
                return JsonResponse(
                    {'status': 'error', 'success': False, 'error': 'Primero cambia tu contraseña.',
                     'login_url': reverse('cambiar_password')},
                    status=401,
                )
            return redirect('cambiar_password')

        return self.get_response(request)
