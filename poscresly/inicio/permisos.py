"""Roles de la app. Son dos grupos de Django (creados por la migración
inicio/0002): Administrador y Empleado. Un superusuario cuenta como
Administrador aunque no esté en el grupo."""
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import render

GRUPO_ADMIN = 'Administrador'
GRUPO_EMPLEADO = 'Empleado'
ROLES = [(GRUPO_ADMIN, 'Administrador'), (GRUPO_EMPLEADO, 'Empleado')]


def es_admin(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    # Se cachea en el objeto: una plantilla puede preguntarlo varias veces.
    if not hasattr(user, '_es_admin'):
        user._es_admin = user.groups.filter(name=GRUPO_ADMIN).exists()
    return user._es_admin


def rol_de(user):
    return GRUPO_ADMIN if es_admin(user) else GRUPO_EMPLEADO


def es_peticion_ajax(request):
    """True si quien pide es un fetch() y espera JSON, no una navegación."""
    modo = request.headers.get('sec-fetch-mode')
    if modo == 'navigate':
        return False
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return True
    if 'application/json' in request.headers.get('accept', ''):
        return True
    if modo in ('cors', 'same-origin', 'no-cors'):
        return True
    if request.method not in ('GET', 'HEAD'):
        return True
    return '/ajax/' in request.path or 'obtener-' in request.path or 'parcial' in request.GET


def solo_admin(vista):
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if es_admin(request.user):
            return vista(request, *args, **kwargs)
        mensaje = 'Solo un administrador puede hacer esto'
        if es_peticion_ajax(request):
            return JsonResponse({'status': 'error', 'success': False, 'error': mensaje, 'message': mensaje}, status=403)
        return render(request, 'auth/sin_permiso.html', {'mensaje': mensaje}, status=403)
    return envoltura


def rol_usuario(request):
    """Context processor: `es_admin` y `rol_nombre` en todas las plantillas."""
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {'es_admin': False, 'rol_nombre': ''}
    return {'es_admin': es_admin(user), 'rol_nombre': rol_de(user)}
