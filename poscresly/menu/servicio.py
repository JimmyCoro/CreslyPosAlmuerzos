"""Lógica del menú del día (handoff_menu_del_dia).

Todo lo que las pantallas de Menú muestran como diagnóstico —qué falta,
cuántos almuerzos quedan, el semáforo de cada plato— se calcula aquí y
nunca en el template. `campos_faltantes()` es la única fuente de verdad
para el botón Publicar, la línea roja bajo él y el resaltado del
subheader.
"""
from datetime import date

from django.db import transaction
from django.db.models import Count, Max, Q
from django.utils.html import format_html

from .models import MenuDia, MenuDiaJugo, MenuDiaSegundo, MenuDiaSopa, Plato

AGUA = 'Agua'

# Quedan esta cantidad o menos → "por agotarse" (ámbar).
UMBRAL_POR_AGOTARSE = 5
CUPO_DEFECTO = 30
CUPO_MAXIMO = 999

DIAS = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
         'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

# Orden de pantalla. min/max son por día; `con_cupo` indica si el plato
# lleva porciones (el jugo no se agota).
CATEGORIAS = [
    {
        'clave': 'sopa', 'nombre': 'Sopas', 'singular': 'sopa', 'plural': 'sopas',
        'obligatoria': True, 'min': 2, 'max': 2, 'con_cupo': True,
        'modelo': MenuDiaSopa, 'campo': 'sopa', 'relacion': 'menudiasopa',
        'titulos': ['Primera sopa', 'Segunda sopa'],
        'vacio_titulo': 'Sin sopas para hoy',
        'vacio_texto': 'Hasta que haya al menos una, no se puede vender el almuerzo.',
        'nueva': 'Crear una sopa nueva', 'buscar': 'Buscar sopa',
    },
    {
        'clave': 'segundo', 'nombre': 'Segundos', 'singular': 'segundo', 'plural': 'segundos',
        'obligatoria': True, 'min': 2, 'max': 3, 'con_cupo': True,
        'modelo': MenuDiaSegundo, 'campo': 'segundo', 'relacion': 'menudiasegundo',
        'titulos': ['Primer segundo', 'Segundo plato', 'Tercer segundo'],
        'vacio_titulo': 'Sin segundos para hoy',
        'vacio_texto': 'Hasta que haya al menos uno, no se puede vender el almuerzo.',
        'nueva': 'Crear un segundo nuevo', 'buscar': 'Buscar segundo',
    },
    {
        'clave': 'jugo', 'nombre': 'Bebidas', 'singular': 'jugo', 'plural': 'jugos',
        'obligatoria': False, 'min': 0, 'max': 2, 'con_cupo': False,
        'modelo': MenuDiaJugo, 'campo': 'jugo', 'relacion': 'menudiajugo',
        'titulos': ['Jugo del día', 'Otro jugo'],
        'vacio_titulo': '', 'vacio_texto': '',
        'nueva': 'Crear un jugo nuevo', 'buscar': 'Buscar jugo',
    },
]
CATEGORIA_POR_CLAVE = {c['clave']: c for c in CATEGORIAS}


# ----------------------------------------------------------------- utilidades

def hoy():
    # Mismo criterio que pedidos/views.py al descontar porciones: si aquí se
    # usara otra fecha, Menú y Pedidos mirarían MenuDia distintos.
    return date.today()


def fecha_corta(fecha):
    """'Sábado 12' — sin mes ni año, la pantalla siempre es de hoy."""
    return f"{DIAS[fecha.weekday()].capitalize()} {fecha.day}"


def nombre_dia_relativo(fecha, referencia):
    dias = (referencia - fecha).days
    if dias == 1:
        return 'de ayer'
    if 1 < dias < 7:
        return f"del {DIAS[fecha.weekday()]}"
    return f"del {fecha.day} de {MESES[fecha.month - 1]}"


def estado_por_restantes(restantes):
    if restantes <= 0:
        return 'agotado'
    if restantes <= UMBRAL_POR_AGOTARSE:
        return 'por_agotarse'
    return 'disponible'


def _plural(n, singular, plural):
    return singular if n == 1 else plural


def menu_de_hoy():
    menu, _ = MenuDia.objects.get_or_create(fecha=hoy())
    agua, _ = Plato.objects.get_or_create(
        nombre_plato=AGUA, tipo='jugo', defaults={'precio': 0},
    )
    MenuDiaJugo.objects.get_or_create(menu=menu, jugo=agua)
    return menu


