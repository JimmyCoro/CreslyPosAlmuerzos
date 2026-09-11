from django.utils import timezone

ANCHO_TICKET = 32


def _hora_pedido(pedido):
    return timezone.localtime(pedido.fecha_creacion).strftime('%H:%M')


def _encabezado_pedido(pedido):
    if pedido.mesa:
        return f"MESA {pedido.mesa.numero}"
    if pedido.tipo == 'delivery':
        return f"DELIVERY - {pedido.contacto or ''}"
    return f"LLEVAR - {pedido.contacto or ''}"


def _fila_monto(texto, monto):
    """Texto a la izquierda y monto alineado a la derecha; si no caben en una
    línea, el monto baja a la siguiente."""
    valor = f"${monto:.2f}"
    if len(texto) + 1 + len(valor) <= ANCHO_TICKET:
        return [texto + valor.rjust(ANCHO_TICKET - len(texto))]
    return [texto, valor.rjust(ANCHO_TICKET)]


def generar_precuenta_pizza(pedido, items, subtotal, iva, iva_pct, total_con_iva):
    """Ticket para que el cliente revise antes de pagar. `items` son tuplas
    (cantidad, descripcion, importe). En delivery agrega los datos de entrega
    y el valor de la moto, que se cobra aparte del total con IVA."""
    lineas = [
        "=" * ANCHO_TICKET,
        "CRESLY PIZZERIA - PRECUENTA",
        "=" * ANCHO_TICKET,
        _encabezado_pedido(pedido),
        f"Pedido #{pedido.numero_pedido_completo}  {_hora_pedido(pedido)}",
    ]
    if pedido.tipo == 'delivery':
        if pedido.observaciones:
            lineas.append(f"Dir: {pedido.observaciones}")
        if pedido.pago_delivery:
            lineas.append(f"Pago: {pedido.get_pago_delivery_display()}")
    lineas.append("-" * ANCHO_TICKET)

    for cantidad, descripcion, importe in items:
        lineas.extend(_fila_monto(f"{cantidad}x {descripcion}", importe))

    lineas.append("-" * ANCHO_TICKET)
    lineas.extend(_fila_monto("Subtotal", subtotal))
    lineas.extend(_fila_monto(f"IVA {iva_pct}%", iva))
    lineas.extend(_fila_monto("TOTAL", total_con_iva))

    if pedido.tipo == 'delivery':
        moto = pedido.valor_moto or 0
        lineas.extend(_fila_monto("Moto", moto))
        lineas.append("-" * ANCHO_TICKET)
        lineas.extend(_fila_monto("TOTAL A PAGAR", total_con_iva + moto))

    lineas.append("=" * ANCHO_TICKET)
    lineas.append("Precuenta - no es factura")
    return lineas


def generar_comanda_pizza(pedido, lineas_items):
    """
    Construye el contenido de la comanda de cocina para un pedido de pizzería.

    Reutiliza el mismo contrato que `impresion.impresora.ImpresoraTermica.imprimir_ticket`
    (una lista de líneas de texto) y el mismo transporte (grupo websocket "impresion").
    `lineas_items` son las líneas ya formateadas de los productos nuevos agregados en
    esta operación de guardado (no se reimprime el historial completo del pedido).
    """
    hora = _hora_pedido(pedido)

    lineas = [
        "=" * 32,
        "CRESLY PIZZERIA - COMANDA",
        "=" * 32,
        _encabezado_pedido(pedido),
        f"Pedido #{pedido.numero_pedido_completo}  {hora}",
        "-" * 32,
    ]
    lineas.extend(lineas_items)
    if pedido.tipo == 'delivery' and pedido.valor_moto:
        lineas.append("-" * 32)
        lineas.append(f"Valor moto: ${pedido.valor_moto:.2f}")
    lineas.append("=" * 32)
    return lineas
