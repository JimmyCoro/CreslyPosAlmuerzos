from django.shortcuts import render, redirect
from datetime import date
from .forms import MenuDiaForm, MenuDiaSopaForm, MenuDiaSegundoForm, MenuDiaJugoForm
from menu.models import MenuDia, MenuDiaSopa, MenuDiaSegundo, MenuDiaJugo, Producto
from pedidos.models import Pedido

import json
from django.core.serializers.json import DjangoJSONEncoder
from decimal import Decimal

def inicio(request):
    hoy = date.today()
    menu, _ = MenuDia.objects.get_or_create(fecha=hoy)



    if request.method == 'POST':
        form_postre = MenuDiaForm(request.POST, instance=menu)
        sopa_forms = [MenuDiaSopaForm(request.POST, prefix=f'sopa{i}') for i in range(2)]
        segundo_forms = [MenuDiaSegundoForm(request.POST, prefix=f'segundo{i}') for i in range(3)]
        jugo_forms = [MenuDiaJugoForm(request.POST, prefix=f'jugo{i}') for i in range(2)]

        if form_postre.is_valid() and all(f.is_valid() for f in sopa_forms + jugo_forms + segundo_forms):
            form_postre.save()

            # Limpiar y volver a guardar sopas
            MenuDiaSopa.objects.filter(menu=menu).delete()
            for form in sopa_forms:
                if form.cleaned_data.get('sopa'):
                    obj = form.save(commit=False)
                    obj.menu = menu
                    # Inicializar cantidad_actual con cantidad
                    obj.cantidad_actual = obj.cantidad
                    obj.save()

            # Limpiar y volver a guardar segundos
            MenuDiaSegundo.objects.filter(menu=menu).delete()
            for form in segundo_forms:
                if form.cleaned_data.get('segundo'):
                    obj = form.save(commit=False)
                    obj.menu = menu
                    # Inicializar cantidad_actual con cantidad
                    obj.cantidad_actual = obj.cantidad
                    obj.save()

            # Limpiar y volver a guardar jugos
            MenuDiaJugo.objects.filter(menu=menu).delete()
            for form in jugo_forms:
                if form.cleaned_data.get('jugo'):
                    obj = form.save(commit=False)
                    obj.menu = menu
                    obj.save()

            return redirect('inicio')

    else:
        form_postre = MenuDiaForm(instance=menu)
        sopa_forms = [MenuDiaSopaForm(prefix=f'sopa{i}') for i in range(2)]
        segundo_forms = [MenuDiaSegundoForm(prefix=f'segundo{i}') for i in range(3)]
        jugo_forms = [MenuDiaJugoForm(prefix=f'jugo{i}') for i in range(2)]

    # -------- Diccionario de precios --------
    precios = {}
    for producto in Producto.objects.all():
        tipo = producto.nombre_producto.lower()  # 'almuerzo', 'sopa', 'segundo'
        precios[tipo] = {
            'servirse': float(producto.precio_servirse),
            'llevar': float(producto.precio_llevar)
        }

    # -------- Cargar pedidos pendientes por categoría --------
    pedidos_todos = Pedido.objects.filter(estado='pendiente').prefetch_related(
        'almuerzos__sopa', 'almuerzos__segundo', 'almuerzos__jugo',
        'sopas__sopa', 'sopas__jugo',
        'segundos__segundo', 'segundos__jugo'
    ).order_by('-fecha_creacion')

    pedidos_servirse = pedidos_todos.filter(tipo='Servirse')
    pedidos_llevar = pedidos_todos.filter(tipo='Levar')
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
        'mesas': range(1, 15),
        'precios': json.dumps(precios, cls=DjangoJSONEncoder),  # Convierte el diccionario Python precios a formato JSON 
        'pedidos_todos': pedidos_todos,
        'pedidos_servirse': pedidos_servirse,
        'pedidos_llevar': pedidos_llevar,
        'pedidos_reservados': pedidos_reservados,
    }

    return render(request, 'inicio/inicio.html', context)
