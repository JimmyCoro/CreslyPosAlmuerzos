# Handoff: Detalle de orden · móvil · Cresly POS

## Overview
La pantalla donde se **gestiona una orden ya abierta**: se consulta su información, se mueve
el estado de cada platillo (pendiente → cocinando → listo → servido), se agregan platillos y
se cobra. Es la pantalla que el mesero abre desde Órdenes o desde el mapa de Mesas.

Es el rediseño de la pantalla que ya existe en la app. Conserva su estructura (cabecera del
pedido, bloque de datos, lista de platillos de cocina, "Agregar" y "Cobrar", y un modal al
tocar un platillo) y cambia tres cosas de fondo:

1. El estado del platillo deja de ser una etiqueta y pasa a ser el **control**: un toque lo
   avanza.
2. La tarjeta negra de datos se reemplaza por una tarjeta con la información de entrega, que
   hoy no se ve.
3. El modal deja de esconder los estados tras un desplegable: los cuatro quedan a la vista.

Diseñado a 390 px de ancho (iPhone 14 base). Debe funcionar de 360 a 430 px sin scroll
horizontal.

## About the Design File
`Detalle orden movil.dc.html` es una **referencia de diseño en HTML**: un prototipo del look
previsto, no código de producción. Los estilos están inline.

Contiene, de izquierda a derecha:
- La **pantalla de detalle** completa, con un pedido en preparación.
- La **hoja del platillo** (el reemplazo del modal actual).
- Las notas de qué cambió y por qué.
- Abajo, **los cuatro estados** de la fila de platillo en detalle.

La tarea es recrearlo en **Django (templates) + Bootstrap 5**, siguiendo los patrones del
proyecto (base template, blocks, partials, staticfiles). No portes los estilos inline:
traduce a utilidades de Bootstrap más un CSS propio para lo que Bootstrap no cubre.

## Fidelity
**Alta fidelidad.** Colores, tipografía, espaciados, radios y alturas son finales.
Reprodúcelos con precisión.

---

## 1 · Estructura

```
┌─────────────────────────────┐
│ Header fijo          52 px  │  ← igual en todo el sistema
├─────────────────────────────┤
│ Subheader            56 px  │  ← ‹ + nº de pedido + pill de estado
├─────────────────────────────┤
│ Tarjeta de entrega          │
│ Progreso de cocina          │  ← zona de scroll
│ Filas de platillo           │
├─────────────────────────────┤
│ Barra de acciones    fija   │  ← ＋ y Cobrar
└─────────────────────────────┘
```

### Header fijo (52 px)
Sin cambios respecto al resto del sistema: ☰ (44 px) · logo 30 px + "Cresly Pizzería"
13.5 px/800 y "Suc. Centro" 10.5 px/600 `#8a929c` · botón de tema ☾/☀ (44 px) ·
avatar 34 px con caret ▼. Fondo `#fff`, borde inferior `1px solid #e6e8ec`,
padding lateral `12px`, `gap:8px`.

### Subheader (56 px)
Fondo `#fafbfc`, borde inferior `1px solid #eef0f3`, `min-height:56px`,
padding `9px 14px`, `gap:10px`. Es una pantalla interna: **sin segunda línea**.
- Botón **‹ atrás** 38 × 38 px, radio `11px`, fondo `#fff`, borde `1px solid #e6e8ec`,
  glifo 15 px `#5b6673`.
- **Título** "Pedido #002" 17 px/800 `letter-spacing:-.02em`, con el **pill de estado de la
  orden** al lado: padding `2px 8px`, radio `999px`, 10.5 px/800, con punto de 5 px.
- **Sub-línea** 11 px/600 `#8a929c`: "Delivery · mesero1 · **hace 22 min**", con el tiempo
  resaltado en `font-weight:800` y color según urgencia (ver "El resaltado en color").
- Botón **⋯** 38 × 38 px, fondo `#fff`, borde `#e6e8ec`. Contiene imprimir comanda,
  cambiar de mesa, dividir cuenta y anular la orden.

**El tiempo relativo va en formato corto**: "hace 22 min", "hace 1 h 06" —
no "hace 6 hours, 6 minutes".

### Tarjeta de entrega
Fondo `#fff`, borde `1px solid #e6e8ec`, radio `16px`, padding `14px 15px`,
columna con `gap:12px`.