def _items(menu, cat):
    qs = cat['modelo'].objects.filter(menu=menu).select_related(cat['campo']).order_by('id')
    if cat['clave'] == 'jugo':
        qs = qs.exclude(jugo__nombre_plato=AGUA)
    return list(qs)


# ------------------------------------------------------- faltantes (única fuente)

def campos_faltantes(conteos):
    """conteos: {'sopa': 1, 'segundo': 0, ...} → [(cat, cuantos_faltan), ...]"""
    faltan = []
    for cat in CATEGORIAS:
        if not cat['obligatoria']:
            continue
        n = cat['min'] - conteos.get(cat['clave'], 0)
        if n > 0:
            faltan.append((cat, n))
    return faltan


def frase_faltantes(faltan, contar=True, mayuscula=False):
    """'faltan 2 sopas y 1 segundo'. Con contar=False y la categoría vacía
    se nombra sin cifra ('faltan sopas y segundos'), como en la pantalla de
    lectura a las 10 de la mañana."""
    if not faltan:
        return ''
    partes = []
    for cat, n in faltan:
        if contar or n < cat['min']:
            partes.append(f"{n} {_plural(n, cat['singular'], cat['plural'])}")
        else:
            partes.append(cat['plural'])
    lista = partes[0] if len(partes) == 1 else ', '.join(partes[:-1]) + ' y ' + partes[-1]
    verbo = 'falta' if sum(n for _, n in faltan) == 1 else 'faltan'
    frase = f"{verbo} {lista}"
    return frase[0].upper() + frase[1:] if mayuscula else frase


# ------------------------------------------------------------- lectura (1A/1B)

def construir_menu(menu):
    categorias = []
    conteos = {}
    restantes_por_cat = {}

    for cat in CATEGORIAS:
        items = _items(menu, cat)
        conteos[cat['clave']] = len(items)
        if cat['clave'] == 'jugo':
            # Bebidas: jugos del día + agua. No llevan porciones, así que
            # su tarjeta no tiene cifra ni semáforo de agotado.
            bebidas = [{'plato': {'id': i.jugo.id, 'nombre': i.jugo.nombre_plato},
                        'estado': 'disponible', 'siempre': False} for i in items]
            bebidas.append({'plato': {'id': None, 'nombre': AGUA},
                            'estado': 'disponible', 'siempre': True})
            n = len(bebidas)
            categorias.append({
                'clave': 'jugo', 'nombre': 'Bebidas', 'ranuras': bebidas, 'faltan': 0,
                'meta': f"{n} {_plural(n, 'opción', 'opciones')}", 'meta_tono': 'suave',
            })
            continue

        ranuras = []
        for item in items:
            plato = getattr(item, cat['campo'])
            restantes = item.cantidad_actual
            ranuras.append({
                'id': item.id,
                'plato': {'id': plato.id, 'nombre': plato.nombre_plato},
                'cupo': item.cantidad,
                'vendidos': max(item.cantidad - item.cantidad_actual, 0),
                'restantes': restantes,
                'estado': estado_por_restantes(restantes),
            })
        total = sum(r['restantes'] for r in ranuras)
        restantes_por_cat[cat['clave']] = total
        faltan = max(cat['min'] - len(ranuras), 0)
        if faltan:
            meta, meta_tono = f"falta elegir {faltan}", 'rojo'
        else:
            meta = (f"{len(ranuras)} {_plural(len(ranuras), 'opción', 'opciones')} · "
                    f"{total} {_plural(total, 'porción', 'porciones')}")
            meta_tono = 'suave'
        categorias.append({
            'clave': cat['clave'], 'nombre': cat['nombre'],
            'vacio_titulo': cat['vacio_titulo'], 'vacio_texto': cat['vacio_texto'],
            'ranuras': ranuras, 'faltan': faltan, 'meta': meta, 'meta_tono': meta_tono,
        })

    faltan = campos_faltantes(conteos)
    publicado = not faltan
    disponibles = min(
        restantes_por_cat.get(c['clave'], 0) for c in CATEGORIAS if c['obligatoria']
    )

    if not publicado:
        sub_hi, tono = frase_faltantes(faltan, contar=False), 'rojo'
    elif disponibles <= 0:
        sub_hi, tono = 'agotado por hoy', 'rojo'
    else:
        sub_hi = f"{disponibles} {_plural(disponibles, 'almuerzo disponible', 'almuerzos disponibles')}"
        tono = 'verde'

    return {
        'fecha': menu.fecha,
        'fecha_texto': fecha_corta(menu.fecha),
        'publicado': publicado,
        'almuerzos_disponibles': disponibles,
        'categorias': categorias,
        'menu_anterior': menu_anterior(menu) if not publicado else None,
        'sub_pre': f"{fecha_corta(menu.fecha)} · ",
        'sub_hi': sub_hi,
        'sub_hi_tono': tono,
    }


