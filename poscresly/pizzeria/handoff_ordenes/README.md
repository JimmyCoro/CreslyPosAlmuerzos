# Handoff — Órdenes (móvil)

POS Cresly Pizzería · Suc. Centro · Django + Bootstrap 5
Diseño de referencia: `Ordenes movil.dc.html` (en esta carpeta) — **turno 2: bloques `2A` y `2B`**

> **Los datos del prototipo son de ejemplo.** Montos, números de orden, nombres y horas
> están puestos para probar la maqueta. Nada de eso debe quedar en el código.

---

## 1. Overview

Órdenes es la lista de todo lo que está en marcha en el turno. Sustituye a la pantalla
actual, donde cada orden imprime su árbol completo de combos y una sola tarjeta puede
medir más de 300 px.

Dos decisiones ordenan el módulo:

**1. El canal son pestañas, no filtros.** Servir, Llevar y Delivery son tres formas de
trabajar distintas —en mesa se sirve platillo por platillo, en llevar se empaca todo
junto, en delivery hay repartidor y dirección—. No es un filtro más de la misma lista:
es de qué lista se trata.

**2. La lista es para mirar, no para actuar.** Ninguna tarjeta lleva botones. Un toque
despliega el detalle, otro toque entra a la orden, el asa pliega. Todas las acciones
viven dentro de la orden, donde ya están diseñadas (`Detalle orden movil` y
`Hoja acciones orden`).

De ahí sale la tercera pieza: el **semáforo por platillo**, una barra de 3 px por línea
que dice si está sin enviar, en cocina, listo o servido. Es lo que hace útil mirar sin
entrar.

**Alcance:** la pantalla de lista. El detalle de la orden y la hoja de acciones ya están
entregados en `handoff_detalle_orden/` y `handoff_hoja_acciones/`.

---

## 2. Estructura

```
Órdenes (móvil, 390 px base)
│
├── Header 52 px            ← idéntico en toda la app
├── Subheader 56 px         ← título + sub-línea con resaltado
├── Pestañas de canal 46 px ← Todas · Servir · Llevar · Delivery
│
└── Lista agrupada por estado
    ├── POR COBRAR   (n órdenes · $suma)
    ├── EN CURSO     (n órdenes)
    └── …
        │
        └── Tarjeta de orden
            ├── plegada    → cabecera sola
            └── desplegada → cabecera + líneas con semáforo + asa
```

**Dos dimensiones, dos mecanismos.** El canal va en las pestañas; el estado va en los
encabezados de grupo. Por eso desaparece la fila de chips de estado de la versión
anterior: competía con las pestañas y costaba 46 px de lista.

### Navegación

| Gesto | Resultado |
|---|---|
| Toque en fila plegada | Despliega el detalle (acordeón: cierra la que estuviera abierta) |
| Toque en la cabecera de una fila desplegada | Entra a `Detalle orden movil` |
| Toque en el asa del pie | Pliega la orden |

Un gesto, un significado. No se navega al detalle sin haber visto antes qué lleva la
orden. El chevron `›` aparece **solo** en la cabecera desplegada, para señalar la puerta;
en la fila plegada no hay chevron, porque ahí el toque despliega, no navega.

### Rutas sugeridas

```
GET  /ordenes/?canal=servir|llevar|delivery      lista (canal por querystring)
GET  /ordenes/<id>/                              detalle (ya entregado)
GET  /ordenes/<id>/lineas/  (HTMX)               parcial del desplegable
```

El desplegable puede cargar por HTMX al primer toque y quedarse cacheado en el DOM, o
venir en la respuesta inicial si la lista es corta. Con 11 órdenes activas, lo segundo
es más simple y no se nota.

---

## 3. Chrome compartido

**Header — 52 px, no cambia nunca.**
☰ 44 px · logo 30 px (radio 9, `#c8102e`) + "Cresly Pizzería" 13.5/800 y "Suc. Centro"
10.5/600 `#8a929c` · ☾ 44 px · avatar 34 px + caret. Fondo `#fff`, borde inferior
`#e6e8ec`.

