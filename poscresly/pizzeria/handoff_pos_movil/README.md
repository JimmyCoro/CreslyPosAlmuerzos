# Handoff: Punto de venta móvil · Cresly POS

## Overview
El **Punto de venta en celular**: la pantalla donde el mesero o cajero arma una orden desde
el teléfono. Cubre el flujo completo — elegir el modo de venta y capturar sus datos, agregar
productos, revisar el pedido y confirmar.

Es la adaptación a móvil del punto de venta que ya existe en escritorio. Conserva su lógica
(catálogo por categorías, buscador, carrito con IVA 15 %, "Confirmar e Imprimir") y resuelve
dos problemas del móvil actual: la cabecera consumía 290 px antes del primer producto, y el
modo de venta (Servirse / Llevar / Delivery) solo se veía al abrir el carrito, cuando la
orden ya estaba armada.

Diseñado a 390 px de ancho (iPhone 14 base). Debe funcionar de 360 a 430 px sin scroll
horizontal.

## About the Design Files
Son **referencias de diseño en HTML**: prototipos del look y el comportamiento previstos, no
código de producción. Los estilos están inline.

| Archivo | Contenido |
|---|---|
| `Punto de venta movil - adaptado.dc.html` | La pantalla de catálogo completa y el carrito abierto, más la tabla de alturas antes/después |
| `Punto de venta movil - modos.dc.html` | El flujo de 4 pasos, **las tres hojas de modo**, los cinco estados del subheader y las reglas de validación |
| `Punto de venta movil - header.dc.html` | La barra superior en contexto y sus seis estados |
| `Punto de venta.dc.html` | La versión de escritorio, como referencia de la lógica y el catálogo |

La tarea es recrear esto en **Django (templates) + Bootstrap 5**, siguiendo los patrones del
proyecto (base template, blocks, partials, staticfiles). No portes los estilos inline:
traduce a utilidades de Bootstrap más un CSS propio para lo que Bootstrap no cubre.

## Fidelity
**Alta fidelidad.** Colores, tipografía, espaciados, radios y alturas son finales.
Reprodúcelos con precisión.

---

## El flujo, en cuatro pasos

1. **Elegir modo** — al entrar en orden nueva, o tocando el chip del subheader.
2. **Capturar sus datos** — en la misma hoja, solo los campos de ese modo.
3. **Agregar productos** — el subheader muestra el resumen de lo capturado.
4. **Confirmar e imprimir** — bloqueado mientras falte algo obligatorio.

**Decisión central: la captura de datos y el carrito son cosas separadas.**
La hoja de modo captura el *quién y el dónde* (mesa, cliente, teléfono, dirección, envío).
El carrito contiene el *qué* (productos, cantidades, totales). Se tocan en dos puntos: el
valor de la moto entra a los totales como una línea, y el botón de confirmar exige las dos
partes completas. El carrito **no** pide datos del cliente — solo muestra una fila resumen
con un "Editar" que reabre la hoja.

---

## 1 · Estructura de la pantalla

```
┌─────────────────────────────┐
│ Header fijo          52 px  │  ← igual en todo el sistema
├─────────────────────────────┤
│ Subheader           107 px  │  ← título + chip de modo + búsqueda
├─────────────────────────────┤
│ Chips de categoría   60 px  │  ← scrollean con el contenido
│ Etiqueta de grupo    22 px  │
│ Filas de producto           │  ← zona de scroll
├─────────────────────────────┤
│ Barra de total       fija   │  ← reemplaza la tab bar
└─────────────────────────────┘
```

**Alturas: 290 px antes → 241 px ahora** hasta el primer producto.

| Zona | Antes | Ahora |
|---|---|---|
| Título / header | 56 px | 52 px |
| Subheader (orden, modo, búsqueda) | — | 107 px |
| Buscador suelto | 72 px | — (integrado al subheader) |
| Chips de categoría (con márgenes) | 76 px | 60 px |
| Etiqueta de grupo | — | 22 px |
| **Total antes del 1.º producto** | **290 px** | **241 px** |

### Header fijo (52 px)
Sin cambios respecto al resto del sistema — ver `handoff_header/README.md` si lo tienes:
☰ (44 px) · logo 30 px + "Cresly Pizzería" 13.5 px/800 y "Suc. Centro" 10.5 px/600
`#8a929c` · botón de tema ☾/☀ (44 px) · avatar 34 px con caret ▼.
Fondo `#fff`, borde inferior `1px solid #e6e8ec`, padding lateral `12px`, `gap:8px`.

