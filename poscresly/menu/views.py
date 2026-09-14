import json

from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from inicio.permisos import es_admin, solo_admin

from . import servicio


@require_GET
def menu_dia(request):
    """1A (sin configurar) o 1B (publicado) — solo lectura. Con ?parcial=1
    devuelve las secciones y la sub-línea para el polling de la pantalla."""
    menu = servicio.construir_menu(servicio.menu_de_hoy())
    sub = servicio.sub_html(menu['sub_pre'], menu['sub_hi'], menu['sub_hi_tono'])

    if request.GET.get('parcial'):
        return JsonResponse({
            'publicado': menu['publicado'],
            'sub': sub,
            'secciones': render_to_string('almuerzos/_menu_secciones.html', {'menu': menu}, request),
        })

    subheader = {
        'titulo': 'Menú del día',
        'sub_pre': menu['sub_pre'],
        'sub_hi': menu['sub_hi'],
        'sub_hi_tono': menu['sub_hi_tono'],
        'sub_id': 'almMenuSub',
        'acciones': [{
            'url': reverse('menu_configurar'),
            'glifo': 'bi-three-dots',
            'label': 'Cambiar el menú',
        }] if es_admin(request.user) else [],
    }
    return render(request, 'almuerzos/menu.html', {'menu': menu, 'subheader': subheader})


@solo_admin
@require_GET
def configurar_menu(request):
    """1C — pantalla completa. Las ranuras se arman en el navegador a partir
    del estado JSON y se guardan juntas al publicar."""
    estado = servicio.estado_configurar(servicio.menu_de_hoy())
    estado['copiar_al_abrir'] = bool(request.GET.get('copiar')) and bool(estado['anterior'])
    estado['urls'] = {
        'menu': reverse('menu'),
        'publicar': reverse('menu_publicar'),
        'crear_plato': reverse('menu_crear_plato'),
    }

    subheader = {
        'titulo': 'Configurar menú',
        'back': {'url': reverse('menu'), 'tipo': 'atras'},
        'sub_pre': f"{estado['fecha_texto']} · ",
        'sub_hi': estado['faltantes_texto'] or 'listo para publicar',
        'sub_hi_tono': 'rojo' if estado['faltantes_texto'] else 'verde',
        'sub_id': 'almConfSub',
    }
    if estado['anterior']:
        subheader['accion'] = {
            'tipo': 'boton',
            'id': 'almCopiarAnterior',
            'label': estado['anterior']['boton'],
        }
    return render(request, 'almuerzos/configurar.html', {'estado': estado, 'subheader': subheader})


def _json(request):
    try:
        return json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return None


@solo_admin
@require_POST
def publicar_menu(request):
    datos = _json(request)
    if not isinstance(datos, dict):
        return JsonResponse({'ok': False, 'error': 'No se pudo leer el menú.'}, status=400)
    try:
        servicio.publicar(servicio.menu_de_hoy(), datos)
    except servicio.MenuInvalido as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    return JsonResponse({'ok': True, 'url': reverse('menu')})


@solo_admin
@require_POST
def crear_plato(request):
    datos = _json(request)
    if not isinstance(datos, dict):
        return JsonResponse({'ok': False, 'error': 'No se pudo leer el plato.'}, status=400)
    try:
        plato = servicio.crear_plato(datos.get('categoria'), datos.get('nombre'))
    except servicio.MenuInvalido as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    return JsonResponse({'ok': True, 'plato': plato})
