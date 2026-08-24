# Handoff: Módulo Mesas (POS Cresly) — rediseño visual

## Overview
Rediseño visual del módulo **Mesas** de un POS de restaurante. Muestra el mapa de mesas
agrupado por zonas, con estado de cada mesa (libre / ocupada / por cobrar), métricas del
turno y los pedidos para llevar abiertos. El objetivo del rediseño fue legibilidad y
jerarquía: el rojo de marca queda reservado para acciones y alertas en vez de rellenar
media pantalla, y las mesas pasan a tarjetas con tinte suave e información útil
(monto, tiempo transcurrido, comensales).

## About the Design Files
`Mesas.dc.html` es una **referencia de diseño hecha en HTML** — un prototipo del look y
comportamiento previsto, no código de producción para copiar tal cual. Todos los estilos
están inline y el HTML se genera desde una clase JS con datos de ejemplo.

La tarea es **recrear este diseño en el stack real: Django (templates) + Bootstrap 5**,
usando los patrones ya establecidos en ese proyecto (base template, blocks, partials,
context processors, staticfiles). No portes los estilos inline; traduce a clases Bootstrap
+ un CSS propio pequeño para lo que Bootstrap no cubre (tokens de color de estado, tarjetas
de mesa).

## Fidelity
**Alta fidelidad (hifi).** Colores, tipografía, espaciados, radios y estados hover son
finales. Reprodúcelos con precisión; solo sustituye la maquetación inline por el sistema
de grid/utilidades de Bootstrap.

## Screens / Views

### Vista única: Mapa de mesas
**Propósito:** el mesero/cajero ve de un golpe qué mesas están libres, cuáles en servicio y
cuáles esperando pago; toca una mesa libre para abrir un pedido nuevo, u ocupada para ver
la cuenta.

**Layout general:** dos columnas en flex, `min-height:100vh`.
- **Sidebar:** ancho fijo `236px` (`flex:0 0 236px`), fondo `#14181d`, padding `18px 14px`,
  contenido en columna; el bloque inferior (Configuración + usuario) empujado con `margin-top:auto`.
- **Main:** `flex:1`, columna. Header sticky-able de `padding:14px 32px`, fondo `#fff`,
  borde inferior `1px solid #e6e8ec`. Cuerpo con `padding:26px 32px 34px` y `gap:20px`
  entre bloques.

#### 1. Sidebar
- **Logo:** cuadro `38×38`, radio `11px`, fondo `#c8102e`, letra “C” blanca 17px/800.
  Al lado: “Cresly” 15px/700 `letter-spacing:-.01em` y “Punto de venta” 11px `#8b939e`.
- **Etiqueta de sección** “OPERACIÓN”: 10px/700, `letter-spacing:.14em`, `#6f7883`.
- **Grupo activo “Pizzería”:** fila 13.5px/700 blanca, fondo `#1d2329`, radio `9px`,
  padding `9px 10px`, chevron `▲` 10px `#8b939e`.
- **Subitems** (Inicio, Mesas, Órdenes, Nueva orden, Delivery): padding `8px 10px`,
  radio `8px`, 13px `#b9c0c9`; contenedor con `border-left:1px solid #262d34`,
  `padding-left:8px`, `margin-left:5px`.
  - Hover subitem: fondo `#1d2329`, texto `#fff`.
  - **Item activo “Mesas”:** fondo `#c8102e`, texto `#fff` 700, más un punto `6px`
    blanco (`opacity:.85`) alineado a la derecha.
- **“Almuerzos”** (grupo colapsado): 13.5px/600 `#b9c0c9`, chevron `▼` `#6f7883`, `margin-top:6px`.
- **Pie:** “Configuración” (mismo estilo que subitem) y tarjeta de usuario: fondo `#1d2329`,
  radio `11px`, padding `10px`, avatar circular `30px` fondo `#2e363e` con “M” 12px/700,
  nombre “mesero1” 12.5px/700, “Cresly · Cajero” 10.5px `#8b939e`.

#### 2. Header
- Izquierda: breadcrumb 13px — “Inicio” `#8a929c`, separador “/” `#c3c8ce`, “Mesas”
  `#14181d` 700.
- Derecha: botón de notificaciones `34×34`, radio `10px`, borde `1px solid #e6e8ec`,
  hover fondo `#f4f5f7`; badge `7px` `#c8102e` con `border:2px solid #fff` en top/right `7px`.
  Junto a él, fecha “Viernes, 14 de agosto” 11.5px `#8a929c` y hora “12:45 a. m.” 15px/800,
  alineadas a la derecha.

