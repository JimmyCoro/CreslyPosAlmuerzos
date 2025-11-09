#!/usr/bin/env python3
"""
Script para probar la funcionalidad WebSocket
"""
import asyncio
import websockets
import json

async def test_websocket():
    """Prueba la conexión WebSocket"""
    try:
        # Conectar al WebSocket
        uri = "ws://localhost:8000/ws/pedidos/"
        print(f"[TEST] Conectando a: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("[TEST] ✅ Conexión WebSocket establecida")
            
            # Esperar mensaje de confirmación
            message = await websocket.recv()
            data = json.loads(message)
            print(f"[TEST] ✅ Mensaje recibido: {data}")
            
            if data.get('type') == 'connection_established':
                print("[TEST] ✅ Conexión confirmada por el servidor")
            else:
                print("[TEST] ⚠️ Mensaje inesperado")
                
            # Enviar mensaje de prueba
            test_message = {
                "type": "get_pedidos"
            }
            await websocket.send(json.dumps(test_message))
            print("[TEST] ✅ Mensaje de prueba enviado")
            
            # Esperar respuesta
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"[TEST] ✅ Respuesta recibida: {response_data}")
            
    except Exception as e:
        print(f"[TEST] ❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 INICIANDO PRUEBA DE WEBSOCKET...")
    asyncio.run(test_websocket())
    print("🧪 PRUEBA COMPLETADA")