### Subheader (107 px)
Fondo `#fafbfc`, borde inferior `1px solid #eef0f3`. Dos líneas:

**Fila de título** — `min-height:52px`, padding `8px 14px 6px`, `gap:10px`:
- Botón **‹ atrás** 38 × 38 px, radio `11px`, fondo `#fff`, borde `1px solid #e6e8ec`,
  glifo 15 px `#5b6673`. Sale del punto de venta.
- **Título** 17 px/800 `letter-spacing:-.02em` con ellipsis. Es "Nueva orden",
  "Nuevo pedido" (delivery) o la mesa ("Mesa 6 · Salón") cuando se entró desde Mesas.
- **Chip de modo** debajo del título: padding `2px 9px`, radio `999px`, 10.5 px/800,
  con caret ▼ de 7 px a `opacity:.7`. **Toca para abrir la hoja de modo.**
  - Servirse y Llevar: fondo `#14181d`, texto `#fff`.
  - Delivery: fondo `#fdecef`, texto `#a90d27`, borde `1px solid #f4d3d9` — es el modo con
    requisitos extra y conviene que se note.
- **Sub-línea** junto al chip: 11 px/600 `#8a929c`, con el dato relevante resaltado en
  `font-weight:800` y color (ver "El resaltado en color").
- Botón **⋯** 38 × 38 px, fondo `#fff`, borde `#e6e8ec`. Contiene comensales, descuento y
  descartar la orden. **Nunca la acción primaria.**

**Segunda línea — campo de búsqueda** — padding `0 14px 11px`:
caja padding `11px 13px`, radio `11px`, fondo `#fff`, borde `1px solid #e6e8ec`,
glifo ⌕ 13 px `#a8afb8`, placeholder "Buscar producto…" 13.5 px/500 `#a8afb8`.
- **Enfocado**: borde `1.5px solid #14181d`, texto `#14181d` 13.5 px/600, a la derecha el
  conteo "5 resultados" 11 px/700 `#8a929c` y una ✕ en círculo 20 px `#eef0f3`.
- Es campo real y no icono porque con 45 productos buscar es más rápido que filtrar. Es la
  única pantalla del sistema donde el buscador ocupa una línea completa.

### Chips de categoría
`display:flex; gap:8px; padding:0 14px; overflow-x:auto`. Cada chip `flex:0 0 auto`,
padding `9px 14px`, radio `999px`, 12.5 px/700, `white-space:nowrap`, con un **badge de
conteo** dentro: padding `1px 6px`, radio `999px`, 10.5 px/800.
- Activo: fondo `#14181d`, texto `#fff`, badge `rgba(255,255,255,.2)`.
- Inactivo: fondo `#fff`, borde `1px solid #dfe2e7`, texto `#5b6673`,
  badge `#eef0f3` con texto `#5b6673`.

Reemplazan las tarjetas de 76 px con icono del escritorio: el conteo cabe en el badge y se
ahorran 40 px, con dos categorías más a la vista. El último chip se corta por el borde de la
pantalla — es la señal de que hay más y se puede desplazar.

### Filas de producto
Etiqueta de grupo antes de cada bloque: 10.5 px/800 `letter-spacing:.1em` `#8a929c`
en mayúsculas (PIZZA, COMBO, ALITAS…).

Cada fila: `display:flex; align-items:center; gap:11px`, padding `11px 12px`,
radio `14px`, fondo `#fff`, borde `1px solid #e6e8ec`.
- Bloque de texto `flex:1; min-width:0`: nombre 14.5 px/700 `letter-spacing:-.01em`,
  descripción opcional 11.5 px/600 `#98a1ab` con ellipsis, y **precio 15 px/800
  `letter-spacing:-.02em` `#c8102e`**.
- Botón **⚙ de opciones** 38 × 38 px, radio `11px`, fondo `#fafbfc`,
  borde `1px solid #e6e8ec`, glifo 13 px `#5b6673`. Abre tamaños, extras y nota.
- Botón **＋** 44 × 44 px, radio `13px`, fondo `#14181d`, glifo 20 px/700 `#fff`,
  `line-height:1`.