**Subheader — 56 px.**
Título "Órdenes" 17/800 `-.02em`. Sub-línea 11/600 con el resaltado del sistema:

| sub_pre | sub_hi | tono | sub_post |
|---|---|---|---|
| — | `$103.25` | rojo `#c8102e` | ` por cobrar en 4 órdenes` |

Se arma en el backend con `sub_pre` / `sub_hi` / `sub_hi_tono` / `sub_post`, nunca
partiendo la cadena en el template. A la derecha, dos acciones de 38 px con borde
`#dfe2e7` y radio 11: `⌕` (buscar por número, mesa o teléfono) y `⋯` (opciones de la
lista: ordenar, ver cerradas del día, imprimir resumen del turno).

**Tab bar — 78 px.** Inicio · Mesas · Órdenes · Delivery, con Órdenes activa
(`#fdecef` / `#c8102e`).

---

## 4. Pestañas de canal (46 px)

Grid de 4 columnas iguales, padding lateral 6 px, sobre fondo `#fff`. Cada pestaña:

- Etiqueta 12.5 px · activa 800 `#c8102e`, inactiva 700 `#8a929c`
- Conteo debajo, 10.5 px · activa 800 `#c8102e`, inactiva 700 `#a8afb8`
- Subrayado de 2.5 px: `#c8102e` en la activa, `transparent` en el resto
- Altura completa táctil: 46 px × ~90 px de ancho

| Pestaña | Contenido |
|---|---|
| Todas | Todo el turno. Para el encargado que revisa de un vistazo |
| Servir | Órdenes de mesa. Es la pestaña por defecto en el turno de salón |
| Llevar | Mostrador, se empaca completo |
| Delivery | Con teléfono, dirección y repartidor |

**Los conteos van bajo la etiqueta, no como globo.** Cambian cada pocos segundos; un
globo rojo permanente deja de significar nada.

La pestaña activa se guarda en la sesión: al volver de una orden, el mesero cae en la
misma lista que dejó.

---

## 5. Grupos de estado

Encabezado 11/800 `.09em` `#5b6673` + conteo 11/600 `#a8afb8`, padding `0 2px 9px`
(y `16px 2px 9px` cuando no es el primero).

| Grupo | Sufijo | Regla |
|---|---|---|
| POR COBRAR | `n órdenes · $suma` | Todo servido/entregado, falta el dinero. Siempre arriba |
| EN CURSO | `n órdenes` | Cualquier cosa pendiente en cocina o sin enviar |
| EN CAMINO | `n órdenes` | Solo pestaña Delivery: despachadas |

Ordenar por estado y no por hora es deliberado: lo que espera dinero queda arriba
siempre, sin depender de en qué orden se abrieron las órdenes. Dentro de cada grupo, sí
cronológico (la más antigua primero — es la que lleva más tiempo esperando).

---

## 6. Tarjeta de orden

### 6.1 Plegada

`#fff`, borde `#e6e8ec`, **borde izquierdo de 3 px** con el color del estado, radio 14,
padding `12px 14px 12px 11px`, gap 11. Cuando el estado es crítico, el borde completo
sube a `#f4d3d9`.

- **Glifo de canal** — cuadro de 38 px, radio 11, fondo tintado del estado:
  `▦` mesa · `⌸` para llevar · `⇢` delivery
- **Título 13.5/800** — *destino primero, número después*: "Mesa 2 · #114",
  "Delivery · #006". El mesero busca la mesa, no el folio
- **Sub-línea 11.5/600 `#8a929c`** — dos platillos de cabecera + conteo de líneas
  (`· 9 líneas` en `#a8afb8`/700), o el resumen de estados cuando hay mezcla:
  "**1 servido** · **2 en cocina**" con cada cifra en su color
- **Derecha** — monto 17/800 `-.025em` y debajo el estado escrito 10.5/800 `.06em` en su
  color. En cocina, el estado se sustituye por el tiempo transcurrido ("18 min"), que
  dice más

Los montos van alineados a la derecha con `tnum` para que formen columna al escanear.

### 6.2 Desplegada

