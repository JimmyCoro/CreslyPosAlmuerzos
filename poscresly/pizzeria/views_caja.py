"""Módulo Caja móvil (pizzeria/handoff_caja): turno, movimientos del cajón,
retiro a bóveda y cortes anteriores. La cifra que manda es lo que debe haber
en el cajón; se calcula aquí, nunca en la plantilla ni en JS."""
import json
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (
    CajaPizzeria,
    CajaPizzeriaEfectivo,
    CajaPizzeriaTarjeta,
    CajaPizzeriaTransferencia,
    MovimientoCajaPizzeria,
    PagoPedido,
)
from .views import LOGIN_URL

# Pendiente de decidir si es configurable por sucursal (handoff §8).
UMBRAL_RETIRO = Decimal('200.00')
ATAJOS_FONDO = [Decimal('30'), Decimal('50'), Decimal('75'), Decimal('100')]
MONTO_MAXIMO = Decimal('99999.99')
CENTAVO = Decimal('0.01')

# (clave del conteo, etiqueta, valor). La clave "m1" separa la moneda de $1 del billete.
BILLETES = [('20', '$20', '20'), ('10', '$10', '10'), ('5', '$5', '5'), ('1', '$1', '1')]
MONEDAS = [
    ('m1', '$1 moneda', '1'), ('0.50', '50¢', '0.50'), ('0.25', '25¢', '0.25'),
    ('0.10', '10¢', '0.10'), ('0.05', '5¢', '0.05'), ('0.01', '1¢', '0.01'),
]
VALOR_DENOMINACION = {clave: Decimal(valor) for clave, _, valor in BILLETES + MONEDAS}

DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
DIAS_LARGOS = ['LUNES', 'MARTES', 'MIÉRCOLES', 'JUEVES', 'VIERNES', 'SÁBADO', 'DOMINGO']
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']


# ===== Formato =====

def _dinero(valor):
    return f'${valor:.2f}'


def _nombre_corto(user):
    if not user:
        return ''
    nombre = (user.first_name or user.username).strip()
    apellido = (user.last_name or '').strip()
    return f'{nombre} {apellido[0]}.' if apellido else nombre


def _nombre_completo(user):
    return (user.get_full_name() or user.username) if user else ''


def _hora(dt):
    local = timezone.localtime(dt)
    hora12 = local.hour % 12 or 12
    return f"{hora12}:{local.minute:02d} {'am' if local.hour < 12 else 'pm'}"