#### 3. Título y acciones
- `h1` “Mapa de mesas · Pizzería”: 27px/800, `letter-spacing:-.025em`.
- Subtítulo: 13.5px `#767e88`, `max-width:620px`, `text-wrap:pretty` —
  “Toca una mesa libre para tomar un pedido, u ocupada para ver su cuenta.”
- Botones (fila, `gap:10px`), todos padding `10px 16px`, radio `10px`, 13.5px:
  - **Para llevar** (primario): fondo `#c8102e`, texto `#fff` 700,
    `box-shadow:0 6px 14px rgba(200,16,46,.22)`; hover `#a90d27`.
  - **Caja pizzería** y **Gestionar mesas** (secundarios): fondo `#fff`,
    borde `1px solid #dfe2e7`, texto 600; hover `border-color:#14181d`.
- El bloque título/acciones es `flex` con `justify-content:space-between`,
  `align-items:flex-end`, `flex-wrap:wrap`, `gap:28px`.

#### 4. Fila de métricas (4 tarjetas)
`display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:12px`.
Cada tarjeta: fondo `#fff`, borde `1px solid #e6e8ec`, radio `14px`, padding `14px 16px`,
columna con `gap:4px`. Fila de valor: `flex; align-items:baseline; gap:7px; flex-wrap:wrap;
min-width:0` (el wrap evita que la etiqueta se desborde en anchos intermedios).
- Etiqueta: 11.5px/700, `letter-spacing:.06em`, `#8a929c`.
- Valor: 26px/800, `letter-spacing:-.03em`.
- Sub-etiqueta: 12.5px `#8a929c`.

| Tarjeta | Etiqueta | Valor (color) | Sub-etiqueta |
|---|---|---|---|
| 1 | LIBRES | conteo libres — `#1c7a4a` | “de {total} mesas” |
| 2 | OCUPADAS | conteo ocupadas — `#c8102e` | “en servicio” |
| 3 | POR COBRAR | conteo por cobrar — `#b07000` | “esperando pago” |
| 4 | EN CURSO | suma de cuentas abiertas — `#fff` | “sin cobrar” |

La cuarta tarjeta es invertida: fondo y borde `#14181d`, texto `#fff`, sub-etiqueta `#98a1ab`.

#### 5. Panel del mapa
Contenedor: fondo `#fff`, borde `1px solid #e6e8ec`, radio `18px`, `overflow:hidden`.

**Barra superior del panel:** padding `14px 20px`, borde inferior `1px solid #eef0f3`,
`flex` con `space-between` y `flex-wrap:wrap`.
- Leyenda: tres pills, `gap:8px`, cada una padding `6px 12px`, radio `999px`, 12.5px/700,
  con punto `8px` antes del texto:
  - Libre — fondo `#eaf6ef`, texto `#1c7a4a`, punto `#23a05f`
  - Ocupada — fondo `#fdecef`, texto `#a90d27`, punto `#c8102e`
  - Por cobrar — fondo `#fdf3e2`, texto `#8a5800`, punto `#d99000`
- Derecha: “Actualizado hace un momento” 12.5px `#8a929c`.

**Cuerpo del panel:** padding `20px`, columna con `gap:22px`, una sección por zona.

**Encabezado de zona:** fila con `gap:12px` —
nombre de zona 12px/800 `letter-spacing:.1em` `#14181d`;
meta “{n} mesas · {n} libres” 11.5px/600 `#9aa2ac`;
después una regla que ocupa el resto (`flex:1; height:1px; background:#eef0f3`).

**Rejilla de mesas por zona:**
`grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:12px`.

**Tarjeta de mesa:** `position:relative`, columna con `justify-content:space-between`,
`min-height:112px`, padding `14px 15px`, radio `16px` (mesas redondas: `999px`),
`cursor:pointer`, borde `1px solid <border de estado>`, fondo `<bg de estado>`,
`transition:transform .12s ease, box-shadow .12s ease`.
Hover: `transform:translateY(-2px)`, `box-shadow:0 10px 22px rgba(20,24,29,.10)`.
- **Fila superior:** número de mesa 25px/800, `letter-spacing:-.03em`, `line-height:1`,
  color `#14181d`; a la derecha un punto `9px` del color de estado con `margin-top:4px`.
