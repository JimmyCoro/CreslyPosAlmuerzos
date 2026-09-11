# Handoff: Cobrar · móvil · Cresly POS

## Overview
La pantalla de **Cobrar**: la que se abre al tocar "Cobrar" en el detalle de una orden.
Cubre el cobro simple, el pago mixto, dividir la cuenta entre personas y el cobro individual
de cada parte.

Es el rediseño de la pantalla que ya existe. Conserva su lógica (subtotal, total a pagar,
métodos de pago, pago mixto activable, monto recibido, restante, dividir cuenta por personas)
y corrige lo que hoy hace lento el cobro:

- El detalle de platillos empuja el pago fuera de pantalla y obliga a hacer scroll para
  cobrar.
- "← Pedido #002" es un enlace azul de navegador: rompe la paleta y no parece tocable.
- Los tres iconos de la esquina superior derecha no dicen qué hacen, y la **✕ roja parece
  cerrar la pantalla** cuando en realidad anula la orden.
- Los campos de pago mixto muestran "$ 0" sin decir cuánto lleva cada método, y el icono a su
  derecha es ambiguo.
- El botón de confirmar está gris sin explicar por qué.
- Los atajos de monto recibido ($0.00 / $5 / $10 / $20) no sirven en una cuenta de $70.75.
- Dividir cuenta crece dentro de la misma página y **no permite elegir cómo paga cada
  persona**.

Diseñado a 390 px de ancho (iPhone 14 base). Debe funcionar de 360 a 430 px sin scroll
horizontal.

## About the Design File
`Cobrar movil.dc.html` es una **referencia de diseño en HTML**: un prototipo del look
previsto, no código de producción. Los estilos están inline.

Contiene seis piezas, de izquierda a derecha:
1. **Cobro simple** (efectivo con vuelto)
2. **Pago mixto** (repartido entre métodos, con faltante)
3. **Dividir cuenta** (asignar platillos a personas)
4. **Hoja de ⋯** (imprimir, descuento, anular)
5. **Cobrar a una persona** (su parte con su propio método)
6. **De vuelta en dividir** (una persona ya pagada)

Al final, las notas de qué cambió y por qué.

La tarea es recrearlo en **Django (templates) + Bootstrap 5**, siguiendo los patrones del
proyecto (base template, blocks, partials, staticfiles). No portes los estilos inline:
traduce a utilidades de Bootstrap más un CSS propio para lo que Bootstrap no cubre.

## Fidelity
**Alta fidelidad.** Colores, tipografía, espaciados, radios y alturas son finales.

---

## 1 · Estructura común

```
┌─────────────────────────────┐
│ Header fijo          52 px  │  ← igual en todo el sistema, sin cambios
├─────────────────────────────┤
│ Subheader            56 px  │  ← ‹ atrás + "Cobrar" + contexto + ⚯ ⋯
├─────────────────────────────┤
│ Contenido                   │  ← zona de scroll
├─────────────────────────────┤
│ Barra de confirmar   fija   │
├─────────────────────────────┤
│ Tab bar              78 px  │  ← se mantiene, sin cambios
└─────────────────────────────┘
```

**El header fijo y la tab bar no cambian.** La tab bar conserva sus cuatro pestañas
(Inicio · Mesas · Órdenes · Delivery) con Órdenes activa y su badge de conteo.
El ＋ flotante central desaparece de esta pantalla: ya se está cobrando, y tapaba la barra
de confirmar.

### Subheader (56 px)
Fondo `#fafbfc`, borde inferior `1px solid #eef0f3`, `min-height:56px`,
padding `9px 14px`, `gap:9px`. Pantalla interna: **sin segunda línea**.

- **Botón ‹ atrás** 38 × 38 px, radio `11px`, fondo `#fff`, borde `1px solid #e6e8ec`,
  glifo 15 px `#5b6673`. **Reemplaza el enlace azul "← Pedido #002".**
- **Título** "Cobrar" 17 px/800 `letter-spacing:-.02em`.
- **Sub-línea** 11 px/600 `#8a929c` con ellipsis: "Pedido #002 · Mesa 7 · 5 platillos".
  Cuando falta algo, el dato pendiente se resalta en `font-weight:800` `#c8102e`
  ("Pedido #002 · **faltan $20.75**").