def sub_html(pre, hi, tono):
    return format_html('{}<strong class="pzsh-hl-{}">{}</strong>', pre, tono, hi)


# ------------------------------------------------------------- menú anterior

def menu_anterior(menu):
    previos = (MenuDia.objects.filter(fecha__lt=menu.fecha)
               .filter(Q(sopas__isnull=False) | Q(segundos__isnull=False))
               .distinct().order_by('-fecha'))
    anterior = previos.first()
    if not anterior:
        return None

    ranuras = {}
    resumen = []
    for cat in CATEGORIAS:
        items = _items(anterior, cat)[:cat['max']]
        ranuras[cat['clave']] = [{
            'plato_id': getattr(i, cat['campo']).id,
            'nombre': getattr(i, cat['campo']).nombre_plato,
            'cupo': getattr(i, 'cantidad', 0) or CUPO_DEFECTO,
            'vendidos': 0,
        } for i in items]
        if cat['con_cupo'] and items:
            nombres = [r['nombre'] for r in ranuras[cat['clave']]]
            resumen.append(', '.join([nombres[0]] + [n.lower() for n in nombres[1:]]))

    dia = nombre_dia_relativo(anterior.fecha, menu.fecha)
    dias_atras = (menu.fecha - anterior.fecha).days
    if dias_atras == 1:
        boton = 'Copiar ayer'
    elif dias_atras < 7:
        boton = f"Copiar {DIAS[anterior.fecha.weekday()]}"
    else:
        boton = 'Copiar anterior'
    return {
        'fecha': anterior.fecha.isoformat(),
        'titulo': f"Repetir el menú {dia}",
        'boton': boton,
        'resumen': ' · '.join(resumen),
        'ranuras': ranuras,
    }


# ------------------------------------------------------ configurar (1C / 1D)

def recetario(cat, referencia):
    inicio_mes = referencia.replace(day=1)
    rel = cat['relacion']
    platos = (Plato.objects.filter(tipo=cat['clave'])
              .exclude(nombre_plato=AGUA)
              .annotate(
                  veces_mes=Count(rel, filter=Q(**{
                      f'{rel}__menu__fecha__gte': inicio_mes,
                      f'{rel}__menu__fecha__lt': referencia,
                  })),
                  ultima_vez=Max(f'{rel}__menu__fecha', filter=Q(**{
                      f'{rel}__menu__fecha__lt': referencia,
                  })),
              )
              .order_by('-veces_mes', 'nombre_plato'))
    lista = []
    for p in platos:
        lista.append({
            'id': p.id,
            'nombre': p.nombre_plato,
            'veces_mes': p.veces_mes,
            'hace_dias': (referencia - p.ultima_vez).days if p.ultima_vez else None,
        })
    return lista


def pista_reciente(lista):
    """El plato de la categoría servido más recientemente (última semana),
    para no repetirlo sin darse cuenta."""
    recientes = [p for p in lista if p['hace_dias'] is not None and p['hace_dias'] <= 7]
    if not recientes:
        return None
    p = min(recientes, key=lambda x: x['hace_dias'])
    cuando = 'ayer' if p['hace_dias'] == 1 else f"hace {p['hace_dias']} días"
    return {'nombre': p['nombre'], 'cuando': cuando}


def estado_configurar(menu):
    referencia = menu.fecha
    categorias = []
    conteos = {}
    recetarios = {}
    for cat in CATEGORIAS:
        items = _items(menu, cat)[:cat['max']]
        conteos[cat['clave']] = len(items)
        lista = recetario(cat, referencia)
        recetarios[cat['clave']] = lista
        categorias.append({
            'clave': cat['clave'], 'nombre': cat['nombre'],
            'singular': cat['singular'], 'plural': cat['plural'],
            'obligatoria': cat['obligatoria'], 'min': cat['min'], 'max': cat['max'],
            'con_cupo': cat['con_cupo'], 'titulos': cat['titulos'],
            'nueva': cat['nueva'], 'buscar': cat['buscar'],
            'pista': pista_reciente(lista),
            'ranuras': [{
                'plato_id': getattr(i, cat['campo']).id,
                'nombre': getattr(i, cat['campo']).nombre_plato,
                'cupo': getattr(i, 'cantidad', 0),
                'vendidos': max(getattr(i, 'cantidad', 0) - getattr(i, 'cantidad_actual', 0), 0),
            } for i in items],
        })
    faltan = campos_faltantes(conteos)
    return {
        'fecha_texto': fecha_corta(referencia),
        'categorias': categorias,
        'recetario': recetarios,
        'anterior': menu_anterior(menu),
        'faltantes_texto': frase_faltantes(faltan),
        'cupo_defecto': CUPO_DEFECTO,
        'cupo_maximo': CUPO_MAXIMO,
    }