- **Bloque inferior** (`gap:3px`):
  - Estado en mayúsculas: 11.5px/700, `letter-spacing:.04em`, color de estado.
  - Fila baseline con `space-between`: monto 15px/800 `letter-spacing:-.02em` `#14181d`
    y sub-texto 11.5px/600 `#98a1ab`.
- **Monto:** `$29.50` si hay cuenta; si no, “Disponible” (libre) o “En cuenta”.
- **Sub-texto:** `"{tiempo} · {comensales}p"` si hay tiempo, si no `"{comensales} personas"`.

**Variante sólida (opcional, flag `solidStatusFills`):** el fondo pasa al color pleno del
estado, borde al tono oscuro, número y monto `#fff`, y el punto a `rgba(255,255,255,.9)`.
- libre `#23a05f` / borde `#1c8a51`
- ocupada `#c8102e` / borde `#a90d27`
- por cobrar `#d99000` / borde `#b87b00`

Existe también un flag `showAmounts` que oculta los montos (muestra “En cuenta”).

#### 6. Pedidos para llevar abiertos
- Encabezado: `h2` 16px/800 `letter-spacing:-.015em` a la izquierda; a la derecha
  “{n} pedidos · {total}” 12.5px/600 `#8a929c`.
- Rejilla: `repeat(auto-fill,minmax(190px,1fr))`, `gap:12px`.
- Tarjeta: fondo `#fff`, borde `1px solid #e6e8ec`, radio `14px`, padding `14px 15px`,
  columna `gap:9px`, `cursor:pointer`; hover `border-color:#14181d`.
  - Fila superior: código `#001` 12.5px/800 `#c8102e` y hora 11px/600 `#98a1ab`.
  - Nombre del cliente 13px `#767e88` (“Sin nombre” cuando no hay).
  - Total 18px/800 `letter-spacing:-.02em`.

## Interactions & Behavior
- **Mesa libre** → abrir flujo de nuevo pedido para esa mesa.
- **Mesa ocupada / por cobrar** → abrir la cuenta abierta de esa mesa.
- **Para llevar** → nuevo pedido sin mesa. **Caja pizzería** → arqueo/caja del área.
  **Gestionar mesas** → CRUD de mesas y zonas.
- **Tarjeta de pedido para llevar** → abrir ese pedido.
- Hover: elevación `-2px` + sombra en mesas; cambio de borde a `#14181d` en tarjetas
  secundarias y botones ghost; en sidebar, fondo `#1d2329`.
- Transiciones: `.12s ease` en `transform` y `box-shadow`. Sin animaciones de entrada.
- **Estado vacío** (zona sin mesas): no está diseñado; usa un texto 13px `#8a929c`
  centrado dentro de la rejilla.
- **Loading:** al recargar el mapa, conserva la altura del panel y muestra las tarjetas
  en gris `#f4f5f7` (skeleton) para evitar salto de layout.
- **Responsive:** las tres rejillas son auto-fit/auto-fill, así que se reflow solas.
  Por debajo de ~900px el sidebar debería colapsar a offcanvas de Bootstrap.
- **Refresco:** el mapa debe actualizarse en vivo (polling cada 10–15 s o websocket);
  la leyenda “Actualizado hace un momento” refleja ese último fetch.

## State Management
Datos que la vista necesita del backend:
- `zones: [{ name, tables: [...] }]`
- `table: { id, label, status ('libre'|'ocupada'|'cobrar'), total|null, seats, opened_at|null, is_round }`
  - `time` mostrado = ahora − `opened_at`, formateado “38 min” / “1 h 05”.
- Derivados (calcúlalos en la vista o con un serializer/annotate, no en el template):
  `count_all`, `count_free`, `count_busy`, `count_bill`, `total_open` (suma de `total`),
  y por zona `len(tables)` + libres.
- `takeaway_orders: [{ code, customer_name, total, created_at }]` + total agregado.
- Sugerencia Django: una vista `mesas` que arme el contexto y un endpoint JSON
  (`/mesas/estado/`) que devuelva lo mismo para el refresco parcial (HTMX o fetch +
  reemplazo del partial `_mapa_mesas.html`).

## Design Tokens