**Con cantidad en el carrito**, la fila cambia: borde `1.5px solid #c8102e` +
`box-shadow:0 6px 14px rgba(200,16,46,.10)`, y el ⚙ se reemplaza por el stepper:
**−** 36 × 44 px (radio `11px`, borde `1px solid #dfe2e7`, glifo 18 px/700 `#5b6673`),
cantidad 15 px/800 con `min-width:24px` centrada, y el **＋** de 44 px.
Bajar a 0 devuelve la fila a su estado normal.

**Filas, no dos columnas**: las tarjetas de dos columnas parten el nombre en dos líneas y
dejan el ⚙ en 32 px. En filas caben 5 productos con precio y el ＋ de 44 px al borde
derecho — agregar con una mano, sin apuntar.

### Barra de total (fija abajo)
`position:fixed`, fondo `#fff`, borde superior `1px solid #e6e8ec`,
padding `12px 14px 20px` (usa `max(20px, env(safe-area-inset-bottom))`),
`box-shadow:0 -8px 22px rgba(20,24,29,.07)`.

Dentro, un botón de ancho completo: padding `13px 15px`, radio `14px`, `gap:12px`.
- Badge de cantidad: `min-width:30px; height:30px`, radio `9px`, 13.5 px/800,
  padding lateral `8px`.
- Etiqueta 11 px/800 `letter-spacing:.07em` y total 19 px/800
  `letter-spacing:-.025em` `line-height:1.1`.
- Glifo ⌃ 17 px a la derecha.

| Estado | Fondo | Texto | Etiqueta | Badge |
|---|---|---|---|---|
| Listo | `#c8102e` + `0 8px 18px rgba(200,16,46,.26)` | `#fff` | "VER PEDIDO" `rgba(255,255,255,.75)` | `rgba(255,255,255,.22)` / `#fff` |
| Faltan datos | `#e9ebef`, sin sombra | `#5b6673` | "FALTA MESA" / "FALTAN DATOS DE ENTREGA" en `#c8102e` | `#fff` / `#5b6673` |

**Reemplaza la tab bar** mientras se arma una orden: no se navega entre módulos en medio de
una venta. Se sale con el ‹ del subheader. **El ＋ flotante del diseño anterior desaparece**:
ya estás dentro de "nueva orden", era redundante y tapaba esta barra.

---

## 2 · La hoja de modo

Se abre al tocar el chip del subheader, y automáticamente al entrar en una orden nueva.
Hoja inferior (`bottom sheet`): fondo `#fff`, radio `22px 22px 0 0`,
padding `14px 16px 20px`, columna con `gap:14px`, fondo de overlay
`rgba(20,24,29,.42)`. Arriba, un asa de 38 × 4 px radio `999px` `#dfe2e7` centrada.

- Título "Modo de la orden" 18 px/800 `letter-spacing:-.02em`.
- **Selector de los tres modos**: fila con `gap:7px`, cada botón `flex:1`,
  padding `12px 6px`, radio `12px`, 13 px.
  Activo Servirse/Llevar: fondo `#14181d`, texto `#fff`, peso 800.
  Activo Delivery: fondo `#c8102e`, texto `#fff`, peso 800.
  Inactivo: fondo `#fff`, borde `1px solid #dfe2e7`, texto `#5b6673`, peso 700.
- Divisor `1px #eef0f3`.
- **Debajo, solo los campos del modo elegido.**
- Botón de cierre: ancho completo, padding `16px`, radio `13px`, fondo `#c8102e`,
  texto `#fff` 15 px/800, `box-shadow:0 8px 20px rgba(200,16,46,.26)`.
  Su texto confirma lo elegido: "Continuar · Mesa 6", "Continuar · envío $2.50".

### Qué exige cada modo

| Modo | Campos | Obligatorio |
|---|---|---|
| **Servirse** | Mesa + nombre de cliente | Las dos |
| **Llevar** | Nombre de cliente | Sí (o "Sin nombre") |
| **Delivery** | Teléfono, nombre, dirección y valor de la moto | Las cuatro |

### Servirse · mesa + cliente
1. **Etiqueta "MESA"** 11 px/800 `letter-spacing:.09em` `#8a929c`, y a la derecha
   "8 libres" 11 px/700 `#1c7a4a`.
