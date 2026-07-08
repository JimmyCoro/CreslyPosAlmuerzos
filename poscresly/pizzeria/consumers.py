import json

from channels.generic.websocket import AsyncWebsocketConsumer


class MesasConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("pizzeria_mesas", self.channel_name)
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Conectado al mapa de mesas de pizzería',
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("pizzeria_mesas", self.channel_name)

    async def mesa_actualizada(self, event):
        await self.send(text_data=json.dumps({
            'type': 'mesa_actualizada',
            'payload': event['payload'],
        }))

    async def pedido_pizzeria_actualizado(self, event):
        await self.send(text_data=json.dumps({
            'type': 'pedido_pizzeria_actualizado',
            'payload': event['payload'],
        }))
