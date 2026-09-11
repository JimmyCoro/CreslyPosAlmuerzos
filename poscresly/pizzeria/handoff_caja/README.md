# Handoff — Módulo Caja (móvil)

POS Cresly Pizzería · Suc. Centro · Django + Bootstrap 5
Diseño de referencia: `Caja movil.dc.html` (en esta carpeta)

> **Los datos del prototipo son de ejemplo.** Montos, nombres, horas y cantidades
> están puestos para probar la maqueta. Nada de eso debe quedar en el código.

---

## 1. Overview

Caja es el módulo donde el cajero abre su turno, ve cuánto efectivo debe haber en el
cajón, registra retiros a bóveda y gastos, y consulta el histórico de cortes.

La decisión de diseño que ordena todo el módulo: **la cifra principal es "debe haber en
el cajón", no el total vendido.** Es lo único que el cajero puede comprobar contando, y
es lo que decide si toca retirar. Lo vendido y el desglose por forma de pago son
contexto.

**Alcance del handoff:** apertura de turno, estado de caja, movimientos, retiro a
bóveda, ingreso/gasto manual, cortes anteriores.

**Fuera de alcance (no diseñado):** cierre de turno con arqueo final y comprobante de
cierre. El bloque de conteo por denominación (§4.5) y el patrón de faltante/sobrante
(§4.7) ya resuelven la mayor parte de esa pantalla cuando se pida.

**Permisos:** cualquier cajero opera su propio turno. Ve los turnos de otros en el
histórico en modo lectura. Una sola caja por sucursal.

---

## 2. Estructura

```
Caja (móvil, 390 px base)
│
├── caja_cerrada ──► 4.3  Abrir caja            (pantalla completa, bloquea el POS)
│
└── caja_abierta ──► 4.1  Estado de caja        ← pantalla principal · VARIANTE A
                     4.2  Estado de caja        ← misma pantalla · VARIANTE B
                     │
                     ├─► 4.4  Movimientos del turno   (pantalla)
                     ├─► 4.5  Retirar a bóveda        (hoja inferior)
                     ├─► 4.6  Registrar movimiento    (hoja inferior)
                     └─► 4.7  Cortes anteriores       (pantalla)
```

### Variantes del estado de caja

Las dos muestran los mismos datos. **Implementar 4.1 (resumen) como default.**

| | 4.1 Resumen breve | 4.2 Desglose completo |
|---|---|---|
| Cifra grande | "Debe haber" $203.90 | igual, al final de la resta |
| Aritmética | oculta tras "Cómo se cobró" | impresa completa |
| Formas de pago | colapsada | tres barras + total |
| Scroll | ninguno | ninguno, pantalla llena |
| Sirve para | consultar a media hora punta | comprobar al cerrar |

Si se quiere una sola, 4.1: el caso frecuente es "¿cuánto debo tener?" a media prisa.

### Rutas sugeridas

```
GET  /caja/                        estado (o apertura si no hay turno abierto)
POST /caja/abrir/                  fondo_inicial
GET  /caja/movimientos/            lista con filtros
POST /caja/retiro/                 conteo por denominación
POST /caja/movimiento/             ingreso o gasto
GET  /caja/cortes/                 histórico
```

---

## 3. Chrome compartido (idéntico al resto de la app)

**Header — 52 px, no cambia nunca.**
☰ 44 px · logo 30 px (radio 9, `#c8102e`) + "Cresly Pizzería" 13.5/800 y "Suc. Centro"
10.5/600 `#8a929c` · ☾ 44 px · avatar 34 px + caret. Fondo `#fff`, borde inferior
`#e6e8ec`.

**Subheader — 56 px, dinámico.**
‹ atrás 38 px · título 17/800 `-.02em` · sub-línea 11/600 · hasta una acción a la
derecha (38 px, borde `#dfe2e7`, radio 11). Segunda línea opcional de chips de 34 px
(pantallas 4.4 y 4.7), que lleva el bloque a 108 px.