def _hace(dt):
    minutos = max(0, int((timezone.now() - dt).total_seconds() // 60))
    if minutos < 60:
        return f'hace {minutos} min'
    if minutos < 24 * 60:
        return f'hace {minutos // 60} h {minutos % 60:02d}'
    dias = minutos // (24 * 60)
    return f"hace {dias} día{'s' if dias != 1 else ''}"


def _fecha_corta(dt):
    fecha = timezone.localtime(dt).date()
    return f'{DIAS[fecha.weekday()]} {fecha.day} {MESES[fecha.month - 1]}'


def _dia_relativo(dt):
    fecha = timezone.localtime(dt).date()
    hoy = timezone.localdate()
    if fecha == hoy:
        return 'Hoy'
    if fecha == hoy - timedelta(days=1):
        return 'Ayer'
    return _fecha_corta(dt)


def _encabezado_dia(fecha):
    hoy = timezone.localdate()
    base = f'{DIAS_LARGOS[fecha.weekday()]} {fecha.day}'
    if fecha == hoy:
        return f'HOY · {base}'
    if fecha == hoy - timedelta(days=1):
        return f'AYER · {base}'
    return base


# ===== Cálculo del turno =====

def _caja_abierta():
    return (
        CajaPizzeria.objects.filter(estado='abierta')
        .select_related('abierta_por').order_by('-fecha_apertura').first()
    )


def _fondo_inicial(caja):
    efectivo = CajaPizzeriaEfectivo.objects.filter(caja=caja).first()
    return efectivo.monto_inicial if efectivo else Decimal('0.00')


def _resumen_turno(caja):
    pagos = PagoPedido.objects.filter(pedido__estado='cobrado', creado_en__gte=caja.fecha_apertura)
    if caja.fecha_cierre:
        pagos = pagos.filter(creado_en__lte=caja.fecha_cierre)
    por_metodo = {row['metodo']: row['total'] for row in pagos.values('metodo').annotate(total=Sum('monto'))}

    por_tipo = {
        row['tipo']: row['total']
        for row in caja.movimientos.filter(anulado=False).values('tipo').annotate(total=Sum('monto'))
    }
    fondo = _fondo_inicial(caja)
    efectivo = por_metodo.get('Efectivo') or Decimal('0.00')
    tarjeta = por_metodo.get('Tarjeta') or Decimal('0.00')
    transferencia = por_metodo.get('Transferencia') or Decimal('0.00')
    ingresos = por_tipo.get('ingreso') or Decimal('0.00')
    retiros = por_tipo.get('retiro') or Decimal('0.00')
    gastos = por_tipo.get('gasto') or Decimal('0.00')

    return {
        'fondo_inicial': fondo,
        'ventas_efectivo': efectivo,
        'ventas_tarjeta': tarjeta,
        'ventas_transferencia': transferencia,
        'total_vendido': efectivo + tarjeta + transferencia,
        'ordenes_cobradas': pagos.values('pedido').distinct().count(),
        'total_ingresos': ingresos,
        'total_retirado': retiros,
        'total_gastos': gastos,
        # Solo el efectivo entra al cajón; tarjeta y transferencia son contexto.
        'esperado_en_caja': fondo + efectivo + ingresos - retiros - gastos,
    }


def _motivo_cierre(caja):
    _, separador, motivo = (caja.observaciones or '').rpartition('Cierre:')
    return motivo.strip() if separador else ''


def _corte(caja):
    """Resultado de un turno cerrado: diferencia = contado al cerrar − esperado."""
    resumen = _resumen_turno(caja)
    efectivo = CajaPizzeriaEfectivo.objects.filter(caja=caja).first()
    contado = efectivo.monto_final if efectivo else None
    if contado is None:
        resultado, diferencia = 'sin_conteo', None
    else:
        diferencia = (contado - resumen['esperado_en_caja']).quantize(CENTAVO)
        resultado = 'cuadro' if diferencia == 0 else ('faltante' if diferencia < 0 else 'sobrante')
    return {'caja': caja, 'resumen': resumen, 'diferencia': diferencia, 'resultado': resultado}


def _texto_diferencia(corte):
    diferencia = corte['diferencia']
    if diferencia is None:
        return 'sin conteo'
    if diferencia == 0:
        return '$0.00'
    signo = '−' if diferencia < 0 else '+'
    return f'{signo} {_dinero(abs(diferencia))}'


def _ultimo_corte():
    caja = CajaPizzeria.objects.filter(estado='cerrada').select_related('cerrada_por').order_by('-fecha_cierre').first()
    return _corte(caja) if caja else None


# ===== Validación compartida (botón, línea de "qué falta" y POST) =====

def _parse_monto(valor, permitir_cero=False):
    try:
        monto = Decimal(str(valor).strip().replace(',', '.'))
    except (InvalidOperation, AttributeError):
        return None
    minimo_valido = monto >= 0 if permitir_cero else monto > 0
    if not monto.is_finite() or not minimo_valido or monto > MONTO_MAXIMO:
        return None
    return monto.quantize(CENTAVO)


def campos_faltantes(monto, categoria=None, pide_categoria=False, etiqueta_monto='el monto'):
    faltan = []
    if monto is None:
        faltan.append(etiqueta_monto)
    if pide_categoria and not categoria:
        faltan.append('la categoría')
    return faltan


def _mensaje_faltantes(faltan):
    return 'Falta ' + ' y '.join(faltan) if faltan else ''


def _error(mensaje, status=400):
    return JsonResponse({'status': 'error', 'message': mensaje}, status=status)


def _caja_para_movimiento(turno_id):
    """Bloquea la caja del POST; un movimiento nunca va contra un turno cerrado."""
    try:
        turno_id = int(turno_id)
    except (TypeError, ValueError):
        return None
    caja = CajaPizzeria.objects.select_for_update().filter(pk=turno_id).first()
    if caja is None or caja.estado != 'abierta':
        return None
    return caja


def _leer_json(request):
    try:
        return json.loads(request.body or b'{}')
    except (json.JSONDecodeError, TypeError):
        return None


# ===== Pantallas =====

def _subheader(titulo, sub_pre='', sub_hi='', tono='neutro', sub_post='', back=None, chips=None):
    subheader = {
        'titulo': titulo, 'sub_pre': sub_pre, 'sub_hi': sub_hi, 'sub_hi_tono': tono, 'sub_post': sub_post,
    }
    if back:
        subheader['back'] = {'url': back}
    if chips:
        subheader['segunda'] = {'tipo': 'chips', 'chips': chips}
    return subheader


def _denominaciones():
    def filas(lista):
        return [{'clave': clave, 'etiqueta': etiqueta, 'valor': valor} for clave, etiqueta, valor in lista]
    return {'billetes': filas(BILLETES), 'monedas': filas(MONEDAS)}


@login_required(login_url=LOGIN_URL)
def estado_caja(request):
    caja = _caja_abierta()
    if caja is None:
        return redirect('pizzeria_caja_abrir')

    turno = _resumen_turno(caja)
    vendido = turno['total_vendido']
    formas_pago = []
    for nombre, clave, color in [
        ('Efectivo', 'ventas_efectivo', '#14181d'),
        ('Tarjeta', 'ventas_tarjeta', '#5b6673'),
        ('Transferencia', 'ventas_transferencia', '#a8afb8'),
    ]:
        monto = turno[clave]
        formas_pago.append({
            'nombre': nombre, 'monto': monto, 'color': color,
            'pct': round(monto / vendido * 100) if vendido else 0,
        })

    movimientos = caja.movimientos.filter(anulado=False)
    ultimo_mov = movimientos.order_by('-creado_en').first()
    ultimo_en = ultimo_mov.creado_en if ultimo_mov else caja.fecha_apertura
    n_registros = movimientos.count() + 1  # + la apertura

    ultimo = _ultimo_corte()
    corte_fila = None
    if ultimo:
        corte_fila = {
            'dia': _dia_relativo(ultimo['caja'].fecha_cierre),
            'diferencia': _texto_diferencia(ultimo),
            'resultado': ultimo['resultado'],
        }

    cajero = _nombre_corto(caja.abierta_por)
    return render(request, 'pizzeria/caja/estado.html', {
        'turno': turno,
        'caja': caja,
        'formas_pago': formas_pago,
        'esperado_centavos': int(turno['esperado_en_caja'] * 100),
        'supera_umbral': turno['esperado_en_caja'] > UMBRAL_RETIRO,
        'umbral_retiro': UMBRAL_RETIRO,
        'movimientos_sub': f"{n_registros} registro{'s' if n_registros != 1 else ''} · último {_hora(ultimo_en)}",
        'corte_fila': corte_fila,
        'denominaciones': _denominaciones(),
        'categorias': MovimientoCajaPizzeria.CATEGORIAS,
        'subheader': _subheader(
            'Caja', sub_pre='Turno abierto ', sub_hi=_hace(caja.fecha_apertura), tono='ambar',
            sub_post=f' · {cajero}' if cajero else '',
        ),
    })


@login_required(login_url=LOGIN_URL)
@require_http_methods(['GET', 'POST'])
def abrir_caja(request):
    if _caja_abierta() is not None:
        return redirect('pizzeria_caja')

    anterior = (
        CajaPizzeria.objects.filter(estado='cerrada').select_related('cerrada_por')
        .order_by('-fecha_cierre').first()
    )
    propuesto = None
    if anterior:
        efectivo = CajaPizzeriaEfectivo.objects.filter(caja=anterior).first()
        if efectivo:
            propuesto = efectivo.monto_final if efectivo.monto_final is not None else efectivo.monto_inicial

    error = ''
    valor_campo = f'{propuesto:.2f}' if propuesto is not None else ''
    if request.method == 'POST':
        valor_campo = (request.POST.get('fondo_inicial') or '').strip()
        fondo = _parse_monto(valor_campo, permitir_cero=True)
        error = _mensaje_faltantes(campos_faltantes(fondo, etiqueta_monto='el fondo inicial'))
        if not error:
            with transaction.atomic():
                if CajaPizzeria.objects.select_for_update().filter(estado='abierta').exists():
                    return redirect('pizzeria_caja')
                observaciones = ''
                if propuesto is not None and fondo != propuesto:
                    observaciones = (
                        f'Fondo propuesto {_dinero(propuesto)}, abrió con {_dinero(fondo)} '
                        f'(diferencia {"+" if fondo > propuesto else "−"}{_dinero(abs(fondo - propuesto))})'
                    )
                caja = CajaPizzeria.objects.create(
                    fecha=timezone.localdate(), estado='abierta', abierta_por=request.user, observaciones=observaciones,
                )
                CajaPizzeriaEfectivo.objects.create(caja=caja, monto_inicial=fondo)
                CajaPizzeriaTransferencia.objects.create(caja=caja, monto_inicial=0)
                CajaPizzeriaTarjeta.objects.create(caja=caja, monto_inicial=0)
            return redirect('pizzeria_caja')

    contexto_anterior = None
    if anterior:
        corte = _corte(anterior)
        contexto_anterior = {
            'fecha': _fecha_corta(anterior.fecha_cierre),
            'cajero': _nombre_corto(anterior.cerrada_por),
            'hora': _hora(anterior.fecha_cierre),
            'diferencia': _texto_diferencia(corte),
            'resultado': corte['resultado'],
        }

    ahora = timezone.now()
    return render(request, 'pizzeria/caja/abrir.html', {
        'valor_campo': valor_campo,
        'propuesto': propuesto,
        'atajos': [f'{a:.2f}' for a in ATAJOS_FONDO],
        'error': error,
        'anterior': contexto_anterior,
        'cajero_nombre': _nombre_completo(request.user),
        'cajero_rol': 'Administrador' if request.user.is_superuser else 'Cajero',
        'turno_texto': f'{_fecha_corta(ahora)} · {_hora(ahora)}',
        'subheader': _subheader(
            'Abrir caja', sub_hi='Falta el fondo inicial', tono='rojo', sub_post=' para empezar a cobrar',
            back=reverse('pizzeria_inicio'),
        ),
    })


FILTROS_MOVIMIENTOS = [('todos', 'Todos'), ('retiro', 'Retiros'), ('gasto', 'Gastos'), ('ingreso', 'Ingresos')]


def _fila_movimiento(mov):
    autor = _nombre_corto(mov.autor)
    partes = [_hora(mov.creado_en)] + ([autor] if autor else [])
    if mov.tipo == 'retiro':
        titulo = 'Retiro a bóveda' + (f' · {mov.detalle}' if mov.detalle else '')
        signo = '−'
    else:
        etiqueta = 'Gasto' if mov.tipo == 'gasto' else 'Ingreso'
        titulo = f'{etiqueta} · {mov.detalle or mov.get_categoria_display() or "sin detalle"}'
        signo = '−' if mov.tipo == 'gasto' else '+'
    return {
        'tipo': mov.tipo,
        'titulo': titulo,
        'sub': ' · '.join(partes),
        'monto': f'{signo} {_dinero(mov.monto)}',
        'saldo': f'quedan {_dinero(mov.saldo_posterior)}',
        'fecha': timezone.localtime(mov.creado_en).date(),
    }


@login_required(login_url=LOGIN_URL)
def movimientos_caja(request):
    caja = _caja_abierta()
    if caja is None:
        return redirect('pizzeria_caja_abrir')

    filtro = request.GET.get('tipo', 'todos')
    if filtro not in dict(FILTROS_MOVIMIENTOS):
        filtro = 'todos'

    movimientos = caja.movimientos.filter(anulado=False).select_related('autor')
    total = movimientos.count() + 1
    if filtro != 'todos':
        movimientos = movimientos.filter(tipo=filtro)
    filas = [_fila_movimiento(m) for m in movimientos]

    if filtro == 'todos':
        filas.append({
            'tipo': 'apertura',
            'titulo': 'Apertura de caja',
            'sub': ' · '.join([_hora(caja.fecha_apertura)] + ([_nombre_corto(caja.abierta_por)] if caja.abierta_por else [])),
            'monto': _dinero(_fondo_inicial(caja)),
            'saldo': 'fondo',
            'fecha': timezone.localtime(caja.fecha_apertura).date(),
        })

    grupos = []
    for fila in filas:
        if not grupos or grupos[-1]['fecha'] != fila['fecha']:
            grupos.append({'fecha': fila['fecha'], 'titulo': _encabezado_dia(fila['fecha']), 'filas': []})
        grupos[-1]['filas'].append(fila)

    base = reverse('pizzeria_caja_movimientos')
    chips = [
        {
            'label': etiqueta, 'value': clave, 'active': clave == filtro,
            'url': base if clave == 'todos' else f'{base}?tipo={clave}',
            'count': total if clave == 'todos' else None,
        }
        for clave, etiqueta in FILTROS_MOVIMIENTOS
    ]
    turno = _resumen_turno(caja)
    return render(request, 'pizzeria/caja/movimientos.html', {
        'grupos': grupos,
        'filtro': filtro,
        'subheader': _subheader(
            'Movimientos', sub_pre='Turno de hoy · saldo ', sub_hi=_dinero(turno['esperado_en_caja']),
            back=reverse('pizzeria_caja'), chips=chips,
        ),
    })


FILTROS_CORTES = [('todos', 'Todos'), ('diferencia', 'Con diferencia'), ('mios', 'Mis turnos')]


def _franja(dt):
    return 'día' if timezone.localtime(dt).hour < 16 else 'noche'


@login_required(login_url=LOGIN_URL)
def cortes_caja(request):
    filtro = request.GET.get('filtro', 'todos')
    if filtro not in dict(FILTROS_CORTES):
        filtro = 'todos'

    cajas = (
        CajaPizzeria.objects.filter(estado='cerrada', fecha_cierre__isnull=False)
        .select_related('abierta_por', 'cerrada_por').order_by('-fecha_apertura')[:14]
    )
    cortes = [_corte(c) for c in cajas]
    con_diferencia = sum(1 for c in cortes if c['resultado'] in ('faltante', 'sobrante'))

    if filtro == 'diferencia':
        cortes = [c for c in cortes if c['resultado'] in ('faltante', 'sobrante')]
    elif filtro == 'mios':
        cortes = [c for c in cortes if request.user.pk in (c['caja'].abierta_por_id, c['caja'].cerrada_por_id)]

    hoy = timezone.localdate()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    grupos = []
    for corte in cortes:
        caja = corte['caja']
        fecha = timezone.localtime(caja.fecha_apertura).date()
        if fecha >= inicio_semana:
            grupo = 'ESTA SEMANA'
        elif fecha >= inicio_semana - timedelta(days=7):
            grupo = 'SEMANA PASADA'
        else:
            grupo = 'ANTERIORES'
        cajero = _nombre_corto(caja.cerrada_por or caja.abierta_por) or 'Sin cajero'
        motivo = _motivo_cierre(caja)
        if corte['resultado'] in ('faltante', 'sobrante') and motivo:
            sub = f'{cajero} · «{motivo}»'
        else:
            sub = f"{cajero} · cerró {_hora(caja.fecha_cierre)} · {_dinero(corte['resumen']['total_vendido'])} vendido"
        if not grupos or grupos[-1]['titulo'] != grupo:
            grupos.append({'titulo': grupo, 'filas': []})
        grupos[-1]['filas'].append({
            'titulo': f'{_fecha_corta(caja.fecha_apertura)} · turno {_franja(caja.fecha_apertura)}',
            'sub': sub,
            'resultado': corte['resultado'],
            'diferencia': _texto_diferencia(corte),
            'etiqueta': {
                'cuadro': 'CUADRÓ', 'faltante': 'FALTANTE', 'sobrante': 'SOBRANTE', 'sin_conteo': 'SIN CONTEO',
            }[corte['resultado']],
        })

    base = reverse('pizzeria_caja_cortes')
    chips = [
        {'label': etiqueta, 'value': clave, 'active': clave == filtro,
         'url': base if clave == 'todos' else f'{base}?filtro={clave}'}
        for clave, etiqueta in FILTROS_CORTES
    ]
    n = len(cajas)
    if con_diferencia:
        sub_hi, tono = f'{con_diferencia} con diferencia', 'rojo'
    else:
        sub_hi, tono = ('todos cuadraron', 'verde') if n else ('sin turnos cerrados', 'neutro')
    volver = reverse('pizzeria_caja') if _caja_abierta() else reverse('pizzeria_caja_abrir')
    return render(request, 'pizzeria/caja/cortes.html', {
        'grupos': grupos,
        'hay_turnos': bool(n),
        'subheader': _subheader(
            'Cortes anteriores', sub_pre=f"Últimos {n} turno{'s' if n != 1 else ''} · " if n else '',
            sub_hi=sub_hi, tono=tono, back=volver, chips=chips,
        ),
    })


# ===== Acciones (POST JSON) =====

@login_required(login_url=LOGIN_URL)
@require_http_methods(['POST'])
def registrar_retiro(request):
    data = _leer_json(request)
    if data is None:
        return _error('Datos inválidos')

    conteo_limpio = {}
    total = Decimal('0.00')
    for clave, cantidad in (data.get('conteo') or {}).items():
        if clave not in VALOR_DENOMINACION:
            return _error('Denominación inválida')
        try:
            cantidad = int(cantidad)
        except (TypeError, ValueError):
            return _error('Cantidad inválida')
        if cantidad < 0 or cantidad > 10000:
            return _error('Cantidad inválida')
        if cantidad:
            conteo_limpio[clave] = cantidad
            total += VALOR_DENOMINACION[clave] * cantidad
    if total <= 0:
        return _error('Cuenta lo que vas a retirar')

    with transaction.atomic():
        caja = _caja_para_movimiento(data.get('turno_id'))
        if caja is None:
            return _error('Este turno ya está cerrado. Recarga la pantalla.', status=409)
        esperado = _resumen_turno(caja)['esperado_en_caja']
        if total > esperado:
            return _error('Estás retirando más de lo que hay en el cajón')
        MovimientoCajaPizzeria.objects.create(
            caja=caja, tipo='retiro', monto=total, conteo=conteo_limpio,
            detalle=(data.get('motivo') or '').strip()[:200], autor=request.user,
            saldo_posterior=esperado - total,
        )
    return JsonResponse({'status': 'ok', 'message': f'Retiraste {_dinero(total)} a bóveda'})


@login_required(login_url=LOGIN_URL)
@require_http_methods(['POST'])
def registrar_movimiento(request):
    data = _leer_json(request)
    if data is None:
        return _error('Datos inválidos')

    tipo = data.get('tipo')
    if tipo not in ('ingreso', 'gasto'):
        return _error('Tipo de movimiento inválido')
    categoria = data.get('categoria') or ''
    if categoria and categoria not in dict(MovimientoCajaPizzeria.CATEGORIAS):
        return _error('Categoría inválida')
    monto = _parse_monto(data.get('monto'))
    faltan = campos_faltantes(monto, categoria, pide_categoria=True)
    if faltan:
        return _error(_mensaje_faltantes(faltan))

    with transaction.atomic():
        caja = _caja_para_movimiento(data.get('turno_id'))
        if caja is None:
            return _error('Este turno ya está cerrado. Recarga la pantalla.', status=409)
        esperado = _resumen_turno(caja)['esperado_en_caja']
        saldo = esperado + monto if tipo == 'ingreso' else esperado - monto
        if saldo < 0:
            return _error('El gasto deja el cajón en negativo')
        MovimientoCajaPizzeria.objects.create(
            caja=caja, tipo=tipo, monto=monto, categoria=categoria,
            detalle=(data.get('detalle') or '').strip()[:200], autor=request.user, saldo_posterior=saldo,
        )
    etiqueta = 'Gasto' if tipo == 'gasto' else 'Ingreso'
    return JsonResponse({'status': 'ok', 'message': f'{etiqueta} de {_dinero(monto)} registrado'})
