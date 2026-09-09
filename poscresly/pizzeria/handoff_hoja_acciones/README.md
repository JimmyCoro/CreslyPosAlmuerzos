# Handoff: Hoja de acciones (⋯) · Detalle de orden · Cresly POS móvil

## Overview
Un cambio puntual en la pantalla **Detalle de orden**: sustituir los tres iconos sueltos de
la esquina superior derecha por **un botón ⋯ en el subheader** que abre una hoja inferior con
las acciones de la orden, escritas y agrupadas.

Hoy esos iconos —dividir cuenta, imprimir y una ✕ roja— no dicen qué hacen, y la ✕ parece
cerrar la pantalla cuando en realidad **anula la venta**. Con la hoja, cada acción tiene
nombre, un subtítulo que dice el valor actual o qué produce, y anular queda al final,
separado y con confirmación.

**Alcance de esta tarea:** solo el subheader de Detalle de orden y la hoja que abre.
No toques el resto de la pantalla (tarjeta de entrega, lista de platillos, barra de acciones
inferior, tab bar).

## About the Design File
`Hoja acciones orden.dc.html` es una **referencia de diseño en HTML**: un prototipo del look
previsto, no código de producción. Los estilos están inline.

Contiene:
- La **hoja abierta** sobre Detalle de orden, con sus tres grupos.
- La **hoja de confirmación de anulación**.
- Las reglas de diseño y una tabla con el contenido del ⋯ en cada pantalla del sistema.

La tarea es recrearlo en **Django (templates) + Bootstrap 5**, siguiendo los patrones del
proyecto.

## Fidelity
**Alta fidelidad.** Colores, tipografía, espaciados y radios son finales.

---

## 1 · El botón en el subheader

En el subheader de Detalle de orden, la esquina derecha pasa a tener **dos botones** de
38 × 38 px, radio `11px`, fondo `#fff`, borde `1px solid #e6e8ec`, glifo 15 px `#5b6673`,
con `gap:6px`:

| Botón | Glifo | Por qué queda visible |
|---|---|---|
| Dividir cuenta | ⚯ | En una mesa con varios comensales se usa en cada cobro |
| Más acciones | ⋯ | Abre la hoja |

**Se elimina la ✕ roja de la barra.** Nunca una acción destructiva como icono suelto.

---

## 2 · La hoja de acciones

Hoja inferior (`bottom sheet`): fondo `#fff`, radio `22px 22px 0 0`,
padding `14px 16px 20px`, columna con `gap:14px`, overlay `rgba(20,24,29,.42)`.
Arriba, asa de 38 × 4 px radio `999px` `#dfe2e7` centrada. Se cierra deslizando o tocando
el overlay — **sin botón ✕**, como el resto de las hojas del sistema.

### Cabecera
`display:flex; align-items:center; gap:10px`:
- Bloque `flex:1; min-width:0`: "Pedido #002" 17 px/800 `letter-spacing:-.02em`, y debajo
  "Mesa 7 · 5 platillos · $70.75" 11.5 px/600 `#8a929c`.
- **Pill de estado de la orden** a la derecha: padding `3px 9px`, radio `999px`,
  10.5 px/800, con punto de 5 px. Usa los mismos colores de estado del sistema
  (en cocina: `#fdf3e2` / `#8a5800` / punto `#d99000`).

Confirma sobre qué orden se va a actuar antes de tocar nada.

### Grupos y filas

Cada grupo: encabezado 10.5 px/800 `letter-spacing:.09em` `#8a929c` y las filas debajo con
`gap:8px`.

Cada fila: `display:flex; align-items:center; gap:11px`, padding `13px 14px`,
radio `12px`, fondo `#fff`, borde `1px solid #dfe2e7` (alto resultante ≈ 46 px):
- glifo 14 px `#5b6673` en una caja de 18 px centrada, `flex:0 0 auto`;
- bloque `flex:1; min-width:0`: etiqueta 13.5 px/700 y **sub-línea 11 px/600 `#98a1ab`**;
- chevron › 14 px `#c3c8ce`, `flex:0 0 auto`.

