# Handoff — Menú del día (Almuerzos, móvil)

POS Cresly · Suc. Centro · Django + Bootstrap 5
Diseño de referencia: `Menu del dia.dc.html` (en esta carpeta)

> **Los datos del prototipo son de ejemplo.** Platos, porciones, precios y fechas están
> puestos para probar la maqueta. Nada de eso debe quedar en el código.

---

## 1. Overview

Almuerzos es el segundo módulo padre de la app, junto a Pizzería. Funciona distinto:
no hay catálogo fijo, hay un **menú que se arma cada mañana** con platos que salen de la
base, cada uno con un número de porciones disponibles.

Este handoff cubre las dos pantallas de ese ciclo:

**Menú del día** — solo lectura. Muestra qué sopas y qué segundos hay hoy y cuántas
porciones quedan de cada uno. Es la pantalla que el cajero mira veinte veces al día para
responder "¿todavía hay pescado?".

**Configurar menú** — la de escritura. Se eligen los platos del recetario y se fija el
cupo de cada uno.

La separación es estricta: la pantalla de menú no edita nada, la de configurar no
informa de ventas.

**Decisión de fondo:** el módulo hereda el sistema visual de Pizzería sin excepciones.
Los degradados por categoría de la versión actual —rojo sopas, verde segundos, naranja
postres— desaparecen: en este sistema el color dice **estado**, no categoría.

---

## 2. Estructura

```
Almuerzos › Menú
│
├── 1A  Menú del día · sin configurar     ← lo que se ve a las 10 am
├── 1B  Menú del día · publicado          ← el resto del día, solo lectura
│       │
│       └── botón / ⋯ ──► 1C  Configurar menú   (pantalla completa)
│                             │
│                             └── ranura ──► 1D  Elegir plato (hoja inferior)
```

### Rutas sugeridas

```
GET  /almuerzos/menu/                  1A o 1B según menu.publicado
GET  /almuerzos/menu/configurar/       1C
GET  /almuerzos/menu/platos/?cat=sopa  1D — parcial de la hoja
POST /almuerzos/menu/ranura/           asignar plato + cupo a una ranura
POST /almuerzos/menu/publicar/         valida campos_faltantes() y publica
POST /almuerzos/menu/copiar/<fecha>/   copia un menú anterior a hoy
```

---

## 3. Chrome compartido

**Header — 52 px, idéntico al de Pizzería.** Solo cambia el nombre: "Cresly Almuerzos" /
"Suc. Centro". ☰ 44 px · logo 30 px radio 9 `#c8102e` · ☾ 44 px · avatar 34 px + caret.

**Subheader — 56 px.** Título 17/800 `-.02em`. La sub-línea usa el resaltado del sistema
(`sub_pre` / `sub_hi` / `sub_hi_tono` / `sub_post`), armado en el backend:

| Pantalla | sub_pre | sub_hi | tono | sub_post |
|---|---|---|---|---|
| 1A sin configurar | `Sábado 12 · ` | `faltan sopas y segundos` | rojo `#c8102e` | — |
| 1B publicado | `Sábado 12 · ` | `48 almuerzos disponibles` | verde `#1c7a4a` | — |
| 1C configurar | `Sábado 12 · ` | `faltan 2 sopas y 1 segundo` | rojo `#c8102e` | — |

La fecha va en español y abreviada: "Sábado 12", no "Saturday, 12 de September". El año
y el mes no se imprimen — siempre es hoy.

**Tab bar — 78 px.** Pedidos · Listos · Caja · Menú, con Menú activa (`#fdecef` /
`#c8102e`). *Las etiquetas están por confirmar: ver §9.*

**El ＋ flotante no va en esta pantalla.** Pertenece a Pedidos. En Menú, la acción
primaria es configurar, y va como botón de 52 px sobre la tab bar.

---

## 4. Pantallas

### 4.1 Menú del día — sin configurar (1A)

Es la pantalla de las 10 de la mañana y la más importante del módulo: define qué se
puede vender hoy.

Dos secciones, SOPAS y SEGUNDOS. Cada una con encabezado 11/800 `.09em` `#5b6673` y, a
su derecha, lo que falta en 11/700 `#c8102e` ("falta elegir 2").