**Fila superior** (`display:flex; align-items:center; gap:10px`):
- Bloque `flex:1; min-width:0`: etiqueta "ENTREGA" 10.5 px/800 `letter-spacing:.09em`
  `#8a929c`; nombre y zona 13.5 px/700 `letter-spacing:-.01em` con ellipsis
  ("Ana R. · Col. Miramonte"); teléfono y envío 11.5 px/600 `#98a1ab`.
- **Botón de llamar** 40 × 40 px, radio `12px`, fondo `#eaf6ef`, glifo ✆ 16 px `#1c7a4a`.
  `href="tel:..."`.

**Pie** separado por `border-top:1px solid #f2f4f6`, `padding-top:11px`,
`justify-content:space-between`: "TOTAL" 12 px/800 `letter-spacing:.07em` `#8a929c` y el
monto **26 px/800 `letter-spacing:-.03em` `line-height:1`**.

**Esta tarjeta cambia según el tipo de orden:**
| Tipo | Contenido de la fila superior | Botón |
|---|---|---|
| Delivery | Nombre · zona / teléfono · costo de envío | Llamar |
| Llevar | Nombre del cliente / hora de retiro si la hay | Llamar (si hay teléfono) |
| Servirse | Mesa y zona / nº de comensales | — |

La tarjeta negra del diseño actual se elimina: repetía el tipo de orden, el mesero y el
tiempo que ya están en el subheader, y no mostraba la dirección — el dato que un delivery sí
necesita a la vista.

### Progreso de cocina
Fila con `align-items:center; gap:10px`:
- "COCINA" 10.5 px/800 `letter-spacing:.1em` `#8a929c`.
- "1 de 3 listos" 11 px/700 `#98a1ab`.
- Barra `flex:1; height:4px`, radio `999px`, pista `#eef0f3`, avance `#23a05f` al
  porcentaje de platillos en estado listo o servido.

Reemplaza el pill de "1 platillo": dice si el pedido puede salir, que es lo que se consulta
al abrir la pantalla.

### Filas de platillo
`display:flex; align-items:center; gap:11px`, padding `11px 12px`, radio `14px`.
- **Badge de cantidad** 26 × 26 px, radio `8px`, fondo `#fdecef`, texto `#a90d27`
  12.5 px/800.
- Bloque `flex:1; min-width:0`: nombre 13.5 px/700 `line-height:1.35` `text-wrap:pretty`,
  y los **modificadores** debajo en 11.5 px/700 **`#8a5800`** con ellipsis
  ("7 BBQ · 7 Broster", "Sin cebolla · extra queso"). El ámbar los distingue del nombre sin
  competir con el estado.
- **Botón de estado** a la derecha: padding `8px 11px`, radio `11px`, punto de 7 px +
  etiqueta 12 px/800. `flex:0 0 auto`.

**Separa el nombre del platillo de sus modificadores.** Hoy la fila dice
"14 alitas: 7 BBQ, 7 Broster" en una sola línea; debe ser "14 alitas" arriba y
"7 BBQ · 7 Broster" en ámbar debajo.

#### Los cuatro estados

| Estado | Punto | Texto | Fondo del pill | Fondo de la fila | Borde de la fila |
|---|---|---|---|---|---|
| Pendiente | `#8a929c` | `#4a545f` | `#f4f5f7` | `#fff` | `#e6e8ec` |
| Cocinando | `#d99000` | `#8a5800` | `#fdf3e2` | `#fffdf7` | `#f2e0bd` |
| Listo | `#23a05f` | `#1c7a4a` | `#eaf6ef` | `#fff` | `#e6e8ec` |
| Servido | `#2f7fd9` | `#1d5a9e` | `#e9f1fb` | `#fff` | `#e6e8ec` |

**Solo "Cocinando" tiñe la fila entera** — es donde debe caer la vista. Si un platillo pasa
del tiempo previsto de cocina, su pill se vuelve rojo (`#fdecef` / `#a90d27` / punto
`#c8102e`) manteniendo el tinte ámbar de la fila.

### Barra de acciones (fija abajo)
`position:fixed`, fondo `#fff`, borde superior `1px solid #e6e8ec`,
padding `12px 14px 20px` (usa `max(20px, env(safe-area-inset-bottom))`),
`box-shadow:0 -8px 22px rgba(20,24,29,.07)`, `display:flex; gap:9px`.
- **＋ Agregar**: 52 × 52 px, radio `14px`, borde `1px solid #dfe2e7`, glifo 20 px
  `#5b6673`, `line-height:1`, `flex:0 0 auto`. Solo icono: la etiqueta le robaba ancho al
  botón que importa.
