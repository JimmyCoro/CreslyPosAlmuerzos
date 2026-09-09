# Handoff: Configurador de combo · móvil · Cresly POS

## Overview
La hoja que se abre al tocar un **combo** en el punto de venta: el artículo con varios
grupos de opciones encadenados. El caso de referencia es "Mega Combo 1", que pide cuatro
decisiones:

1. **Tamaño** — Pequeña / Mediana / Familiar. **Define el precio base del combo.**
2. **Pizza** — un solo sabor o mitad y mitad (2 sabores). Algunos sabores tienen recargo.
3. **14 alitas** — repartidas entre hasta 3 sabores de un catálogo de 8 (ej. 6 BBQ + 8
   Maracuyá). La suma debe dar exactamente 14.
4. **Bebida** — sabor (6 opciones) **y temperatura** (helada / al ambiente).

Es el rediseño de la hoja que ya existe. Conserva la lógica (grupos, requeridos, contadores
de alitas, "Faltan N", cantidad y botón "Agregar · $X") y resuelve lo que hoy la hace lenta:

- Los cuatro grupos están **abiertos a la vez**: la hoja mide más de tres pantallas y hay que
  recorrer unos 30 botones sin saber cuánto falta.
- El total dice **$0.00** hasta el final, aunque el tamaño ya esté elegido.
- "Mitad y mitad (2 sabores)" es un checkbox que **no dice qué mitad se está eligiendo**.
- El pill naranja "Premium" **no dice el recargo**.
- Las 8 filas de alitas muestran **un "0" cada una**: hay que leerlas todas para encontrar las
  que tienen algo, y el "Faltan 6" en rojo queda lejos de los contadores.
- **Falta la temperatura de la bebida** — hoy se pregunta de viva voz.
- El botón "Agregar · $0.00" está **activo aunque no se haya elegido nada**.

Diseñado a 390 px de ancho (iPhone 14 base). Debe funcionar de 360 a 430 px sin scroll
horizontal.

## About the Design File
`Combo configurador.dc.html` es una **referencia de diseño en HTML**: un prototipo del look
previsto, no código de producción. Los estilos están inline.

Contiene:
- **Panel A** — paso 2 activo (sabor de pizza, con mitad y mitad a medio resolver).
- **Panel B** — paso 3 activo (reparto de las 14 alitas).
- **Panel C** — paso 4 activo (bebida) con el combo completo y el resumen.
- Las notas de qué cambió y por qué.
- **"Los tres estados de un paso"**: resuelto, activo y pendiente, en detalle.

Nota: los paneles A y B muestran la rejilla de sabores **recortada** (con la nota
"+7 sabores más al desplazar") solo para que el mockup quepa en el marco. **En la
implementación real la lista va completa** y la hoja hace scroll.

La tarea es recrearlo en **Django (templates) + Bootstrap 5**, siguiendo los patrones del
proyecto (base template, blocks, partials, staticfiles). No portes los estilos inline:
traduce a utilidades de Bootstrap más un CSS propio para lo que Bootstrap no cubre.

## Fidelity
**Alta fidelidad.** Colores, tipografía, espaciados y radios son finales.

---

## 1 · Estructura de la hoja

Hoja inferior casi a pantalla completa: `top:40px`, fondo `#fff`,
radio `22px 22px 0 0`, overlay `rgba(20,24,29,.42)`.
Tres zonas en columna, **la del medio con scroll**:

```
┌─────────────────────────────┐
│ Cabecera fija               │  ← nombre, progreso, precio, barra de 4 segmentos
├─────────────────────────────┤
│ Pasos                       │  ← zona de scroll
├─────────────────────────────┤
│ Pie fijo                    │  ← cantidad + Agregar
└─────────────────────────────┘
```

### Cabecera fija
`flex:0 0 auto`, padding `12px 16px 11px`, borde inferior `1px solid #eef0f3`,
columna con `gap:10px`. Asa de 38 × 4 px radio `999px` `#dfe2e7` centrada.

- Fila: bloque `flex:1; min-width:0` con el nombre "Mega Combo 1" 17 px/800
  `letter-spacing:-.02em`, y debajo el estado 11.5 px/600 `#8a929c`:
  "Mediana · **3 de 4 pasos**" con el conteo resaltado en `font-weight:800` `#c8102e`,
  o "**completo**" en `#1c7a4a` cuando ya no falta nada.
  A la derecha, **el precio en 19 px/800 `letter-spacing:-.03em`**, actualizado en vivo.