Cuerpo de cada sección: tarjeta `#fff`, borde `#f4d3d9`, banda izquierda de 3 px
`#c8102e`, radio 14, padding 15:

- Título 12.5/800 `#a90d27` — "Sin sopas para hoy"
- Explicación 11.5/600 `#8a929c` — "Hasta que haya al menos una, no se puede vender el
  almuerzo."

**"No configurado" es un diagnóstico, no una instrucción.** Por eso la copia dice qué
falta y qué consecuencia tiene.

Al pie, tarjeta `#fafbfc` borde `#eef0f3`: "Repetir el menú del viernes" con los platos
de ese día en la sub-línea. Configurar desde cero cada mañana es el trabajo real de esta
pantalla; conviene poder corregir en vez de empezar en blanco.

**Barra de acción** sobre la tab bar: botón de 52 px `#c8102e` radio 14, sombra
`0 8px 18px rgba(200,16,46,.26)` — "Configurar el menú".

### 4.2 Menú del día — publicado (1B)

**Solo lectura.** Ni un botón. Para cambiar algo se entra a 1C desde el `⋯` del
subheader.

Misma estructura de dos secciones. El encabezado lleva ahora el resumen en 11/600
`#a8afb8`: "2 opciones · 22 porciones".

Cuerpo: tarjeta `#fff` borde `#e6e8ec` radio 14, padding `12px 15px 12px 12px`, con una
línea por plato (gap 7):

```
[barra 3×15px]  Crema de zapallo                      18
[barra 3×15px]  Sancocho de pescado                    4
[barra 3×15px]  Tallarín saltado                 AGOTADO
```

- Barra de 3 × 15 px radio 2 con el color del estado
- Nombre 12.5/700 `-.01em` (en `#a8afb8` si está agotado)
- Porciones restantes 12/800 en el color del estado, o la etiqueta `AGOTADO`
  10.5/800 `.06em` `#a8afb8`

Al pie de la sección de segundos, la línea del jugo: punto verde de 7 px + "Jugo del
día: **maracuyá** · agua siempre disponible" en 11.5/600.

**Semáforo de disponibilidad** — el mismo patrón que las líneas de Órdenes:

| Estado | Barra | Cifra | Regla |
|---|---|---|---|
| `disponible` | `#23a05f` | `#1c7a4a` | quedan más de 5 porciones |
| `por_agotarse` | `#d99000` | `#8a5800` | quedan 5 o menos |
| `agotado` | `#c3c8ce` | `#a8afb8` + AGOTADO | quedan 0 |

El umbral de "por agotarse" es configurable; 5 es el valor del prototipo.

### 4.3 Configurar menú (1C)

**Pantalla completa, no modal.** El modal con ✕ en la esquina es un patrón de escritorio:
en 390 px ocupa toda la pantalla igual, pero con menos sitio y una cabecera prestada.
Aquí hay ‹ atrás de 38 px, subheader propio y barra de acción fija, como en *Cobrar* o
*Abrir caja*.

En el subheader, a la derecha: botón "Copiar ayer" de 38 px, borde `#dfe2e7`, 12/800
`#4a545f`. Llena todas las ranuras con el menú del día anterior.

**Secciones.** Encabezado con tres datos en una línea: nombre 11/800 `.09em` `#5b6673`,
la regla en el centro (`obligatorio · elige 2` en `#c8102e`, u `opcional` en `#8a929c`) y
el avance a la derecha (`1 de 2` en 11/700 `#a8afb8`).

**Ranura vacía** — 52 px, radio 13, **borde discontinuo**. La siguiente por llenar va en
`#fff` con borde `#dfe2e7` y texto `#c8102e`; las posteriores en `#fafbfc` con borde
`#e6e8ec` y texto `#a8afb8`. Hay un orden sugerido, pero no se bloquea nada.

```
＋ Elegir primera sopa      ← activa, roja
＋ Elegir segunda sopa      ← siguiente, gris
```

**Ranura llena** — tarjeta `#fff` borde `#e6e8ec` radio 13, padding `11px 12px`:
nombre del plato 13/800, sub-línea "Toca para cambiar" 11/600 `#8a929c`, y a la derecha
el stepper de porciones: `−` 38 px · cifra 15/800 (min-width 28, centrada) · `+` 38 px.
Es el mismo control del conteo por denominación de Caja.

