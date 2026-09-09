# Handoff: Header fijo + subheader dinámico · Cresly POS móvil

## Overview
El sistema de barra superior del POS Cresly en móvil. Son **dos piezas independientes**:

1. **Header fijo (52 px)** — idéntico en todas las pantallas, nunca cambia:
   menú hamburguesa, logo de la pizzería con sucursal, botón de tema claro/oscuro y avatar
   de usuario.
2. **Subheader dinámico (56 / 92 / 104 px)** — lo define cada módulo: título, sub-línea con
   el dato relevante del módulo, acción secundaria a la derecha, y una segunda línea opcional
   (chips de estado, filtros o campo de búsqueda).

Entre las dos puede insertarse una **cinta de alerta** cuando algo bloquea el servicio
(impresora caída, sin conexión).

Diseñado a 390 px de ancho (iPhone 14 base). Debe funcionar de 360 a 430 px sin scroll
horizontal.

## About the Design File
`Header fijo y subheader.dc.html` es una **referencia de diseño en HTML**: un prototipo del
look final, no código de producción. Los estilos están inline.

El archivo contiene, en este orden:
- El header fijo en **tema claro** y en **tema oscuro**.
- Una tabla con los cuatro elementos del header.
- **Diez tarjetas de subheader**, una por pantalla, cada una montada bajo el mismo header
  para que se vea que el header no cambia.
- Dos ejemplos de **cinta de alerta**.
- Una **tabla resumen** con las cuatro ranuras del subheader por pantalla.

La tarea es recrear este sistema en **Django (templates) + Bootstrap 5**, siguiendo los
patrones del proyecto (base template, blocks, partials, staticfiles). No portes los estilos
inline: traduce a utilidades de Bootstrap más un CSS propio para lo que Bootstrap no cubre.

## Fidelity
**Alta fidelidad.** Colores, tipografía, tamaños, radios y alturas son finales.
Reprodúcelos con precisión.

---

## 1 · Header fijo (52 px)

`position:sticky; top:0`, altura **52 px**, fondo `#fff`, borde inferior
`1px solid #e6e8ec`, padding lateral `12px`, `display:flex; align-items:center; gap:8px`.

Cuatro elementos, siempre en el mismo orden y posición:

| # | Elemento | Especificación |
|---|---|---|
| 1 | **Menú ☰** | Botón 44 × 44 px, radio `12px`, glifo 17 px `#14181d`. Hover fondo `#f4f5f7`. Abre el panel lateral. `flex:0 0 auto`. |
| 2 | **Logo** | Bloque `flex:1; min-width:0`, `display:flex; align-items:center; gap:9px`. Cuadro de marca 30 × 30 px, radio `9px`, fondo `#c8102e`, inicial blanca 13 px/800. Al lado, en columna: nombre "Cresly Pizzería" 13.5 px/800 `letter-spacing:-.015em` con `text-overflow:ellipsis`, y "Suc. Centro" 10.5 px/600 `#8a929c`. Toca para cambiar de sucursal. |
| 3 | **Tema** | Botón 44 × 44 px, radio `12px`. Glifo **☾** 16 px `#5b6673` en tema claro; **☀** `#ffd479` sobre fondo `#242b33` en tema oscuro. Cambio inmediato, se persiste por usuario. |
| 4 | **Usuario** | Bloque `display:flex; align-items:center; gap:7px`, padding `4px 8px 4px 4px`, radio `11px`, hover `#f4f5f7`. Avatar circular 34 px fondo `#14181d`, inicial blanca 13 px/800, más un caret ▼ de 8 px `#8a929c`. Abre perfil, cambiar usuario y cerrar sesión. |

**El header es byte-idéntico en todas las pantallas.** No se le añaden ni se le quitan
elementos por módulo, no cambia de altura, y el caret del avatar está presente siempre —
incluso cuando hay una cinta de alerta debajo.

### Tema oscuro
| Elemento | Claro | Oscuro |
|---|---|---|
| Fondo del header | `#fff` | `#1a1f25` |
| Borde inferior | `#e6e8ec` | `#2b333b` |
| Marca (cuadro del logo) | `#c8102e` | `#e02040` |
| Texto principal | `#14181d` | `#f2f4f6` |
| Texto secundario | `#8a929c` | `#8d97a2` |
| Glifo ☰ | `#14181d` | `#eceef1` |
| Botón de tema | ☾ `#5b6673`, sin fondo | ☀ `#ffd479` sobre `#242b33` |
| Avatar | fondo `#14181d` | fondo `#333c45`, texto `#f2f4f6` |

