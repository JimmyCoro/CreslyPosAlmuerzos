from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/pedidos/', consumers.PedidosConsumer.as_asgi()),
    path('ws/impresion/', consumers.ImpresionConsumer.as_asgi()),
]