Misma cabecera, más `›` en `#c3c8ce` al final (15 px, `padding-top:9px` para alinear con
el monto). Debajo, bloque con `padding:0 14px 12px 60px` — la sangría de 60 px alinea las
líneas con el título, no con el glifo.

**Nombre del combo** 12.5/800 cuando las líneas pertenecen a uno.

**Líneas de platillo** — gap 6, cada una:

```
[barra 3×15px]  1 · Pizza Pequeña Ranchera           SIN ENVIAR
```

- Barra de 3 × 15 px, radio 2, color del estado de la línea
- Texto 12.5/700 `-.01em`, con la cantidad delante
- Etiqueta de estado 10.5/800 `.06em` a la derecha, en el color del estado

**Asa de cierre** — franja de 24 px al pie, con una barra de 38 × 4 px radio 999
`#c3c8ce` centrada. Mismo lenguaje que las hojas inferiores. Queda donde el ojo termina
de leer, no de vuelta arriba.

---

## 7. El semáforo por platillo

| Estado | Barra | Etiqueta | Significado |
|---|---|---|---|
| `sin_enviar` | `#c8102e` | SIN ENVIAR `#c8102e` | Está en la orden, la cocina no lo ha recibido |
| `en_cocina` | `#d99000` | EN COCINA `#8a5800` | Enviado y en preparación |
| `listo` | `#2f7fd9` | LISTO `#1d5a9e` | Terminado, espera que lo lleven a la mesa |
| `servido` | `#23a05f` | SERVIDO `#1c7a4a` | Entregado. Estado final |

**Reglas**

- La etiqueta escrita solo aparece en la orden desplegada. En la fila plegada el estado
  del platillo se resume en la sub-línea ("1 servido · 2 en cocina").
- **El peor estado de las líneas decide la banda de la tarjeta.** Si algo está sin
  enviar, la orden entera se marca en rojo, aunque el resto esté servido. El orden de
  gravedad es: `sin_enviar` > `en_cocina` > `listo` > `servido`.
- El tiempo de cocina corre desde `linea.enviado_en`, no desde que se abrió la orden.
- `servido` no vuelve atrás desde la lista. Revertirlo vive en el ⋯ de la orden, bajo
  ZONA DE RIESGO, con confirmación y motivo.

---

## 8. Datos que necesita la vista

```python
orden = {
  "numero": str,                    # "#114"
  "canal": "mesa|llevar|delivery",
  "destino": str,                   # "Mesa 2" | "Para llevar" | "0986106848"
  "comensales": int | None,
  "estado": "por_cobrar|en_curso|en_camino|pagada",
  "estado_peor": str,               # mínimo de las líneas → decide la banda de 3 px
  "total": Decimal,
  "metodo_pago": str | None,
  "abierta_en": datetime,
  "minutos_en_cocina": int | None,  # max(now - linea.enviado_en) de las líneas activas
  "resumen_items": [str, str],      # los dos primeros nombres de cabecera
  "lineas_count": int,
  "resumen_estados": str | None,    # "1 servido · 2 en cocina", armado en la vista
  "lineas_sin_enviar": int,
}

linea = {
  "cantidad": int,
  "nombre": str,                    # "Pizza Pequeña Ranchera"
  "combo": str | None,              # "Mega Combo 1 Pequeña"
  "estado": "sin_enviar|en_cocina|listo|servido",
  "enviado_en": datetime | None,
}

conteo_por_canal = {"todas": 11, "mesa": 5, "llevar": 2, "delivery": 4}
```

**Se calcula en la vista, nunca en el template:** `resumen_items`, `lineas_count`,
`resumen_estados`, `estado_peor`, los totales por grupo y los conteos por canal. El
template no recorre el árbol de combos para contar.

---

## 9. Tokens