**Añadir opcional** — fila de 38 px centrada, 12.5/700 `#8a929c`:
"＋ Añadir un tercer segundo". Sin borde: es una acción secundaria, no una ranura.

**Nota del agua** — `#fafbfc`, borde `#eef0f3`, radio 13, punto verde de 7 px:
"**Agua** siempre está disponible. No se configura ni se agota." En la versión actual
esto era una línea suelta —"Jugo fijo: Agua"— sin control ni explicación.

**Barra de acción** — `#fff`, borde superior `#e6e8ec`, sombra
`0 -8px 22px rgba(20,24,29,.07)`, padding `12px 14px 16px`:

- Botón "Publicar menú" de 52 px. **Bloqueado** mientras falten obligatorios:
  `#e9ebef` / texto `#a8afb8`
- Debajo, línea 11/700 `#c8102e`: "Faltan 2 sopas y 1 segundo"

Una sola función en el backend —`campos_faltantes()`— alimenta el estado del botón, esa
línea y el resaltado del subheader. Nunca un botón gris sin explicación.

### 4.4 Elegir plato (1D, hoja inferior)

Reemplaza al `<select>` nativo con "---------". Radio `22px 22px 0 0`, padding
`14px 16px 20px`, asa de 38 × 4 px `#dfe2e7`, overlay `rgba(20,24,29,.42)`, sin ✕.

- **Título** 17/800 con el nombre de la ranura ("Primera sopa"), y sub-línea con el dato
  que evita repetir plato: "**Sancocho** se sirvió hace 3 días"
- **Buscador** de 44 px, fondo `#f4f5f7`, radio 12
- **LAS MÁS SERVIDAS** — lista ordenada por frecuencia del mes. Cada fila: nombre 13/800,
  sub-línea "Servida 9 veces este mes" 11/600, y a la derecha un radio de 22 px.
  Seleccionada: borde 1.5 px `#c8102e`, fondo `#fdecef`, texto `#a90d27`, radio relleno
  con ✓
- **Crear una sopa nueva** — fila de 44 px con borde discontinuo. Da de alta en el
  recetario sin salir de la hoja
- **Porciones** — "¿Cuántas porciones salen?" 12.5/800 + el stepper de 38 px
- **Acción** — botón de 52 px `#c8102e` con el resultado escrito en el label:
  "Poner sancocho, 30 porciones"

El plato se elige tocando el plato, no desplegando una rueda del sistema.

---

## 5. Datos que necesita la vista

```python
menu = {
  "fecha": date,
  "publicado": bool,
  "precio_almuerzo": Decimal,
  "almuerzos_disponibles": int,   # mínimo entre categorías obligatorias
  "categorias": [
    {
      "nombre": "Sopas",
      "obligatoria": True,
      "min": 2, "max": 3,
      "ranuras": [
        {
          "plato": {"id", "nombre"} | None,
          "cupo": int,
          "vendidos": int,
          "restantes": int,
          "estado": "disponible|por_agotarse|agotado",
        },
      ],
    },
  ],
  "jugo_del_dia": str | None,     # el agua no se modela como ranura
  "menu_anterior": {"fecha", "resumen": str},
}

# Recetario, para 1D
plato = {"id", "nombre", "categoria", "veces_servido_mes": int,
         "ultima_vez": date | None}
```

**Reglas de cálculo**

```
restantes             = cupo − vendidos
almuerzos_disponibles = min( Σ restantes de cada categoría obligatoria )
campos_faltantes()    → ["2 sopas", "1 segundo"]   # única fuente de verdad
```

`almuerzos_disponibles` y `campos_faltantes()` se calculan en la vista, nunca en el
template. El template no recorre categorías para contar.

---

## 6. Tokens

**Tipografía** — Plus Jakarta Sans 400–800, fallback Helvetica/Arial.
`font-feature-settings:'tnum' 1` en el contenedor raíz.
Escala usada: 10.5 · 11 · 11.5 · 12 · 12.5 · 13 · 13.5 · 15 · 17 px.
`letter-spacing` −.01 a −.02em en cifras y títulos, +.06 a .09em en etiquetas mayúsculas.

**Color** — el mismo sistema de Pizzería, sin añadidos:

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
| verde / disponible | `#23a05f` · texto `#1c7a4a` |
| ámbar / por agotarse | `#d99000` · texto `#8a5800` |

