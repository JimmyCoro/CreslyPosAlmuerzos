from django.shortcuts import render, redirect
from datetime import date
from .forms import MenuDiaForm, MenuDiaSopaForm, MenuDiaSegundoForm, MenuDiaJugoForm
from menu.models import MenuDia, MenuDiaSopa, MenuDiaSegundo, MenuDiaJugo, MenuDiaExtra, Producto
from pedidos.models import Pedido

import json
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal

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

def menu(request):
    """
    Vista para mostrar la página del menú del día
    """
    hoy = date.today()
    menu, _ = MenuDia.objects.get_or_create(fecha=hoy)
    
    # Manejar POST para configuración del menú
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
            MenuDiaJugo.objects.filter(menu=menu).exclude(pk__in=jugos_guardados).delete()

            return redirect('menu')
    else:
        form_postre = MenuDiaForm(instance=menu)
        sopa_forms, segundo_forms, jugo_forms = crear_formularios_menu(menu)
    
    # Obtener datos del menú del día
    sopas_dia = MenuDiaSopa.objects.filter(menu=menu).select_related('sopa')
    segundos_dia = MenuDiaSegundo.objects.filter(menu=menu).select_related('segundo')
    jugos_dia = MenuDiaJugo.objects.filter(menu=menu).select_related('jugo')
    extras_dia = MenuDiaExtra.objects.filter(menu=menu).select_related('extra')
    
    context = {
        'form_postre': form_postre,
        'sopa_forms': sopa_forms,
        'segundo_forms': segundo_forms,
        'jugo_forms': jugo_forms,
        'sopas_dia': sopas_dia,
        'segundos_dia': segundos_dia,
        'jugos_dia': jugos_dia,
        'extras_dia': extras_dia,
    }
    
    return render(request, 'menu.html', context)

def inicio(request):
    hoy = date.today()
    menu, _ = MenuDia.objects.get_or_create(fecha=hoy)
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
            MenuDiaJugo.objects.filter(menu=menu).exclude(pk__in=jugos_guardados).delete()

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

    context = {
        'form_postre': form_postre,
        'sopa_forms': sopa_forms,
        'segundo_forms': segundo_forms,
        'jugo_forms': jugo_forms,
        'sopas_dia': MenuDiaSopa.objects.filter(menu=menu),
        'segundos_dia': MenuDiaSegundo.objects.filter(menu=menu),
        'jugos_dia': MenuDiaJugo.objects.filter(menu=menu),
        'extras_dia': Plato.objects.filter(tipo='extra'),  # Mostrar TODOS los extras siempre
        'mesas': range(1, 15),
        'precios': json.dumps(precios, cls=DjangoJSONEncoder),  # Convierte el diccionario Python precios a formato JSON 
        'pedidos_todos': pedidos_todos,
        'pedidos_servirse': pedidos_servirse,
        'pedidos_llevar': pedidos_llevar,
        'pedidos_reservados': pedidos_reservados,
    }

    return render(request, 'inicio/inicio.html', context)