El rojo de marca **sube a `#e02040` en oscuro** para mantener contraste; no uses `#c8102e`
sobre fondos oscuros. Deriva el resto de la paleta oscura con la misma lógica: superficies
`#1a1f25` / `#242b33`, bordes `#2b333b`, texto `#f2f4f6` / `#8d97a2`.

---

## 2 · Subheader dinámico

Va inmediatamente debajo del header, fondo `#fafbfc`, borde inferior
`1px solid #eef0f3`. También es sticky (se pega bajo el header).

**Tres alturas, según su contenido:**
| Caso | Altura | Pantallas |
|---|---|---|
| Base | **56 px** | Orden, Cobrar, Detalle de orden, Corte de caja |
| Con segunda línea de chips (34 px) | **92 px** | Inicio, Mesas, Órdenes, Delivery |
| Con campo de búsqueda (52 px) | **104 px** | Vender |
| Base + barra de progreso 3 px | **59 px** | Nuevo pedido delivery |

### Fila principal
`display:flex; align-items:center; gap:10px`, padding `8px 14px 6px` cuando hay segunda
línea, `9px 14px` cuando no.

- **Botón atrás** (solo pantallas internas): 38 × 38 px, radio `11px`, fondo `#fff`,
  borde `1px solid #e6e8ec`, glifo 15 px `#5b6673`. Es **‹** en pantallas internas y
  **✕** en pantallas modales (Orden/carrito). En pantallas raíz no existe.
- **Título**: 18 px/800 en pantallas raíz, 17 px/800 en internas,
  `letter-spacing:-.02em`, `text-overflow:ellipsis`.
- **Pill de estado** junto al título (solo Detalle de orden): padding `2px 8px`,
  radio `999px`, 10.5 px/800, con punto de 5 px. Colores del estado (ver tabla de estados).
- **Sub-línea**: 11 px/600 `#8a929c`, una sola línea con ellipsis.
- **Acción derecha**: máximo una. Icono en botón 38 px (fondo `#fff`, borde `#e6e8ec`,
  glifo 15 px `#5b6673`) o texto 12.5 px/700 sin fondo.

### El dato relevante va en color
La sub-línea no es texto plano: **la cifra o el estado que importa se resalta** con
`font-weight:800` y color propio, sobre el resto en `#8a929c`.

| Color | Significado | Ejemplo |
|---|---|---|
| `#1c7a4a` verde | disponibilidad, todo bien | "**8 libres** de 13", "**Turno abierto** desde las 11:00" |
| `#c8102e` rojo | exige acción o dinero pendiente | "6 abiertas · **$145.30** sin cobrar", "5 en curso · **2 fuera de tiempo**" |
| `#8a5800` ámbar | tiempo transcurrido | "Mesa 7 · Centro · **22 min**" |
| `#4a545f` gris oscuro | contexto sin urgencia | "**3 productos** · mesero1" |

Implementa esto marcando el fragmento resaltado desde el backend (un campo aparte o un
`<strong class="hl hl--red">`), no partiendo la cadena en el template.

### Segunda línea
Solo en pantallas raíz y en Vender. Padding `0 14px 11px`, `overflow:hidden` con scroll
horizontal si no cabe.

- **Chips de filtro**: padding `6px 12px`, radio `999px`, 11.5 px/700, `flex:0 0 auto`.
  Activo: fondo `#14181d`, texto `#fff`, borde `#14181d`.
  Inactivo: fondo `#fff`, texto `#5b6673`, borde `1px solid #dfe2e7`.
- **Chips de estado** (solo Inicio): igual pero con punto de 6 px antes del texto y
  peso 800. Turno activo: fondo `#eaf6ef`, texto `#1c7a4a`, borde `#cfeadb`, punto
  `#23a05f`. Impresora y conexión en reposo: fondo `#fff`, texto `#4a545f`,
  borde `#dfe2e7`, punto `#23a05f`.
- **Campo de búsqueda** (solo Vender): padding `11px 13px`, radio `11px`, fondo `#fff`,
  borde `1px solid #e6e8ec`, glifo ⌕ 13 px `#a8afb8`, placeholder 13.5 px/500 `#a8afb8`.
- **Barra de progreso** (solo Nuevo pedido delivery): 3 px de alto al borde inferior del
  subheader, pista `#eef0f3`, avance `#c8102e`.

### Tabla de subheaders por pantalla