**Sin círculos de color en los iconos**: competían con el estado del platillo por la
atención.

#### Grupo 1 — IMPRIMIR
| Acción | Glifo | Sub-línea |
|---|---|---|
| Precuenta | ▤ | "Para que el cliente revise antes de pagar" |
| Reimprimir comanda | ⎙ | "Copia completa para cocina" |

#### Grupo 2 — LA ORDEN
| Acción | Glifo | Sub-línea |
|---|---|---|
| Cambiar de mesa | ▦ | El valor actual: "Actualmente Mesa 7 · Centro" |
| Comensales | ◕ | El valor actual: "4 personas" |
| Aplicar descuento | % | "Porcentaje o monto fijo" |
| Dividir cuenta | ⚯ | "Reparte los platillos entre personas" |

La sub-línea de "Cambiar de mesa" y "Comensales" **muestra el valor actual**, no una
descripción: así se consulta sin entrar.

#### Divisor
`1px solid #eef0f3` entre el grupo 2 y el 3.

#### Grupo 3 — ZONA DE RIESGO
Encabezado en **`#a90d27`** en vez de `#8a929c`.

| Acción | Glifo | Estilo de la fila |
|---|---|---|
| Anular pedido | ✕ | borde `1px solid #f4d3d9`, glifo y etiqueta `#c8102e`, sub-línea "Pide confirmación y motivo" en `#a9707c`, chevron `#f4d3d9` |

### Variantes por tipo de orden

**Servirse**: la hoja completa como se describe arriba.

**Llevar**: se omiten "Cambiar de mesa" y "Comensales". La cabecera muestra
"Llevar · Ana R. · 4 platillos · $18.40".

**Delivery**: cambia más. Mesa y comensales no existen, y en su lugar entra un grupo
**ENTREGA al principio de la hoja** — es lo que de verdad se hace con un pedido en ruta:

Grupo 1 — ENTREGA
| Acción | Glifo | Sub-línea |
|---|---|---|
| Llamar al cliente | ✆ | El número: "0991073962" — abre `tel:` |
| Editar dirección | ⌖ | La dirección actual, con ellipsis |
| Cambiar valor del envío | ⇢ | "$2.50 · se suma al total" |

Grupo 2 — IMPRIMIR
| Acción | Glifo | Sub-línea |
|---|---|---|
| **Ticket con dirección** | ▤ | "Va con el motorista" — reemplaza a "Precuenta" |
| Reimprimir comanda | ⎙ | "Copia completa para cocina" |

Grupo 3 — LA ORDEN: solo "Aplicar descuento". Sin mesa, sin comensales, y **sin dividir
cuenta** (un delivery se cobra completo a una persona).

Grupo 4 — ZONA DE RIESGO: **dos filas**, ambas con el estilo rojo.
| Acción | Glifo | Sub-línea |
|---|---|---|
| Marcar como no entregado | ↺ | "El pedido salió pero volvió sin entregar" |
| Anular pedido | ✕ | "Pide confirmación y motivo" |

"Marcar como no entregado" devuelve el pedido sin cobrar y libera al motorista **sin anular
la venta** — el pedido queda para reintentar o resolver. Es distinto de anular y va arriba de
él. También pide motivo: *Nadie contestó · Dirección incorrecta · Cliente rechazó · Otro*.

La cabecera de la hoja muestra "Delivery · Ana R. · 4 platillos · $44.90" y el pill del
estado de reparto (en cocina / listo / en ruta / entregado) con sus colores del módulo
Delivery.

**Orden ya pagada** (cualquier tipo): se omiten Descuento y Dividir cuenta; "Anular pedido"
se reemplaza por "Anular cobro", que exige permiso de administrador.

---

## 3 · La confirmación de anulación

Segunda hoja, encima de la primera. Overlay más oscuro: `rgba(20,24,29,.52)`.
Fondo `#fff`, radio `22px 22px 0 0`, padding `14px 16px 20px`, `gap:15px`.

