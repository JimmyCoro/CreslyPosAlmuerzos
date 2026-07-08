"""
ASGI config for poscresly project.

Configurado para manejar HTTP y WebSockets.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'poscresly.settings')

# Inicializar Django ASGI application antes de importar routing
django_asgi_app = get_asgi_application()

# Importar routing después de inicializar Django
from pedidos import routing as pedidos_routing
from pizzeria import routing as pizzeria_routing

websocket_urlpatterns = pedidos_routing.websocket_urlpatterns + pizzeria_routing.websocket_urlpatterns

# Configurar ASGI application
application = ProtocolTypeRouter({
    # Peticiones HTTP normales
    "http": django_asgi_app,

    # Peticiones WebSocket
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