- **Barra de progreso por pasos**: `display:flex; gap:4px`, un segmento `flex:1` de 4 px
  radio `999px` por paso. Resuelto `#23a05f`, activo `#c8102e`, pendiente `#eef0f3`.

**El precio nunca es $0.00**: en cuanto hay tamaño elegido muestra el precio base, y suma
los recargos a medida que se eligen.

### Zona de pasos
`flex:1; min-height:0; overflow-y:auto`, padding `12px 16px`, columna con `gap:9px`.
Cada tarjeta de paso lleva **`flex:0 0 auto`** para que no se comprima.

### Pie fijo
`flex:0 0 auto`, padding `12px 16px 20px` (usa `max(20px, env(safe-area-inset-bottom))`),
borde superior `1px solid #e6e8ec`, `display:flex; gap:9px`,
`box-shadow:0 -8px 22px rgba(20,24,29,.06)`.

- **Stepper de cantidad** `flex:0 0 auto`: − y ＋ de 40 × 50 px, radio `12px`,
  borde `1px solid #dfe2e7`, glifo 18 px/700 `#5b6673` (`#c3c8ce` en el límite),
  y la cantidad 16 px/800 con `min-width:26px`.
- **Botón Agregar** `flex:1`, alto 50 px, radio `13px`, 14.5–15 px/800:
  - Completo: fondo `#c8102e`, texto `#fff`, glifo ✓ antes,
    `box-shadow:0 8px 18px rgba(200,16,46,.26)`.
  - **Incompleto**: fondo `#e9ebef`, texto `#8a929c`, sin sombra, **y debajo una línea de
    10.5 px/700 `#c8102e` que dice qué falta**: "Elige la mitad 2 para continuar",
    "Reparte las 6 alitas restantes".

El botón nunca está activo con la configuración incompleta, ni gris sin explicación.

---

## 2 · Los tres estados de un paso

Este patrón es el corazón del rediseño y **sirve para cualquier combo**, con dos grupos o con
seis. Solo un paso puede estar activo.

### Resuelto
Fila de `display:flex; align-items:center; gap:11px`, padding `10–11px 13px`,
radio `13px`, fondo `#f4fbf7`, borde `1px solid #cfeadb`:
- Check en círculo de 22 px, fondo `#23a05f`, glifo ✓ 11 px `#fff`.
- **La etiqueta del grupo arriba** 11 px/800 `letter-spacing:.07em` `#1c7a4a`
  ("TAMAÑO", "TAMAÑO Y SABOR"), y **la respuesta abajo** 12.5–13.5 px/700 `#14181d`
  ("Mediana · $20.50", "Mediana · Peperoni / Chorizo") con ellipsis.
- "Cambiar" 12 px/800 `#1c7a4a` a la derecha — reabre ese paso.

Se lee la respuesta, no la pregunta. El cajero puede repetirle al cliente lo que ya lleva sin
desarmar nada.

Pasos contiguos ya resueltos **pueden fusionarse en una sola fila** ("TAMAÑO Y SABOR") para
ahorrar alto cuando hay muchos grupos.

### Activo
Tarjeta con borde `1.5px solid #14181d`, radio `14px`, `overflow:hidden`:
- **Cabecera** padding `12px 13px`, fondo `#fafbfc`, borde inferior `1px solid #eef0f3`:
  número del paso en círculo de 22 px fondo `#14181d` texto `#fff` 11 px/800; título
  13.5 px/800 `letter-spacing:-.01em`; sub-línea 11 px/600 `#8a929c` con lo que falta
  resaltado en `#c8102e` ("Mitad y mitad · **falta la mitad 2**",
  "**Faltan 6** por repartir").
- **Cuerpo** padding `12px 13px`, columna con `gap:11–12px`.

### Pendiente
Fila padding `12px 13px`, radio `13px`, fondo `#fff`, borde `1px solid #e6e8ec`:
número en círculo de 22 px fondo `#eef0f3` texto `#8a929c`; título 13.5 px/700 `#5b6673`;
sub-línea 11 px/600 `#98a1ab` con lo que pedirá ("Hasta 3 sabores",
"Sabor y temperatura"); chevron › 14 px `#c3c8ce`.

**Se puede tocar para saltar adelante.** El orden sugerido es el natural, no una imposición.

