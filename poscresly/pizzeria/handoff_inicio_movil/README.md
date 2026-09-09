# Handoff: Inicio móvil · Cresly POS

## Overview
Una sola pantalla: el **Inicio** del POS Cresly en celular (390 × 844, mobile first).
El cajero/admin abre la app y ve cuánto se ha vendido en el turno, cuánto falta por cobrar,
y cómo está repartido el dinero que hay en caja entre efectivo, transferencia y tarjeta.

## About the Design File
`Inicio movil.dc.html` es una **referencia de diseño en HTML**: un prototipo del look final,
no código de producción. Los estilos están inline.

La tarea es recrear esta pantalla en **Django (templates) + Bootstrap 5**, siguiendo los
patrones ya existentes del proyecto (base template, blocks, partials, staticfiles).
No portes los estilos inline: traduce a utilidades de Bootstrap más un CSS propio pequeño
para lo que Bootstrap no cubre.

El archivo muestra la pantalla completa y, al lado, una **variante de la tarjeta de caja**
(barra apilada en vez de dona). Implementa **una sola** — si no hay preferencia, la dona.

## Fidelity
**Alta fidelidad.** Colores, tipografía, tamaños, radios y jerarquía son finales.
Reprodúcelos con precisión.

---

## Estructura de la pantalla

Marco de diseño 390 × 844 (iPhone 14 base). Debe funcionar de 360 a 430 px de ancho sin
scroll horizontal. Tres zonas: header fijo arriba, contenido con scroll, tab bar fija abajo.

### 1 · Header
Fondo `#fff`, borde inferior `1px solid #e6e8ec`, padding `6px 18px 14px`,
`display:flex; align-items:center; justify-content:space-between; gap:12px`.

- **Saludo** según la hora ("Buenas noches"): 20 px/800, `letter-spacing:-.025em`.
- Debajo, en fila con `gap:7px`:
  - Pill **"Turno abierto"**: fondo `#eaf6ef`, texto `#1c7a4a` 11 px/800,
    padding `3px 9px`, radio `999px`, con un punto de 6 px `#23a05f` antes del texto.
    Turno cerrado: fondo `#eef0f3`, texto `#4a545f`, punto `#8a929c`.
  - "desde 11:00" 11.5 px/600 `#8a929c`.
- **Avatar** a la derecha: círculo 44 px, fondo `#14181d`, inicial blanca 15 px/800,
  `flex:0 0 auto`.

### 2 · Contenido
Padding lateral `18px`, padding superior `14px`, columna con `gap:12px`.
Es la única zona con scroll.

#### Tarjeta 1 — Venta del turno (la principal)
Fondo `#14181d`, texto blanco, radio `18px`, padding `18px 19px`, columna con `gap:14px`.

- Fila superior, `justify-content:space-between`:
  - Etiqueta **"VENTA DEL TURNO"** 11 px/800, `letter-spacing:.09em`, `#98a1ab`.
  - Monto **38 px/800**, `letter-spacing:-.035em`, `line-height:1.05`.
  - Pill de variación a la derecha: fondo `rgba(255,255,255,.14)`, 11 px/800,
    `white-space:nowrap`. Al alza texto `#c8e6cf` con "▲"; a la baja `#f4b5bf` con "▼".
- Pie separado por `border-top:1px solid #262d34`, `padding-top:13px`, dos columnas
  `flex:1` (la segunda con `border-left:1px solid #262d34` y `padding-left:12px`):
  valor 17 px/800 y etiqueta 11 px/600 `#98a1ab`.
  Columna A: nº de órdenes cobradas. Columna B: ticket promedio.

#### Tarjeta 2 — Por cobrar
Fondo `#fff`, borde `1px solid #f4d3d9`, radio `16px`, padding `15px 17px`,
`display:flex; align-items:center; justify-content:space-between; gap:14px`.

- Etiqueta **"POR COBRAR"** 11 px/800, `letter-spacing:.09em`, `#a90d27`.
- Monto 28 px/800, `letter-spacing:-.03em`, `#c8102e`.
- Sub-línea "6 órdenes abiertas · 4 mesas" 11.5 px/600 `#8a929c`.
- A la derecha, chevron "›" en cuadro de 44 px, radio `13px`, fondo `#fdecef`,
  color `#c8102e`, 19 px. Navega a Órdenes filtrado por abiertas.

**Va en tarjeta aparte a propósito: ese dinero no está en caja.** No lo sumes al total
de caja ni lo incluyas en la dona.

#### Tarjeta 3 — Dinero en caja
Fondo `#fff`, borde `1px solid #e6e8ec`, radio `18px`, padding `17px`,
columna con `gap:15px`.

**Cabecera:** "DINERO EN CAJA" 11 px/800 `letter-spacing:.09em` `#8a929c`;
"Ver corte" 11.5 px/700 `#8a929c` a la derecha.

