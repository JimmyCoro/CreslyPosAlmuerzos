# Handoff — Nuevo pedido (Almuerzos)

Flujo de toma de pedido del módulo Almuerzos: lista de pedidos del día, hoja de
nuevo pedido (cliente + productos + pago en una sola vista), hoja de selección de
almuerzo, pago mixto y hoja de acciones del pedido.

Diseño: `Nuevo pedido almuerzos.dc.html` (abrir en el navegador; canvas mode, todas
las pantallas lado a lado con la columna de notas).

> Los datos del prototipo son de ejemplo: nombres, precios, porciones y horas.
> Nada de eso viene de la base.

---

## 1. Overview

El almuerzo **se cobra por adelantado**. Eso define todo el flujo:

- Tomar el pedido y cobrarlo es **un solo acto**. No existe un botón "Cobrar" en la
  lista; el pedido nace cobrado.
- La forma de pago es **obligatoria** para poder confirmar.
- Después de creado, el pedido solo se **edita**, se **completa** (se entregó) o se
  **anula** (con devolución de dinero).

## 2. Estructura de pantallas

| Id | Pantalla | Descripción |
|---|---|---|
| 2A | Pedidos del día | Lista. Cards siempre expandidas, sin colapsar. |
| 3A | Nuevo pedido | Hoja única: cliente + productos + pago. Pago sin elegir → bloqueado. |
| 3B | Nuevo pedido · efectivo | Misma hoja con recibe/vuelto en línea y botón activo. |
| 3D | Nuevo pedido · mixto | Reparto efectivo + transferencia con "por asignar". |
| 2D | Agregar almuerzo | Hoja de selección: sopa, segundo, jugo, observación, cantidad. |
| 3E | Acciones del pedido (⋯) | Editar, completar, reimprimir, cambiar pago, anular. |
| 2B/2C | *Descartadas* | Versión en dos pasos. Se conservan como referencia de por qué se unificó. |

Todo mobile first a **390 px**, funcionando de 360 a 430 sin scroll horizontal.

---

## 3. Medidas exactas

**Shell (igual que el resto del POS)**

- Header fijo 52 px · subheader 56 px (+ fila de chips 34 px = 112 px de bloque)
- Tab bar 78 px · FAB ＋ de 56 px, elevado 20 px, borde blanco de 3 px
- Lista: `height: calc(100% - 33px - 52px - 112px - 78px)`, `overflow-y:auto`,
  padding `12px 14px 0`, `gap:10px`. Cada card `flex:0 0 auto` (nunca se encogen).

**Card de pedido (2A)**

- Contenedor: `background:#fff`, borde `#e6e8ec`, radio 16, `overflow:hidden`
- Fila 1 (padding `12px 14px 0`): `#003` 13/800 · chip de modo 21 px alto,
  radio 7, 10/800, `letter-spacing:.07em` · hora 11/600 `#98a1ab`
- Fila 2: nombre 14/800 · modo secundario 11.5/700 con color de tono
- Ítems: columna 17 px para la cantidad · nombre 12.5/800 · detalle 11.5/600 `#8a929c`
  · precio 12.5/700 a la derecha
- Pie: borde superior `#eef0f3`, padding `11px 14px 12px`, dos filas con `gap:9px`
  - Fila A: `TOTAL` 10.5/800 `.08em` `#98a1ab` · monto 15/800 · a la derecha
    `✓ Cobrado · <forma>` 11/700 `#1c7a4a`, `white-space:nowrap`
  - Fila B: `Editar` (flex 1, 40 px, borde `#dfe2e7`) · `Completar` (flex 1.35, 40 px,
    verde `#1c7a4a`, sombra `0 6px 14px rgba(28,122,74,.22)`) · `⋯` 40 × 40

**Hoja de nuevo pedido (3A / 3B / 3D)**

- Hoja: `top:74px; bottom:0`, radio `22px 22px 0 0`, sombra `0 -14px 34px rgba(20,24,29,.18)`
- Cabecera fija: asa 38 × 4 · título 19/800 · sub-línea 11/600 con resaltado ·
  total 26/800 `letter-spacing:-.03em` a la derecha · borde inferior `#eef0f3`
- Cuerpo: `flex:1; overflow-y:auto`, padding `12px 16px 0`, `gap:13px`
- Barra fija inferior: padding `11px 16px 18px`, borde superior `#eef0f3`,
  botón ⎙ 52 × 52 + botón principal 52 px, y debajo la línea de estado 10.5/700
- Bloques: etiqueta 11/800 `.09em` `#5b6673` + resaltado a la derecha 11/700
- Modo (3 columnas, 42 px) · mesa + nombre (`1fr 1.35fr`, 44 px) · observación 40 px
- Productos: card `#fafbfc` borde `#eef0f3` radio 13, padding `10px 12px`;
  stepper − / n / ＋ de 30 px; precio columna fija de 42 px a la derecha