**Sub-líneas de este módulo** — el dato relevante va en 800 con color propio, el resto
en `#8a929c`. Se arma en el backend con `sub_pre` / `sub_hi` / `sub_hi_tono` /
`sub_post`, no partiendo la cadena en el template.

| Pantalla | sub_pre | sub_hi | tono | sub_post |
|---|---|---|---|---|
| Estado de caja | `Turno abierto ` | `hace 4 h 48` | ámbar `#8a5800` | ` · Marta R.` |
| Abrir caja | — | `Falta el fondo inicial` | rojo `#c8102e` | ` para empezar a cobrar` |
| Movimientos | `Turno de hoy · saldo ` | `$203.90` | neutro `#4a545f` | — |
| Cortes anteriores | `Últimos 14 turnos · ` | `2 con diferencia` | rojo `#c8102e` | — |

**Tab bar — 78 px.** Inicio · Mesas · Órdenes · Delivery. Caja **no** es una pestaña:
se entra desde el acceso rápido de Inicio, así que la pestaña activa sigue siendo
Inicio (`#fdecef` / `#c8102e`). Excepción: en 4.3 la tab bar se reemplaza por la barra
de acción "Abrir caja con $X".

**Hojas inferiores.** Radio `22px 22px 0 0`, padding `14px 16px 20px`, asa 38 × 4 px
`#dfe2e7` centrada, overlay `rgba(20,24,29,.42)`. Se cierran deslizando o tocando el
overlay. Sin botón ✕.

---

## 4. Pantallas

### 4.1 Estado de caja — resumen breve (variante A, default)

**Tarjeta principal** — `#fff`, borde `#e6e8ec`, radio 18, padding `18px 18px 16px`,
gap 14.

- Etiqueta `DEBE HABER EN EL CAJÓN` 11/800 `.09em` `#8a929c`
- Cifra 28/800 `-.03em`, line-height 1.05
- Pie 12/600 `#8a929c`: "Fondo $50.00 + efectivo cobrado − retiros y gastos"
- Separador 1 px `#eef0f3`
- Dos columnas (grid 1fr 1fr, gap 10): `VENDIDO EN EL TURNO` / `RETIRADO A BÓVEDA`,
  etiqueta 10.5/800 `.07em` `#8a929c`, cifra 19/800 `-.025em` (la de retirado en
  `#4a545f` — es dinero que ya no está)

**Cinta de umbral** — solo si `esperado_en_caja > umbral_retiro`. Fondo `#fdf3e2`,
borde `#f2e0bd`, radio 13, padding `11px 13px`. Punto 7 px `#d99000`, texto 12/700
`#8a5800` con el umbral en 800. Si no se pasa el umbral, no se dibuja.

**Lista de accesos** — una tarjeta `#fff` radio 16 con tres filas de 13/15 px
separadas por 1 px `#eef0f3`:

| Fila | Sub-línea | Afordancia |
|---|---|---|
| Cómo se cobró | "Efectivo, tarjeta y transferencia" | ▾ despliega en sitio |
| Movimientos | "9 registros · último 2:52 pm" | › va a 4.4 |
| Cortes anteriores | "Ayer cerró con **$0.00** de diferencia" (verde) | › va a 4.7 |

**Acciones** — grid 1fr 1fr, gap 9, botones de 50 px `#fff` borde `#dfe2e7` radio 13,
13/800: "↑ Retirar" (abre 4.5) y "± Ingreso o gasto" (abre 4.6). Secundarios a
propósito: son excepciones, no el flujo normal.

### 4.2 Estado de caja — desglose completo (variante B)

**Tarjeta "EFECTIVO EN EL CAJÓN"** — cuatro filas 12.5/600 `#4a545f` a la izquierda y
13.5/700 a la derecha, en el orden en que se comprueba a mano:

```
Fondo de apertura        $50.00
Cobrado en efectivo    + $312.40    ← verde #1c7a4a
Retirado a bóveda      − $150.00    ← #4a545f
Gastos del turno       − $8.50      ← #4a545f
───────────────────── 1px #dfe2e7
Debe haber              $203.90     ← 26/800 -.03em
```

