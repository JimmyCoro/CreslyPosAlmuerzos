"""Configuración → Usuarios. Solo administradores. Las cuentas nunca se
borran: se desactivan, para que su historial de caja y cobros siga teniendo
autor."""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms_usuarios import RestablecerPasswordForm, UsuarioCrearForm, UsuarioEditarForm
from .models import PerfilUsuario
from .permisos import GRUPO_ADMIN, es_admin, solo_admin

User = get_user_model()


def _subheader(titulo, sub_pre='', sub_hi='', tono='neutro', back=None, acciones=None):
    return {
        'titulo': titulo, 'sub_pre': sub_pre, 'sub_hi': sub_hi, 'sub_hi_tono': tono,
        'back': {'url': back} if back else None, 'acciones': acciones or [],
    }


def _ultimo_ingreso(user):
    if not user.last_login:
        return 'nunca ha ingresado'
    local = timezone.localtime(user.last_login)
    dias = (timezone.localdate() - local.date()).days
    hora = local.strftime('%H:%M')
    if dias == 0:
        return f'ingresó hoy {hora}'
    if dias == 1:
        return f'ingresó ayer {hora}'
    return f'ingresó {local.strftime("%d/%m/%Y")}'


@solo_admin
def usuarios_lista(request):
    usuarios = list(User.objects.prefetch_related('groups').order_by('-is_active', 'first_name', 'username'))
    pendientes = set(
        PerfilUsuario.objects.filter(debe_cambiar_password=True).values_list('user_id', flat=True)
    )
    filas = []
    for u in usuarios:
        admin = u.is_superuser or any(g.name == GRUPO_ADMIN for g in u.groups.all())
        partes = [u.username, 'Administrador' if admin else 'Empleado']
        if not u.is_active:
            estado = 'Desactivada'
        elif u.pk in pendientes:
            estado = 'Clave temporal sin cambiar'
        else:
            estado = _ultimo_ingreso(u)
        filas.append({
            'user': u,
            'nombre': u.get_full_name() or u.username,
            'sub': ' · '.join(partes + [estado]),
            'admin': admin,
            'inactivo': not u.is_active,
            'yo': u.pk == request.user.pk,
        })

    activos = sum(1 for f in filas if not f['inactivo'])
    return render(request, 'configuracion/usuarios.html', {
        'filas': filas,
        'subheader': _subheader(
            'Usuarios', sub_hi=f"{activos} activo{'s' if activos != 1 else ''}",
            sub_pre='', tono='neutro',
            acciones=[{'url': reverse('usuario_crear'), 'glifo': 'bi-person-plus', 'label': 'Nuevo usuario'}],
        ),
    })


@solo_admin
@require_http_methods(['GET', 'POST'])
def usuario_crear(request):
    form = UsuarioCrearForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        messages.success(request, f'Usuario «{user.username}» creado. Entrégale su contraseña temporal.')
        return redirect('usuarios')
    return render(request, 'configuracion/usuario_form.html', {
        'form': form,
        'modo': 'crear',
        'subheader': _subheader('Nuevo usuario', back=reverse('usuarios')),
    })


@solo_admin
@require_http_methods(['GET', 'POST'])
def usuario_editar(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    form = UsuarioEditarForm(request.POST or None, instance=usuario, editor=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Cambios guardados para «{usuario.username}».')
        return redirect('usuarios')
    return render(request, 'configuracion/usuario_form.html', {
        'form': form,
        'modo': 'editar',
        'usuario': usuario,
        'usuario_es_admin': es_admin(usuario),
        'subheader': _subheader(usuario.get_full_name() or usuario.username, sub_pre=usuario.username, back=reverse('usuarios')),
    })


@solo_admin
@require_http_methods(['GET', 'POST'])
def usuario_password(request, user_id):
    usuario = get_object_or_404(User, pk=user_id)
    if usuario.pk == request.user.pk:
        # Para la cuenta propia se usa el flujo normal, que pide la clave nueva dos veces.
        return redirect('cambiar_password')
    form = RestablecerPasswordForm(usuario, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Contraseña de «{usuario.username}» restablecida. Entrégale la nueva.')
        return redirect('usuarios')
    return render(request, 'configuracion/usuario_password.html', {
        'form': form,
        'usuario': usuario,
        'subheader': _subheader(
            'Restablecer contraseña', sub_pre=usuario.get_full_name() or usuario.username,
            back=reverse('usuario_editar', args=[usuario.pk]),
        ),
    })
