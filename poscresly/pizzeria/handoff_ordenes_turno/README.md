# Órdenes del turno — auditoría de caja

Pantalla de drill-down desde **Caja**, al lado de Movimientos. Lista las órdenes **pagadas del
turno abierto**, agrupadas por método de pago con subtotal por grupo, para responder una sola
pregunta: *si la caja no cuadra, ¿de dónde salió la diferencia?*

No propone el cuadre ni concilia contra el conteo físico. Lista y suma.

> **Los datos del prototipo son de ejemplo.** Montos, nombres, horas y folios son inventados
> para mostrar los estados. Nada de esto se copia a producción.

---

## 1. Por qué vive en Caja y no en Órdenes

Son dos preguntas distintas sobre el mismo dato:

| | Órdenes → filtro «Cerradas» | Caja → Órdenes del turno |
|---|---|---|
| Pregunta | ¿la mesa 6 ya pagó? | ¿por qué no cuadra? |
| Frecuencia | ~20 veces por turno | 1 vez, al cerrar |
| Orden | por hora descendente | por método de pago |
| Totales | ninguno | subtotal por grupo + total |

Forzarlas en una sola vista deja a las dos a medias. Esta entrega cubre **solo la segunda**.
El filtro «Cerradas» de Órdenes queda pendiente y es independiente.

---

## 2. Estructura

```
Caja
└── Órdenes del turno          ← esta pantalla
    ├── grupo EFECTIVO         ← subtotal + filas
    │   └── fila               ← toca para desplegar el detalle
    │       └── ⋯ hoja de acciones
    │           └── Corregir método de pago  ← hoja con motivo obligatorio
    ├── grupo TARJETA
    ├── grupo TRANSFERENCIA
    ├── grupo MIXTO
    └── bloque de totales
```

Pantallas del archivo de diseño (`Ordenes del turno.dc.html`, canvas mode):

| Id | Qué muestra |
|---|---|
| `2A` | **Fila desplegable, interactiva.** Toca cualquier fila para abrir/cerrar. |
| `1A` | Lista completa, grupo efectivo, con la fila EDITADA y el pie de mixtas/retiros |
| `1B` | Cola de la lista: tarjeta, transferencia, mixto y bloque de totales |
| `1C` | Hoja de acciones del ⋯ |
| `1D` | Hoja «Corregir método de pago» con el botón bloqueado |
| `1E` | La fila de entrada dentro de Caja |

`1C` todavía muestra «Ver detalle» en la hoja. **Se elimina**: el turno 2 lo reemplazó por el
acordeón. La hoja queda con una sola acción. Ver §5.

---

## 3. Medidas exactas

### Header y subheader
Sin cambios respecto a `handoff_header`. Se reutilizan tal cual.

- Header 52 px: ☰ 44×44 r12 · logo 30×30 r9 `#c8102e` · marca 13.5px/800/−.015em ·
  sub 10.5px/600 `#8a929c` · ☾ 44×44 r12 · avatar 34×34 r50% `#14181d` texto blanco,
  envoltorio `padding:4px 8px 4px 4px;border-radius:11px` · caret ▼ 8px.
  Gaps: `8px` en el header, `9px` en el grupo de marca.
- Subheader 56 px: ‹ 38×38 r11 borde `#e6e8ec` fondo `#fff`, glifo 15px `#5b6673` ·
  título 17px/800/−.02em · sub-línea 11px/600.
- **Sub-línea:** `15 pagadas · ` en `#8a929c` + `$572.65` en 800 `#4a545f`.
  Tono `#4a545f` = contexto resuelto (el total existe y está calculado). Si hubiera una orden
  sin método asignado, ese monto sube a `#c8102e`.
- Segunda línea de chips (34 px, `padding:0 14px 12px`, `gap:7px`): `Todas 15` activo
  (`#14181d` fondo, texto blanco) · `Editadas 1` (`#fdf3e2` / borde `#f2e0bd` / texto `#8a5800`)
  · `Mixtas 1` (fondo blanco, borde `#dfe2e7`).

### Cuerpo
- Padding del scroll: `12px 14px 20px`, `gap:9px`.
- **Encabezado de grupo:** `padding:2px 4px 0`, etiqueta 11px/800/`.09em` `#5b6673`,
  conteo 11px/600 `#a8afb8`, subtotal 15px/800/−.025em `#14181d`.