- **Dos botones** de 38 px a la derecha, `gap:6px`: **⚯ dividir cuenta** y **⋯ más
  acciones**.

**Se elimina la ✕ roja de la barra.** Anular vive en el ⋯, en su propio grupo, con
confirmación — ver `handoff_hoja_acciones` si ya lo implementaste.

### Barra de confirmar (fija, sobre la tab bar)
`position:absolute; bottom:78px` (encima de la tab bar), fondo `#fff`,
borde superior `1px solid #e6e8ec`, padding `12px 14px`,
`box-shadow:0 -8px 22px rgba(20,24,29,.07)`.

Botón de ancho completo, alto 52 px, radio `14px`, 15 px/800:
- **Habilitado**: fondo `#c8102e`, texto `#fff`, glifo ✓ antes,
  `box-shadow:0 8px 18px rgba(200,16,46,.26)`. Texto: "Confirmar cobro · $70.75".
- **Deshabilitado**: fondo `#e9ebef`, texto `#8a929c`, sin sombra ni glifo, **y debajo una
  línea de 11 px/700 `#c8102e` que dice qué falta**: "Asigna los $20.75 restantes para
  continuar".

El botón nunca está gris sin explicación.

---

## 2 · Cobro simple

### Fila de detalle colapsada
`display:flex; align-items:center; gap:11px`, padding `12px 14px`, radio `14px`,
fondo `#fff`, borde `1px solid #e6e8ec`:
- "DETALLE" 10.5 px/800 `letter-spacing:.09em` `#8a929c` y debajo el resumen
  12.5 px/600 `#4a545f` con ellipsis: "5 platillos · 1 pizza, 4 alitas".
- "Ver" 12 px/700 `#5b6673` y un caret ▾ 13 px `#c3c8ce`.

**Al cobrar el detalle ya se revisó**: las cuatro tarjetas de platillos del diseño actual
empujan el pago fuera de pantalla. Se despliega solo cuando hace falta (el cliente pregunta),
mostrando las líneas con el mismo estilo que el carrito.

### Tarjeta de pago
Fondo `#fff`, borde `1px solid #e6e8ec`, radio `16px`, padding `15px`, columna con
`gap:14px`. Bloques separados por divisores `1px #eef0f3`.

**Totales**: Subtotal e IVA 15 % en 12.5 px (`#767e88` etiqueta / peso 700 valor); "Total a
pagar" separado por `border-top:1px solid #eef0f3` `padding-top:10px`, etiqueta
13.5 px/800 y monto **28 px/800 `letter-spacing:-.03em` `line-height:1`**.

**MÉTODO DE PAGO** — fila de **cuatro** opciones `flex:1`, `gap:6px`, cada una columna
centrada con `gap:5px`, padding `11px 4px`, radio `12px`: glifo 15 px y etiqueta 11 px.
- Activa: fondo `#14181d`, borde `#14181d`, glifo y texto `#fff` peso 800.
- Inactiva: fondo `#fff`, borde `1px solid #dfe2e7`, glifo y texto `#5b6673` peso 700.

| Opción | Glifo | Etiqueta |
|---|---|---|
| Efectivo | ▬ | Efectivo |
| Transferencia | ⇄ | Transf. |
| Tarjeta | ▭ | Tarjeta |
| Mixto | ⧉ | Mixto |

**Mixto es un método más, no un interruptor.** El botón "Pago mixto" a la derecha de la
etiqueta parecía un filtro; ahora es la cuarta opción de la misma fila.

**MONTO RECIBIDO** (solo en efectivo y en mixto con línea de efectivo):
- Etiqueta con una nota a la derecha: "cubre el total" 11 px/700 `#1c7a4a`, o
  "faltan $X" en `#c8102e`.
- Campo grande: padding `14px 15px`, radio `12px`, borde `1.5px solid #14181d`,
  con "$" 17 px/700 `#8a929c` y el número **26 px/800 `letter-spacing:-.03em`**.
  `inputmode="decimal"`.