class MenuInvalido(Exception):
    pass


def publicar(menu, datos):
    """datos: {'sopa': [{'plato_id', 'cupo'}], 'segundo': [...], 'jugo': [...]}.
    Valida en el servidor (el botón bloqueado es solo ayuda visual) y
    reemplaza el menú de hoy conservando lo ya vendido de cada plato."""
    limpio = {}
    for cat in CATEGORIAS:
        filas = datos.get(cat['clave']) or []
        if not isinstance(filas, list) or len(filas) > cat['max']:
            raise MenuInvalido(f"Como máximo {cat['max']} {cat['plural']}.")
        vistos = set()
        normalizadas = []
        for fila in filas:
            try:
                plato_id = int(fila.get('plato_id'))
                cupo = int(fila.get('cupo') or 0) if cat['con_cupo'] else 0
            except (TypeError, ValueError, AttributeError):
                raise MenuInvalido('Datos del menú incompletos.')
            if plato_id in vistos:
                raise MenuInvalido(f"Hay {cat['plural']} repetidas en el menú." if cat['clave'] == 'sopa'
                                   else f"Hay {cat['plural']} repetidos en el menú.")
            if cat['con_cupo'] and not 1 <= cupo <= CUPO_MAXIMO:
                raise MenuInvalido('Cada plato necesita entre 1 y 999 porciones.')
            vistos.add(plato_id)
            normalizadas.append((plato_id, cupo))
        platos = Plato.objects.filter(id__in=vistos, tipo=cat['clave']).in_bulk()
        if len(platos) != len(vistos):
            raise MenuInvalido(f"Algún {cat['singular']} ya no existe en el recetario.")
        limpio[cat['clave']] = [(platos[pid], cupo) for pid, cupo in normalizadas]

    faltan = campos_faltantes({k: len(v) for k, v in limpio.items()})
    if faltan:
        raise MenuInvalido(frase_faltantes(faltan, mayuscula=True))

    with transaction.atomic():
        for cat in CATEGORIAS:
            modelo, campo = cat['modelo'], cat['campo']
            existentes = {}
            for item in _items(menu, cat):
                existentes.setdefault(getattr(item, f'{campo}_id'), item)
            conservar = []
            for plato, cupo in limpio[cat['clave']]:
                item = existentes.get(plato.id)
                if item is None:
                    item = modelo(menu=menu, **{campo: plato})
                    if cat['con_cupo']:
                        item.cantidad = cupo
                    item.save()
                elif cat['con_cupo']:
                    vendidos = max(item.cantidad - item.cantidad_actual, 0)
                    item.cantidad = cupo
                    item.cantidad_actual = max(cupo - vendidos, 0)
                    item.save(update_fields=['cantidad', 'cantidad_actual'])
                conservar.append(item.pk)
            sobrantes = modelo.objects.filter(menu=menu).exclude(pk__in=conservar)
            if cat['clave'] == 'jugo':
                sobrantes = sobrantes.exclude(jugo__nombre_plato=AGUA)
            sobrantes.delete()


def crear_plato(clave, nombre):
    cat = CATEGORIA_POR_CLAVE.get(clave)
    nombre = ' '.join((nombre or '').split())
    if not cat:
        raise MenuInvalido('Categoría desconocida.')
    if not nombre:
        raise MenuInvalido('Escribe el nombre del plato.')
    if len(nombre) > 100:
        raise MenuInvalido('El nombre es demasiado largo.')
    if nombre.lower() == AGUA.lower() and clave == 'jugo':
        raise MenuInvalido('El agua ya está siempre disponible.')
    existente = Plato.objects.filter(tipo=clave, nombre_plato__iexact=nombre).first()
    plato = existente or Plato.objects.create(nombre_plato=nombre[0].upper() + nombre[1:], tipo=clave)
    return {'id': plato.id, 'nombre': plato.nombre_plato, 'veces_mes': 0,
            'hace_dias': None, 'existia': bool(existente)}
