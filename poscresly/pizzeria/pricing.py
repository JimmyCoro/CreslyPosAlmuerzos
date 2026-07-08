def calcular_recargo_premium(tamano, sabor_1, sabor_2=None):
    """
    Calcula el recargo por sabores premium para una pizza (sola o dentro de un combo).

    - 0 sabores premium -> sin recargo.
    - 1 sabor (pizza completa) premium -> recargo completo del tamaño.
    - Mitad y mitad con 1 premium + 1 regular -> recargo de mitad del tamaño.
    - Mitad y mitad con ambos premium -> recargo completo (cubre toda la pizza).
    """
    premium_1 = sabor_1.es_premium
    premium_2 = sabor_2.es_premium if sabor_2 else False

    if sabor_2 is None:
        return tamano.recargo_premium_completo if premium_1 else 0

    if premium_1 and premium_2:
        return tamano.recargo_premium_completo
    if premium_1 or premium_2:
        return tamano.recargo_premium_mitad
    return 0


def calcular_precio_pizza(tamano, sabor_1, sabor_2=None):
    """Precio de una pizza suelta: precio base del tamaño + recargo premium."""
    return tamano.precio_base + calcular_recargo_premium(tamano, sabor_1, sabor_2)


def calcular_precio_combo(combo_tamano, sabor_1, sabor_2=None):
    """Precio de un combo: precio fijo del tamaño de combo + recargo premium del tamaño de pizza."""
    return combo_tamano.precio + calcular_recargo_premium(combo_tamano.tamano, sabor_1, sabor_2)
