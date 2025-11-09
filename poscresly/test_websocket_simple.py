#!/usr/bin/env python3
"""
Script simple para probar WebSockets
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Prueba la conexión WebSocket"""
    try:
        # Conectar al WebSocket
        uri = "ws://localhost:8000/ws/pedidos/"
        print(f"Conectando a: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("Conexion WebSocket establecida")
            
            # Esperar mensaje de confirmación
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Mensaje recibido: {data}")
            
            if data.get('type') == 'connection_established':
                print("Conexion confirmada por el servidor")
            else:
                print("Mensaje inesperado")
                
            print("WebSocket funcionando correctamente!")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("INICIANDO PRUEBA DE WEBSOCKET...")
    asyncio.run(test_websocket())
    print("PRUEBA COMPLETADA")