from django.shortcuts import render, redirect
from datetime import date
from .forms import MenuDiaForm, MenuDiaSopaForm, MenuDiaSegundoForm, MenuDiaJugoForm
from menu.models import MenuDia, MenuDiaSopa, MenuDiaSegundo, MenuDiaJugo, MenuDiaExtra, Producto, Plato
from pedidos.models import Pedido
from menu import servicio

import json
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal

WATER_JUGO_NAME = 'Agua'


def asegurar_jugo_agua(menu):
    agua_plato, _ = Plato.objects.get_or_create(
        nombre_plato=WATER_JUGO_NAME,
        tipo='jugo',
        defaults={'precio': Decimal('0.00')}
    )
    if not MenuDiaJugo.objects.filter(menu=menu, jugo=agua_plato).exists():
        MenuDiaJugo.objects.create(menu=menu, jugo=agua_plato)
    return agua_plato

def crear_formularios_menu(menu, data=None):
    """
    Función helper para crear formularios del menú con o sin datos POST
    """
    # Crear formularios de sopa
    sopas_existentes = MenuDiaSopa.objects.filter(menu=menu).order_by('id')
    sopa_forms = []
    for i in range(2):
        if i < len(sopas_existentes):
            sopa_forms.append(MenuDiaSopaForm(data, prefix=f'sopa{i}', instance=sopas_existentes[i]))
        else:
            sopa_forms.append(MenuDiaSopaForm(data, prefix=f'sopa{i}'))
    
    # Crear formularios de segundo
    segundos_existentes = MenuDiaSegundo.objects.filter(menu=menu).order_by('id')
    segundo_forms = []
    for i in range(3):
        if i < len(segundos_existentes):
            segundo_forms.append(MenuDiaSegundoForm(data, prefix=f'segundo{i}', instance=segundos_existentes[i]))
        else:
            segundo_forms.append(MenuDiaSegundoForm(data, prefix=f'segundo{i}'))
    
    # Crear formularios de jugo
    jugos_existentes = MenuDiaJugo.objects.filter(menu=menu).order_by('id')
    jugo_forms = []
    for i in range(2):
        if i < len(jugos_existentes):
            jugo_forms.append(MenuDiaJugoForm(data, prefix=f'jugo{i}', instance=jugos_existentes[i]))
        else:
            jugo_forms.append(MenuDiaJugoForm(data, prefix=f'jugo{i}'))
    
    return sopa_forms, segundo_forms, jugo_forms