**Tarjeta "CÓMO SE COBRÓ"** — con `32 órdenes` alineado a la derecha de la etiqueta.
Tres filas, cada una: nombre 12.5/700 + monto 13.5/800, y debajo barra de 6 px
(riel `#eef0f3`, radio 999) proporcional al total. Rellenos en escala de grises
—`#14181d`, `#5b6673`, `#a8afb8`— **no** en colores de marca: son magnitudes, no
estados. Cierra con total 17/800.

**Fila "Movimientos"** al pie, igual que en 4.1.

### 4.3 Abrir caja

Única pantalla accesible mientras `caja.abierta == False`. Sin caja abierta no se puede
cobrar; el POS redirige aquí.

**Tarjeta "FONDO INICIAL"**
- Campo de 64 px, radio 14, borde 1.5 px `#c8102e` (foco): `$` 19/700 `#8a929c` +
  monto 26/800 `-.03em` + cursor 2 × 26 px `#c8102e`
- Cuatro atajos en fila, 40 px, radio 11: `$30 $50 $75 $100`. Seleccionado con fondo
  `#fdecef`, borde 1.5 px y texto `#c8102e`; el resto borde `#dfe2e7`, texto `#4a545f`
- Nota 11.5/600 `#8a929c`: el fondo propuesto viene del cierre anterior. Si el cajero
  escribe otra cifra se abre igual, pero la diferencia queda registrada en la apertura

**Tarjeta "QUIÉN ABRE"** — avatar 38 px, nombre 13.5/800, rol 11.5/600; separador; fila
"Turno" con fecha y hora de apertura.

**Tarjeta de contexto** — `#fafbfc`, borde `#eef0f3`: turno anterior, quién cerró, a qué
hora y con cuánta diferencia (en verde si cuadró).

**Barra de acción** (reemplaza la tab bar) — `#fff`, borde superior `#e6e8ec`, sombra
`0 -8px 22px rgba(20,24,29,.07)`, padding `12px 14px 16px`. Botón de 52 px `#c8102e`
radio 14, 15/800, sombra `0 8px 18px rgba(200,16,46,.26)`. El label **lleva el monto**:
"Abrir caja con $50.00".

### 4.4 Movimientos del turno

Solo lo que entra y sale del cajón fuera de la venta: apertura, retiros, ingresos y
gastos. **Las ventas se consultan en Órdenes**, no aquí.

Subheader de 108 px: acción ⌕ y chips `Todos 9 · Retiros · Gastos · Ingresos`
(activo `#14181d` / `#fff`, el conteo en `opacity:.55`).

Encabezado de día `HOY · LUNES 10` 11/800 `.09em` `#5b6673`.

**Fila de movimiento** — `#fff`, borde `#e6e8ec`, borde izquierdo de 3 px según tipo,
radio 14, padding `12px 14px 12px 11px`, gap 12:

- Glifo en cuadro de 38 px, radio 11, fondo tintado
- Título 13/800 · autor y hora 11.5/600 `#8a929c` (y "con comprobante" si lo hay)
- Derecha: monto 15/800 con signo, y debajo **el saldo que quedó** 11/600 `#98a1ab`
  ("quedan $203.90") — es lo que permite reconstruir a mano cualquier descuadre

| Tipo | Banda | Glifo · fondo | Monto |
|---|---|---|---|
| Retiro a bóveda | `#4a545f` | ↑ · `#f4f5f7` | `− $X` `#4a545f` |
| Gasto | `#d99000` | − · `#fdf3e2` | `− $X` `#8a5800` |
| Ingreso | `#23a05f` | + · `#f4fbf7` | `+ $X` `#1c7a4a` |
| Apertura | `#c3c8ce` | ⌂ · `#f4f5f7` | `$X` ink, sub "fondo" |

Los movimientos van en orden cronológico inverso. Anular uno ya registrado vive en el
⋯ del propio movimiento, bajo ZONA DE RIESGO, con confirmación y motivo.