- **Cuatro atajos calculados a partir del total**, `flex:1`, padding `10px 4px`,
  radio `10px`, 12.5 px:
  | Atajo | Valor | Estilo |
  |---|---|---|
  | Exacto | el total | fondo `#eaf6ef`, borde `#cfeadb`, texto `#1c7a4a` peso 800 |
  | siguiente múltiplo de 5 | $75 | fondo `#fff`, borde `#dfe2e7`, texto `#5b6673` peso 700 |
  | billete siguiente | $80 | idem (activo: fondo `#14181d`, texto `#fff`) |
  | billete siguiente | $100 | idem |

  Los chips fijos $0.00 / $5 / $10 / $20 no sirven en una cuenta de $70.75.

**Tarjeta de vuelto** — el número que el cajero busca:
padding `13px 15px`, radio `13px`, `justify-content:space-between`.
- Etiqueta "VUELTO" 10.5 px/800 `letter-spacing:.09em`, sub-línea "Recibido $80.00"
  11 px/600, y el monto **27 px/800 `letter-spacing:-.03em`**.
- **Cubierto**: fondo `#eaf6ef`, borde `1px solid #cfeadb`, etiqueta y monto `#1c7a4a`,
  sub-línea `#5f8a72`.
- **Falta dinero**: la misma tarjeta cambia a fondo `#fdecef`, borde `#f4d3d9`,
  etiqueta **"FALTA CUBRIR"** y monto `#c8102e`, sub-línea `#a9707c`.

Reemplaza el texto suelto "Restante: $70.75" en rojo, que no se lee como estado.

---

## 3 · Pago mixto

Se muestra al elegir el método **Mixto**. La tarjeta de pago cambia su bloque central por:

**REPARTIR ENTRE MÉTODOS** con un contador "3 de 4" 11 px/700 `#98a1ab` a la derecha.

Una **línea por método**, `display:flex; align-items:center; gap:9px`, padding `10px 12px`,
radio `12px`, fondo `#fff`:
- Cuadro de icono 34 × 34 px, radio `10px`, con el **color del método**:
  efectivo `#fdecef`/`#a90d27`, transferencia `#e9f1fb`/`#1d5a9e`,
  tarjeta `#fdf3e2`/`#8a5800`.
- Bloque `flex:1; min-width:0`: nombre del método 11 px/700 `#8a929c` y el
  **monto en 19 px/800 `letter-spacing:-.025em`**. `inputmode="decimal"`.
- Botón **"Resto"** `flex:0 0 auto`, padding `7px 10px`, radio `9px`, 11 px/800:
  le asigna a esa línea todo lo que falta de un toque.
  Inactivo fondo `#f4f5f7` texto `#5b6673`; en la línea enfocada fondo `#14181d`
  texto `#fff`.
- Línea enfocada: borde `1.5px solid #14181d`; el resto `1px solid #dfe2e7`.

**Fila para agregar un método**: borde `1px dashed #dfe2e7`, fondo `#fafbfc`,
cuadro de icono en `#fff` con borde, etiqueta "Agregar tarjeta" 12.5 px/700 `#8a929c` y
un ＋ 17 px `#c3c8ce`.

Debajo, la **tarjeta de faltante** (misma pieza que el vuelto, en su variante roja):
"FALTA CUBRIR · Asignado $50.00 de $70.75 · **$20.75**".

**Los montos van en 19 px, no en campos con "$ 0"**: tus dos campos actuales no dicen cuánto
lleva cada método ni tienen el método identificado por color.

Si la suma **excede** el total, la tarjeta pasa a ámbar (`#fdf3e2` / `#f2e0bd` /
`#8a5800`) con "SOBRA $X" y el botón se deshabilita: en mixto no hay vuelto por método.

---

## 4 · Dividir cuenta

**Pantalla propia, no un bloque que crece bajo el pago.** Hoy la sección de personas se
inserta sobre el pago y hay que recorrer toda la página para volver.

Subheader: título **"Dividir cuenta"**, sub-línea "Pedido #002 · **3 sin asignar** de 5" con
el pendiente en `#c8102e`. A la derecha solo ⋯ (dividir ya es esta pantalla).

### Tarjetas de persona
Fila con scroll horizontal, `gap:9px`, padding lateral `14px`. Cada tarjeta
`flex:0 0 auto`, ancho 128 px, radio `14px`, padding `12px 13px`, columna con `gap:3px`:
- Nombre 12 px/800, **monto 20 px/800 `letter-spacing:-.03em`** y el conteo
  10.5 px/600.
