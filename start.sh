#!/bin/sh
# Arranque de producción en Railway.
#
# Gunicorn levanta varios procesos Uvicorn (ASGI: HTTP + WebSockets) para que
# las peticiones se atiendan en paralelo; con un solo daphne todas las vistas
# síncronas de Django hacían fila en un único hilo.
#
# Los procesos solo comparten los mensajes de WebSocket a través de Redis. Sin
# REDIS_URL cada proceso tendría su propia capa en memoria y las pantallas
# dejarían de sincronizarse, así que en ese caso se usa un único proceso.
# WEB_CONCURRENCY permite fijar el número desde las variables de Railway.
set -e

cd poscresly

python manage.py migrate --noinput
python manage.py crear_superusuario

if [ -n "$WEB_CONCURRENCY" ]; then
    WORKERS="$WEB_CONCURRENCY"
elif [ -n "$REDIS_URL" ]; then
    WORKERS=3
else
    WORKERS=1
    echo "[start] REDIS_URL no configurado: se usa 1 solo proceso para no romper los WebSockets"
fi

echo "[start] Iniciando gunicorn con $WORKERS procesos"

exec gunicorn poscresly.asgi:application \
    -k uvicorn_worker.UvicornWorker \
    -w "$WORKERS" \
    -b "0.0.0.0:${PORT:-8000}" \
    --timeout 60 \
    --graceful-timeout 30 \
    --access-logfile -