### 4.5 Retirar a bóveda (hoja inferior)

**Este bloque de conteo es el componente que reusará el cierre de turno.** Escribirlo
una sola vez.

Título 17/800 + sub-línea "En el cajón hay **$303.90**. Cuenta lo que sacas."

**Tabla de denominaciones** — contenedor borde `#e6e8ec` radio 16, `overflow:hidden`.
Cabecera `#fafbfc`: `DENOMINACIÓN` / `CANTIDAD · SUBTOTAL` 10.5/800 `.08em`.

Cada fila (padding `8px 12px 8px 14px`, borde inferior `#eef0f3`):
`$20` 13.5/800 · `−` 38 px / cantidad 15/800 (min-width 26, centrada) / `+` 38 px ·
subtotal 13.5/800 alineado a la derecha, min-width 62.
En cero: cantidad y subtotal en `#c3c8ce` y el `−` deshabilitado.

Billetes visibles por defecto ($20, $10, $5, $1); monedas colapsadas en una fila
`#fafbfc` "Monedas · ver 6 más ▾".

**Totales** — "Total a retirar" 12.5/800 + cifra 26/800; debajo, caja `#fafbfc` borde
`#eef0f3` radio 13 con "Quedan en el cajón" y el resultado en 13.5/800. Ambos se
recalculan en cada toque.

**Motivo (opcional)** — campo de 44 px, radio 12, borde `#dfe2e7`.

**Acción** — botón de 52 px `#c8102e` con el total en el label, y debajo 11/600
`#8a929c`: "Queda a tu nombre en el registro del turno."

*Al reusarlo en el cierre:* cambia el marco, no la tabla. En vez de "quedan en el
cajón" se compara el conteo con `esperado_en_caja`, se muestra el faltante o sobrante
con el color de 4.7, y **se exige motivo escrito** para poder cerrar (regla confirmada).

### 4.6 Registrar movimiento (hoja inferior)

Selector de dos posiciones dentro de un riel `#f4f5f7` radio 14 padding 4: "− Gasto" /
"+ Ingreso", pastillas de 44 px radio 11. La activa en `#fff` con borde 1.5 px del tono
del tipo (ámbar `#d99000` para gasto, verde `#23a05f` para ingreso).

Luego: **MONTO** (campo de 60 px, mismo tratamiento que 4.3, placeholder `0.00` en
`#c3c8ce`) · **CATEGORÍA** (chips de 38 px radio 999 que envuelven: Insumos, Transporte,
Mantenimiento, Servicios, Otro) · **DETALLE** (campo de 44 px) · **Adjuntar
comprobante** (fila con ⊕ de 38 px, opcional).

**Botón bloqueado.** Deshabilitado `#e9ebef` / texto `#a8afb8`, y debajo una línea
11/700 `#c8102e` que dice qué falta: "Falta el monto y la categoría".
Una sola función en el backend —`campos_faltantes()`— alimenta el estado del botón, esa
línea y el resaltado del subheader. Nunca un botón gris sin explicación.

### 4.7 Cortes anteriores

Subheader de 108 px con chips `Todos · Con diferencia · Mis turnos`. El filtro "Mis
turnos" existe porque la lista incluye turnos de otros cajeros: se leen, no se editan.

Encabezado de grupo `ESTA SEMANA`.

**Fila de corte** — `#fff`, radio 14, padding `12px 14px`:
título "Dom 9 sep · turno noche" 13/800 · sub-línea 11.5/600 `#8a929c` con cajero, hora
de cierre y monto vendido; **si no cuadró, la sub-línea muestra el motivo escrito entre
comillas** en vez del monto, porque es lo que se va a buscar.

Derecha: diferencia 15/800 + etiqueta 10.5/800 `.06em`.

| Resultado | Diferencia · etiqueta | Marco |
|---|---|---|
| Cuadró | `$0.00` `#1c7a4a` · CUADRÓ | borde `#e6e8ec` |
| Faltante | `− $3.25` `#c8102e` · FALTANTE | borde `#f4d3d9` + banda 3 px `#c8102e` |
| Sobrante | `+ $2.00` `#8a5800` · SOBRANTE | banda 3 px `#d99000` |