- Fila de agregar: 4 columnas de 44 px (Almuerzo, Sopa, Segundo, Extra)
- Pago: 3 columnas de 48 px (Efectivo, Transferencia, Mixto)
- Efectivo: recibe / vuelto 46 px + atajos de billete 38 px
- Mixto: lista de 48 px por medio + fila "POR ASIGNAR" 42 px sobre `#fdecef` +
  dos atajos de 38 px ("Resto en efectivo" / "Resto transferido")

**Hoja agregar almuerzo (2D)**

- Filas de plato 48 px, radio 12; seleccionada `#eaf6ef` + borde 1.5 `#1c7a4a` y
  círculo ✓ de 19 px; no seleccionada borde `#dfe2e7`
- Jugo: 3 botones de 46 px en una línea
- Observación 46 px · pie: stepper de 38 px + botón 52 px con el precio dentro

**Hoja de acciones (3E)**

- Filas de 46 px con glifo neutro de 19 px, etiqueta 13.5/700 y sub-línea 11/600
  con el valor actual, separadas por `1px #f2f4f6`
- ZONA DE RIESGO: etiqueta 11/800 `#a90d27` + card `#fdecef` borde `#f4d3d9`,
  motivo obligatorio 44 px y botón `#c8102e` de 46 px

Táctil: nada bajo 38 px; acciones primarias 50–52 px.

---

## 4. Interacciones

**Lista (2A)**

1. Chips de filtro: Todos / Servirse / Llevar / Reserva, con contador.
2. Card: **Editar** abre 3A con los datos actuales cargados. **Completar** marca
   entregado y lo saca de la lista (pasa a Listos). **⋯** abre 3E.
3. Las cards **no colapsan**. Su alto lo define el pedido.

**Nuevo pedido (3A)**

1. El ＋ de la tab bar abre la hoja.
2. Cliente, productos y pago conviven; cualquier dato se edita en el sitio sin
   cambiar de paso (el cliente cambia de idea a menudo).
3. `＋ Almuerzo` abre 2D; `＋ Sopa`, `＋ Segundo`, `＋ Extra` abren la misma hoja
   recortada a esa sección.
4. Forma de pago obligatoria:
   - Efectivo → aparecen recibe / vuelto y los atajos de billete.
   - Transferencia → no pide monto.
   - Mixto → dos montos; escribir uno completa el otro. Mientras la suma no cubra
     el total, la fila "por asignar" queda en rojo y el botón bloqueado.
5. **Cobrar e imprimir $X** confirma, cobra e imprime comanda + recibo. El ⎙ aparte
   es para confirmar sin ticket.
6. Bloqueos: el botón nunca queda gris y mudo — debajo va la línea 10.5/700
   `#c8102e` diciendo qué falta, y el mismo dato se resalta en la sub-línea.

**Agregar almuerzo (2D)**

1. Toda la fila es área tocable; un plato sin stock se deshabilita entero con
   etiqueta AGOTADA y no se puede elegir.
2. Porciones con semáforo: verde disponible, ámbar quedan pocas.
3. Cantidad antes de agregar: evita repetir la hoja para dos almuerzos iguales.

**Acciones (3E)**

Editar · Completar · Reimprimir · Cambiar forma de pago · **Anular** al final, bajo
ZONA DE RIESGO, con motivo obligatorio. Como ya está cobrado, el aviso dice el monto
a devolver y queda registrado en caja con el usuario.

---

## 5. Datos que necesita la vista

```python
pedido = {
  "numero": "003",
  "modo": "servirse|llevar|reserva",
  "mesa": 3 | None,
  "hora_reserva": time | None,
  "cliente": "Marisol Vera" | None,
  "observacion": "Sin cebolla en las dos sopas" | None,
  "creado": datetime,
  "estado": "en_curso|completado|anulado",
  "items": [
    {"id":..,"tipo":"almuerzo|sopa|segundo|extra","nombre":"Almuerzo",
     "detalle":"Locro de espinaca · Pechuga rellena · Melón",
     "observacion": str|None, "cantidad":1, "precio_unitario":"3.50",
     "subtotal":"3.50"}
  ],
  "total": "5.50",
  "pago": {"forma":"efectivo|transferencia|mixto",
           "monto_efectivo":"5.00","monto_transferencia":"1.75",
           "recibido":"10.00","vuelto":"4.50",
           "por_asignar":"0.00"},
}
```