2. **Teclado de mesas**: `grid-template-columns:repeat(5,1fr); gap:7px`, celdas de 46 px de
   alto, radio `11px`, número 15 px/800.
   - Libre: fondo `#fff`, borde `1px solid #dfe2e7`.
   - **Ocupada**: fondo `#fef6f7`, borde `1px solid #f4d3d9`, número `#a90d27`,
     **no tocable**.
   - Seleccionada: fondo `#14181d`, borde `1.5px solid #14181d`, número `#fff`.
   - Última celda "Ver" 13 px/700 `#5b6673` → abre el mapa completo de mesas.
   Se eligió teclado y no desplegable: es el gesto más rápido y muestra de una vez qué está
   ocupado.
3. **Campo "CLIENTE"**: padding `13px`, radio `11px`, borde `1px solid #dfe2e7`,
   texto 14 px/600.

### Llevar · solo cliente
1. **Campo "NOMBRE DEL CLIENTE"** enfocado al abrir (teclado ya arriba):
   padding `14px 13px`, radio `11px`, borde `1.5px solid #14181d`, texto 15 px/700,
   con cursor `2 × 19px` `#c8102e`.
   Ayuda debajo: "Se imprime en el ticket para llamar al cliente." 11.5 px/600 `#98a1ab`.
2. **Chips "RECIENTES"**: padding `9px 13px`, radio `999px`, 12.5 px/700.
   Nombres previos con fondo `#fff` y borde `#dfe2e7` `#4a545f`;
   **"Sin nombre"** con fondo `#f4f5f7` y texto `#8a929c` — permite salir rápido cuando el
   cliente no lo da. Los recientes evitan teclear en la mayoría de los casos.

### Delivery · teléfono, nombre, dirección, envío
La hoja crece hasta `top:44px` con scroll interno. Los campos van en este orden:
1. **"TELÉFONO"**: padding `13px`, radio `11px`, borde `1px solid #dfe2e7`,
   **16 px/700 `letter-spacing:.03em`** (más grande que el resto: se dicta por llamada),
   `inputmode="tel"`. Si el número existe, a la derecha "✓ conocido" 11 px/800 `#1c7a4a`.
2. **Tarjeta de cliente conocido** (solo si el teléfono existe): fondo `#f4fbf7`,
   borde `1px solid #cfeadb`, radio `11px`, padding `11px 12px`. Punto 8 px `#23a05f`,
   "Ana R. · Col. Miramonte" 12.5 px/800 `#1c7a4a`, la referencia 11 px/600 `#5f8a72`,
   y "Usar" 11 px/800 `#1c7a4a`. **Al tocarla rellena nombre y dirección y desaparece.**
3. **"NOMBRE"**: padding `13px`, radio `11px`, borde `#dfe2e7`, 14 px/600.
4. **"DIRECCIÓN Y REFERENCIA"**: textarea, padding `13px`, radio `11px`, 13.5 px/600,
   `line-height:1.45`.
5. **"VALOR DE LA MOTO"** con la nota "se suma al total" 11 px/700 `#98a1ab` a la derecha:
   tres botones `flex:1` ($2.00 · $2.50 · $3.00) más uno de 52 px "Otro" para monto libre.
   Padding `12px 6px`, radio `11px`, 14 px/800. Activo fondo `#14181d` texto `#fff`;
   inactivo fondo `#fff` borde `#dfe2e7` texto `#5b6673`.

**El teléfono va primero porque es la llave**: resuelto ese campo, los otros tres se
rellenan de un toque en la mayoría de los pedidos repetidos.

---

## 3 · El subheader como recibo

Sale de la hoja y queda a la vista mientras se agregan productos. Cinco estados:

| Estado | Título | Chip | Sub-línea (resaltado) | Barra de total |
|---|---|---|---|---|
| Servirse completo | Mesa 6 · Salón | Servirse (oscuro) | #001 · **Familia Rivas** (gris) | Rojo · "VER PEDIDO" |
| Servirse sin mesa | Nueva orden | Servirse (oscuro) | #001 · **Falta mesa** (rojo) y cliente | Gris · "FALTA MESA" |
| Llevar completo | Nueva orden | Llevar (oscuro) | #001 · **Ana R.** (gris) · mesero1 | Rojo · "VER PEDIDO" |
| Delivery completo | Nuevo pedido | Delivery (rojo) | Ana R. · Miramonte · **envío $2.50** | Rojo · "VER PEDIDO" |
| Delivery incompleto | Nuevo pedido | Delivery (rojo) | 7433-7781 · **falta dirección** (rojo) | Gris · "FALTAN DATOS DE ENTREGA" |

