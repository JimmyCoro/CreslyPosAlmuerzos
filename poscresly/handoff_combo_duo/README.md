# Handoff: Combo Duo · unidades repetidas · Cresly POS móvil

## Overview
El **Combo Duo** es un combo con unidades repetidas: 2 porciones de pizza, 4 alitas y
2 bebidas. Este documento define cómo configurarlo en móvil sin repetir el catálogo una vez
por unidad.

En la versión actual cada unidad muestra su propio grupo con la lista completa de sabores, y
las alitas ocupan 8 filas con un "0" cada una. El resultado son unas 3,5 pantallas de scroll
y unos 12 toques para el pedido más común.

**La regla del rediseño: una elección por grupo, no por unidad.** Cada grupo pide una sola
respuesta que se aplica a todas sus unidades ("Las 2 de Peperoni", "Las 4 BBQ"). Solo cuando
el cliente pide algo distinto se abren las unidades, y aun así **el catálogo aparece una sola
vez**.

Diseñado a 390 px de ancho (iPhone 14 base). Debe funcionar de 360 a 430 px sin scroll
horizontal.

## About the Design File
`Combo Duo.dc.html` es una **referencia de diseño en HTML**: un prototipo del look previsto,
no código de producción. Los estilos están inline.

Contiene:
- **Camino rápido** — los tres grupos con todo igual, la hoja completa en una pantalla.
- **Unidades abiertas** — el grupo de porciones con "Distintas" activado.
- Las notas de cómo se optimiza y una tabla de cuánto se ahorra.

Nota: las rejillas de sabores se muestran **recortadas** (con "+7 sabores más al desplazar")
solo para que el mockup quepa en el marco. **En producción la lista va completa** y la hoja
hace scroll.

La tarea es recrearlo en **Django (templates) + Bootstrap 5**, siguiendo los patrones del
proyecto. No portes los estilos inline: traduce a utilidades de Bootstrap más un CSS propio
para lo que Bootstrap no cubre.

Este combo usa el **mismo configurador** que el resto (cabecera con progreso, pasos
resuelto/activo/pendiente, pie con cantidad y Agregar). Si ya implementaste
`handoff_combo`, esto añade un tipo de grupo más; si no, ese documento tiene la estructura
base de la hoja.

## Fidelity
**Alta fidelidad.** Colores, tipografía, espaciados y radios son finales.

---

## 1 · Estructura de la hoja

Hoja inferior casi a pantalla completa: `top:40px`, fondo `#fff`,
radio `22px 22px 0 0`, overlay `rgba(20,24,29,.42)`. Tres zonas en columna,
**la del medio con scroll**:

### Cabecera fija
`flex:0 0 auto`, padding `12px 16px 11px`, borde inferior `1px solid #eef0f3`,
columna con `gap:10px`. Asa de 38 × 4 px radio `999px` `#dfe2e7` centrada.

- Nombre "Combo Duo" 17 px/800 `letter-spacing:-.02em`, y debajo el estado
  11.5 px/600 `#8a929c`. **Cuando todo está resuelto, la sub-línea describe el combo**
  ("2 porciones · 4 alitas · 2 bebidas"); cuando falta algo, lo dice con el pendiente
  resaltado en `font-weight:800` `#c8102e` ("2 porciones · **falta la porción 2**").
- A la derecha, el precio en **19 px/800 `letter-spacing:-.03em`**, actualizado en vivo.
  Nunca $0.00.
- **Barra de progreso**: `display:flex; gap:4px`, un segmento `flex:1` de 4 px
  radio `999px` **por grupo** — tres, no uno por unidad. Resuelto `#23a05f`,
  activo `#c8102e`, pendiente `#eef0f3`.

### Zona de grupos
`flex:1; min-height:0; overflow-y:auto`, padding `12px 16px`, columna con `gap:9px`.
Cada tarjeta lleva **`flex:0 0 auto`** para que no se comprima.

### Pie fijo
`flex:0 0 auto`, padding `12px 16px 20px` (usa `max(20px, env(safe-area-inset-bottom))`),
borde superior `1px solid #e6e8ec`, `display:flex; gap:9px`,
`box-shadow:0 -8px 22px rgba(20,24,29,.06)`.

- **Stepper de cantidad** `flex:0 0 auto`: − y ＋ de 40 × 50 px, radio `12px`,
  borde `1px solid #dfe2e7`, glifo 18 px/700 `#5b6673` (`#c3c8ce` en el límite),
  cantidad 16 px/800 con `min-width:26px`.