- **Activa**: fondo `#14181d`, texto `#fff`, conteo `rgba(255,255,255,.7)`.
- Inactiva: fondo `#fff`, borde `1px solid #dfe2e7`, monto `#8a929c`,
  conteo `#98a1ab`.
- **Pagada**: fondo `#f4fbf7`, borde `1px solid #cfeadb`, un check en círculo de 15 px
  `#23a05f` antes del nombre, todo en `#1c7a4a` / `#5f8a72`, y la sub-línea dice el método
  ("Pagado · transferencia"). **Ya no se puede editar.**
- Última tarjeta, ancho 104 px: **"＋ Agregar"**, borde `1px dashed #c3c8ce`,
  fondo `#fafbfc`, glifo 17 px `#8a929c` y etiqueta 11 px/700 `#5b6673`.

El monto de cada persona **ya viene calculado**: hoy las tarjetas muestran "$0.00 · 0
platillos" sin decir cuánto le toca.

### Barra de asignación
Fila con `gap:9px`, padding lateral `14px`: "ASIGNAR A PERSONA 1" 10.5 px/800
`letter-spacing:.1em` `#8a929c`, una barra `flex:1; height:4px` radio `999px`
(pista `#eef0f3`, avance `#c8102e`) y el conteo "2/5" 11 px/800 `#c8102e`.

### Filas de platillo
Padding lateral `14px`, `gap:8px`. Cada fila: `display:flex; align-items:center; gap:11px`,
padding `11px 12px`, radio `14px`, fondo `#fff`:
- Bloque `flex:1; min-width:0`: nombre 13.5 px/700 `line-height:1.3` y debajo los
  modificadores con el precio unitario en **11.5 px/700 `#8a5800`**
  ("3 Quesos · $2.75 c/u"). En tu diseño el precio va en rojo, que aquí está reservado a
  acciones y faltantes.
- **Stepper de asignación** `flex:0 0 auto`: **−** 36 × 40 px y **＋** 36 × 40 px
  (radio `10px`, borde `1px solid #dfe2e7`, glifo 17 px/700), y en medio
  **"1`/1`"** — el asignado en 14 px/800 y el total disponible en 11 px/700 `#98a1ab`.
  Los botones al límite van en `#c3c8ce` (sin efecto).
- **Con algo asignado a la persona activa**: borde `1.5px solid #c8102e` +
  `box-shadow:0 6px 14px rgba(200,16,46,.10)`. Sin asignar: borde `1px solid #e6e8ec` y el
  contador en `#8a929c`.

El contador "asignado / total" evita el problema de tu diseño, donde cuatro filas idénticas
de "20 alitas: 20 BBQ" con "0" no dicen cuántas quedan por repartir.

### Barra inferior
Dos botones, `gap:9px`, alto 52 px, radio `14px`:
- **"Repartir igual"** `flex:0 0 auto`, padding lateral `15px`, borde
  `1px solid #dfe2e7`, 13 px/700 `#5b6673`. Divide el total en partes iguales entre las
  personas — el caso más común.
- **"Cobrar P1 · $19.75"** `flex:1`, fondo `#c8102e`, texto `#fff` 14.5 px/800,
  `box-shadow:0 8px 18px rgba(200,16,46,.26)`. Deshabilitado si esa persona no tiene nada
  asignado.

---

## 5 · Cobrar a una persona

**Es donde cada persona elige su propio método de pago** — lo que hoy falta por completo.

Subheader: título "Cobrar · Persona 1", sub-línea "Pedido #002 · parte 1 de 2 · 2
platillos".

1. **Dos tarjetas de persona** arriba (`gap:8px`, `flex:1` cada una, radio `13px`,
   padding `11px 13px`): la activa en `#14181d` con "cobrando ahora", las otras en `#fff`
   con borde y "pendiente" o "Pagado · método".
