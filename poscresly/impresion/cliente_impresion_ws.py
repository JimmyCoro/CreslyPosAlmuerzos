#!/usr/bin/env python3
"""
Cliente WebSocket para imprimir pedidos desde Railway.

Uso (en tablet):
  export PRINT_WS_URL="wss://TU_APP.railway.app/ws/impresion/?token=TU_TOKEN"
  export IMPRESORAS_IPS="192.168.1.100,192.168.1.110"
  python cliente_impresion_ws.py
"""
import asyncio
import json
import os

import websockets

from impresora import ImpresoraMultiple


def obtener_impresoras(payload):
    ips_payload = payload.get("impresoras") or []
    if ips_payload:
        return ips_payload

    ips_env = os.getenv("IMPRESORAS_IPS", "192.168.1.100,192.168.1.110")
    return [ip.strip() for ip in ips_env.split(",") if ip.strip()]


def imprimir_contenido(payload):
    contenido = payload.get("contenido") or []
    if not contenido:
        print("[IMPRESION] Contenido vacío, no se imprime")
        return

    ips = obtener_impresoras(payload)
    impresoras = ImpresoraMultiple(ips)

    if impresoras.conectar_todas():
        impresoras.imprimir_en_todas(contenido)
        impresoras.desconectar_todas()
    else:
        print("[IMPRESION] No se pudo conectar a impresoras")


async def escuchar():
    ws_url = os.getenv("PRINT_WS_URL", "").strip()
    if not ws_url:
        raise RuntimeError("Falta PRINT_WS_URL en variables de entorno")

    while True:
        try:
            print(f"[WS] Conectando a {ws_url}")
            async with websockets.connect(ws_url) as websocket:
                print("[WS] Conectado. Esperando trabajos de impresión...")
                async for message in websocket:
                    data = json.loads(message)
                    if data.get("type") == "print_job":
                        imprimir_contenido(data)
        except Exception as e:
            print(f"[WS] Error de conexión: {e}. Reintentando en 5s...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(escuchar())