- **Botón Agregar** `flex:1`, alto 50 px, radio `13px`, 14.5–15 px/800:
  - Completo: fondo `#c8102e`, texto `#fff`, glifo ✓ antes,
    `box-shadow:0 8px 18px rgba(200,16,46,.26)`.
  - Incompleto: fondo `#e9ebef`, texto `#8a929c`, sin sombra, **y debajo una línea de
    10.5 px/700 `#c8102e`** que dice qué falta: "Elige la porción 2 para continuar".

**La cantidad del pie multiplica el combo configurado**: dos Combo Duo idénticos se piden
subiendo la cantidad a 2, no configurando dos veces.

---

## 2 · Los tres estados de un grupo

Idénticos al resto de combos. Solo un grupo puede estar activo.

### Resuelto
Fila `display:flex; align-items:center; gap:11px`, padding `11px 13px`, radio `13px`,
fondo `#f4fbf7`, borde `1px solid #cfeadb`:
- Check en círculo de 22 px, fondo `#23a05f`, glifo ✓ 11 px `#fff`.
- **Etiqueta del grupo con el número de unidades por delante**, 11 px/800
  `letter-spacing:.07em` `#1c7a4a`: "2 PORCIONES DE PIZZA", "4 ALITAS", "2 BEBIDAS".
- **La respuesta debajo**, 13.5 px/700 `#14181d`, también con el número:
  **"Las 2 de Peperoni"**, **"Las 4 BBQ"**, "Coca-Cola · helada". Si son distintas,
  las lista: "Peperoni · Hawaiana", "2 BBQ · 2 Maracuyá".
- "Cambiar" 12 px/800 `#1c7a4a` a la derecha.

**El número por delante es lo que evita la ambigüedad** sin repetir el grupo: "Las 2 de
Peperoni" dice cuántas unidades cubre esa elección.

### Activo
Tarjeta borde `1.5px solid #14181d`, radio `14px`, `overflow:hidden`:
- **Cabecera** padding `12px 13px`, fondo `#fafbfc`, borde inferior `1px solid #eef0f3`:
  número del paso en círculo de 22 px fondo `#14181d` texto `#fff` 11 px/800;
  título 13.5 px/800 con el número de unidades ("2 porciones de pizza", "2 bebidas");
  sub-línea 11 px/600 `#8a929c` con el modo y lo que falta resaltado en `#c8102e`
  ("Distintas · **falta la porción 2**", "Ambas iguales").
- **Cuerpo** padding `12px 13px`, columna con `gap:11–12px`.

### Pendiente
Fila padding `12px 13px`, radio `13px`, fondo `#fff`, borde `1px solid #e6e8ec`:
número en círculo de 22 px fondo `#eef0f3` texto `#8a929c`; título 13.5 px/700 `#5b6673`
con el número de unidades; sub-línea 11 px/600 `#98a1ab` con lo que pedirá
("Hasta 2 sabores", "Sabor y temperatura"); chevron › 14 px `#c3c8ce`.
Se puede tocar para saltar adelante.

---

## 3 · El interruptor iguales / distintas

Es la pieza central. Todo grupo con **más de una unidad** lo lleva, en la primera fila de su
cuerpo:

Dos botones `flex:1`, `gap:7px`, padding `10px 6px`, radio `11px`, 12.5 px:
- **"Las 2 iguales"** / **"Las 4 iguales"** — el número sale del grupo.
- **"Distintas"**.

Activo: fondo `#14181d`, borde `#14181d`, texto `#fff` peso 800.
Inactivo: fondo `#fff`, borde `1px solid #dfe2e7`, texto `#5b6673` peso 700.

**Arranca siempre en "iguales".** Casi nadie pide dos porciones distintas; quien lo hace paga
un toque más, no todos los demás.

### Modo "iguales"
El catálogo aparece directamente y **una sola elección cubre todas las unidades**. La fila
resuelta dice "Las 2 de Peperoni".

### Modo "distintas" · ranuras
Aparecen **N ranuras numeradas** (`display:flex; gap:8px`, cada una `flex:1; min-width:0`,
padding `11px 12px`, radio `12px`), con la etiqueta 10 px/800 `letter-spacing:.08em`
arriba y el valor 13 px/800 abajo con ellipsis:

| Estado | Fondo | Borde | Etiqueta | Contenido |
|---|---|---|---|---|
| Llena | `#f4fbf7` | `1px solid #cfeadb` | "PORCIÓN 1" `#1c7a4a` | el sabor en `#14181d` |
| **Pendiente** | `#fff` | **`1.5px dashed #c8102e`** | "PORCIÓN 2" `#c8102e` | "Elige abajo" `#a8afb8` |