---

## 3 · Paso de tamaño

Primer paso, siempre requerido. Botones en rejilla de 2 columnas, `gap:7px`,
padding `12px`, radio `11px`: nombre 13.5 px/700 y el precio debajo 12 px/700.
Activo: fondo `#14181d`, texto `#fff`. Inactivo: fondo `#fff`,
borde `1px solid #dfe2e7`.

**El tamaño elegido fija el precio base del combo** y se refleja de inmediato en la cabecera.
Cambiarlo después conserva las demás elecciones y solo recalcula el total.

---

## 4 · Paso de pizza · mitad y mitad

### Selector de modo
Dos botones `flex:1`, `gap:7px`, padding `10px 6px`, radio `11px`, 12.5 px:
**"Un solo sabor"** y **"Mitad y mitad"**. Activo fondo `#14181d` texto `#fff` peso 800;
inactivo fondo `#fff` borde `1px solid #dfe2e7` texto `#5b6673` peso 700.

Reemplaza el checkbox "Mitad y mitad (2 sabores)": un interruptor con dos estados nombrados
se entiende sin leer.

### Las dos ranuras
Al elegir "Mitad y mitad" aparecen **dos ranuras** (`display:flex; gap:8px`, cada una
`flex:1; min-width:0`, padding `11px 12px`, radio `12px`), con la etiqueta
10 px/800 `letter-spacing:.08em` arriba y el sabor 13 px/800 abajo con ellipsis:

| Estado | Fondo | Borde | Etiqueta | Contenido |
|---|---|---|---|---|
| Llena | `#f4fbf7` | `1px solid #cfeadb` | "MITAD 1" `#1c7a4a` | el sabor en `#14181d` |
| **Pendiente** | `#fff` | **`1.5px dashed #c8102e`** | "MITAD 2" `#c8102e` | "Elige abajo" `#a8afb8` |

**El sabor que se toca cae en la ranura pendiente.** Si las dos están llenas, el siguiente
toque reemplaza la ranura 1 (y la 2 pasa a pendiente), o se toca una ranura para fijar cuál
se está editando.

Esto resuelve el problema central del diseño actual: con el checkbox marcado, tocar sabores
no dice a qué mitad van.

### Rejilla de sabores
`display:grid; grid-template-columns:1fr 1fr; gap:7px`. Cada botón padding `12px 10px`,
radio `11px`, 13 px/700, centrado. Los nombres largos ("Pimientos y Peperoni") bajan a
12.5 px con `line-height:1.25` y `text-align:center`.
- Seleccionado: fondo `#14181d`, borde `1.5px solid #14181d`, texto `#fff` peso 800,
  con un ✓ después del nombre.
- Sin seleccionar: fondo `#fff`, borde `1px solid #dfe2e7`.

**Sabores con recargo**: pill de `padding:1px 6px`, radio `999px`, fondo `#fdf3e2`,
texto `#8a5800` 9.5 px/800 con **el monto: "+$1"** — no la palabra "Premium".
El recargo aparece luego desglosado en el resumen.

En mitad y mitad, el recargo se cobra **una vez** aunque solo una mitad sea premium (o según
tu regla de negocio — decídelo en el modelo, no en el template).

---

## 5 · Paso de alitas · repartir N entre hasta M sabores

El paso más delicado: **la suma debe dar exactamente 14**.

### Barra de reparto
`display:flex; align-items:center; gap:8px`:
- Barra `flex:1; height:9px`, radio `999px`, fondo `#eef0f3`, `overflow:hidden`,
  `display:flex` — **un segmento por sabor elegido**, con su color y su ancho al
  porcentaje correspondiente. Los colores salen de una paleta fija por sabor
  (ej. BBQ `#d99000`, Maracuyá `#8a5800`).
- Contador **"8`/14`"** 12 px/800: el asignado en `#14181d` y el total en `#98a1ab`.

Reemplaza el "Faltan 6" en rojo que aparecía lejos de los contadores.

### Atajos
Tres botones `flex:1`, `gap:6px`, padding `8px 5px`, radio `9px`, 11.5 px:
- **"Todas iguales"** — pone las 14 en el primer sabor elegido (activo fondo `#14181d`).
- **"Mitad y mitad"** — reparte entre los dos primeros (7 y 7; el impar va al primero).
- **"Limpiar"** — vuelve todo a 0.