**Sub-línea del subheader** (marcada desde el backend, no partiendo la cadena en el
template): `sub_pre` / `sub_hi` / `sub_hi_tono` / `sub_post`.
En 2A: `Sábado 12 · ` + **`3 por entregar`** (`ambar`) + ` · $11.50`.

**Puerta única de validación.** Una sola función alimenta el botón, el aviso de abajo
y el resaltado del subheader:

```python
def puede_cobrar(pedido):
    faltan = []
    if pedido.modo == "servirse" and not pedido.mesa: faltan.append("mesa")
    if not pedido.items: faltan.append("productos")
    if not pedido.pago.forma: faltan.append("pago")
    if pedido.pago.forma == "mixto" and pedido.pago.por_asignar > 0:
        faltan.append("reparto")
    return (not faltan), faltan
```

Mensajes: `mesa` → "Elige la mesa" · `productos` → "Agrega al menos un plato" ·
`pago` → "Elige efectivo, transferencia o mixto" · `reparto` → "Asigna los $X que
faltan entre efectivo y transferencia".

**Menú del día.** Las opciones de 2D salen del menú publicado del día; cada plato
trae `porciones_restantes` y `agotado`. Pendiente de definir: si el cupo se descuenta
por plato o por almuerzo completo.

---

## 6. Tokens

Almuerzos usa el **verde** como color de marca; el rojo queda reservado para lo que
falta y para la zona de riesgo.

| Uso | Hex |
|---|---|
| marca / acción | `#1c7a4a` · tinte `#eaf6ef` · borde `#cfeadb` · claro `#f4fbf7` |
| ink | `#14181d` |
| texto secundario | `#4a545f` · `#5b6673` |
| metadatos | `#8a929c` · `#98a1ab` |
| atenuado | `#a8afb8` · `#c3c8ce` |
| superficies | `#ffffff` · `#fafbfc` · fondo `#f4f5f7` |
| bordes | `#e6e8ec` · `#eef0f3` · `#dfe2e7` · `#f2f4f6` |
| deshabilitado | `#e9ebef` |
| falta / riesgo | `#c8102e` · oscuro `#a90d27` · bg `#fdecef` · borde `#f4d3d9` |
| ámbar / pendiente | `#d99000` · texto `#8a5800` · bg `#fdf3e2` · borde `#f2e0bd` |
| azul / llevar | `#2f7fd9` · texto `#1d5a9e` · bg `#e9f1fb` |

Tipografía Plus Jakarta Sans 400–800, `font-feature-settings:'tnum' 1` en la raíz.
Radios 9–22 y 999. Sombras: primario `0 8px 18px rgba(28,122,74,.26)`; card
`0 6px 14px rgba(28,122,74,.22)`; tab bar `0 -8px 22px rgba(20,24,29,.07)`;
hoja `0 -14px 34px rgba(20,24,29,.18)`; overlay `rgba(20,24,29,.42)`.

---

## 7. Notas de implementación (Django + Bootstrap 5)

- **Hojas inferiores:** `offcanvas-bottom`. La de nuevo pedido con altura `calc(100% - 74px)`
  y `.offcanvas-body` en `overflow-y:auto`; cabecera y barra de acción fuera del body,
  fijas. Sin botón ✕: se cierra deslizando o tocando el backdrop (`data-bs-backdrop`).
- **No usar `collapse` en las cards de la lista.** Se descartó a propósito.
- **Una vista, dos entradas.** `nuevo_pedido` y `editar_pedido` renderizan el mismo
  partial `_hoja_pedido.html`; editar solo precarga la instancia. El título cambia
  ("Nuevo pedido" / "Pedido #003") y el botón también ("Cobrar e imprimir" /
  "Guardar cambios" cuando ya está cobrado).
- **Recalcular en el servidor.** Total, vuelto y `por_asignar` se recalculan en cada
  cambio de ítem o de monto (htmx / fetch que devuelve el partial de cabecera + barra).
  El JS del cliente solo pinta lo que devuelve el servidor.
- **Cobro atómico.** Confirmar crea pedido + movimiento de caja en una transacción.
  Botón con idempotency key: dos toques no cobran dos veces.
- **Impresión.** Comanda de cocina y recibo del cliente son dos plantillas distintas;
  el ⎙ suelto confirma sin imprimir el recibo.
- **Anular.** Requiere motivo, genera movimiento de devolución en caja y guarda usuario
  y hora. No borra el pedido: lo marca `anulado` y deja de sumar en la venta del turno.
  *Pendiente de confirmar: si exige permiso de administrador.*
- **Formato de montos** con `floatformat:2` y `tnum` para que la columna de precios
  quede alineada.
- Clases utilitarias de Bootstrap donde alcancen; las medidas de arriba son las que
  mandan cuando no hay utilidad equivalente.