**Cuerpo:** fila con `align-items:center; gap:18px`.

*Dona* — 118 × 118 px, `flex:0 0 auto`, `border-radius:50%`:
```css
background: conic-gradient(#c8102e 0 62%, #2f7fd9 62% 83%, #d99000 83% 100%);
```
Encima, un círculo interior `position:absolute; inset:15px; border-radius:50%;
background:#fff` (grosor del anillo = 15 px) centrado en columna, con:
"TOTAL" 10 px/800 `letter-spacing:.07em` `#8a929c` y el monto 19 px/800
`letter-spacing:-.03em`.

Los stops se calculan en la vista: `efectivo%`, `efectivo% + transferencia%`, `100%`.
Pásalos como una sola cadena al template
(`style="background: conic-gradient({{ caja.stops }})"`) o como variables CSS.
No dibujes SVG a mano.

*Leyenda* — a la derecha, `flex:1; min-width:0`, columna con `gap:11px`.
Una fila por método, `align-items:center; gap:9px`:
- cuadro de 9 px, `border-radius:3px`, del color del método, `flex:0 0 auto`;
- nombre 12.5 px/700 y debajo "62% · 14 órdenes" 11 px/600 `#98a1ab`;
- monto 14 px/800 `letter-spacing:-.02em` alineado a la derecha.

**Efectivo en gaveta:** caja `#fafbfc`, borde `1px solid #eef0f3`, radio `12px`,
padding `12px 14px`, `justify-content:space-between`.
Etiqueta "EFECTIVO EN GAVETA" 11 px/800 `letter-spacing:.07em` `#8a929c`,
sub-línea "Fondo inicial $50.00" 11.5 px/600 `#98a1ab`, monto 19 px/800.
Es `efectivo_cobrado + fondo_inicial`: el número que se cuenta al cerrar caja.

**Colores de método de pago — fijos en todo el sistema:**
efectivo `#c8102e` · transferencia `#2f7fd9` · tarjeta `#d99000`.

#### Variante incluida: barra apilada
En el archivo, la segunda columna muestra la misma tarjeta con una **barra apilada** en
lugar de dona. Es más compacta y más fácil de comparar porcentajes.

- Cabecera con el total en 30 px/800 arriba a la izquierda y "Ver corte" a la derecha.
- Barra: `display:flex; height:12px; border-radius:999px; overflow:hidden; gap:2px`,
  un `div` por método con `width` = su porcentaje.
- Leyenda como lista de filas con `border-bottom:1px solid #f2f4f6` (la última sin borde),
  padding `12px 0`: cuadro 10 px, nombre 13.5 px/700 + "14 órdenes" 11.5 px/600,
  y a la derecha monto 15 px/800 con el porcentaje 11.5 px/700 `#98a1ab` debajo.

#### Accesos rápidos
Grid de 2 columnas, `gap:10px`. Cada uno `display:flex; align-items:center; gap:11px`,
padding `14px 15px`, radio `14px`.
- **"Nueva orden"**: fondo `#c8102e`, texto blanco 13.5 px/800, glifo ＋ 19 px,
  `box-shadow:0 8px 18px rgba(200,16,46,.24)`.
- **"Ver mesas"**: fondo `#fff`, borde `1px solid #dfe2e7`, texto 13.5 px/700,
  glifo 17 px `#5b6673`.

### 3 · Tab bar (fija abajo)
`position:fixed`, fondo `#fff`, borde superior `1px solid #e6e8ec`,
padding `9px 10px 22px` — usa `padding-bottom: max(22px, env(safe-area-inset-bottom))`.
Grid de 4 columnas, `gap:2px`.

Cada pestaña: columna centrada, `gap:3px`, padding `7px 4px`, icono 17 px, label 10.5 px.
- **Activa** (Inicio): fondo `#fdecef`, radio `12px`, icono y texto `#c8102e` peso 800.
- Inactiva: icono `#9aa2ac`, texto `#8a929c` peso 700.
- Badge de conteo en Órdenes: `position:absolute; top:4px; right:16px`,
  mínimo 17 × 17 px, radio `999px`, fondo `#c8102e`, texto blanco 10 px/800.

Pestañas, en orden: **Inicio · Mesas · Órdenes · Delivery**.

---

## Datos que necesita la vista
```
turno:        { abierto: bool, hora_apertura, fondo_inicial }
ventas_turno: { total, ordenes_cobradas, ticket_promedio, variacion_pct }
por_cobrar:   { total, ordenes_abiertas, mesas_ocupadas }
caja: [ { metodo: 'efectivo'|'transferencia'|'tarjeta', total, ordenes, pct } ]
efectivo_en_gaveta = caja.efectivo.total + turno.fondo_inicial
total_caja         = suma de caja[].total   (= ventas_turno.total)
ordenes_abiertas_badge = por_cobrar.ordenes_abiertas
```
- Calcula porcentajes y los stops de la dona **en la vista**, no en el template.
- `variacion_pct` compara contra el mismo turno del día anterior; si no hay dato, oculta
  el pill en lugar de mostrar 0 %.