Casi ningún cliente pide tres sabores con números exactos: estos atajos resuelven la mayoría
de un toque.

### Sabores elegidos · con contador
Solo los que tienen cantidad > 0, arriba. Fila `display:flex; align-items:center; gap:10px`,
padding `8px 10px`, radio `12px`, borde `1.5px solid #14181d`, fondo `#fff`:
- punto de 8 px con **el color del sabor** (el mismo de la barra);
- nombre 13.5 px/700 `flex:1; min-width:0`;
- stepper: − y ＋ de 34 × 38 px, radio `10px`, borde `1px solid #dfe2e7`,
  glifo 16 px/700 `#5b6673`, y la cantidad 16 px/800 con `min-width:26px`.
  Bajar a 0 devuelve ese sabor a los chips.
- El ＋ se deshabilita (`#c3c8ce`) al llegar al total.

### Sabores disponibles · como chips
Divisor `1px #eef0f3`, y debajo `display:flex; flex-wrap:wrap; gap:6px`.
Cada chip padding `9px 12px`, radio `999px`, fondo `#fff`,
borde `1px solid #dfe2e7`, nombre 12.5 px/700 `#4a545f` y un ＋ de 14 px `#8a929c`.
**Tocarlo lo sube a la lista con contador en 1** (o con el resto pendiente, si prefieres).

Con el máximo de sabores alcanzado (3), los chips restantes se atenúan:
fondo `#f4f5f7`, texto `#a8afb8`, sin borde, no tocables.

Nota de ayuda debajo: "Toca un sabor para sumarlo. Con 3 elegidos el resto se atenúa."
10.5 px/600 `#98a1ab`.

**Ocho filas con un "0" cada una** obligan a leerlas todas para encontrar las que tienen
algo. Con este patrón, lo elegido está arriba y lo disponible ocupa una fracción del alto.

---

## 6 · Paso de bebida · sabor y temperatura

Dos sub-grupos dentro del mismo paso, cada uno con su etiqueta 10.5 px/800
`letter-spacing:.08em` `#8a929c`:

**SABOR** — rejilla de 2 columnas, `gap:7px`, mismos botones que los sabores de pizza
(padding `12px 10px`, radio `11px`, 13 px/700; seleccionado `#14181d` con ✓).

**TEMPERATURA** — dos botones `flex:1`, `gap:7px`, padding `12px 8px`, radio `11px`,
13 px, con glifo antes del texto:
| Opción | Glifo | Seleccionado |
|---|---|---|
| Helada | ❄ | fondo `#e9f1fb`, borde `1.5px solid #1d5a9e`, texto `#1d5a9e` peso 800 |
| Al ambiente | ☀ | fondo `#fff`, borde `1px solid #dfe2e7`, texto `#5b6673` peso 700 |

**La temperatura viaja en la comanda**, junto al sabor. Hoy no existe en la interfaz y se
pregunta de viva voz.

---

## 7 · Resumen del combo

Aparece **al completarse todos los pasos**, debajo del último. Caja `#fafbfc`,
borde `1px solid #eef0f3`, radio `14px`, padding `12px 13px`, columna con `gap:9px`.

- Etiqueta "RESUMEN DEL COMBO" 10.5 px/800 `letter-spacing:.08em` `#8a929c`.
- Una fila por grupo (`display:flex; align-items:baseline; gap:9px`):
  - etiqueta de grupo en columna fija de 52 px, 10.5 px/800 `#98a1ab`
    `letter-spacing:.05em` (TAMAÑO, PIZZA, ALITAS, BEBIDA);
  - lo elegido `flex:1; min-width:0`, 12.5 px/700 `line-height:1.35`
    ("½ Peperoni · ½ Chorizo", "8 BBQ · 6 Maracuyá", "Coca-Cola · helada");
  - a la derecha el importe: el base en 12 px/700 `#8a929c` y **los recargos en
    `#8a5800`** ("+$1.00").
- Pie separado por `border-top:1px solid #e6e8ec`, `padding-top:9px`:
  **"Nota para cocina (opcional)"** 12.5 px/600 `#a8afb8` y un "Agregar"
  12 px/700 `#5b6673` que abre un campo de texto.

Es la última lectura antes de sumar al pedido, y el texto que se imprime en la comanda.

---

## Interactions & Behavior
- **Al abrir**, el paso 1 está activo y el resto pendientes. Al resolver uno, se colapsa y se
  abre el siguiente pendiente automáticamente.