**Tipografía** — Plus Jakarta Sans 400–800, fallback Helvetica/Arial.
`font-feature-settings:'tnum' 1` en el contenedor raíz: los montos tienen que alinearse
en columna.
Escala usada: 10.5 · 11 · 11.5 · 12.5 · 13.5 · 15 · 17 px.
`letter-spacing` −.01 a −.025em en cifras y títulos, +.06 a .09em en etiquetas mayúsculas.

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
| marca / acción | `#c8102e` · tinte `#fdecef` / borde `#f4d3d9` |
| verde / servido | `#23a05f` · texto `#1c7a4a` · `#f4fbf7` |
| ámbar / en cocina | `#d99000` · texto `#8a5800` · `#fdf3e2` |
| azul / listo | `#2f7fd9` · texto `#1d5a9e` · `#e9f1fb` |

Tema oscuro: superficies `#1a1f25` / `#242b33`, bordes `#2b333b`, texto `#f2f4f6` /
`#8d97a2`, marca `#e02040`.

**Radios** — 2 (barras) · 9 · 11 · 14 · 999px
**Sombras** — barra inferior `0 -8px 22px rgba(20,24,29,.07)`
**Táctil** — nada por debajo de 38 px

---

## 10. Notas de implementación (Django + Bootstrap 5)

**Plantillas**

```
templates/ordenes/
  lista.html              # extiende base_movil.html
  _pestanas_canal.html    # recibe canal_activo y conteo_por_canal
  _grupo.html             # encabezado + lista de tarjetas
  _tarjeta_orden.html     # cabecera; incluye _detalle si está desplegada
  _linea_semaforo.html    # barra 3px + texto + etiqueta
  _subheader.html         # compartido con el resto de la app
```

**Qué no hacer**

- No recorrer el árbol de combos en el template para contar líneas ni armar el resumen.
  Viene calculado.
- No partir la sub-línea buscando el dato a resaltar. El backend manda los cuatro campos.
- No poner botones en las tarjetas. La lista es de lectura; la acción vive dentro de la
  orden. Si aparece la tentación de un botón "Cobrar" en la fila, es señal de que el
  detalle de la orden no está resolviendo bien ese caso.
- No usar globos de conteo en las pestañas.
- No imprimir la fecha completa en órdenes de hoy: hora sola si es de hoy, "ayer 9:14 pm"
  si no, y tiempo transcurrido cuando la orden está en cocina.

**Acordeón** — una orden abierta a la vez. Al abrir otra, la anterior se cierra. El
estado abierto no se persiste entre cargas: al volver del detalle, la lista se muestra
plegada. Con `<details>` nativo se resuelve sin JS, cerrando los hermanos con un listener
de `toggle`; con Bootstrap, `collapse` con `data-bs-parent`.

**Actualización en vivo** — la lista cambia sola mientras la cocina marca platillos. Un
refresco por polling cada 10–15 s (HTMX `hx-trigger="every 12s"`) es suficiente; lo
importante es **no re-renderizar la orden que el usuario tiene desplegada** con el foco
puesto. Si se usa polling, que el parcial reemplace solo los grupos, no la tarjeta
abierta.

**Bootstrap** — la retícula no se usa para las tarjetas: son flex con `gap`. De Bootstrap
se aprovechan `collapse` para el acordeón y los utilities de espaciado. Las clases de
color de Bootstrap no se usan: todos los tonos son los de arriba.

**Estados vacíos**
- Pestaña sin órdenes: texto centrado 12.5/600 `#8a929c` — "No hay órdenes para llevar
  ahora mismo". Sin ilustración.
- Ninguna orden activa en todo el turno: el mismo patrón, más una línea 11.5/600
  `#a8afb8` con la última orden cerrada y su hora.

---

## 11. Pendiente de decidir

- **Pestaña Delivery.** Tiene datos que las otras no —repartidor, dirección, estado de
  entrega— y probablemente necesita su propia fila. Aquí está diseñada con el mismo
  patrón; conviene revisarla contra `Delivery.dc.html` antes de implementar.
- **Órdenes cerradas.** Salieron de la lista activa. Hoy se llega por el `⋯` del
  subheader; falta decidir si merecen su propia pestaña o una pantalla aparte.
- **Sonido o vibración** cuando la cocina marca un platillo `listo`. No diseñado; cambia
  mucho el valor de la pantalla si el mesero no la está mirando.
- **Órdenes de otro cajero.** Ahora se ven todas. Falta decidir si el mesero solo debe ver
  las suyas.