**El catálogo se muestra una sola vez debajo de las ranuras**, y el sabor que se toca cae en
la ranura pendiente. Si todas están llenas, el siguiente toque reemplaza la ranura 1 (y la 2
pasa a pendiente), o se toca una ranura para fijar cuál se edita.

Es exactamente el patrón de "mitad y mitad" del combo de pizza, generalizado a cualquier
número de unidades. **Con 3 o 4 unidades las ranuras van en dos filas** (`flex-wrap:wrap`,
cada una con `flex:1 1 calc(50% - 4px)`).

Nota de ayuda al pie del grupo, en caja `#fafbfc` borde `1px solid #eef0f3` radio `12px`
padding `11px 13px`, con glifo ⧉ 13 px `#8a929c` y texto 11.5 px/600 `#5b6673`:
"Un catálogo, no uno por unidad: el sabor que tocas cae en la ranura pendiente."

**Repetir el grupo entero por unidad (cada uno con su lista) multiplica la hoja.** Las
ranuras ocupan una fila y muestran las respuestas juntas, que es como se lee al cliente.

---

## 4 · Grupo de reparto · las 4 alitas

Mismo tipo de grupo que las 14 alitas del Mega Combo, pero con el total y el máximo del
grupo: **4 unidades entre hasta 2 sabores**.

### Con "Las 4 iguales" (por defecto)
El catálogo de sabores aparece directo y una elección pone las 4. La fila resuelta dice
"Las 4 BBQ". **Un toque.**

### Con "Distintas"
- **Barra de reparto**: `display:flex; align-items:center; gap:8px` — barra
  `flex:1; height:9px` radio `999px` fondo `#eef0f3` `overflow:hidden` `display:flex`,
  con un segmento por sabor elegido en su color y su porcentaje; al lado el contador
  **"2`/4`"** 12 px/800 (asignado en `#14181d`, total en `#98a1ab`).
- **Atajos** `flex:1`, `gap:6px`, padding `8px 5px`, radio `9px`, 11.5 px:
  "Mitad y mitad" (2 y 2) y "Limpiar".
- **Sabores elegidos con contador**, solo los que tienen cantidad > 0: fila padding
  `8px 10px`, radio `12px`, borde `1.5px solid #14181d`, punto de 8 px con el color del
  sabor, nombre 13.5 px/700, y stepper − / ＋ de 34 × 38 px radio `10px` con la cantidad
  16 px/800. Bajar a 0 devuelve el sabor a los chips.
- **Sabores disponibles como chips**: `flex-wrap:wrap; gap:6px`, padding `9px 12px`,
  radio `999px`, fondo `#fff`, borde `1px solid #dfe2e7`, nombre 12.5 px/700 `#4a545f`
  y un ＋ de 14 px `#8a929c`. Al alcanzar el máximo de sabores, los restantes se atenúan
  (fondo `#f4f5f7`, texto `#a8afb8`, sin borde, no tocables).

**El máximo de sabores sale del grupo, no de una constante**: 14 alitas → 3 sabores,
4 alitas → 2. Repartir 4 unidades entre 3 sabores no tiene sentido en la práctica.

**Nunca las 8 filas del catálogo con un cero cada una**: obligan a leerlas todas para
encontrar las que tienen algo.

---

## 5 · Grupo compuesto · las 2 bebidas

Un grupo con **sub-grupos**: sabor y temperatura. Con el interruptor en "Las 2 iguales", una
elección de cada sub-grupo cubre ambas bebidas.

**SABOR** — etiqueta 10.5 px/800 `letter-spacing:.08em` `#8a929c` y rejilla de 2 columnas,
`gap:7px`: botones padding `12px 10px`, radio `11px`, 13 px/700, centrados.
Seleccionado: fondo `#14181d`, borde `1.5px solid #14181d`, texto `#fff` peso 800 con ✓.

**TEMPERATURA** — dos botones `flex:1`, `gap:7px`, padding `12px 8px`, radio `11px`,
13 px, con glifo antes:
| Opción | Glifo | Seleccionado |
|---|---|---|
| Helada | ❄ | fondo `#e9f1fb`, borde `1.5px solid #1d5a9e`, texto `#1d5a9e` peso 800 |
| Al ambiente | ☀ | fondo `#fff`, borde `1px solid #dfe2e7`, texto `#5b6673` peso 700 |