### El resaltado en color
La sub-línea no es texto plano: **el dato que importa se resalta** con `font-weight:800` y
color propio, sobre el resto en `#8a929c`. Es el mismo sistema del resto de la app.

| Color | Significado |
|---|---|
| `#c8102e` rojo | falta algo obligatorio ("Falta mesa", "falta dirección") |
| `#1c7a4a` verde | disponibilidad ("8 libres") |
| `#4a545f` gris oscuro | contexto resuelto (nombre del cliente, monto del envío) |

Marca el fragmento resaltado desde el backend (`sub_pre` / `sub_hi` / `sub_hi_tono` /
`sub_post`), no partas la cadena en el template.

En Delivery completo se resumen los cuatro datos como "nombre · zona · envío": el valor de la
moto va resaltado porque es el que se discute con el cliente.

---

## 4 · El carrito

Hoja inferior, radio `22px 22px 0 0`, padding `14px 16px 20px`, `gap:14px`,
`max-height:calc(100% - 74px)` (el header queda visible detrás, atenuado).

- **Cabecera**: "Pedido" 19 px/800 `letter-spacing:-.025em`, pill "#001"
  (padding `3px 9px`, radio `999px`, fondo `#eef0f3`, texto `#4a545f` 11.5 px/800),
  **chip de modo** con su caret (mismo estilo del subheader) y "Vaciar" 12.5 px/700
  `#c8102e` a la derecha.
- **Fila resumen del cliente**: lo capturado en la hoja, con un "Editar" que **reabre la
  hoja de modo**. El carrito no tiene campos de captura.
- **Líneas del pedido**: padding `13px 0`, borde inferior `1px solid #f2f4f6`.
  Nombre 14 px/700 `line-height:1.35`, modificadores 11.5 px/700 `#8a5800`
  (los extras del producto van en ámbar para distinguirlos del nombre),
  y a la derecha el importe 16 px/800.
  Debajo: "Editar" 12 px/700 `#5b6673` en caja `#f4f5f7` radio `9px`, y el stepper
  **− / cantidad / ＋** con botones de 40 px, radio `11px`, borde `1px solid #dfe2e7`,
  cantidad 16 px/800 `min-width:30px`.
- **Totales**: Subtotal e IVA 15 % en 12.5 px (`#767e88` etiqueta / `#14181d` 700 valor);
  en Delivery se añade "Costo de envío". Total separado por `border-top:1px solid #e6e8ec`,
  `padding-top:9px`: etiqueta 14 px/800 y monto **26 px/800 `letter-spacing:-.03em`**.
- **Botón "Confirmar e Imprimir"**: ancho completo, padding `16px`, radio `13px`,
  fondo `#c8102e`, texto `#fff` 15 px/800, glifo ⎙ antes del texto,
  `box-shadow:0 8px 20px rgba(200,16,46,.26)`.
  Deshabilitado: fondo `#e9ebef`, texto `#a8afb8`, sin sombra.
- Debajo, línea de ayuda 11.5 px/600 `#98a1ab` centrada que dice qué falta o qué va a pasar:
  | Situación | Texto |
  |---|---|
  | Carrito vacío | "Agrega al menos un producto" |
  | Servirse sin mesa | "Falta asignar la mesa" |
  | Delivery incompleto | "Falta teléfono y dirección de entrega" |
  | Delivery listo | "Imprime comanda y ticket con la dirección" |
  | Servirse / Llevar listo | "Imprime la comanda para cocina" |

---

## Interactions & Behavior

- **Tap en ＋** agrega 1 y convierte la fila a su estado con stepper. Bajar a 0 la revierte.
- **Tap en ⚙** abre tamaños, extras y nota del producto.
- **Tap en el chip de modo** (subheader o carrito) abre la hoja de modo.
- **Se puede agregar productos sin completar los datos.** Si el cliente empieza a pedir antes
  de darlos, se cierra la hoja y se sigue. Lo que falta queda en rojo en el subheader.
- **La barra de total con datos pendientes abre la hoja de modo en el campo que falta**, no el
  carrito. Es el atajo para resolver el bloqueo.
- **Cambiar de modo no borra nada**: de Servirse a Llevar la mesa se libera pero el nombre
  queda; de Llevar a Delivery el nombre se conserva y solo se piden teléfono, dirección y
  envío. Los productos nunca se tocan.