2. **Tarjeta de pago** con:
   - Las líneas de **sus** platillos (12.5 px, etiqueta `#767e88` / valor peso 700) y
     **"Su parte"** con el monto en 28 px/800.
   - **"CÓMO PAGA PERSONA 1"**: la misma fila de cuatro métodos, con la nota
     "Cada persona elige su propio método. Persona 2 puede pagar distinto."
     11 px/600 `#98a1ab`.
   - El bloque que corresponda al método: **monto recibido + vuelto** en efectivo,
     **campo de referencia** en transferencia (padding `13px 14px`, radio `12px`,
     borde `1.5px solid #14181d`, texto 16 px/700 `letter-spacing:.02em`),
     o las **líneas por método** si elige mixto dentro de su parte.
   - Tarjeta verde **"LISTO PARA COBRAR"** con la sub-línea del método
     ("Transferencia · sin vuelto") y el monto en 27 px.
3. **Barra inferior**: "Cobrar Persona 1 · $19.75" y debajo, en 11 px/600 `#98a1ab`,
   quién sigue: "Después sigue Persona 2 · $51.00".

### Al volver
Se regresa a Dividir cuenta con:
- La persona cobrada **en verde con su método**, no editable.
- La siguiente **activa**.
- Una barra de progreso de cobro: "COBRADO" + barra (avance `#23a05f`) +
  "**$19.75 / $70.75**" en 11 px/800 `#1c7a4a`.
- El botón pasa a "Cobrar P2 · $51.00".

**La orden se cierra sola cuando lo cobrado llega al total.**

---

## 6 · Hoja de ⋯

Hoja inferior: fondo `#fff`, radio `22px 22px 0 0`, padding `14px 16px 20px`,
`gap:14px`, overlay `rgba(20,24,29,.42)`, asa de 38 × 4 px `#dfe2e7`.
Se cierra deslizando o tocando el overlay — sin botón ✕.

Cabecera: "Pedido #002" 17 px/800 y "Mesa 7 · 5 platillos · $70.75" 11.5 px/600 `#8a929c`.

Filas de ≈46 px: `display:flex; gap:11px`, padding `13px 14px`, radio `12px`,
borde `1px solid #dfe2e7`, glifo 14 px `#5b6673` en caja de 18 px, etiqueta 13.5 px/700,
sub-línea 11 px/600 `#98a1ab`, chevron › 14 px `#c3c8ce`.

| Grupo | Acciones |
|---|---|
| **IMPRIMIR** | Precuenta ▤ ("Para que el cliente revise antes de pagar") · Reimprimir comanda ▤ ("Copia para cocina") |
| **AJUSTES DE LA CUENTA** | Aplicar descuento % ("Porcentaje o monto fijo") · Dividir cuenta ⚯ ("También está como icono en la barra") |
| **ZONA DE RIESGO** | Anular pedido ✕ ("Pide confirmación y motivo") |

- Encabezados de grupo 10.5 px/800 `letter-spacing:.09em` `#8a929c`;
  el de riesgo en `#a90d27`.
- Divisor `1px #eef0f3` antes del último grupo.
- La fila de anular: borde `1px solid #f4d3d9`, glifo y etiqueta `#c8102e`,
  sub-línea `#a9707c`, chevron `#f4d3d9`.
- **Anular abre una confirmación** que nombra qué se pierde, avisa si hay platillos en cocina
  y exige un motivo. Ver `handoff_hoja_acciones` para el detalle de esa hoja.

**En delivery** la hoja cambia: se omite Dividir cuenta, "Precuenta" se reemplaza por
"Ticket con dirección", y la zona de riesgo suma "Marcar como no entregado".

---

## Interactions & Behavior
- **Tap en "Ver"** despliega el detalle de platillos en su lugar; el caret rota.
- **Tap en un método** cambia el bloque inferior de la tarjeta. Lo ya escrito se conserva
  por si el usuario vuelve.
- **Tap en un atajo de monto** rellena el campo; se recalcula el vuelto al instante.
- **Tap en "Resto"** asigna a esa línea el faltante exacto.
- **Validación de confirmar**: en efectivo/transferencia/tarjeta, monto recibido ≥ total; en
  mixto, la suma de las líneas = total exacto. En dividir, cada persona por separado.
- **Un cobro confirmado no se edita** desde esta pantalla: se corrige con "Anular cobro"
  desde el ⋯, con permiso de administrador.