**El monto vendido va en gris.** La diferencia es la única cifra en color de la
pantalla.

---

## 5. Datos que necesita la vista

```python
# GET /caja/
turno = {
  "abierta": bool,
  "abierto_en": datetime,          # "hace 4 h 48" se formatea en la vista
  "cajero": {"nombre", "inicial"},
  "fondo_inicial": Decimal,
  "ventas_por_metodo": {"efectivo": D, "tarjeta": D, "transferencia": D},
  "ordenes_cobradas": int,
  "total_retirado": Decimal,
  "total_gastos": Decimal,
  "total_ingresos": Decimal,
  "esperado_en_caja": Decimal,     # calculado en la vista, NUNCA en el template
  "umbral_retiro": Decimal,        # config de sucursal; dispara la cinta ámbar
  "movimientos_count": int,
  "ultimo_movimiento_en": datetime,
}

# GET /caja/movimientos/
movimiento = {
  "tipo": "apertura|retiro|ingreso|gasto",
  "monto": Decimal,
  "categoria": str | None,         # solo ingreso/gasto
  "detalle": str | None,
  "autor": str,
  "creado_en": datetime,
  "comprobante": File | None,
  "saldo_posterior": Decimal,      # se guarda al registrar, no se recalcula al leer
  "anulado": bool,
}

# POST /caja/retiro/
{"conteo": {"20": 5, "10": 4, "5": 0, "1": 10, "0.25": 0, ...},
 "total": Decimal,                 # el backend lo recalcula y valida contra el conteo
 "motivo": str | None}

# GET /caja/cortes/
corte = {"fecha", "turno", "cajero", "cerrado_en",
         "total_vendido": D, "diferencia": D, "motivo": str | None}
```

**Reglas de cálculo**

```
esperado_en_caja = fondo_inicial
                 + ventas_efectivo
                 + total_ingresos
                 − total_retirado
                 − total_gastos
```

Solo el efectivo entra en el cálculo del cajón. Tarjeta y transferencia se muestran en
el desglose de ventas y nada más.

---

## 6. Tokens

**Tipografía** — Plus Jakarta Sans 400–800, fallback Helvetica/Arial.
`font-feature-settings:'tnum' 1` en el contenedor raíz: los montos tienen que alinearse
en columna.
Escala usada: 10.5 · 11 · 11.5 · 12 · 12.5 · 13 · 13.5 · 15 · 17 · 19 · 24 · 26 · 28 px.
`letter-spacing` −.01 a −.03em en cifras y títulos, +.06 a .09em en etiquetas mayúsculas.

**Color**

| Uso | Hex |
|---|---|
| ink | `#14181d` |
| texto secundario | `#4a545f` · `#5b6673` |
| metadatos | `#8a929c` · `#98a1ab` |
| atenuado | `#a8afb8` · `#c3c8ce` |
| superficies | `#ffffff` · `#fafbfc` |
| fondo de página | `#f4f5f7` |
| bordes | `#e6e8ec` · `#eef0f3` · `#dfe2e7` |
| deshabilitado | `#e9ebef` |
| marca / acción | `#c8102e` (oscuro `#a90d27`) · tinte `#fdecef` / borde `#f4d3d9` |
| verde / OK | `#23a05f` · texto `#1c7a4a` · `#eaf6ef` `#f4fbf7` / borde `#cfeadb` |
| ámbar / atención | `#d99000` · texto `#8a5800` · `#fdf3e2` / borde `#f2e0bd` |

Tema oscuro: superficies `#1a1f25` / `#242b33`, bordes `#2b333b`, texto `#f2f4f6` /
`#8d97a2`, y la marca sube a `#e02040`.

