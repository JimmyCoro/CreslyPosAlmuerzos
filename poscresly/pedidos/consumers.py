import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Pedido

class PedidosConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Aceptar la conexión WebSocket
        await self.accept()
        
        # Unirse al grupo "pedidos" para recibir actualizaciones
        await self.channel_layer.group_add("pedidos", self.channel_name)
        
        # Enviar mensaje de confirmación
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado al sistema de pedidos'
        }))

    async def disconnect(self, close_code):
        # Salir del grupo "pedidos"
        await self.channel_layer.group_discard("pedidos", self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'get_pedidos':
                # Obtener todos los pedidos y enviarlos
                pedidos = await self.get_pedidos()
                await self.send(text_data=json.dumps({
                    'type': 'pedidos_data',
                    'pedidos': pedidos
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Formato de mensaje inválido'
            }))

    async def pedido_actualizado(self, event):
        # Enviar actualización de pedido a todos los clientes conectados
        await self.send(text_data=json.dumps({
            'type': 'pedido_actualizado',
            'pedido': event['pedido']
        }))

    async def pedido_creado(self, event):
        # Enviar nuevo pedido a todos los clientes conectados
        await self.send(text_data=json.dumps({
            'type': 'pedido_creado',
            'pedido': event['pedido']
        }))

    async def pedido_eliminado(self, event):
        # Enviar notificación de pedido eliminado a todos los clientes conectados
        await self.send(text_data=json.dumps({
            'type': 'pedido_eliminado',
            'pedido': event['pedido']
        }))

    async def pedidos_marcados_completados(self, event):
        # Enviar notificación de pedidos marcados como completados a todos los clientes conectados
        await self.send(text_data=json.dumps({
            'type': 'pedidos_marcados_completados',
            'pedidos_ids': event['pedidos_ids'],
            'cantidad': event['cantidad']
        }))

    @database_sync_to_async
    def get_pedidos(self):
        # Obtener todos los pedidos del día actual
        from django.utils import timezone
        today = timezone.now().date()
        
        pedidos = Pedido.objects.filter(fecha_creacion__date=today).order_by('-fecha_creacion')
        
        pedidos_data = []
        for pedido in pedidos:
            pedidos_data.append({
                'id': pedido.id,
                'numero_dia': pedido.numero_dia,
                'tipo': pedido.tipo,
                'subtipo': pedido.subtipo,
                'forma_pago': pedido.forma_pago,
                'total': float(pedido.total),
                'estado_pedido': pedido.estado_pedido,
                'fecha_creacion': pedido.fecha_creacion.isoformat(),
                'contacto': pedido.contacto,
                'observaciones_generales': pedido.observaciones_generales,
            })
        
        return pedidos_data