- **Cobrar $12.00**: `flex:1`, alto 52 px, radio `14px`, fondo `#c8102e`,
  texto `#fff` 15 px/800 con glifo ▤ antes,
  `box-shadow:0 8px 18px rgba(200,16,46,.26)`.
  Deshabilitado (orden ya pagada o sin platillos): fondo `#e9ebef`, texto `#a8afb8`,
  sin sombra.

**Reemplaza la tab bar y el ＋ flotante** mientras se gestiona una orden: no se navega entre
módulos en medio de la gestión, y el ＋ central del diseño actual tapa esta barra. Se sale
con el ‹ del subheader.

### Se quita la pista en rojo
"Toca un platillo para gestionarlo" en rojo cursiva parecía un mensaje de error. Con el
estado convertido en botón visible, la pista sobra.

---

## 2 · La hoja del platillo

Reemplaza el modal actual. Hoja inferior: fondo `#fff`, radio `22px 22px 0 0`,
padding `14px 16px 20px`, columna con `gap:15px`, overlay `rgba(20,24,29,.42)`.
Arriba, asa de 38 × 4 px radio `999px` `#dfe2e7` centrada.

### Cabecera
`display:flex; align-items:flex-start; gap:11px`:
- Badge de cantidad 30 × 30 px, radio `9px`, fondo `#fdecef`, texto `#a90d27` 13.5 px/800.
- Nombre 17 px/800 `letter-spacing:-.02em` `line-height:1.25`, y los modificadores
  12 px/700 `#8a5800` debajo.
- Importe de la línea 16 px/800 `letter-spacing:-.02em` a la derecha.

No lleva ✕: se cierra deslizando o tocando el overlay, como el resto de las hojas del
sistema.

### Bloque ESTADO
Etiqueta "ESTADO" 10.5 px/800 `letter-spacing:.09em` `#8a929c`, y debajo:

**Fila de cuatro estados** (`display:flex; gap:6px`), cada uno `flex:1`, columna centrada
con `gap:5px`, padding `11px 4px`, radio `12px`:
- Punto de 9 px del color del estado y etiqueta 11 px.
- Inactivo: fondo `#fff`, borde `1px solid #dfe2e7`, texto `#5b6673` peso 700.
- **Activo**: fondo del color pleno del estado, borde del mismo color, punto `#fff`,
  texto `#fff` peso 800, y `box-shadow` del color al 24 %
  (ej. cocinando: `#d99000` + `0 6px 14px rgba(217,144,0,.24)`).

**Botón del siguiente estado**: ancho completo, padding `14px`, radio `12px`,
fondo `#14181d`, texto `#fff` 14 px/800, con glifo ✓ antes. Su etiqueta es siempre el
siguiente paso: "Empezar a cocinar", "Marcar como listo", "Marcar como servido".
En el último estado el botón no se muestra.

**Línea de tiempo** debajo, centrada, 11 px/600 `#98a1ab`:
"Cocinando desde las 12:23 · 22 min".

Los cuatro estados van a la vista y no dentro de un desplegable: mover el estado es la razón
de abrir esta hoja y debe costar un toque, no dos.

### Bloque CANTIDAD
Etiqueta "CANTIDAD" y una fila con el stepper: botones **−** y **＋** de 44 × 44 px,
radio `12px`, borde `1px solid #dfe2e7`, glifo 19 px/700 `#5b6673`, `line-height:1`;
cantidad 18 px/800 con `min-width:38px` centrada. A la derecha, "$12.00 c/u"
12 px/600 `#98a1ab`.

Cambiar la cantidad aquí evita entrar a "Editar" para el ajuste más común.

### Bloque ACCIONES
Filas de `display:flex; align-items:center; gap:11px`, padding `13px 14px`, radio `12px`,
fondo `#fff`, borde `1px solid #dfe2e7`:
- glifo 14 px `#5b6673` en una caja de 18 px centrada, etiqueta 13.5 px/700 `flex:1`,
  y un chevron › 14 px `#c3c8ce`.

| Acción | Glifo | Qué hace |
|---|---|---|
| Editar personalización | ✎ | Abre el editor de tamaño, extras y notas |
| Pedir otro igual | ⧉ | Añade una línea nueva con la misma personalización |
| Reimprimir en cocina | ⎙ | Envía un ticket solo con este platillo |
| **Quitar de la orden** | ✕ | Elimina la línea — borde `#f4d3d9`, glifo y texto `#c8102e`, chevron `#f4d3d9` |