- **Tarjeta del grupo:** fondo `#fff`, borde `#e6e8ec`, radio 16, `overflow:hidden`.
- **Fila:** alto mínimo 62 px, `padding:0 6px 0 14px`, `gap:8px`.
  Título 13px/800/−.01em · sub-línea 11.5px/600 `#8a929c` · monto 13.5px/800/−.02em.
  Separador `1px #eef0f3` con `margin-left:14px`.
  Zona táctil del caret 26×38, del ⋯ 30×38.
- **Fila editada:** fondo `#fdf3e2`, `border-left:3px solid #d99000`, sub-línea en `#8a5800`,
  chip `EDITADA` 19 px de alto, `padding:0 7px`, r6, fondo `#fff`, borde `#f2e0bd`,
  texto 9.5px/800/`.05em` `#8a5800`.

### Panel desplegado (2A)
- Contenedor: `padding:0 14px 14px`, `gap:10px`. La fila abierta toma fondo `#fafbfc`
  (la editada conserva `#fdf3e2`).
- **Platillos:** caja `#fafbfc`, borde `#eef0f3`, r12, `padding:11px 12px`, `gap:8px`.
  Cantidad 11.5px/800 `#8a929c` ancho mín. 14px · nombre 12.5px/600 `#14181d` ·
  precio 12.5px/700 `#4a545f`.
- Separador `1px #e6e8ec`, luego Subtotal (11.5px/600 `#5b6673` + 12px/700 `#4a545f`),
  Descuento cuando existe (ambos `#8a5800`, monto en 800) y Total (12.5px/800 + 14px/800/−.02em).
- **Terna recibió / cambio / método:** tres cajas iguales en fila, `gap:8px`, `flex:1`,
  fondo `#fff`, borde `#e6e8ec`, r12, `padding:9px 11px`.
  Etiqueta 10px/800/`.07em` `#8a929c`, valor 13px/800/−.015em.
- **Aviso de edición** (solo si aplica): fondo `#fff`, borde `#f2e0bd`, r12, `padding:10px 12px`,
  título 11px/800 `#8a5800`, cuerpo 11px/600 `#8a5800` `line-height:1.5`.

### Pie del grupo efectivo
Caja `#fafbfc` / borde `#eef0f3` / r14 / `padding:11px 13px` con dos líneas:
`+ parte en efectivo de la orden mixta … $20.00` y
`Retiros al cajón del turno … ver Movimientos ›` (enlace 11.5px/800 `#c8102e`).

### Bloque de totales
Fondo `#fff`, borde `#d6dae0`, r16, `padding:13px 15px`, `gap:8px`.
Cuatro líneas de método (12.5px/600 `#4a545f` + 13px/700 `#4a545f`), separador `1px #dfe2e7`,
línea final `Vendido en el turno` 12.5px/800 + monto 17px/800/−.025em, y nota al pie
11px/600 `#8a929c`.

### Hojas inferiores
Patrón del sistema sin desviaciones: r `22px 22px 0 0`, `padding:14px 16px 20px`,
asa 38×4 `#dfe2e7`, overlay `rgba(20,24,29,.42)`, sin ✕.
Filas de acción de 46 px, glifo neutro en 22 px, etiqueta 13px/700, sub-línea 11px/600 con el
valor actual.

---

## 4. Decisiones que no son obvias

**Agrupar por método, no por hora.** El subtotal del grupo es el número que se compara contra
el conteo físico. La hora queda como dato de la fila.

**El mixto tiene grupo propio.** Repartir $20 al grupo efectivo y $13.85 al de tarjeta haría
cuadrar los subtotales pero escondería la orden donde suele estar el error. Va aparte, con el
desglose escrito en la fila. Para que el cajero pueda sumar el efectivo real, el grupo efectivo
lleva al pie `+ parte en efectivo de la orden mixta $20.00`.

> **Efectivo esperado en el cajón** = subtotal EFECTIVO + `efectivo_en_mixtas` − retiros + fondo inicial.
> La pantalla da los dos primeros; los retiros y el fondo viven en Movimientos.

**Los retiros se enlazan, no se listan.** Un retiro no es una venta; mezclarlo rompe el subtotal.

**Desplegar en vez de navegar.** Cuadrar es comparar. Abrir pantalla nueva por orden pierde el
subtotal del grupo y la posición en la lista. Una abierta a la vez: con varias, los encabezados
de grupo quedan fuera de vista.

**La fila mira, el ⋯ actúa.** Tocar la fila nunca cambia datos. Corregir el método vive solo en
la hoja.