| Pantalla | Atrás | Título | Sub-línea (resaltado) | Acción der. | Segunda línea |
|---|---|---|---|---|---|
| **Inicio** | — | Inicio | **Turno abierto** desde las 11:00 | — | Chips de estado (turno · cocina · en línea) |
| **Mesas** | — | Mesas | **8 libres** de 13 · 4 en servicio | ⌕ | Filtro de zonas (Todas · Salón · Centro · Terraza · Barra) |
| **Órdenes** | — | Órdenes | 6 abiertas · **$145.30** sin cobrar | ⌕ | Filtro de estado (Todas · En cocina · Servidas · Pagadas) |
| **Delivery** | — | Delivery | 5 en curso · **2 fuera de tiempo** | ⌕ | Filtro de estado (En curso · En cocina · En ruta · Entregado) |
| **Vender** | ‹ | Mesa 6 · Salón | Orden nueva · **2 personas** | ⋯ | Campo "Buscar producto…" |
| **Orden (carrito)** | ✕ | Orden · Mesa 6 | **3 productos** · mesero1 | "Vaciar" (texto `#c8102e`) | — |
| **Cobrar** | ‹ | Cobrar · Mesa 6 | Orden **#0154** · 3 productos | — | — |
| **Detalle de orden** | ‹ | #0149 + pill "En cocina" | Mesa 7 · Centro · **22 min** | ⋯ | — |
| **Nuevo pedido delivery** | ‹ | Nuevo pedido | **Paso 1 de 2** · datos del cliente | "Cancelar" (texto `#8a929c`) | Progreso 3 px |
| **Corte de caja** | ‹ | Corte de caja | Turno **11:00 – 12:45** · mesero1 | ⎙ | — |

**Decisiones de diseño a respetar:**
- **Inicio no lleva buscador**: no hay nada que buscar ahí.
- **En Cobrar la ranura derecha va vacía**: dividir cuenta y descuento están en el cuerpo,
  donde se leen. Nada crítico oculto en un ⋯ mientras el cliente espera.
- **En Vender el buscador es campo real, no icono**: se usa constantemente.
- **"Vaciar" es texto, no icono**: una acción destructiva debe poder leerse.
- **En Mesas la segunda línea son zonas, no chips de estado**: con 13 mesas, filtrar por
  zona se usa más. El estado operativo se consulta en Inicio.
- **⋯ nunca contiene la acción primaria**: esa vive en el cuerpo o en la barra inferior.

---

## 3 · Cinta de alerta

Se inserta **entre header y subheader**. Padding `9px 14px`, borde superior del color de su
tinte, `justify-content:space-between`.

- Icono 12 px + mensaje 11.5 px/800 con ellipsis, y a la derecha un botón de acción
  (padding `5px 11px`, radio `8px`, 11 px/800) o una nota del mismo tamaño.

| Caso | Fondo | Borde | Texto/icono | Acción |
|---|---|---|---|---|
| Impresora caída | `#fdecef` | `#f4d3d9` | `#a90d27` | Botón "Reintentar" `#c8102e`/blanco |
| Sin conexión | `#fdf3e2` | `#f2e0bd` | `#8a5800` | Nota "Se guardan aquí" |
| Turno cerrado | `#f4f5f7` | `#e6e8ec` | `#4a545f`, punto `#8a929c` | Botón "Abrir turno" `#14181d`/blanco |

**Reglas:**
- La cinta **empuja el subheader hacia abajo, no lo reemplaza**: el título del módulo nunca
  desaparece.
- **Máximo una cinta a la vez.** Si coinciden dos fallos, gana el que bloquea cobrar
  (turno cerrado > impresora > conexión).
- La cinta puede aparecer en **cualquier** pantalla, incluidas las de tarea.
- El header no se altera por la cinta: mismos cuatro elementos, mismo caret.

---

## Datos que necesita cada plantilla

**Header (context processor global, disponible en todas las vistas):**
```
sucursal:  { nombre, alias }        # "Cresly Pizzería", "Suc. Centro"
usuario:   { nombre, inicial, rol }
tema:      'claro' | 'oscuro'       # persistido por usuario
```

**Subheader (por vista):**
```
subheader: {
  back:       null | 'atras' | 'cerrar',
  titulo:     str,
  pill:       null | { texto, estado },
  sub_pre:    str,       # texto antes del resaltado
  sub_hi:     str,       # el dato relevante
  sub_hi_tono:'verde' | 'rojo' | 'ambar' | 'neutro',
  sub_post:   str,       # texto después
  accion:     null | { tipo: 'icono'|'texto', glifo|label, url },
  segunda:    null | { tipo: 'chips'|'estado'|'busqueda'|'progreso', ... }
}
```

**Alerta (global, del estado del dispositivo/turno):**
```
alerta: null | { tipo: 'impresora'|'conexion'|'turno', mensaje, accion }
```

El tono del resaltado y el tipo de segunda línea los decide la vista, no el template.

---

## Design Tokens

