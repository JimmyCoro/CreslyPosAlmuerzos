from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from .forms_usuarios import CambiarPasswordForm
from .middleware import SESION_DEBE_CAMBIAR
from .models import PerfilUsuario

DESTINO_POR_DEFECTO = '/pizzeria/'


def _destino(request):
    siguiente = request.POST.get('next') or request.GET.get('next') or ''
    if siguiente and url_has_allowed_host_and_scheme(
        siguiente, allowed_hosts={request.get_host()}, require_https=request.is_secure(),
    ):
        return siguiente
    return DESTINO_POR_DEFECTO


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect(_destino(request))

    error = None
    username = ''
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            perfil = PerfilUsuario.objects.filter(user=user).first()
            if perfil and perfil.debe_cambiar_password:
                request.session[SESION_DEBE_CAMBIAR] = True
                return redirect('cambiar_password')
            return redirect(_destino(request))
        # authenticate() devuelve None tanto si la clave está mal como si la
        # cuenta está desactivada: no se distingue a propósito.
        error = 'Usuario o contraseña incorrectos'

    return render(request, 'auth/login.html', {
        'error': error,
        'username': username,
        'next': request.POST.get('next') or request.GET.get('next', ''),
    })


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login')


@require_http_methods(['GET', 'POST'])
def cambiar_password(request):
    obligatorio = bool(request.session.get(SESION_DEBE_CAMBIAR))
    form = CambiarPasswordForm(request.user, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        update_session_auth_hash(request, form.user)
        PerfilUsuario.objects.update_or_create(user=form.user, defaults={'debe_cambiar_password': False})
        request.session.pop(SESION_DEBE_CAMBIAR, None)
        return redirect(DESTINO_POR_DEFECTO)

    return render(request, 'auth/cambiar_password.html', {'form': form, 'obligatorio': obligatorio})