**Corregir el método no es destructivo.** Cambia la clasificación del dinero, no el monto ni los
platillos. Por eso **no** va bajo ZONA DE RIESGO. Pero exige motivo, y el motivo aparece en el
corte y en el historial de la orden.

---

## 5. Interacciones

| Gesto | Resultado |
|---|---|
| Toque en la fila | Despliega el detalle debajo. Cierra la que estuviera abierta. |
| Segundo toque en la misma fila | La cierra. Ninguna queda abierta. |
| Toque en el caret ▾/▴ | Igual que la fila. No es un objetivo aparte. |
| Toque en ⋯ | Abre la hoja de acciones. **No** despliega la fila. |
| Toque en un chip del subheader | Filtra la lista. Los subtotales se recalculan sobre lo filtrado. |
| `ver Movimientos ›` | Navega a Movimientos del mismo turno. |
| Deslizar la hoja / tocar overlay | Cierra. Sin botón ✕. |

### Hoja de acciones (⋯)
```
Mesa 7 · #117
Pagada 12:38 pm · $51.30 · efectivo

LA ORDEN
⇄  Corregir método de pago
   Ahora: efectivo

HISTORIAL                        ← solo si editada_post_cobro
⚠ Editada después de cobrar
  1:04 pm · Marta R. cambió tarjeta → efectivo. Motivo: «…»
```

**Cambio respecto a `1C`:** se elimina la fila «Ver detalle». El acordeón la volvió redundante.
La hoja queda con una sola acción bajo el encabezado `LA ORDEN`.
Sin ZONA DE RIESGO en esta pantalla: no hay acción destructiva.

### Hoja «Corregir método de pago»
1. Encabezado con orden, monto y la advertencia `El monto no cambia`.
2. Radios de 50 px: Efectivo / Tarjeta / Transferencia / Mixto. El actual lleva la etiqueta
   `ACTUAL` a la derecha en 10.5px/800 `#a8afb8`. El seleccionado toma borde `#c8102e` y
   fondo `#fdecef`.
3. Campo `MOTIVO`, alto mín. 62 px. **Obligatorio.**
4. Bloque azul `#e9f1fb` / texto `#1d5a9e`: los dos subtotales ya recalculados y el recordatorio
   de que el total del turno no cambia. Se actualiza al cambiar la selección.
5. Botón 52 px. Deshabilitado `#e9ebef` / `#a8afb8` hasta que haya método distinto **y** motivo.
   Debajo, línea 11px/700 `#c8102e` con lo que falta: `Falta escribir el motivo` /
   `Elige un método distinto al actual`.

---

## 6. Datos que necesita la vista

### Por orden
| Campo | Notas |
|---|---|
| `numero` | folio visible, ej. `117` |
| `origen` | `mesa` / `llevar` / `delivery` + número de mesa |
| `pagada_en` | datetime; se muestra `12:38 pm` |
| `cobrada_por` | nombre corto del usuario |
| `total` | decimal |
| `subtotal` | antes de descuento |
| `descuento` | nullable; si es `null` la línea no se dibuja |
| `metodo` | `efectivo` / `tarjeta` / `transferencia` / `mixto` |
| `pagos[]` | solo en mixto: `{metodo, monto, referencia}` |
| `recibido`, `cambio` | solo en efectivo; en tarjeta la caja muestra `—` |
| `referencia` | 4 dígitos de la tarjeta o folio de transferencia |
| `items[]` | `{cantidad, nombre, precio_linea}` |
| `editada_post_cobro` | booleano |
| `ultimo_cambio` | `{hora, usuario, de, a, motivo}`; requerido si el anterior es `true` |

### Agregados — se calculan en la vista, **nunca en el template**
- `subtotal_por_metodo` → dict con los cuatro grupos
- `efectivo_en_mixtas` → suma de los tramos en efectivo de las órdenes mixtas
- `total_turno` → debe coincidir con la cifra que encabeza Caja
- `conteo_editadas`, `conteo_mixtas` → alimentan los chips

---

## 7. Tokens usados