Con "Distintas", cada ranura de bebida abre **sabor y temperatura propios**: la ranura
muestra "Coca-Cola · helada" y al tocarla se editan sus dos sub-grupos. La temperatura viaja
en la comanda.

---

## 6 · Cuánto se ahorra

| Grupo | Hoy | Ahora | Toques |
|---|---|---|---|
| 2 porciones de pizza | 2 listas de 11 | 1 elección | −1 |
| 4 alitas | 8 filas con 0 | 1 atajo | −7 |
| 2 bebidas | 2 listas de 6 | 1 elección + temperatura | −1 |
| **Alto de la hoja** | **≈3,5 pantallas** | **1 pantalla** | — |
| **Toques para el pedido común** | **12** | **4** | **−8** |

---

## Interactions & Behavior
- **Al abrir**, el grupo 1 está activo, el resto pendientes, y **todos los interruptores en
  "iguales"**. Al resolver un grupo se colapsa y se abre el siguiente pendiente.
- **"Cambiar"** reabre un grupo resuelto sin perder los demás.
- **Pasar de "iguales" a "distintas"** copia la elección actual a la ranura 1 y deja la 2
  pendiente. **De "distintas" a "iguales"** conserva la ranura 1 y descarta el resto,
  avisando en la sub-línea.
- **El precio se recalcula en cada toque**: base + recargos de las unidades que los tengan.
  En modo "iguales", un sabor con recargo lo aplica a **todas** las unidades del grupo
  (2 porciones premium = 2 recargos) — confírmalo con tu regla de negocio y decídelo en el
  modelo.
- **Validación de "Agregar"**: todos los grupos requeridos resueltos, todas las ranuras
  llenas y, en los de reparto, la suma exacta. El motivo del bloqueo se muestra bajo el
  botón.
- Transiciones `.12s ease`; la hoja entra deslizando desde abajo; el colapso/expansión de un
  grupo anima su alto en `.15s ease`.
- **Táctil**: botones de sabor y temperatura 44–46 px de alto, steppers 38–50 px,
  chips 36 px, Agregar 50 px. Nada por debajo de 36 px.

## State Management

Los combos se modelan como **grupos genéricos**, no con campos fijos por producto. El Combo
Duo añade el atributo `unidades` y el modo `iguales|distintas`:

```
producto: {
  id, nombre, es_combo: true, precio_base: Decimal,
  grupos: [ {
    id, nombre,                  # "Porciones de pizza", "Alitas", "Bebidas"
    tipo: 'unico'                # elige uno
        | 'reparto'              # reparte N unidades entre hasta M opciones
        | 'compuesto',           # sub-grupos (bebida: sabor + temperatura)
    unidades: int,               # 2 porciones, 4 alitas, 2 bebidas  (1 = grupo simple)
    permite_distintas: bool,     # muestra el interruptor si unidades > 1
    max_opciones: int|null,      # 2 en las 4 alitas, 3 en las 14
    subgrupos: [grupo]|null,
    requerido: bool,
    opciones: [ { id, nombre, recargo: Decimal, color: str|null } ]
  } ]
}

seleccion: {
  cantidad: int,
  nota: str,
  grupos: { <grupo_id>: {
      modo: 'iguales' | 'distintas',
      valor: opcion_id                       # modo iguales, tipo 'unico'
           | [opcion_id, opcion_id, ...]     # modo distintas, una por unidad
           | { <opcion_id>: cantidad }       # tipo 'reparto'
           | { <subgrupo_id>: opcion_id }    # tipo 'compuesto', modo iguales
           | [ {<subgrupo_id>: opcion_id}, … ]  # tipo 'compuesto', modo distintas
  } }
}
```

Derivados que calcula la **vista o el modelo**, no el template:
- `precio(seleccion)` = base + recargos, × cantidad.
- `etiqueta_grupo(grupo)` → "2 porciones de pizza", "4 alitas" (número + nombre).
- `resumen(grupo, seleccion)` → **el texto con el número por delante**:
  "Las 2 de Peperoni", "Las 4 BBQ", "Peperoni · Hawaiana", "2 BBQ · 2 Maracuyá".
- `ranura_pendiente(grupo)` → índice de la primera ranura vacía, para dirigir el toque.
- `asignado(grupo)` / `unidades` y los segmentos de la barra de reparto.
- `puede_agregar(seleccion)` → bool + **motivo en texto**. De ahí sale el estado del botón,
  la línea roja debajo y el resaltado de la cabecera y de la sub-línea del grupo activo —
  **una sola fuente de verdad**, no cuatro comprobaciones distintas.