1. **Cabecera**: cuadro de 38 px radio `12px` fondo `#fdecef` con glifo ✕ 17 px `#c8102e`;
   al lado, título "Anular pedido #002" 17 px/800 `line-height:1.25` y el cuerpo
   12.5 px/600 `#4a545f` `line-height:1.45` `text-wrap:pretty`:
   **"Se cancelan los 5 platillos por $70.75 y la Mesa 7 queda libre. Esta acción no se puede
   deshacer."** — el texto debe nombrar qué se pierde y qué se libera, con las cifras reales.
2. **Aviso de cocina** (solo si hay platillos en estado cocinando o listo):
   caja `#fdf3e2`, borde `1px solid #f2e0bd`, radio `12px`, padding `11px 13px`,
   glifo ⚠ 13 px `#8a5800` y el texto 11.5 px/700 `#8a5800`:
   "2 platillos ya están cocinando. Avisa a cocina antes de anular."
3. **MOTIVO** (obligatorio): chips padding `9px 13px`, radio `999px`, 12.5 px/700.
   Activo fondo `#14181d` texto `#fff`; inactivo fondo `#fff` borde `1px solid #dfe2e7`
   texto `#5b6673`. Opciones: **Cliente canceló · Error al tomar · Sin producto · Otro**
   ("Otro" abre un campo de texto libre).
4. **Botones**, en columna con `gap:8px`:
   - "Sí, anular pedido": padding `16px`, radio `13px`, fondo `#c8102e`, texto `#fff`
     15 px/800, glifo ✕ antes, `box-shadow:0 8px 20px rgba(200,16,46,.26)`.
     **Deshabilitado hasta elegir motivo** (fondo `#e9ebef`, texto `#a8afb8`, sin sombra).
   - "Volver": padding `15px`, radio `13px`, fondo `#fff`, borde `1px solid #dfe2e7`,
     texto 14 px/700 `#5b6673`.

**El botón destructivo va arriba de "Volver"**, no abajo: así el pulgar no lo alcanza por
inercia al cerrar la hoja.

---

## 4 · Contenido del ⋯ en el resto del sistema

Para que quede consistente cuando se implementen las otras pantallas:

| Pantalla | Acciones |
|---|---|
| **Detalle · servirse** | Precuenta · Reimprimir comanda · Cambiar de mesa · Comensales · Descuento · Dividir cuenta · Anular |
| **Detalle · llevar** | Precuenta · Reimprimir comanda · Descuento · Dividir cuenta · Anular |
| **Detalle · delivery** | Llamar · Editar dirección · Cambiar valor del envío · Ticket con dirección · Reimprimir comanda · Descuento · No entregado · Anular |
| Cobrar | Precuenta · Reimprimir comanda · Descuento · Dividir cuenta · Anular |
| Punto de venta | Comensales · Descuento · Descartar la orden |
| Cobrar persona | Precuenta de esta parte · Volver al reparto |

**Regla común:** la acción destructiva (anular / descartar) va siempre al final, en su propio
grupo bajo "ZONA DE RIESGO", y siempre con confirmación. Nunca como icono en la barra.

Pantallas **sin** ⋯: Inicio, Mesas, Órdenes y Delivery — no hay una orden concreta sobre la
que actuar.

---

## Interactions & Behavior
- **Tap en ⋯** abre la hoja. Tap en el overlay, deslizar hacia abajo o el botón físico de
  atrás la cierran.
- **Tap en una acción** cierra la hoja y ejecuta (imprimir) o navega (cambiar de mesa,
  dividir cuenta) o abre su propia hoja (comensales, descuento, anular).
- **Imprimir** muestra un toast de confirmación ("Precuenta enviada a la impresora") en vez
  de dejar la hoja abierta. Si la impresora no responde, aparece la cinta de alerta del
  sistema bajo el header.
- **Anular** solo procede con motivo elegido. Registra usuario, hora y motivo en el historial
  de la orden.
- Las acciones no disponibles según el estado de la orden **se omiten**, no se muestran
  deshabilitadas.
- Transiciones `.12s ease`; las hojas entran deslizando desde abajo.
- **Táctil**: filas de 46 px, botones de la confirmación de 50–52 px. Nada por debajo
  de 38 px.