```
ink            #14181d      marca            #c8102e   (hover #a90d27)
texto 2º       #4a545f      tinte rojo       #fdecef bg · #f4d3d9 borde
metadatos      #8a929c      ámbar            #d99000 · texto #8a5800
atenuado       #a8afb8                       #fdf3e2 bg · #f2e0bd borde
               #c3c8ce      azul             #2f7fd9 · texto #1d5a9e · #e9f1fb bg
superficies    #ffffff · #fafbfc             verde   #23a05f · texto #1c7a4a
fondo página   #f4f5f7      deshabilitado    #e9ebef
bordes         #e6e8ec · #eef0f3 · #dfe2e7 · #d6dae0

radios   6 · 9 · 11 · 12 · 13 · 14 · 16 · 22 · 999
```

Verde: solo en `1E`, en `Ayer cerró con $0.00 de diferencia`. En esta pantalla no hay estado
«bueno» que marcar — todo lo listado ya está pagado.

---

## 8. Implementación en Django + Bootstrap

**Una vista, un contexto.** `OrdenesTurnoView` arma la lista ya agrupada y los agregados. El
template solo itera. No hay `{% if %}` calculando montos.

```python
def get_context_data(self, **kw):
    turno = Turno.objects.abierto(self.request.user.sucursal)
    ordenes = (turno.ordenes
               .filter(estado=Orden.PAGADA)
               .select_related('cobrada_por', 'mesa')
               .prefetch_related('items', 'pagos', 'cambios')
               .order_by('pagada_en'))
    return {
        'grupos': agrupar_por_metodo(ordenes),     # [(clave, etiqueta, filas, subtotal)]
        'efectivo_en_mixtas': efectivo_en_mixtas(ordenes),
        'total_turno': sum(o.total for o in ordenes),
        'conteo_editadas': sum(1 for o in ordenes if o.editada_post_cobro),
    }
```

**El resaltado del subheader** se expone como campos separados, igual que el resto del sistema:
`sub_pre="15 pagadas · "`, `sub_hi="$572.65"`, `sub_hi_tono="contexto"`, `sub_post=""`.
No partir la cadena en el template.

**El botón bloqueado** de la hoja de corrección lo alimenta una sola función:

```python
def campos_faltantes(self):
    faltan = []
    if not self.motivo.strip():           faltan.append('Falta escribir el motivo')
    if self.metodo_nuevo == self.metodo:  faltan.append('Elige un método distinto al actual')
    return faltan
```

Esa lista rellena el `disabled` del botón y la línea roja debajo. Un solo origen de verdad.

**El acordeón.** El detalle viene precargado en el HTML y se muestra con el colapso de
Bootstrap (`data-bs-toggle="collapse"` + `data-bs-parent` en la tarjeta del grupo, que da el
comportamiento de «una abierta a la vez» sin JS propio). Con ~15 órdenes por turno el peso es
despreciable y evita el salto de un fetch. Si una sucursal pasa de ~60 órdenes por turno,
cambiar a carga diferida por AJAX.

El caret ▾/▴ se resuelve con CSS sobre `[aria-expanded]`, sin tocar el DOM desde JS.

**Corregir el método** es `POST` con CSRF a `CorregirMetodoPagoView`. En una transacción:
escribe `CambioMetodoPago` (orden, de, a, usuario, motivo, timestamp), actualiza
`orden.metodo`, marca `editada_post_cobro=True` y recalcula los agregados del turno. No toca
`total` ni `items`. Si el turno ya está cerrado, la vista rechaza con 409.

**Permisos.** `LoginRequiredMixin` + turno abierto de la sucursal del usuario. La lista es
visible para cualquier cajero. Ver §9 sobre el permiso de corrección.

**Responsive.** Mobile first a 390 px, sin scroll horizontal de 360 a 430. Las tres cajas de la
terna recibió/cambio/método usan `flex:1;min-width:0`; a 360 px los valores siguen entrando
porque son cortos. Nada por debajo de 38 px táctiles; el botón primario a 52.

---

## 9. Pendientes de producto

1. **¿Corregir el método es libre para el cajero o pide permiso de encargado?**
   El diseño asume libre + motivo obligatorio + registro en el corte. Si se decide pedir
   permiso, cabe un paso de PIN antes del guardado sin rediseñar la hoja.
2. **¿Qué pasa al elegir «Mixto» en la corrección?** Hoy es una fila seleccionable sin flujo
   detrás. O abre el repartidor de montos del cobro mixto, o se bloquea la opción.
3. **Anuladas y reabiertas quedaron fuera** (el alcance acordado fue solo pagadas). Cuando
   exista la pantalla de cierre de turno conviene sumarlas como cuarto grupo: una anulación
   tardía también descuadra.
4. **El filtro «Cerradas» de Órdenes** sigue pendiente y es otra entrega.