- **Refresco**: si otro dispositivo agrega platillos a la orden mientras se cobra, avisa con
  la cinta de alerta del sistema y recalcula el total en lugar de cobrar un monto viejo.
- **Impresión**: al confirmar se imprime el ticket. Si la impresora no responde, el cobro
  **se registra igual** y aparece la cinta de alerta con "Reintentar" — nunca se pierde un
  cobro por un fallo de impresión.
- Transiciones `.12s ease`; las hojas entran deslizando desde abajo.
- **Táctil**: botón de confirmar 52 px, campos y métodos 44–48 px, steppers 40 px,
  botones del subheader 38 px. Nada por debajo de 38 px.

## State Management
```
cobro: {
  orden_id, numero, tipo, mesa, n_platillos,
  subtotal, iva, total,
  metodo: 'efectivo' | 'transferencia' | 'tarjeta' | 'mixto',
  monto_recibido: Decimal,                       # efectivo
  referencia: str,                               # transferencia
  lineas_pago: [ { metodo, monto } ],            # mixto
  division: null | {
    personas: [ {
      id, nombre, monto, n_platillos,
      pagado: bool, metodo_usado: str|null,
      asignaciones: [ { linea_id, cantidad } ]
    } ]
  }
}
```
Derivados que calcula la **vista o el modelo**, no el template:
- `vuelto = monto_recibido - total` (o `faltante` si es negativo).
- `asignado = sum(lineas_pago)`, `faltante = total - asignado`, `sobrante`.
- `atajos_monto(total)` → [exacto, siguiente múltiplo de 5, dos billetes siguientes].
- `sin_asignar(division)` → platillos sin repartir, para el subheader y la barra.
- `cobrado(division)` / `total` para la barra de progreso.
- `puede_confirmar(cobro)` → bool + **motivo del bloqueo en texto**. De ahí sale el estado
  del botón, la línea roja debajo y el resaltado del subheader — **una sola fuente de
  verdad**, no tres comprobaciones distintas.

Los cambios (método, monto, "Resto", asignaciones) son endpoints POST que devuelven el
parcial afectado (HTMX encaja bien). El cobro se confirma en **una sola transacción**: registra
pagos, cierra la orden, libera la mesa e imprime.

---

## Design Tokens

**Colores**
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | texto principal, método activo, persona activa, campo enfocado |
| text-2 | `#4a545f` | resumen del detalle |
| text-3 | `#5b6673` | glifos, métodos inactivos, "Ver", "Repartir igual" |
| muted | `#767e88` | etiquetas de totales |
| muted-2 | `#8a929c` | etiquetas de sección, sub-línea, "$" del campo |
| muted-3 | `#98a1ab` | notas, contadores, "quién sigue" |
| faint | `#a8afb8` / `#c3c8ce` | deshabilitado, chevrons, steppers al límite |
| surface | `#ffffff` | tarjetas, hoja, filas |
| page | `#f4f5f7` | fondo de pantalla, botón "Resto" inactivo |
| surface-2 | `#fafbfc` | subheader, fila de agregar método |
| segmented-bg | `#e9ebef` | botón de confirmar deshabilitado |
| border | `#e6e8ec` | bordes de tarjeta y fila |
| border-soft | `#eef0f3` | divisores, pista de progreso |
| border-input | `#dfe2e7` | bordes de control, asa, dashed de agregar |
| brand | `#c8102e` | confirmar, faltante, cursor, fila asignada, anular |
| brand-dark | `#a90d27` | icono de efectivo, "ZONA DE RIESGO" |
| brand-tint | `#fdecef` bg · `#f4d3d9` borde | tarjeta de faltante, efectivo, anular |
| brand-muted | `#a9707c` | sub-línea sobre tinte rojo |
| green | `#23a05f` | check de pagado, barra de cobrado |
| green-dark | `#1c7a4a` | vuelto, "Exacto", "cubre el total", persona pagada |
| green-mid | `#5f8a72` | sub-línea sobre tinte verde |
| green-tint | `#eaf6ef` / `#f4fbf7` bg · `#cfeadb` borde | vuelto, persona pagada |
| blue | `#1d5a9e` sobre `#e9f1fb` | icono de transferencia |
| amber-dark | `#8a5800` | **modificadores y precio unitario**, sobrante |
| amber-tint | `#fdf3e2` bg · `#f2e0bd` borde | icono de tarjeta, sobrante |
| overlay | `rgba(20,24,29,.42)` | fondo detrás de la hoja |