**Semántica del color en este módulo** — importa respetarla:
`#c8102e` = falta algo obligatorio o hay un faltante de dinero ·
`#d99000` = atención sin urgencia (umbral de retiro, gasto, sobrante) ·
`#1c7a4a` = cuadra o entra dinero · `#4a545f` = salida de dinero normal, sin alarma.
El rojo no se usa para "mucho dinero en caja": eso es ámbar.

**Radios** — 9 · 11 · 12 · 13 · 14 · 16 · 18 · 22 · 999px
**Sombras** — primario `0 8px 18px rgba(200,16,46,.26)` · barra `0 -8px 22px rgba(20,24,29,.07)`
**Táctil** — nada por debajo de 38 px; acciones primarias 50–52 px

---

## 7. Notas de implementación (Django + Bootstrap 5)

**Plantillas**

```
templates/caja/
  estado.html            # 4.1 (variante A). Extiende base_movil.html
  abrir.html             # 4.3
  movimientos.html       # 4.4
  cortes.html            # 4.7
  _subheader.html        # recibe titulo, sub_pre, sub_hi, sub_hi_tono, sub_post, accion
  _conteo.html           # tabla de denominaciones — compartida por retiro y cierre
  _fila_movimiento.html
  _hoja_retiro.html      # 4.5
  _hoja_movimiento.html  # 4.6
```

**Qué no hacer**

- No partir la sub-línea en el template buscando el dato a resaltar. El backend manda
  los cuatro campos ya separados.
- No calcular `esperado_en_caja` en la plantilla ni en JS. Lo calcula la vista; el
  conteo del cliente solo suma denominaciones para dar feedback inmediato, y el backend
  vuelve a sumar y valida al recibir el POST.
- No mostrar el botón deshabilitado sin la línea de qué falta. Ambos salen de
  `campos_faltantes()`.
- No poner la acción destructiva (anular movimiento) como icono en una barra. Va en la
  hoja de acciones ⋯, al final, bajo ZONA DE RIESGO, con confirmación y motivo.
- No usar los tintes de marca para las barras de proporción de "cómo se cobró". Son
  magnitudes; van en escala de grises.

**Bootstrap** — la retícula de Bootstrap no se usa para las tarjetas: son flex y grid
con `gap`, no columnas. De Bootstrap se aprovechan el offcanvas inferior para las hojas
(con el radio, el padding y el asa sobreescritos, y `data-bs-backdrop` al 42%), los
modales de confirmación y los utilities de espaciado. Las clases de color de Bootstrap
no se usan: todos los tonos son los de arriba.

**Estados vacíos**
- Sin movimientos: la fila de apertura siempre existe, así que la lista nunca está
  vacía. No hace falta empty state en 4.4.
- Sin cortes previos (sucursal nueva): en 4.7 un texto centrado 12.5/600 `#8a929c`,
  "Aún no hay turnos cerrados". En 4.1 la fila "Cortes anteriores" se oculta.
- Conteo en cero en 4.5: el botón queda deshabilitado con la línea "Cuenta lo que vas a
  retirar".

**Validaciones**
- El retiro no puede exceder `esperado_en_caja`; si el conteo lo pasa, se bloquea el
  botón con la línea "Estás retirando más de lo que hay en el cajón".
- Los gastos tampoco pueden dejar el cajón en negativo.
- Doble apertura: si otro dispositivo ya abrió el turno, la vista de 4.3 redirige a 4.1
  en vez de crear un segundo turno.
- Cada POST lleva `turno_id`; un movimiento nunca se registra contra un turno cerrado.

---

## 8. Pendiente de decidir

- **Cierre de turno y arqueo final.** No diseñado. Regla ya confirmada: se cuenta por
  denominación, se muestra faltante/sobrante y se exige motivo escrito.
- **Comprobante de cierre** (impreso o compartido). Sin diseñar.
- **Propinas.** No entraron en el desglose. Si se cobran en efectivo, afectan el cálculo
  del cajón y habrá que añadir la línea.
- **Umbral de retiro.** Está fijo en $200 en el prototipo. Decidir si es configurable
  por sucursal o un valor global.