- Turno cerrado: las cifras muestran el último turno y el pill cambia a "Turno cerrado".

**Refresco:** polling cada 15 s (o websocket) contra un endpoint JSON `/api/inicio/`
que devuelva el mismo shape. Al refrescar sólo se actualizan cifras — nada se reordena.

**Loading:** skeletons `#eef0f3` con la altura de cada tarjeta. Nunca un spinner de página
completa: el header y la tab bar deben permanecer.

**Estado sin ventas:** las tarjetas se muestran con `$0.00`; la dona se reemplaza por un
círculo `#eef0f3` del mismo tamaño y la leyenda por una línea 12.5 px `#98a1ab`
"Sin cobros en este turno".

---

## Design Tokens

**Colores**
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | texto principal, tarjeta de venta, avatar |
| ink-3 | `#262d34` | divisores dentro de la tarjeta oscura |
| text-2 | `#4a545f` | texto de notas |
| text-3 | `#5b6673` | glifos secundarios |
| muted-2 | `#8a929c` | etiquetas y metadatos |
| muted-3 | `#98a1ab` | metadatos sobre fondo claro y oscuro |
| muted-4 | `#9aa2ac` | iconos inactivos |
| surface | `#ffffff` | tarjetas, header, tab bar |
| page | `#f4f5f7` | fondo de pantalla |
| surface-2 | `#fafbfc` | caja de efectivo en gaveta |
| border | `#e6e8ec` | bordes de tarjeta |
| border-soft | `#eef0f3` / `#f2f4f6` | divisores, skeletons |
| border-input | `#dfe2e7` | borde de "Ver mesas" |
| brand | `#c8102e` | acción primaria, activo, efectivo, por cobrar |
| brand-dark | `#a90d27` | texto sobre tinte rojo |
| brand-tint | `#fdecef` bg · `#f4d3d9` borde | tarjeta por cobrar, pestaña activa |
| green | `#23a05f` | punto de turno abierto |
| green-dark | `#1c7a4a` | texto del pill de turno |
| green-tint | `#eaf6ef` | fondo del pill de turno |
| green-light | `#c8e6cf` | variación al alza sobre fondo negro |
| red-light | `#f4b5bf` | variación a la baja sobre fondo negro |
| blue | `#2f7fd9` | transferencia |
| amber | `#d99000` | tarjeta (método de pago) |

**Tipografía:** Plus Jakarta Sans (400/500/600/700/800), fallback Helvetica, Arial,
sans-serif. `font-feature-settings:'tnum' 1` en el contenedor raíz para que los montos
queden alineados.
Escala usada: 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14, 15, 17, 19, 20, 28, 30, 38 px.
`letter-spacing` negativo en cifras (−.02 a −.035em), positivo en etiquetas mayúsculas
(.07 a .09em).

**Espaciado:** 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 22 px.

**Radios:** 3, 12, 13, 14, 16, 18, 999px.

**Sombras:** botón primario `0 8px 18px rgba(200,16,46,.24)`.

**Táctil:** todo objetivo interactivo mínimo **44 × 44 px** (avatar, chevron de por cobrar,
accesos rápidos, pestañas). Texto de contenido nunca bajo 12 px; las etiquetas de 10–11 px
son sólo mayúsculas con `letter-spacing` amplio.

---

## Notas de implementación (Django + Bootstrap 5)
- Variables Sass: `$primary: #c8102e`, `$body-bg: #f4f5f7`, `$body-color: #14181d`,
  `$border-color: #e6e8ec`, `$border-radius: 1.125rem` (18px), familia Plus Jakarta Sans.
  Si no compilas Sass, un `inicio-movil.css` con las variables CSS de la tabla basta.
- Templates sugeridos:
  `movil/base_movil.html` (header + tab bar + safe-area),
  `movil/inicio.html`,
  y parciales `_tabbar.html`, `_caja_dona.html`, `_accesos_rapidos.html`.
- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`
  y `env(safe-area-inset-bottom)` en la tab bar.
- El saludo por hora se resuelve en la vista, no con JS.
- Los datos del prototipo son **de ejemplo**. Sustitúyelos por los reales; si un campo no
  existe (variación, fondo inicial), omite esa línea en vez de inventarla.

## Assets
Ninguno. El prototipo usa glifos de texto (`＋ ▦ ☰ ⌂ ⇢ ›`) como marcadores.
Reemplázalos por el set de iconos del proyecto — Bootstrap Icons encaja:
`plus-lg`, `grid-3x3-gap`, `list-ul`, `house`, `scooter`, `chevron-right`.

## Files
- `Inicio movil.dc.html` — la pantalla de Inicio más la variante del gráfico de caja.