**Tipografía:** Plus Jakarta Sans (400/500/600/700/800), fallback Helvetica, Arial,
sans-serif. `font-feature-settings:'tnum' 1` en el contenedor raíz — **imprescindible** aquí
para que los montos queden alineados.
Escala usada: 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14, 14.5, 15, 16, 17, 19, 20, 26, 27,
28 px.
`letter-spacing` negativo en cifras (−.02 a −.03em), positivo en etiquetas mayúsculas
(.09 a .1em) y en la referencia (.02em).

**Espaciado:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20 px.

**Radios:** 9, 10, 11, 12, 13, 14, 16, 22, 999px.

**Sombras:**
- confirmar / cobrar `0 8px 18px rgba(200,16,46,.26)`
- fila de platillo asignada `0 6px 14px rgba(200,16,46,.10)`
- barra de confirmar `0 -8px 22px rgba(20,24,29,.07)`

---

## Notas de implementación (Django + Bootstrap 5)
- Variables Sass: `$primary: #c8102e`, `$body-bg: #f4f5f7`, `$body-color: #14181d`,
  `$border-color: #e6e8ec`, familia Plus Jakarta Sans. Si no compilas Sass, un `cobrar.css`
  con las variables CSS de la tabla basta.
- Templates sugeridos:
  `movil/cobrar.html`, `movil/dividir.html`, `movil/cobrar_persona.html`,
  y parciales `_subheader_cobro.html`, `_detalle_colapsado.html`, `_metodos_pago.html`,
  `_monto_recibido.html`, `_lineas_mixto.html`, `_tarjeta_resultado.html`
  (vuelto / faltante / sobrante — **una sola pieza con tres tonos**),
  `_barra_confirmar.html`, `_tarjetas_persona.html`, `_fila_asignacion.html`,
  `_hoja_acciones_cobro.html`.
- **Dividir cuenta es una URL propia** (`/cobrar/<id>/dividir/`), no un bloque
  condicional dentro de cobrar. Cobrar a una persona, otra
  (`/cobrar/<id>/persona/<n>/`).
- La fila de métodos es flex directo con `flex:1`, no un `btn-group`: radios ocultos +
  labels para que funcione sin JS.
- Las hojas inferiores: **offcanvas de Bootstrap con `placement="bottom"`** u `<dialog>`.
- El color del icono de cada método sale como clase del backend
  (`class="metodo-icon metodo-icon--efectivo"`); los colores viven en CSS.
- Todos los campos de monto con `inputmode="decimal"`; el de referencia con
  `inputmode="numeric"`.
- Usa `Decimal`, nunca float, y redondea a 2 decimales en un solo lugar. Al usar "Resto",
  asigna el faltante exacto para que la suma cierre al centavo.
- El IVA está al 15 %. Si es configurable, lee la tasa de la configuración del negocio.
- Los montos, nombres y platillos son **datos de ejemplo**. Si un campo no existe en tu
  modelo, omite ese fragmento en vez de inventarlo.

## Assets
Ninguno. El prototipo usa glifos de texto como marcadores:
`☰ ☾ ▼ ‹ ⚯ ⋯ ▬ ⇄ ▭ ⧉ ✓ ✕ ＋ − ▤ ⎙ % ⚠ ↺ › ⌂ ▦ ⇢`. Reemplázalos por el set de iconos del
proyecto — Bootstrap Icons encaja: `list`, `moon`, `chevron-down`, `chevron-left`,
`people` (dividir), `three-dots`, `cash` (efectivo), `arrow-left-right` (transferencia),
`credit-card` (tarjeta), `layers` (mixto), `check-lg`, `x-lg`, `plus-lg`, `dash-lg`,
`receipt`, `printer`, `percent`, `exclamation-triangle`, `chevron-right`.

## Files
- `Cobrar movil.dc.html` — cobro simple, pago mixto, dividir cuenta, hoja de ⋯, cobrar a una
  persona, el reparto con una persona ya pagada, y las notas de diseño.