def inicio(request):
    hoy = date.today()
    menu, _ = MenuDia.objects.get_or_create(fecha=hoy)
    agua_plato = asegurar_jugo_agua(menu)
    if request.method == 'POST':
        form_postre = MenuDiaForm(request.POST, instance=menu)
        sopa_forms, segundo_forms, jugo_forms = crear_formularios_menu(menu, request.POST)

        if form_postre.is_valid() and all(f.is_valid() for f in sopa_forms + jugo_forms + segundo_forms):
            form_postre.save()

            # Guardar sopas (actualizar existentes o crear nuevas)
            sopas_guardadas = []
            for form in sopa_forms:
                if form.cleaned_data.get('sopa'):
                    obj = form.save(commit=False)
                    obj.menu = menu
                    # SIEMPRE sincronizar cantidad_actual con cantidad
                    obj.cantidad_actual = obj.cantidad
                    obj.save()
                    sopas_guardadas.append(obj.pk)
            
            # Eliminar sopas que ya no están en el formulario
            MenuDiaSopa.objects.filter(menu=menu).exclude(pk__in=sopas_guardadas).delete()

            # Guardar segundos (actualizar existentes o crear nuevos)
            segundos_guardados = []
            for form in segundo_forms:
                if form.cleaned_data.get('segundo'):
                    obj = form.save(commit=False)
                    obj.menu = menu
                    # SIEMPRE sincronizar cantidad_actual con cantidad
                    obj.cantidad_actual = obj.cantidad
                    obj.save()
                    segundos_guardados.append(obj.pk)
            
            # Eliminar segundos que ya no están en el formulario
            MenuDiaSegundo.objects.filter(menu=menu).exclude(pk__in=segundos_guardados).delete()

            # Guardar jugos (actualizar existentes o crear nuevos)
            jugos_guardados = []
            for form in jugo_forms:
                if form.cleaned_data.get('jugo'):
                    obj = form.save(commit=False)
                    obj.menu = menu
                    obj.save()
                    jugos_guardados.append(obj.pk)
            
            # Eliminar jugos que ya no están en el formulario
            MenuDiaJugo.objects.filter(menu=menu).exclude(pk__in=jugos_guardados).exclude(jugo=agua_plato).delete()

            return redirect('inicio')

    else:
        form_postre = MenuDiaForm(instance=menu)
        sopa_forms, segundo_forms, jugo_forms = crear_formularios_menu(menu)

    # -------- Diccionario de precios --------
    precios = {}
    for producto in Producto.objects.all():
        tipo = producto.nombre_producto.lower()  # 'almuerzo', 'sopa', 'segundo'
        precios[tipo] = {
            'Servirse': float(producto.precio_servirse),
            'Llevar': float(producto.precio_llevar)
        }
    
    # Agregar precios de extras (precio único, no diferencia servirse/llevar)
    from menu.models import Plato
    extras = Plato.objects.filter(tipo='extra')
    precios['extra'] = {}
    for extra in extras:
        precios['extra'][extra.nombre_plato] = float(extra.precio)

    # -------- Cargar pedidos pendientes por categoría --------
    pedidos_todos = Pedido.objects.filter(estado='pendiente').prefetch_related(
        'almuerzos__sopa', 'almuerzos__segundo', 'almuerzos__jugo',
        'sopas__sopa', 'sopas__jugo',
        'segundos__segundo', 'segundos__jugo'
    ).order_by('-fecha_creacion')

    pedidos_servirse = pedidos_todos.filter(tipo='Servirse')
    pedidos_llevar = pedidos_todos.filter(tipo='Llevar')
    pedidos_reservados = pedidos_todos.filter(tipo='Reservado')

    # Calcular totales para cada pedido
    for pedido in pedidos_todos:
        total_calculado = Decimal('0.00')
        
        # Sumar almuerzos
        for almuerzo in pedido.almuerzos.all():
            total_calculado += almuerzo.precio_unitario * Decimal(str(almuerzo.cantidad))
        
        # Sumar sopas
        for sopa in pedido.sopas.all():
            total_calculado += sopa.precio_unitario * Decimal(str(sopa.cantidad))
        
        # Sumar segundos
        for segundo in pedido.segundos.all():
            total_calculado += segundo.precio_unitario * Decimal(str(segundo.cantidad))
        
        pedido.total_calculado = total_calculado

    # -------- Pantalla de pedidos (handoff_nuevo_pedido_almuerzos) --------
    sopas_dia = list(MenuDiaSopa.objects.filter(menu=menu).select_related('sopa').order_by('id'))
    segundos_dia = list(MenuDiaSegundo.objects.filter(menu=menu).select_related('segundo').order_by('id'))
    jugos_dia = list(MenuDiaJugo.objects.filter(menu=menu).select_related('jugo').order_by('id'))
    extras_dia = list(Plato.objects.filter(tipo='extra').order_by('nombre_plato'))

    def _plato_con_cupo(item, plato):
        return {
            'id': plato.id,          # Plato.id: lo que espera guardar_pedido
            'dia_id': item.id,       # MenuDiaSopa/Segundo.id: lo que devuelve obtener-cantidades-modal
            'nombre': plato.nombre_plato,
            'restantes': item.cantidad_actual,
            'estado': servicio.estado_por_restantes(item.cantidad_actual),
        }

    menu_pedidos = {
        'sopas': [_plato_con_cupo(s, s.sopa) for s in sopas_dia],
        'segundos': [_plato_con_cupo(s, s.segundo) for s in segundos_dia],
        'jugos': [{'id': j.jugo.id, 'nombre': j.jugo.nombre_plato} for j in jugos_dia],
        'extras': [{'id': e.id, 'nombre': e.nombre_plato, 'precio': float(e.precio)} for e in extras_dia],
        'umbral': servicio.UMBRAL_POR_AGOTARSE,
    }

    por_entregar = pedidos_todos.count()
    monto_pendiente = sum((p.total or Decimal('0.00')) for p in pedidos_todos)
    subheader = {
        'titulo': 'Pedidos',
        'sub_id': 'almPedSub',
        'sub_pre': f"{servicio.fecha_corta(hoy)} · ",
        'sub_hi': f"{por_entregar} por entregar" if por_entregar else 'nada por entregar',
        'sub_hi_tono': 'ambar' if por_entregar else 'neutro',
        'sub_post': f" · ${monto_pendiente:.2f}",
        'acciones': [{'id': 'almPedBuscarBtn', 'glifo': 'bi-search', 'label': 'Buscar pedido'}],
        'segunda': {
            'tipo': 'chips',
            'chip_group_id': 'almPedFiltros',
            'chips': [
                {'label': 'Todos', 'value': 'todos', 'active': True, 'count': por_entregar, 'count_id': 'contador-todos'},
                {'label': 'Servirse', 'value': 'servirse', 'count': pedidos_servirse.count(), 'count_id': 'contador-servirse'},
                {'label': 'Llevar', 'value': 'llevar', 'count': pedidos_llevar.count(), 'count_id': 'contador-llevar'},
                {'label': 'Reserva', 'value': 'reservados', 'count': pedidos_reservados.count(), 'count_id': 'contador-reservados'},
            ],
        },
    }

    context = {
        'subheader': subheader,
        'menu_pedidos': menu_pedidos,
        'form_postre': form_postre,
        'sopa_forms': sopa_forms,
        'segundo_forms': segundo_forms,
        'jugo_forms': jugo_forms,
        'sopas_dia': MenuDiaSopa.objects.filter(menu=menu),
        'segundos_dia': MenuDiaSegundo.objects.filter(menu=menu),
        'jugos_dia': MenuDiaJugo.objects.filter(menu=menu),
        'extras_dia': Plato.objects.filter(tipo='extra'),  # Mostrar TODOS los extras siempre
        'mesas': range(1, 16),
        'precios': precios,  # json_script en el template
        'pedidos_todos': pedidos_todos,
        'pedidos_servirse': pedidos_servirse,
        'pedidos_llevar': pedidos_llevar,
        'pedidos_reservados': pedidos_reservados,
    }

    return render(request, 'inicio/inicio.html', context)