- **Validación de confirmar**: al menos un producto **y** los campos obligatorios del modo
  (ver tabla). Servirse exige mesa y cliente; Llevar cliente (o "Sin nombre"); Delivery los
  cuatro.
- **Confirmar e Imprimir** cierra la orden, imprime comanda (y ticket con dirección en
  delivery) y limpia el carrito con número de orden nuevo.
- Transiciones `.12s ease`. Las hojas entran deslizando desde abajo.
- **Táctil**: ＋ y celdas de mesa 44–46 px; ⚙, ‹, ⋯ y steppers 38–40 px (aceptable, son
  secundarios y están rodeados de espacio). Nada por debajo de 38 px.

## State Management

El carrito y los datos del modo deben vivir en la **sesión** o en un modelo `Orden` en
estado borrador, para no perderse al navegar.

```
orden: {
  numero,
  modo: 'servirse' | 'llevar' | 'delivery',
  mesa_id:   null | int,          # servirse
  cliente:   str,                 # servirse, llevar, delivery
  telefono:  str,                 # delivery
  direccion: str,                 # delivery
  costo_envio: Decimal,           # delivery — se suma al total
  lineas: [ { producto_id, nombre, modificadores, precio_unit, cantidad } ]
}
categorias: [ { nombre, slug, conteo } ]
productos:  [ { id, categoria, nombre, descripcion, precio } ]
mesas:      [ { numero, estado } ]   # para el teclado de servirse
clientes_recientes: [ str ]          # para los chips de llevar
tasa_iva: 15
```

- Subtotal, IVA, envío y total se calculan **en la vista o en el modelo**, no en el template.
- `cliente_conocido(telefono)` busca en pedidos anteriores; devuelve
  `{ nombre, direccion, referencia }` o `null`.
- `campos_faltantes(orden)` devuelve la lista de campos obligatorios pendientes según el
  modo. De ahí salen el resaltado rojo del subheader, la etiqueta de la barra de total, la
  línea de ayuda del carrito y el estado del botón de confirmar — **una sola fuente de
  verdad**, no cuatro comprobaciones distintas.
- Las mutaciones (agregar, +, −, vaciar, fijar modo/datos) son endpoints POST que devuelven
  el parcial afectado (HTMX encaja bien) para no recargar la pantalla.

---

## Design Tokens

**Colores**
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | texto principal, ＋, chip activo, mesa seleccionada |
| text-2 | `#4a545f` | resaltado neutro, pill de nº de orden |
| text-3 | `#5b6673` | glifos secundarios, chips inactivos, "Editar" |
| muted | `#767e88` | etiquetas de totales |
| muted-2 | `#8a929c` | etiquetas de sección, sub-línea |
| muted-3 | `#98a1ab` | descripciones, línea de ayuda |
| faint | `#a8afb8` / `#b6bcc4` | placeholders, botón deshabilitado |
| surface | `#ffffff` | tarjetas, hojas, header, barra de total |
| page | `#f4f5f7` | fondo de pantalla, caja de "Editar" |
| surface-2 | `#fafbfc` | subheader, botón ⚙ |
| segmented-bg | `#e9ebef` | barra de total bloqueada |
| border | `#e6e8ec` | bordes de tarjeta y header |
| border-soft | `#eef0f3` / `#f2f4f6` | divisores |
| border-input | `#dfe2e7` | bordes de control, asa de la hoja |
| brand | `#c8102e` | precios, acción primaria, barra de total, "Vaciar" |
| brand-dark | `#a90d27` | texto sobre tinte rojo, mesa ocupada |
| brand-tint | `#fdecef` bg · `#f4d3d9` borde | chip de delivery, mesa ocupada |
| brand-tint-2 | `#fef6f7` | fondo de celda de mesa ocupada |
| green | `#23a05f` | punto de cliente conocido |
| green-dark | `#1c7a4a` | "8 libres", "✓ conocido", texto de la tarjeta verde |
| green-mid | `#5f8a72` | referencia de dirección sugerida |
| green-tint | `#f4fbf7` bg · `#cfeadb` borde | tarjeta de cliente conocido |
| amber-dark | `#8a5800` | modificadores de producto en el carrito |
| overlay | `rgba(20,24,29,.42)` | fondo detrás de las hojas |

