# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

**CreslyPos** — Sistema POS (punto de venta) para Cresly Pizzería / Restaurante. Gestiona pedidos de almuerzo en tiempo real, impresión de tickets a impresora térmica de red, y un dashboard de caja diario.

## Comandos esenciales

Todos los comandos se ejecutan desde `poscresly/`:

```bash
# Desarrollo local
cd poscresly
python manage.py runserver

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Estáticos
python manage.py collectstatic --noinput

# Servidor de producción (ASGI/WebSockets)
daphne -b 0.0.0.0 -p 8000 poscresly.asgi:application
```

## Deploy

El proyecto corre en **Railway** con deploy automático al hacer push a `master`. El flujo habitual es:

```bash
# Trabajar en desarrollo
git checkout desarrollo
# ... commits ...
git push origin desarrollo

# Cuando se quiere publicar en producción
git checkout master && git merge desarrollo && git push origin master && git checkout desarrollo
```

Railway ejecuta automáticamente `collectstatic`, `migrate` y reinicia `daphne`.

## Arquitectura

### Apps Django

| App | Responsabilidad |
|-----|----------------|
| `inicio` | Vista principal de pedidos, autenticación, vista de menú para clientes |
| `pedidos` | Modelos de pedido, toda la lógica de crear/editar/completar pedidos, WebSocket consumers, lógica de impresión |
| `menu` | Modelos del menú del día (sopas, segundos, jugos, extras, postres) |
| `caja` | Dashboard de caja: totales del día, gráfico por hora, dona de métodos de pago |

### Stack

- **Backend**: Django 5 + Django Channels 4 (ASGI) + Daphne
- **Base de datos**: PostgreSQL (local: `bd_cresly_almuerzos`, producción via `DATABASE_URL`)
- **WebSockets**: `channels_redis` en producción, `InMemoryChannelLayer` en desarrollo sin Redis
- **Estáticos**: WhiteNoise con `CompressedManifestStaticFilesStorage`
- **Frontend**: Bootstrap 5 + Vanilla JS (sin framework), PWA con service worker (`static/sw.js`)

### Flujo de un pedido

1. El cajero abre el modal `#tomarPedidoModal` (componente `templates/components/modal_tomar_pedido.html`)
2. Selecciona tipo (Servirse/Llevar/Reservado), agrega productos abriendo modales por tipo (Almuerzo/Sopa/Segundo/Extra)
3. Al confirmar, el JS en `inicio/inicio.html` llama `guardarPedidoFrontend(conImpresion)` → POST a `/guardar-pedido/`
4. `pedidos/views.py::guardar_pedido` crea el `Pedido` y sus sub-modelos (`PedidoAlmuerzo`, `PedidoSopa`, etc.), emite evento WebSocket al grupo `"pedidos"`, e intenta imprimir vía `impresion/impresora.py` (impresora térmica de red en IP `192.168.1.100:9100`)
5. La card del pedido aparece en tiempo real en todas las pestañas abiertas via WebSocket

### Modelos clave

- `Pedido` — cabecera del pedido. `numero_dia` se auto-incrementa por día usando `timezone.localdate()` (importante: **no** usar `timezone.now().date()` porque genera mismatch con la zona horaria `America/Guayaquil`)
- `PedidoAlmuerzo / PedidoSopa / PedidoSegundo / PedidoExtra` — ítems del pedido, cada uno FK a `Pedido`
- `MenuDia` + `MenuDiaSopa / MenuDiaSegundo / MenuDiaJugo` — menú del día con control de cantidades disponibles
- `Plato` — catálogo de platos (sopas, segundos, jugos, postres, extras)

### WebSockets

Dos consumers en `pedidos/consumers.py`:
- `PedidosConsumer` (`ws/pedidos/`) — sincroniza cards de pedidos entre pestañas
- `ImpresionConsumer` (`ws/impresion/`) — canal para tablet de impresión independiente

### CSS y diseño

- `static/CSS/variables.css` — tokens de color: `--primary-color: #A80018` (rojo), `--secondary-color: #00833B` (verde)
- Cada página tiene su propio CSS: `base.css`, `inicio.css`, `caja.css`, `menu.css`, `tomar-pedido.css`
- El sidebar oscuro usa breakpoints en `base.css` (`max-width: 1023px` → panel deslizable) y un `<style>` inline en `base.html` para el modo icon-only en tablets horizontal (768px–1439px landscape)
- El service worker (`static/sw.js`) cachea assets — al cambiar CSS hay que hacer hard refresh en el navegador o incrementar la versión de caché

### Variables de entorno relevantes

| Variable | Uso |
|----------|-----|
| `DATABASE_URL` | Conexión PostgreSQL (Railway la inyecta automáticamente) |
| `REDIS_URL` | Canal layer para WebSockets (Railway Redis plugin) |
| `DJANGO_SECRET_KEY` | Clave secreta de producción |
| `DJANGO_DEBUG` | `0` en producción |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos separados por coma |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes CSRF (ej: `https://tuapp.railway.app`) |