- **"Cambiar"** en un paso resuelto lo reabre y colapsa el que estaba activo; **lo demás no
  se pierde**. Si el cambio invalida algo (cambiar de "mitad y mitad" a "un solo sabor"), se
  conserva la ranura 1 y se descarta la 2.
- **Tocar un paso pendiente** salta a él sin exigir el orden.
- **El precio se recalcula en cada toque**: base del tamaño + recargos de sabores.
- **Validación de "Agregar"**: todos los grupos requeridos resueltos y, en los de reparto, la
  suma exacta. El motivo del bloqueo se muestra bajo el botón.
- **La cantidad del pie multiplica el combo configurado**: subirla a 2 agrega dos combos
  idénticos. Para dos combos distintos, se agrega uno y se vuelve a abrir el producto.
- **Al agregar**, la hoja se cierra y la fila del producto en el catálogo muestra su badge
  "N en carrito".
- Transiciones `.12s ease`; la hoja entra deslizando desde abajo. El colapso/expansión de un
  paso anima su alto en `.15s ease`.
- **Táctil**: botones de sabor y temperatura 44–46 px de alto, steppers 38–50 px,
  chips 36 px, Agregar 50 px. Nada por debajo de 36 px.

## State Management

Los combos deben modelarse como **grupos de opciones genéricos**, no con campos fijos por
producto: un combo puede tener dos grupos o seis.

```
producto: {
  id, nombre, es_combo: true,
  grupos: [ {
    id, nombre,                          # "Tamaño", "Sabor de la pizza", "14 alitas", "Bebida"
    tipo: 'precio_base'                  # elige uno y fija el precio del producto
        | 'unico'                        # elige uno
        | 'mitades'                      # elige 1 o 2 (mitad y mitad)
        | 'reparto'                      # reparte N unidades entre hasta M opciones
        | 'compuesto',                    # varios sub-grupos (bebida: sabor + temperatura)
    requerido: bool,
    total_unidades: int|null,            # 14, solo en 'reparto'
    max_opciones: int|null,              # 3, solo en 'reparto'
    subgrupos: [grupo]|null,             # solo en 'compuesto'
    opciones: [ { id, nombre, recargo: Decimal, color: str|null, precio: Decimal|null } ]
  } ]
}

seleccion: {
  cantidad: int,
  nota: str,
  grupos: { <grupo_id>: valor }
  # 'precio_base'/'unico' → opcion_id
  # 'mitades'             → [opcion_id, opcion_id|null]
  # 'reparto'             → { <opcion_id>: cantidad }
  # 'compuesto'           → { <subgrupo_id>: opcion_id }
}
```

Derivados que calcula la **vista o el modelo**, no el template:
- `precio(seleccion)` = precio del tamaño + suma de recargos, × cantidad.
- `paso_activo`, `pasos_resueltos`, `total_pasos` para la cabecera y la barra.
- `resumen(grupo)` → el texto de la fila colapsada y del resumen final
  ("½ Peperoni · ½ Chorizo", "8 BBQ · 6 Maracuyá").
- `asignado(grupo)` / `total_unidades` y los segmentos de la barra de reparto.
- `puede_agregar(seleccion)` → bool + **motivo en texto**. De ahí sale el estado del botón,
  la línea roja debajo y el resaltado de la cabecera y de la sub-línea del paso activo —
  **una sola fuente de verdad**, no cuatro comprobaciones distintas.

La selección vive en el cliente mientras la hoja está abierta (Alpine, HTMX con estado en
sesión, o un pequeño store JS): recalcular el precio en cada toque no debe costar un
round-trip.

---

## Design Tokens

