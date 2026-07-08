def generar_comanda_pizza(pedido, lineas_items):
    """
    Construye el contenido de la comanda de cocina para un pedido de pizzería.

    Reutiliza el mismo contrato que `impresion.impresora.ImpresoraTermica.imprimir_ticket`
    (una lista de líneas de texto) y el mismo transporte (grupo websocket "impresion").
    `lineas_items` son las líneas ya formateadas de los productos nuevos agregados en
    esta operación de guardado (no se reimprime el historial completo del pedido).
    """
    encabezado = f"MESA {pedido.mesa.numero}" if pedido.mesa else f"LLEVAR - {pedido.contacto or ''}"
    hora = pedido.fecha_creacion.strftime('%H:%M')

    lineas = [
        "=" * 32,
        "CRESLY PIZZERIA - COMANDA",
        "=" * 32,
        encabezado,
        f"Pedido #{pedido.numero_pedido_completo}  {hora}",
        "-" * 32,
    ]
    lineas.extend(lineas_items)
    lineas.append("=" * 32)
    return lineas