**Sin círculos de color en los iconos.** Los círculos ámbar del modal actual competían con el
estado por la atención; solo la acción destructiva se marca en rojo.

---

## 3 · El resaltado en color

La sub-línea del subheader usa el mismo sistema del resto de la app: el dato relevante va en
`font-weight:800` con color propio, sobre el resto en `#8a929c`.

| Color | Cuándo |
|---|---|
| `#8a5800` ámbar | tiempo transcurrido normal ("hace 22 min") |
| `#c8102e` rojo | pasado el tiempo previsto, o falta un dato obligatorio |
| `#4a545f` gris oscuro | contexto sin urgencia |

Marca el fragmento resaltado desde el backend (`sub_pre` / `sub_hi` / `sub_hi_tono` /
`sub_post`), no partas la cadena en el template.

---

## Interactions & Behavior

- **Tap en el botón de estado de una fila** → avanza al siguiente estado, sin abrir nada.
  Es la interacción principal de la pantalla.
- **Tap en el resto de la fila** (o mantener pulsado sobre el estado) → abre la hoja del
  platillo.
- **Tap en un estado de la fila de cuatro** (dentro de la hoja) → salta a ese estado
  directamente, incluso hacia atrás (corregir un error de marcado).
- **Retroceder de estado** debe registrarse en el historial de la orden, no borrar el
  anterior.
- **Al marcar el último platillo como listo**, la orden pasa a "Lista" y la barra de progreso
  se completa. No se cobra automáticamente.
- **＋ Agregar** lleva al punto de venta con la orden ya cargada; al volver, los platillos
  nuevos entran en estado Pendiente.
- **Cobrar** abre la pantalla de cobro con el total de la orden.
- **Refresco**: la pantalla debe actualizarse en vivo (polling cada 10–15 s o websocket) —
  cocina puede mover estados desde su propia pantalla. Al refrescar solo cambian estados y
  contadores; nada se reordena.
- Transiciones `.12s ease`. La hoja entra deslizando desde abajo.
- **Táctil**: botón de estado, ＋/− y Cobrar de 44–52 px; ‹, ⋯ y filas de acción de 38–46 px.
  Nada por debajo de 38 px.

## State Management

```
orden: {
  numero,
  tipo: 'servirse' | 'llevar' | 'delivery',
  estado: 'abierta' | 'en_cocina' | 'lista' | 'servida' | 'por_cobrar' | 'pagada' | 'anulada',
  mesero,
  abierta_en,                       # para el tiempo relativo
  mesa: null | { numero, zona, comensales },
  cliente: null | { nombre, telefono },
  entrega: null | { direccion, zona, costo_envio },
  lineas: [ {
      id, nombre, modificadores: [str], cantidad, precio_unit, importe,
      estado: 'pendiente' | 'cocinando' | 'listo' | 'servido',
      estado_desde                  # timestamp del estado actual
  } ],
  total
}
```

Derivados que calcula la **vista o el modelo**, no el template:
- `listos` / `total_lineas` y el porcentaje de la barra.
- `siguiente_estado(linea)` → el estado al que avanza y la etiqueta del botón.
- `linea_demorada(linea)` → `estado == 'cocinando'` y `now - estado_desde > umbral`;
  de ahí sale el pill rojo.
- `tiempo_relativo(abierta_en)` en formato corto.

Los cambios de estado son endpoints POST que devuelven el parcial de la fila (HTMX encaja
bien) y registran el evento en el historial de la orden.

---

## Design Tokens

