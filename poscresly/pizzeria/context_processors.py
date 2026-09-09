from .models import PedidoPizzeria


def bottom_nav(request):
    """Cuenta de pedidos abiertos para el badge de components/pizzeria_bottom_nav.html.
    Solo consulta la base cuando hace falta: dentro de /pizzeria/ y con
    sesión iniciada, para no golpear la DB en cada página de Almuerzos."""
    if not request.path.startswith('/pizzeria/') or not request.user.is_authenticated:
        return {}
    return {
        'pz_ordenes_abiertas': PedidoPizzeria.objects.filter(estado__in=['abierto', 'por_cobrar']).count(),
    }