**Semántica** — `#c8102e` falta algo obligatorio · `#1c7a4a` disponible ·
`#8a5800` se está acabando · `#a8afb8` agotado u opcional vacío.
**Nunca** un color por categoría.

Tema oscuro: superficies `#1a1f25` / `#242b33`, bordes `#2b333b`, texto `#f2f4f6` /
`#8d97a2`, marca `#e02040`.

**Radios** — 2 (barras) · 11 · 12 · 13 · 14 · 22 · 999px
**Sombras** — primario `0 8px 18px rgba(200,16,46,.26)` · barra `0 -8px 22px rgba(20,24,29,.07)`
**Táctil** — nada por debajo de 38 px; acciones primarias 52 px

---

## 7. Qué cambió respecto a la versión actual

| Antes | Ahora |
|---|---|
| Degradados rojo/verde/naranja por categoría | La categoría es un título; el color dice estado |
| "No configurado" | "Falta elegir 2" + la consecuencia escrita |
| Modal con ✕ | Pantalla completa con ‹ atrás y barra de acción |
| `<select>` nativo con "---------" | Hoja inferior con buscador y frecuencia de uso |
| Campo numérico suelto | Stepper −/+ de 38 px, el mismo de Caja |
| "Jugo fijo: Agua" sin explicar | Nota con punto verde y la regla escrita |
| Tarjeta negra con precio y totales | Fuera: el dato vivo está en el subheader |
| Postre y extras compitiendo en la lista | Fuera de la pantalla de menú |
| "Saturday, 12 de September" | "Sábado 12" |
| ＋ flotante sobre la tab bar | La acción primaria es un botón de 52 px |

---

## 8. Notas de implementación (Django + Bootstrap 5)

**Plantillas**

```
templates/almuerzos/
  menu.html              # 1A o 1B según menu.publicado
  configurar.html        # 1C
  _subheader.html        # compartido con Pizzería
  _seccion_lectura.html  # encabezado + líneas con semáforo
  _ranura.html           # vacía (borde discontinuo) o llena (con stepper)
  _hoja_plato.html       # 1D
```

**Qué no hacer**

- No reintroducir color por categoría, ni en badges, ni en bordes, ni en fondos.
- No poner acciones en 1B. Es de lectura; la edición vive en 1C.
- No usar `<select>` nativo para elegir plato: la hoja da búsqueda, frecuencia y alta
  nueva, y un `<select>` no da ninguna de las tres.
- No calcular `almuerzos_disponibles` ni `campos_faltantes()` en el template.
- No mostrar el botón "Publicar" habilitado sin validar en el POST. El estado del botón
  es una ayuda visual, no la validación.

**Bootstrap** — de Bootstrap se usan el offcanvas inferior para 1D (con radio, padding y
asa sobreescritos, `data-bs-backdrop` al 42%) y los utilities de espaciado. Las tarjetas
son flex con `gap`, no la retícula. Las clases de color de Bootstrap no se usan.

**Actualización en vivo** — 1B cambia sola mientras se venden almuerzos. Polling cada
15–20 s del parcial de secciones es suficiente; no hace falta websocket.

**Estados intermedios**
- Menú a medias (una sopa, ningún segundo): 1A muestra la sopa elegida en su sección y
  el bloque rojo solo en segundos.
- Todo agotado antes de cerrar: la sub-línea pasa a `agotado por hoy` en `#c8102e` y el
  módulo de pedidos debe impedir vender. Esa regla vive en Pedidos, no aquí.

---

## 9. Pendiente de confirmar

- **Las pestañas.** Las puse como *Pedidos · Listos · Caja · Menú*; en la captura la
  tercera no se lee. Confirmar nombres e iconos.
- **El postre.** ¿Entra en el precio del almuerzo o se cobra aparte? Ahora mismo está
  fuera de la pantalla de menú; si entra en el precio, necesita su propia sección en 1C.
- **Los extras.** Se configuran, pero ¿dónde? No están en este handoff.
- **El cupo.** Lo dibujé **por plato**, que es lo que permite agotar el pescado sin
  cerrar la venta del almuerzo. Si en la práctica se lleva un cupo único por almuerzo
  completo, cambia 1B entero.
- **Menús por franja** (almuerzo y merienda el mismo día). No contemplado.