La selección vive en el cliente mientras la hoja está abierta (Alpine, HTMX con estado en
sesión, o un pequeño store JS): recalcular el precio en cada toque no debe costar un
round-trip.

---

## Design Tokens

**Colores**
| Token | Hex | Uso |
|---|---|---|
| ink | `#14181d` | texto principal, opción seleccionada, grupo activo |
| text-2 | `#4a545f` | nombre en los chips de sabor, nota de ayuda |
| text-3 | `#5b6673` | glifos, grupo pendiente, opciones inactivas |
| muted-2 | `#8a929c` | etiquetas de sección, sub-líneas |
| muted-3 | `#98a1ab` | notas, total de la fracción |
| faint | `#a8afb8` / `#c3c8ce` | "Elige abajo", chips atenuados, steppers al límite |
| surface | `#ffffff` | hoja, tarjetas, botones sin seleccionar |
| surface-2 | `#fafbfc` | cabecera del grupo activo, caja de la nota |
| page | `#f4f5f7` | chips atenuados |
| segmented-bg | `#e9ebef` | botón Agregar deshabilitado |
| border | `#e6e8ec` | borde de grupo pendiente |
| border-soft | `#eef0f3` | divisores, pista de las barras |
| border-input | `#dfe2e7` | bordes de botón, steppers, asa |
| brand | `#c8102e` | Agregar, lo que falta, grupo activo en la barra, ranura pendiente |
| green | `#23a05f` | check de resuelto, segmentos resueltos de la barra |
| green-dark | `#1c7a4a` | etiqueta y "Cambiar" de un grupo resuelto |
| green-tint | `#f4fbf7` bg · `#cfeadb` borde | grupo resuelto, ranura llena |
| blue | `#1d5a9e` sobre `#e9f1fb` | temperatura helada |
| amber-dark | `#8a5800` | recargos ("+$1") |
| amber-tint | `#fdf3e2` | pill de recargo |
| overlay | `rgba(20,24,29,.42)` | fondo detrás de la hoja |

**Tipografía:** Plus Jakarta Sans (600/700/800), fallback Helvetica, Arial, sans-serif.
`font-feature-settings:'tnum' 1` en el contenedor raíz.
Escala usada: 9.5, 10, 10.5, 11, 11.5, 12, 12.5, 13, 13.5, 14.5, 16, 17, 18, 19 px.
`letter-spacing` negativo en cifras y títulos (−.01 a −.03em), positivo en etiquetas
mayúsculas (.07 a .08em).

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
- **Un solo parcial por tipo de grupo**, con el interruptor y las ranuras dentro:
  `_grupo_unico.html`, `_grupo_reparto.html`, `_grupo_compuesto.html`, más
  `_interruptor_unidades.html`, `_ranuras.html`, `_paso_resuelto.html`,
  `_paso_pendiente.html`. Un bucle sobre `producto.grupos` los renderiza todos — **no
  escribas markup específico para "Combo Duo"**.
- La zona de grupos es `overflow-y:auto` y **cada tarjeta lleva `flex-shrink:0`**: sin eso
  el contenido del grupo activo se comprime y se recorta.
- Las rejillas de opciones son CSS Grid directo
  (`grid-template-columns:repeat(2,1fr)`), no las 12 columnas de Bootstrap.
- El color de cada sabor de reparto sale del modelo (`opcion.color`); si no lo tiene, asigna
  uno de una paleta cíclica de 8 tonos.
- Usa `Decimal` para precios y recargos, nunca float.
- Los botones de opción no son `btn-check` de Bootstrap si necesitas el ✓ y el pill de
  recargo dentro: radios ocultos + labels propios.
- El catálogo del prototipo es **de ejemplo** (sabores, precios, recargos). Sustitúyelo por el
  real. Si un grupo no tiene recargos, no muestres pills.
- Las rejillas del prototipo están recortadas para que el mockup quepa: **en producción la
  lista va completa**.

## Assets
Ninguno. El prototipo usa glifos de texto como marcadores: `✓ ＋ − › ❄ ☀ ⧉`.
Reemplázalos por el set de iconos del proyecto — Bootstrap Icons encaja:
`check-lg`, `plus-lg`, `dash-lg`, `chevron-right`, `snow`, `sun`, `copy`.
**No hay imágenes de producto.**

## Files
- `Combo Duo.dc.html` — el camino rápido, las unidades abiertas, las notas de optimización y
  la tabla de ahorro.