**Colores**
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | texto principal, sidebar, tarjeta invertida |
| ink-2 | `#1d2329` | superficies dentro del sidebar, hover |
| ink-3 | `#262d34` | borde interno sidebar |
| ink-4 | `#2e363e` | avatar |
| muted-dark | `#b9c0c9` | texto sidebar |
| muted-dark-2 | `#8b939e` / `#98a1ab` | texto secundario oscuro/claro |
| muted-dark-3 | `#6f7883` | etiquetas sidebar |
| text-muted | `#767e88` | párrafos |
| text-soft | `#8a929c` | etiquetas y metadatos |
| text-faint | `#9aa2ac` / `#c3c8ce` | meta de zona / separadores |
| surface | `#ffffff` | tarjetas, header, panel |
| page | `#f4f5f7` | fondo de página |
| border | `#e6e8ec` | bordes de tarjeta |
| border-soft | `#eef0f3` | divisores internos |
| border-input | `#dfe2e7` | botones secundarios |
| brand | `#c8102e` | acción primaria, activo, ocupada |
| brand-dark | `#a90d27` | hover / borde ocupada |
| green | `#23a05f` | libre (punto/relleno) |
| green-dark | `#1c8a51` / `#1c7a4a` | borde libre / texto libre |
| green-soft | `#f4fbf7` bg, `#cfeadb` borde, `#eaf6ef` pill | libre tinte |
| red-soft | `#fef6f7` bg, `#f4d3d9` borde, `#fdecef` pill | ocupada tinte |
| amber | `#d99000` | por cobrar |
| amber-dark | `#b87b00` / `#b07000` / `#8a5800` | borde / valor / texto pill |
| amber-soft | `#fffaf1` bg, `#f2e0bd` borde, `#fdf3e2` pill | por cobrar tinte |

**Tipografía:** Plus Jakarta Sans (Google Fonts, pesos 400/500/600/700/800),
fallback Helvetica, Arial, sans-serif. `font-feature-settings:'tnum' 1` en el contenedor
raíz para que los montos y horas queden alineados.
Escala usada: 10, 11, 11.5, 12, 12.5, 13, 13.5, 15, 16, 18, 25, 26, 27 px.
Letter-spacing negativo en titulares (-.015 a -.03em) y positivo en etiquetas
mayúsculas (.04 a .14em).

**Espaciado:** 2, 3, 4, 6, 8, 9, 10, 11, 12, 14, 15, 16, 18, 20, 22, 26, 28, 32, 34 px.

**Radios:** 8, 9, 10, 11, 14, 16, 18, 999px (pill / mesa redonda).

**Sombras:**
- botón primario `0 6px 14px rgba(200,16,46,.22)`
- mesa hover `0 10px 22px rgba(20,24,29,.10)`

## Notas de implementación en Django + Bootstrap 5
- Sobrescribe variables Sass de Bootstrap donde coincida: `$primary: #c8102e`,
  `$body-bg: #f4f5f7`, `$body-color: #14181d`, `$border-color: #e6e8ec`,
  `$border-radius: .875rem` (14px), `$font-family-sans-serif` con Plus Jakarta Sans.
  Si no compilas Sass, un `mesas.css` con las variables CSS de la tabla anterior basta.
- Estructura de templates sugerida:
  - `mesas/mesas.html` (extiende el base con el sidebar)
  - `mesas/_metricas.html`, `mesas/_mapa_mesas.html`, `mesas/_mesa_card.html`,
    `mesas/_para_llevar.html`
- El sidebar es propio (no un componente de Bootstrap): usa flex utilities
  (`d-flex flex-column vh-100`) + offcanvas para móvil.
- Las tres rejillas no se pueden hacer con el grid de 12 columnas de Bootstrap sin perder
  el comportamiento auto-fill; usa CSS Grid directo en tu `mesas.css`
  (`.mesas-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:.75rem }`).
- El estado de la mesa debería salir como clase desde el backend
  (`class="mesa-card mesa-card--{{ mesa.status }}"`) y los colores vivir en CSS,
  no calcularse en el template.
- Los datos de tiempo (“38 min”) y comensales del prototipo son **de ejemplo**; sustitúyelos
  por los campos reales del modelo. Si un campo no existe, omite el sub-texto en vez de
  inventarlo.

## Assets
Ninguno. No hay imágenes ni iconos externos: el prototipo usa glifos de texto (`▲ ▼ ◔ /`)
como marcadores. En la implementación real, reemplázalos por el set de iconos que ya use
el proyecto (Bootstrap Icons encaja: `house`, `grid-3x3-gap`, `journal`, `plus`, `scooter`,
`gear`, `bell`, `chevron-up/down`).

## Files
- `Mesas.dc.html` — el diseño completo (una sola página, estilos inline, datos de ejemplo
  en la clase JS al final del archivo).