**Colores**
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | texto principal, opción seleccionada, paso activo |
| text-2 | `#4a545f` | nombre en los chips de sabor |
| text-3 | `#5b6673` | glifos, paso pendiente, opciones inactivas |
| muted-2 | `#8a929c` | etiquetas de sección, sub-líneas |
| muted-3 | `#98a1ab` | notas de ayuda, etiquetas del resumen, total de la fracción |
| faint | `#a8afb8` / `#c3c8ce` | "Elige abajo", chips atenuados, steppers al límite |
| surface | `#ffffff` | hoja, tarjetas, botones sin seleccionar |
| surface-2 | `#fafbfc` | cabecera del paso activo, caja del resumen |
| page | `#f4f5f7` | chips atenuados |
| segmented-bg | `#e9ebef` | botón Agregar deshabilitado |
| border | `#e6e8ec` | borde de paso pendiente, divisor del resumen |
| border-soft | `#eef0f3` | divisores, pista de las barras |
| border-input | `#dfe2e7` | bordes de botón, steppers, asa |
| brand | `#c8102e` | Agregar, lo que falta, paso activo en la barra, ranura pendiente |
| green | `#23a05f` | check de resuelto, segmentos resueltos de la barra |
| green-dark | `#1c7a4a` | etiqueta y "Cambiar" de un paso resuelto, "completo" |
| green-tint | `#f4fbf7` bg · `#cfeadb` borde | paso resuelto, ranura llena |
| blue | `#1d5a9e` sobre `#e9f1fb` | temperatura helada |
| amber | `#d99000` | color de sabor (BBQ) en barra y punto |
| amber-dark | `#8a5800` | **recargos** ("+$1", "+$1.00"), color de sabor (Maracuyá) |
| amber-tint | `#fdf3e2` | pill de recargo |
| overlay | `rgba(20,24,29,.42)` | fondo detrás de la hoja |

**Tipografía:** Plus Jakarta Sans (600/700/800), fallback Helvetica, Arial, sans-serif.
`font-feature-settings:'tnum' 1` en el contenedor raíz — necesario para los contadores y
precios.
Escala usada: 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14.5, 16, 17, 18, 19 px.
`letter-spacing` negativo en cifras y títulos (−.01 a −.03em), positivo en etiquetas
mayúsculas (.05 a .08em).

**Espaciado:** 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 20 px.

**Radios:** 9, 10, 11, 12, 13, 14, 22, 999px.

**Sombras:** Agregar `0 8px 18px rgba(200,16,46,.26)`;
pie de la hoja `0 -8px 22px rgba(20,24,29,.06)`.

---

## Notas de implementación (Django + Bootstrap 5)
- Variables Sass: `$primary: #c8102e`, `$body-color: #14181d`, `$border-color: #e6e8ec`,
  familia Plus Jakarta Sans. Si no compilas Sass, un `combo.css` con las variables CSS de la
  tabla basta.
- Usa el **offcanvas de Bootstrap con `placement="bottom"`** y alto `calc(100vh - 40px)`,
  o `<dialog>` con animación propia.
- Templates sugeridos: `pos/_hoja_combo.html` y un parcial **por tipo de grupo**:
  `_grupo_unico.html`, `_grupo_mitades.html`, `_grupo_reparto.html`,
  `_grupo_compuesto.html`, más `_paso_resuelto.html`, `_paso_pendiente.html`,
  `_resumen_combo.html`. **Un bucle sobre `producto.grupos` los renderiza todos** — no
  escribas markup específico para "Mega Combo 1".
- La zona de pasos es `overflow-y:auto` y **cada tarjeta de paso lleva
  `flex-shrink:0`**: sin eso, el contenido del paso activo se comprime y se recorta.
- Las rejillas de opciones son CSS Grid directo
  (`grid-template-columns:repeat(2,1fr)`), no las 12 columnas de Bootstrap.
- El color de cada sabor de reparto sale del modelo (`opcion.color`), no del template; si un
  sabor no lo tiene, asigna uno de una paleta cíclica de 8 tonos.
- Usa `Decimal` para precios y recargos, nunca float.
- Los botones de opción no son `btn-check` de Bootstrap si necesitas el ✓ y el pill de
  recargo dentro: radios ocultos + labels propios.
- El catálogo del prototipo es **de ejemplo** (sabores, precios, recargos). Sustitúyelo por el
  real. Si un grupo no tiene recargos, no muestres pills.
- Los paneles A y B del prototipo recortan la lista de sabores para que el mockup quepa:
  **en producción la lista va completa**.

## Assets
Ninguno. El prototipo usa glifos de texto como marcadores:
`✓ ＋ − › ❄ ☀`. Reemplázalos por el set de iconos del proyecto — Bootstrap Icons encaja:
`check-lg`, `plus-lg`, `dash-lg`, `chevron-right`, `snow`, `sun`.
**No hay imágenes de producto.**

## Files
- `Combo configurador.dc.html` — los tres pasos en detalle, los tres estados de un paso, el
  resumen del combo y las notas de diseño.