**Tipografía:** Plus Jakarta Sans (400/500/600/700/800), fallback Helvetica, Arial,
sans-serif. `font-feature-settings:'tnum' 1` en el contenedor raíz para que precios y
totales queden alineados.
Escala usada: 8, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14, 14.5, 15, 16, 17, 18, 19, 20, 26 px.
`letter-spacing` negativo en cifras y títulos (−.01 a −.03em), positivo en etiquetas
mayúsculas (.07 a .1em) y en el teléfono (.03em).

**Espaciado:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 20 px.

**Radios:** 8, 9, 11, 12, 13, 14, 22, 999px.

**Sombras:**
- barra de total / botón primario `0 8px 18px rgba(200,16,46,.26)` y
  `0 8px 20px rgba(200,16,46,.26)`
- fila de producto con cantidad `0 6px 14px rgba(200,16,46,.10)`
- barra de total (elevación sobre el contenido) `0 -8px 22px rgba(20,24,29,.07)`

---

## Notas de implementación (Django + Bootstrap 5)
- Variables Sass: `$primary: #c8102e`, `$body-bg: #f4f5f7`, `$body-color: #14181d`,
  `$border-color: #e6e8ec`, familia Plus Jakarta Sans. Si no compilas Sass, un `pos-movil.css`
  con las variables CSS de la tabla basta.
- Templates sugeridos:
  `movil/pos.html` (extiende `base_movil.html`) y parciales
  `_subheader_pos.html`, `_chips_categoria.html`, `_producto_fila.html`,
  `_barra_total.html`, `_hoja_modo.html`, `_hoja_modo_servirse.html`,
  `_hoja_modo_llevar.html`, `_hoja_modo_delivery.html`, `_hoja_carrito.html`.
- Las hojas inferiores: usa el **offcanvas de Bootstrap con `placement="bottom"`**, o
  `<dialog>` con animación propia. El overlay es `rgba(20,24,29,.42)`.
- Chips con scroll horizontal: `overflow-x:auto; scrollbar-width:none` en el contenedor y
  `flex:0 0 auto` en cada chip. **No** los envuelvas ni los recortes con ellipsis: el corte
  por el borde de la pantalla es intencional.
- El teclado de mesas es CSS Grid directo
  (`grid-template-columns:repeat(5,1fr)`), no las 12 columnas de Bootstrap.
- El estado de cada mesa y el tono de cada resaltado salen como clase desde el backend
  (`class="mesa mesa--ocupada"`, `class="hl hl--rojo"`); los colores viven en CSS.
- Header y subheader son sticky apilados: `top:0` el header y `top:52px` el subheader.
- `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`
  y `env(safe-area-inset-bottom)` en la barra de total.
- El campo de nombre en Llevar debe recibir foco al abrir la hoja (`autofocus`), y el de
  teléfono en Delivery con `inputmode="tel"`.
- **El catálogo del prototipo está incompleto**: los conteos de categoría son los reales
  (45 / 5 / 13 / 5 …) pero solo están cargados los productos visibles. Reemplázalos por el
  catálogo real desde la base de datos.
- El IVA está al 15 %. Si es configurable, lee la tasa de la configuración del negocio.
- Los nombres, teléfonos y direcciones son **datos de ejemplo**. Si un campo no existe en tu
  modelo, omite ese fragmento en vez de inventarlo.

## Assets
Ninguno. El prototipo usa glifos de texto como marcadores:
`☰ ☾ ☀ ▼ ‹ ⌕ ⋯ ⚙ ⎙ ＋ − ⌃ ✓ ✕ ◕`. Reemplázalos por el set de iconos del proyecto —
Bootstrap Icons encaja: `list`, `moon`, `sun`, `chevron-down`, `chevron-left`,
`search`, `three-dots`, `sliders`, `printer`, `plus-lg`, `dash-lg`, `chevron-up`,
`check-lg`, `x-lg`, `person`.
**No hay imágenes de producto.** Si más adelante se añaden, la fila admite una miniatura
cuadrada de 48 px a la izquierda sin cambiar el resto.

## Files
- `Punto de venta movil - adaptado.dc.html` — catálogo y carrito, con la tabla de alturas
- `Punto de venta movil - modos.dc.html` — flujo, las tres hojas de modo, estados del
  subheader y reglas
- `Punto de venta movil - header.dc.html` — la barra superior y sus seis estados
- `Punto de venta.dc.html` — la versión de escritorio, como referencia