**Colores — tema claro**
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | texto principal, avatar, chip activo, glifo ☰ |
| text-2 | `#4a545f` | resaltado neutro, texto de cinta gris |
| text-3 | `#5b6673` | glifos secundarios, chip inactivo |
| muted-2 | `#8a929c` | sub-línea, sucursal, caret |
| faint | `#a8afb8` | placeholder de búsqueda |
| surface | `#ffffff` | header, botones, chips inactivos |
| surface-2 | `#fafbfc` | fondo del subheader |
| border | `#e6e8ec` | borde del header, botones |
| border-soft | `#eef0f3` | borde inferior del subheader, pista de progreso |
| border-input | `#dfe2e7` | borde de chips inactivos |
| brand | `#c8102e` | marca, resaltado rojo, progreso, botón de alerta |
| brand-dark | `#a90d27` | texto sobre tinte rojo |
| brand-tint | `#fdecef` bg · `#f4d3d9` borde | cinta de impresora |
| green-dark | `#1c7a4a` | resaltado verde, texto de chip de turno |
| green | `#23a05f` | punto de estado OK |
| green-tint | `#eaf6ef` bg · `#cfeadb` borde | chip de turno |
| amber-dark | `#8a5800` | resaltado ámbar, texto de cinta de conexión |
| amber | `#d99000` | punto de estado en cocina |
| amber-tint | `#fdf3e2` bg · `#f2e0bd` borde | cinta de conexión, pill en cocina |

**Colores — tema oscuro**
| Token | Hex |
|---|---|
| surface | `#1a1f25` |
| surface-2 | `#242b33` |
| border | `#2b333b` |
| ink (texto) | `#f2f4f6` |
| muted | `#8d97a2` |
| brand | `#e02040` |
| accent-warm | `#ffd479` (glifo ☀) |
| avatar | `#333c45` |

**Tipografía:** Plus Jakarta Sans (400/500/600/700/800), fallback Helvetica, Arial,
sans-serif. `font-feature-settings:'tnum' 1` en el contenedor raíz para que las cifras
queden alineadas.
Escala del sistema de barras: 8, 10.5, 11, 11.5, 12.5, 13, 13.5, 15, 16, 17, 18 px.
`letter-spacing` negativo en títulos (−.015 a −.02em), positivo en etiquetas mayúsculas
(.04 a .09em).

**Espaciado:** 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14 px.

**Radios:** 8, 9, 11, 12, 999px.

**Táctil:** ☰, tema y avatar son objetivos de 44 px; los botones del subheader 38 px
(aceptable porque son acciones secundarias y están rodeados de espacio). Ningún objetivo
interactivo por debajo de 38 px.

---

## Notas de implementación (Django + Bootstrap 5)
- Variables Sass: `$primary: #c8102e`, `$body-bg: #f4f5f7`, `$body-color: #14181d`,
  `$border-color: #e6e8ec`, familia Plus Jakarta Sans. Si no compilas Sass, un
  `barras.css` con las variables CSS de las tablas basta.
- Implementa el tema con `data-bs-theme="dark"` en `<html>` más overrides propios para los
  tokens que Bootstrap no cubre (marca `#e02040`, superficies). Persiste la elección en el
  perfil del usuario y aplícala en el render inicial para evitar el parpadeo.
- Templates sugeridos:
  `movil/base_movil.html` — incluye `_header.html`, `{% block alerta %}`,
  `{% block subheader %}` y `_tabbar.html`.
  Parciales: `_header.html`, `_subheader.html`, `_cinta_alerta.html`,
  `_chips_filtro.html`, `_chips_estado.html`.
- Un solo `_subheader.html` parametrizado con el dict `subheader` sirve para las diez
  pantallas; no dupliques markup por módulo.
- El header y el subheader son sticky apilados: usa `position:sticky` con `top:0` en el
  header y `top:52px` en el subheader, o envuelve ambos en un contenedor sticky.
- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`.
- Los chips con scroll horizontal: `overflow-x:auto; scrollbar-width:none` en el contenedor
  y `flex:0 0 auto` en cada chip.
- Los datos del prototipo son **de ejemplo**. Sustitúyelos por los reales; si un campo no
  existe (comensales, tiempo transcurrido), omite ese fragmento en vez de inventarlo.

## Assets
Ninguno. El prototipo usa glifos de texto como marcadores:
`☰ ☾ ☀ ▼ ‹ ✕ ⌕ ⋯ ⎙ ⇅`. Reemplázalos por el set de iconos del proyecto —
Bootstrap Icons encaja: `list`, `moon`, `sun`, `chevron-down`, `chevron-left`,
`x-lg`, `search`, `three-dots`, `printer`, `arrow-down-up`.

## Files
- `Header fijo y subheader.dc.html` — header fijo (claro y oscuro), los diez subheaders,
  las cintas de alerta y la tabla resumen.