## Datos que necesita la hoja
```
orden: { numero, tipo, estado, mesa: {numero, zona}, comensales,
         n_platillos, total,
         lineas_en_cocina  # int, para el aviso de anulación
       }
entrega: null | { telefono, direccion, costo_envio }   # solo delivery
acciones_disponibles: [str]      # calculado en la vista según estado y tipo
motivos_anulacion: [str]
motivos_no_entrega: [str]        # solo delivery
```
`acciones_disponibles` se calcula **en la vista**, no con `{% if %}` repartidos por el
template: una sola función decide qué se muestra según estado y tipo de orden.

## Design Tokens
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | títulos, chip de motivo activo |
| text-2 | `#4a545f` | cuerpo de la confirmación |
| text-3 | `#5b6673` | glifos, etiquetas de chips inactivos, "Volver" |
| muted-2 | `#8a929c` | encabezados de grupo, cabecera de la hoja |
| muted-3 | `#98a1ab` | sub-líneas de las filas |
| faint | `#a8afb8` / `#c3c8ce` | botón deshabilitado, chevrons |
| surface | `#ffffff` | hoja, filas |
| surface-2 | `#fafbfc` | subheader |
| border | `#e6e8ec` | borde de los botones del subheader |
| border-soft | `#eef0f3` | divisor entre grupos |
| border-input | `#dfe2e7` | bordes de fila, asa, "Volver" |
| brand | `#c8102e` | anular, botón destructivo |
| brand-dark | `#a90d27` | encabezado "ZONA DE RIESGO" |
| brand-tint | `#fdecef` bg · `#f4d3d9` borde | fila de anular, cuadro de la confirmación |
| brand-muted | `#a9707c` | sub-línea de anular |
| amber-dark | `#8a5800` | aviso de cocina |
| amber-tint | `#fdf3e2` bg · `#f2e0bd` borde | aviso de cocina |
| overlay | `rgba(20,24,29,.42)` / `.52` | hoja / confirmación |

**Tipografía:** Plus Jakarta Sans (600/700/800), fallback Helvetica, Arial, sans-serif.
Escala: 10.5, 11, 11.5, 12.5, 13, 13.5, 14, 15, 17 px.
`letter-spacing` −.02em en títulos, .09em en encabezados de grupo.

**Espaciado:** 1, 2, 3, 5, 6, 7, 8, 10, 11, 13, 14, 15, 16, 20 px.
**Radios:** 11, 12, 13, 22, 999px.
**Sombra:** botón destructivo `0 8px 20px rgba(200,16,46,.26)`.

## Notas de implementación (Django + Bootstrap 5)
- Usa el **offcanvas de Bootstrap con `placement="bottom"`** para ambas hojas, o `<dialog>`
  con animación propia. La confirmación es un segundo offcanvas encima, con overlay más
  oscuro.
- Templates sugeridos: parciales `_hoja_acciones_orden.html` y
  `_hoja_confirmar_anulacion.html`, más `_fila_accion.html` (glifo, etiqueta, sub-línea,
  chevron) reutilizable por las cuatro pantallas.
- Un solo `_hoja_acciones_orden.html` parametrizado sirve para Detalle de orden, Cobrar y
  Punto de venta: cambia la lista de acciones, no el markup.
- Los glifos del prototipo son marcadores. Reemplázalos por Bootstrap Icons:
  `three-dots`, `people` (dividir), `receipt` (precuenta), `printer`,
  `grid-3x3-gap` (mesa), `person` (comensales), `percent`, `x-lg`,
  `telephone`, `geo-alt` (dirección), `scooter` (envío), `arrow-counterclockwise` (no entregado),
  `exclamation-triangle`, `chevron-right`.
- Los datos del prototipo son **de ejemplo**. Si un campo no existe en tu modelo (comensales,
  motivos), omite esa fila en vez de inventarla.

## Files
- `Hoja acciones orden.dc.html` — la hoja (servirse), la **variante delivery**, la
  confirmación de anulación, las reglas y la tabla del ⋯ por pantalla.