**Colores**
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | texto principal, botón de siguiente estado |
| text-2 | `#4a545f` | estado pendiente, resaltado neutro |
| text-3 | `#5b6673` | glifos secundarios, estados inactivos en la hoja |
| muted-2 | `#8a929c` | etiquetas de sección, sub-línea, punto de pendiente |
| muted-3 | `#98a1ab` | metadatos, "$12.00 c/u", línea de tiempo |
| faint | `#a8afb8` / `#c3c8ce` | botón deshabilitado, chevrons |
| surface | `#ffffff` | tarjetas, filas, hoja, header |
| page | `#f4f5f7` | fondo de pantalla, pill de pendiente |
| surface-2 | `#fafbfc` | subheader |
| segmented-bg | `#e9ebef` | botón de cobrar deshabilitado |
| border | `#e6e8ec` | bordes de tarjeta y fila |
| border-soft | `#eef0f3` / `#f2f4f6` | divisores, pista de progreso |
| border-input | `#dfe2e7` | bordes de control, asa de la hoja |
| brand | `#c8102e` | Cobrar, acción destructiva, badge de cantidad |
| brand-dark | `#a90d27` | texto del badge de cantidad |
| brand-tint | `#fdecef` bg · `#f4d3d9` borde | badge de cantidad, quitar de la orden |
| green | `#23a05f` | estado listo, barra de progreso |
| green-dark | `#1c7a4a` | texto de listo, glifo de llamar |
| green-tint | `#eaf6ef` | pill de listo, botón de llamar |
| amber | `#d99000` | estado cocinando |
| amber-dark | `#8a5800` | texto de cocinando, **modificadores del platillo** |
| amber-tint | `#fdf3e2` pill · `#fffdf7` fila · `#f2e0bd` borde | cocinando |
| blue | `#2f7fd9` | estado servido |
| blue-dark | `#1d5a9e` | texto de servido |
| blue-tint | `#e9f1fb` | pill de servido |
| overlay | `rgba(20,24,29,.42)` | fondo detrás de la hoja |

**Tipografía:** Plus Jakarta Sans (400/500/600/700/800), fallback Helvetica, Arial,
sans-serif. `font-feature-settings:'tnum' 1` en el contenedor raíz para que montos y
tiempos queden alineados.
Escala usada: 8, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14, 15, 16, 17, 18, 19, 20, 26 px.
`letter-spacing` negativo en cifras y títulos (−.01 a −.03em), positivo en etiquetas
mayúsculas (.07 a .1em).

**Espaciado:** 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 20 px.

**Radios:** 8, 9, 11, 12, 14, 16, 22, 999px.

**Sombras:**
- Cobrar `0 8px 18px rgba(200,16,46,.26)`
- estado activo en la hoja `0 6px 14px rgba(<color del estado>,.24)`
- barra de acciones `0 -8px 22px rgba(20,24,29,.07)`

---

## Notas de implementación (Django + Bootstrap 5)
- Variables Sass: `$primary: #c8102e`, `$body-bg: #f4f5f7`, `$body-color: #14181d`,
  `$border-color: #e6e8ec`, familia Plus Jakarta Sans. Si no compilas Sass, un
  `detalle-orden.css` con las variables CSS de la tabla basta.
- Templates sugeridos:
  `movil/detalle_orden.html` (extiende `base_movil.html`) y parciales
  `_subheader_orden.html`, `_tarjeta_entrega.html`, `_progreso_cocina.html`,
  `_linea_platillo.html`, `_barra_acciones.html`, `_hoja_platillo.html`.
- El estado de cada línea sale como clase desde el backend
  (`class="linea linea--cocinando"`); los colores viven en CSS. Define los cuatro estados
  como un mapa único en el CSS y en Python, no repetido por plantilla.
- La hoja inferior: **offcanvas de Bootstrap con `placement="bottom"`**, o `<dialog>` con
  animación propia. Overlay `rgba(20,24,29,.42)`.
- La fila de cuatro estados es flex directo (`display:flex; gap:6px` con `flex:1`), no un
  `btn-group`: cada opción es un radio oculto + label para que funcione sin JS.
- Header y subheader sticky apilados: `top:0` el header y `top:52px` el subheader.
- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`
  y `env(safe-area-inset-bottom)` en la barra de acciones.
- **Los estados del prototipo son una suposición** (pendiente / cocinando / listo / servido).
  Si tu modelo usa otros, mantén la estructura y sustituye los nombres y los colores 1 a 1.
- Nombres, teléfonos, direcciones y platillos son **datos de ejemplo**. Si un campo no existe
  en tu modelo, omite ese fragmento en vez de inventarlo.

## Assets
Ninguno. El prototipo usa glifos de texto como marcadores:
`☰ ☾ ▼ ‹ ⋯ ✆ ✓ ✎ ⧉ ⎙ ✕ ＋ − ▤ ›`. Reemplázalos por el set de iconos del proyecto —
Bootstrap Icons encaja: `list`, `moon`, `chevron-down`, `chevron-left`, `three-dots`,
`telephone`, `check-lg`, `pencil`, `copy`, `printer`, `x-lg`, `plus-lg`, `dash-lg`,
`credit-card`, `chevron-right`.

## Files
- `Detalle orden movil.dc.html` — la pantalla, la hoja del platillo, las notas de diseño y
  los cuatro estados en detalle.
