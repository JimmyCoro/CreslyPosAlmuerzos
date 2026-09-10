(function () {
  const catalogo = window.PZ_CATALOGO;
  const IVA_RATE = 0.15;
  const PEDIDO_ID = window.PZ_PEDIDO_ID || null;

  const carrito = [];
  let categoriaActiva = 'Todas';
  let busqueda = '';

  function actualizarNumeroOrden(numero) {
    const numeroStr = String(numero).padStart(3, '0');
    document.getElementById('vrNumeroOrden').textContent = '#' + numeroStr;
    window.PZ_NUMERO_STR = numeroStr;
  }

  function productoPorcionIndividual() {
    return catalogo.productos.find(p => p.es_porcion_individual);
  }

  // ===== CATEGORÍAS =====
  function construirCategorias() {
    const categorias = ['Todas', 'Pizzas', 'Combos'];
    const vistas = new Set();
    catalogo.productos.forEach(p => {
      if (!p.es_porcion_individual && !vistas.has(p.categoria_display)) {
        vistas.add(p.categoria_display);
        categorias.push(p.categoria_display);
      }
    });
    return categorias;
  }

  function renderCategorias() {
    const categorias = construirCategorias();
    const cont = document.getElementById('vrCategorias');
    cont.innerHTML = '';
    categorias.forEach(cat => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'vr-cat-chip' + (categoriaActiva === cat ? ' vr-cat-chip-active' : '');
      chip.textContent = cat;
      chip.addEventListener('click', () => { categoriaActiva = cat; renderCategorias(); renderGrid(); });
      cont.appendChild(chip);
    });
  }

  // ===== GRID DE PRODUCTOS =====
  function construirItems(cat, texto) {
    let items = [];

    if (cat === 'Todas' || cat === 'Pizzas') {
      catalogo.tamanos.forEach(t => items.push({ tipo: 'tamano', data: t }));
      const porcion = productoPorcionIndividual();
      if (porcion) items.push({ tipo: 'porcion', data: porcion });
    }
    if (cat === 'Todas' || cat === 'Combos') {
      catalogo.combos.forEach(c => items.push({ tipo: 'combo', data: c }));
    }
    if (cat === 'Todas') {
      catalogo.productos.filter(p => !p.es_porcion_individual)
        .forEach(p => items.push({ tipo: 'producto', data: p }));
    } else if (cat !== 'Pizzas' && cat !== 'Combos') {
      catalogo.productos.filter(p => p.categoria_display === cat && !p.es_porcion_individual)
        .forEach(p => items.push({ tipo: 'producto', data: p }));
    }

    if (texto) {
      items = items.filter(it => coincideBusqueda(it.data.nombre, texto));
    }
    return items;
  }

  function coincideBusqueda(nombre, texto) {
    return nombre.toLowerCase().includes(texto.toLowerCase());
  }

  function renderGrid() {
    const cont = document.getElementById('vrGrid');
    cont.innerHTML = '';
    const items = construirItems(categoriaActiva, busqueda);

    if (!items.length) {
      cont.innerHTML = '<p class="text-muted">No se encontraron productos</p>';
      return;
    }

    items.forEach(it => cont.appendChild(crearCardProducto(it)));
  }

  function crearCardProducto(it) {
    if (it.tipo === 'tamano') {
      const t = it.data;
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'vr-card';
      card.innerHTML = `
        <div class="vr-card-body">
          <div class="vr-card-cat">Pizza</div>
          <div class="vr-card-nombre">${t.nombre}</div>
          <div class="vr-card-footer">
            <span class="vr-card-precio">$${parseFloat(t.precio_base).toFixed(2)}</span>
            <span class="vr-card-icon-btn"><i class="fas fa-sliders-h"></i></span>
          </div>
        </div>`;
      card.addEventListener('click', () => abrirSelectorTamanoPizza(t));
      return card;
    }

    if (it.tipo === 'porcion') {
      const p = it.data;
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'vr-card';
      card.innerHTML = `
        <div class="vr-card-body">
          <div class="vr-card-cat">Pizza</div>
          <div class="vr-card-nombre">${p.nombre}</div>
          <div class="vr-card-footer">
            <span class="vr-card-precio">$${parseFloat(p.precio).toFixed(2)}</span>
            <span class="vr-card-icon-btn"><i class="fas fa-sliders-h"></i></span>
          </div>
        </div>`;
      card.addEventListener('click', () => abrirSelectorPorcion(p));
      return card;
    }

    if (it.tipo === 'combo') {
      const c = it.data;
      const tieneVariosTamanos = c.tamanos && c.tamanos.length > 1;
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'vr-card';
      card.innerHTML = `
        <div class="vr-card-body">
          <div class="vr-card-cat">Combo</div>
          <div class="vr-card-nombre">${c.nombre}</div>
          ${c.descripcion ? `<div class="vr-card-desc">${c.descripcion}</div>` : ''}
          <div class="vr-card-footer">
            <span class="vr-card-precio">${tieneVariosTamanos ? 'desde ' : ''}$${parseFloat(c.precio_desde).toFixed(2)}</span>
            <span class="vr-card-icon-btn"><i class="fas fa-sliders-h"></i></span>
          </div>
        </div>`;
      card.addEventListener('click', () => abrirSelectorCombo(c));
      return card;
    }

    const p = it.data;

    if (p.alitas_cantidad > 0) {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'vr-card';
      card.innerHTML = `
        <div class="vr-card-body">
          <div class="vr-card-cat">${p.categoria_display}</div>
          <div class="vr-card-nombre">${p.nombre}</div>
          <div class="vr-card-footer">
            <span class="vr-card-precio">$${parseFloat(p.precio).toFixed(2)}</span>
            <span class="vr-card-icon-btn"><i class="fas fa-sliders-h"></i></span>
          </div>
        </div>`;
      card.addEventListener('click', () => abrirSelectorProductoAlitas(p));
      return card;
    }

    if (p.tipo_sabor_bebida === 'bebida' || p.tipo_sabor_bebida === 'michelada') {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'vr-card';
      card.innerHTML = `
        <div class="vr-card-body">
          <div class="vr-card-cat">${p.categoria_display}</div>
          <div class="vr-card-nombre">${p.nombre}</div>
          <div class="vr-card-footer">
            <span class="vr-card-precio">$${parseFloat(p.precio).toFixed(2)}</span>
            <span class="vr-card-icon-btn"><i class="fas fa-sliders-h"></i></span>
          </div>
        </div>`;
      card.addEventListener('click', () => (
        p.tipo_sabor_bebida === 'bebida' ? abrirSelectorProductoBebida(p) : abrirSelectorProductoMichelada(p)
      ));
      return card;
    }

    // producto simple: sin modal. Empieza con "+" y al agregarlo se activa el stepper
    const cantidadInicial = obtenerCantidadCarrito(p.id);

    const card = document.createElement('div');
    card.className = 'vr-card' + (cantidadInicial > 0 ? ' vr-card-selected' : '');
    card.dataset.productoId = p.id;
    card.innerHTML = `
      <div class="vr-card-body">
        <div class="vr-card-cat">${p.categoria_display}</div>
        <div class="vr-card-nombre">${p.nombre}</div>
        <div class="vr-card-footer">
          <span class="vr-card-precio">$${parseFloat(p.precio).toFixed(2)}</span>
          <div class="vr-card-accion">${renderAccionProducto(cantidadInicial)}</div>
        </div>
      </div>`;

    vincularAccionProducto(card, p);

    return card;
  }

  function renderAccionProducto(cantidad) {
    if (cantidad > 0) {
      return `
        <div class="vr-stepper">
          <button type="button" class="vr-step-btn" data-accion="menos">-</button>
          <span class="vr-step-qty">${cantidad}</span>
          <button type="button" class="vr-step-btn vr-step-btn-plus" data-accion="mas">+</button>
        </div>`;
    }
    return `<button type="button" class="vr-card-icon-btn vr-card-icon-btn-plus" data-accion="mas"><i class="fas fa-plus"></i></button>`;
  }

  function vincularAccionProducto(card, p) {
    const accionEl = card.querySelector('.vr-card-accion');
    const masBtn = accionEl.querySelector('[data-accion="mas"]');
    const menosBtn = accionEl.querySelector('[data-accion="menos"]');

    if (masBtn) {
      masBtn.addEventListener('click', () => {
        agregarProductoSimple(p);
        actualizarAccionProducto(card, p);
      });
    }
    if (menosBtn) {
      menosBtn.addEventListener('click', () => {
        quitarUnoProductoSimple(p.id);
        actualizarAccionProducto(card, p);
      });
    }
  }

  function actualizarAccionProducto(card, p) {
    const nuevaCantidad = obtenerCantidadCarrito(p.id);
    card.classList.toggle('vr-card-selected', nuevaCantidad > 0);
    card.querySelector('.vr-card-accion').innerHTML = renderAccionProducto(nuevaCantidad);
    vincularAccionProducto(card, p);
  }

  function obtenerCantidadCarrito(productoId) {
    const item = carrito.find(it => it.kind === 'producto' && it.producto_id === productoId);
    return item ? item.cantidad : 0;
  }

  function quitarUnoProductoSimple(productoId) {
    const idx = carrito.findIndex(it => it.kind === 'producto' && it.producto_id === productoId);
    if (idx === -1) return;
    carrito[idx].cantidad -= 1;
    if (carrito[idx].cantidad <= 0) carrito.splice(idx, 1);
    renderCarrito();
  }


  // Todo producto configurable se arma en la misma hoja por pasos
  // (handoff_combo): pizza, porción, alitas, bebida, michelada y combos.
  const configurador = window.pzCrearConfiguradorCombo({
    catalogo: catalogo,
    calcularPrecioUrl: window.PZ_URLS.calcularPrecio,
    csrfToken: window.CSRF_TOKEN,
    mostrarToast: mostrarToast,
    onAgregar: function (item) {
      carrito.push(item);
      mostrarToast(`Agregado: ${item._label}`);
      renderCarrito();
    },
  });

  function abrirSelectorTamanoPizza(tamano) {
    configurador.abrir({
      kind: 'pizza',
      nombre: `Pizza ${tamano.nombre}`,
      tamano: tamano,
      // La "Porción" es una sola porción: no tiene sentido partirla en dos sabores.
      permiteMitad: tamano.nombre !== 'Porción',
    });
  }

  function abrirSelectorCombo(combo) {
    configurador.abrir({ kind: 'combo', nombre: combo.nombre, combo: combo });
  }

  function abrirSelectorPorcion(producto) {
    configurador.abrir({ kind: 'porcion', nombre: producto.nombre, producto: producto });
  }

  function abrirSelectorProductoAlitas(producto) {
    configurador.abrir({ kind: 'producto_alitas', nombre: producto.nombre, producto: producto });
  }

  function abrirSelectorProductoBebida(producto) {
    configurador.abrir({ kind: 'producto_bebida', nombre: producto.nombre, producto: producto });
  }

  function abrirSelectorProductoMichelada(producto) {
    configurador.abrir({ kind: 'producto_michelada', nombre: producto.nombre, producto: producto });
  }

  function agregarProductoSimple(producto) {
    const existente = carrito.find(it => it.kind === 'producto' && it.producto_id === producto.id);
    if (existente) {
      existente.cantidad += 1;
    } else {
      carrito.push({
        kind: 'producto', cantidad: 1, observacion: '', producto_id: producto.id,
        _label: producto.nombre, _precio_unitario: parseFloat(producto.precio),
      });
    }
    mostrarToast(`Agregado: ${producto.nombre}`);
    renderCarrito();
  }

  // ===== TOAST =====
  let toastTimeout;
  function mostrarToast(texto) {
    const toast = document.getElementById('vrToast');
    document.getElementById('vrToastTexto').textContent = texto;
    toast.classList.remove('d-none');
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => toast.classList.add('d-none'), 2500);
  }

  // ===== CARRITO =====
  // `_label` siempre llega como una sola cadena armada por el backend-side
  // equivalente en Python (ver ItemPreparacion.nombre_corto/modificadores
  // en pizzeria/models.py) — acá se parte igual, del lado del cliente,
  // porque el carrito se arma 100% en JS antes de guardar el pedido.
  function separarNombreMod(label) {
    const seps = [' - ', ': ', ' | '];
    let mejorPos = -1;
    let mejorSep = '';
    seps.forEach((sep) => {
      const pos = label.indexOf(sep);
      if (pos !== -1 && (mejorPos === -1 || pos < mejorPos)) { mejorPos = pos; mejorSep = sep; }
    });
    if (mejorPos === -1) return { nombre: label.trim(), mods: '' };
    const nombre = label.slice(0, mejorPos).trim();
    const mods = label.slice(mejorPos + mejorSep.length).trim().replace(/ \| /g, ' / ').replace(/, /g, ' / ');
    return { nombre, mods };
  }

  function renderCarrito() {
    const cont = document.getElementById('vrCartItems');

    if (!carrito.length) {
      cont.innerHTML = `
        <div class="vr-cart-empty">
          <div class="vr-cart-empty-icon"><i class="fas fa-cart-shopping"></i></div>
          <p class="vr-cart-empty-title">Tu orden está vacía</p>
          <p class="vr-cart-empty-subtitle">Toca un platillo para empezar a armarla.</p>
        </div>`;
      actualizarTotales(0);
      actualizarBotonesConfirmar();
      return;
    }

    let total = 0;
    cont.innerHTML = carrito.map((item, idx) => {
      const subtotal = item._precio_unitario * item.cantidad;
      total += subtotal;
      const { nombre, mods } = separarNombreMod(item._label);
      return `
        <div class="vr-cart-item">
          <div class="vr-cart-item-top">
            <div class="vr-cart-item-info">
              <span class="vr-cart-item-nombre">${escapeHtml(nombre)}</span>
              ${mods ? `<span class="vr-cart-item-mods">${escapeHtml(mods)}</span>` : ''}
            </div>
            <span class="vr-cart-item-precio">$${subtotal.toFixed(2)}</span>
          </div>
          ${item.observacion ? `<div class="vr-cart-item-nota"><i class="fas fa-note-sticky me-1"></i>${escapeHtml(item.observacion)}</div>` : ''}
          <div class="vr-cart-item-bottom">
            <button type="button" class="vr-cart-item-editar" onclick="vrEditarNotaCarrito(${idx})">
              <i class="fas fa-pencil"></i> Editar
            </button>
            <div class="vr-cart-item-stepper">
              <button type="button" class="vr-cart-item-step" onclick="vrCambiarCantidadCarrito(${idx}, -1)">-</button>
              <span class="vr-cart-item-qty">${item.cantidad}</span>
              <button type="button" class="vr-cart-item-step vr-cart-item-step-plus" onclick="vrCambiarCantidadCarrito(${idx}, 1)">+</button>
            </div>
          </div>
        </div>`;
    }).join('');

    actualizarTotales(total);
    actualizarBotonesConfirmar();
  }

  function actualizarTotales(total) {
    const subtotal = total / (1 + IVA_RATE);
    const iva = total - subtotal;
    document.getElementById('vrSubtotal').textContent = `$${subtotal.toFixed(2)}`;
    document.getElementById('vrIva').textContent = `$${iva.toFixed(2)}`;
    document.getElementById('vrTotal').textContent = `$${total.toFixed(2)}`;
  }

  window.vrCambiarCantidadCarrito = function (idx, delta) {
    carrito[idx].cantidad += delta;
    if (carrito[idx].cantidad <= 0) {
      carrito.splice(idx, 1);
    }
    renderCarrito();
  };

  window.vrEditarNotaCarrito = function (idx) {
    const actual = carrito[idx].observacion || '';
    const nota = prompt('Nota para este producto (ej: sin cebolla, extra picante):', actual);
    if (nota === null) return;
    carrito[idx].observacion = nota.trim();
    renderCarrito();
  };

  function escapeHtml(texto) {
    const div = document.createElement('div');
    div.textContent = texto;
    return div.innerHTML;
  }

  document.getElementById('vrVaciar').addEventListener('click', function () {
    if (!carrito.length) return;
    if (confirm('¿Vaciar el carrito?')) {
      carrito.length = 0;
      renderCarrito();
    }
  });

  // ===== TIPO DE VENTA (Servirse / Llevar / Delivery) =====
  let tipoVentaSeleccionado = 'llevar';

  // ===== TECLADO DE MESAS (modo Servirse) =====
  function renderMesaGrid() {
    const cont = document.getElementById('vrMesaGrid');
    if (!cont) return;
    const mesas = catalogo.mesas || [];
    const libres = mesas.filter(m => m.libre).length;
    const libresLabel = document.getElementById('vrMesasLibresCount');
    if (libresLabel) libresLabel.textContent = `${libres} libre${libres === 1 ? '' : 's'}`;

    const seleccionada = document.getElementById('vrMesaSelect').value;
    cont.innerHTML = '';
    mesas.forEach(function (m) {
      const activa = String(m.id) === String(seleccionada);
      const celda = document.createElement('button');
      celda.type = 'button';
      celda.className = 'vr-mesa-celda'
        + (!m.libre && !activa ? ' vr-mesa-celda-ocupada' : '')
        + (activa ? ' vr-mesa-celda-activa' : '');
      celda.textContent = m.nombre || m.numero;
      if (m.libre || activa) {
        celda.addEventListener('click', function () { seleccionarMesa(m.id); });
      } else {
        celda.disabled = true;
      }
      cont.appendChild(celda);
    });

    const verCelda = document.createElement('button');
    verCelda.type = 'button';
    verCelda.className = 'vr-mesa-celda vr-mesa-celda-ver';
    verCelda.textContent = 'Ver';
    verCelda.addEventListener('click', function () { window.location.href = window.PZ_URLS.mapaMesas; });
    cont.appendChild(verCelda);
  }

  // ===== PERSONAS EN LA MESA =====
  // Se precarga con la capacidad de la mesa elegida (lo más común es que la
  // ocupen completa) y queda editable. Alimenta el "Dividir cuenta" del cobro.
  let personasSeleccionadas = 1;
  let personasEditadasAMano = false;

  function renderPersonas() {
    const num = document.getElementById('vrPersonasNum');
    if (!num) return;
    num.textContent = String(personasSeleccionadas);
    document.getElementById('vrPersonasTexto').textContent = personasSeleccionadas === 1 ? 'persona' : 'personas';
    document.getElementById('vrPersonasMenos').disabled = personasSeleccionadas <= 1;

    const mesa = mesaSeleccionada();
    const hint = document.getElementById('vrPersonasHint');
    hint.textContent = mesa
      ? `Mesa ${mesa.nombre || mesa.numero} · ${mesa.capacidad} puestos`
      : '';
  }

  function cambiarPersonas(delta) {
    const nuevo = personasSeleccionadas + delta;
    if (nuevo < 1 || nuevo > 40) return;
    personasSeleccionadas = nuevo;
    personasEditadasAMano = true;
    renderPersonas();
    actualizarTextoContinuar();
  }

  function mesaSeleccionada() {
    const mesaId = document.getElementById('vrMesaSelect').value;
    return (catalogo.mesas || []).find(m => String(m.id) === String(mesaId)) || null;
  }

  function seleccionarMesa(mesaId) {
    document.getElementById('vrMesaSelect').value = String(mesaId);
    // Solo autocompletamos mientras el mesero no haya tocado el stepper: si ya
    // ajustó el número a mano, cambiar de mesa no debe pisarle el dato.
    if (!personasEditadasAMano) {
      const mesa = mesaSeleccionada();
      if (mesa && mesa.capacidad) personasSeleccionadas = mesa.capacidad;
    }
    renderMesaGrid();
    renderPersonas();
    actualizarTextoContinuar();
    actualizarBotonesConfirmar();
    actualizarResumenSubheader();
  }

  // ===== SUBHEADER COMO "RECIBO" (handoff_pos_movil/README.md §3) =====
  // Mesa: verde si ya hay mesa asignada, rojo si falta. Llevar: nombre del
  // cliente (o "Sin nombre"). Delivery: teléfono + valor de la moto (rojo
  // si aún no se fija el envío).
  function actualizarResumenSubheader() {
    // Al agregar a un pedido ya abierto el tipo no se puede cambiar, así que
    // el resumen que ya renderizó el servidor (con los datos reales
    // guardados) es el correcto — no lo pisamos con el estado del JS.
    if (PEDIDO_ID) return;
    const el = document.getElementById('pzshResumen');
    if (!el) return;
    const numero = window.PZ_NUMERO_STR || '';
    const mesero = window.PZ_MESERO_NOMBRE || '';
    let html;
    if (tipoVentaSeleccionado === 'mesa') {
      const mesaId = document.getElementById('vrMesaSelect').value;
      const mesa = (catalogo.mesas || []).find(m => String(m.id) === mesaId);
      html = `#${numero} · ` + (mesa
        ? `<strong class="pzsh-hl-verde">Mesa ${escapeHtml(mesa.nombre || String(mesa.numero))}</strong>`
        : `<strong class="pzsh-hl-rojo">Falta mesa</strong>`);
    } else if (tipoVentaSeleccionado === 'llevar') {
      const nombre = document.getElementById('vrNombreLlevar').value.trim();
      html = `#${numero} · <strong class="pzsh-hl-neutro">${escapeHtml(nombre || 'Sin nombre')}</strong> · ${escapeHtml(mesero)}`;
    } else {
      const tel = document.getElementById('vrTelefonoDelivery').value.trim();
      const valor = document.getElementById('vrValorMoto').value;
      const pre = tel ? `${escapeHtml(tel)} · ` : '';
      html = pre + (valor
        ? `<strong class="pzsh-hl-neutro">envío $${parseFloat(valor).toFixed(2)}</strong>`
        : `<strong class="pzsh-hl-rojo">Falta envío</strong>`);
    }
    el.innerHTML = html;
  }

  // ===== CHIPS "RECIENTES" (modo Llevar) =====
  function renderClientesRecientes() {
    const cont = document.getElementById('vrClientesRecientes');
    if (!cont) return;
    cont.innerHTML = '';
    (catalogo.clientes_recientes || []).forEach(function (nombre) {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'vr-modo-chip';
      chip.textContent = nombre;
      chip.addEventListener('click', function () {
        document.getElementById('vrNombreLlevar').value = nombre;
        actualizarBotonesConfirmar();
        actualizarResumenSubheader();
      });
      cont.appendChild(chip);
    });
    const sinNombre = document.createElement('button');
    sinNombre.type = 'button';
    sinNombre.className = 'vr-modo-chip vr-modo-chip-sinnombre';
    sinNombre.textContent = 'Sin nombre';
    sinNombre.addEventListener('click', function () {
      document.getElementById('vrNombreLlevar').value = '';
      actualizarBotonesConfirmar();
      actualizarResumenSubheader();
    });
    cont.appendChild(sinNombre);
  }

  function actualizarGrupoClienteDatos() {
    document.getElementById('vrGrupoMesa').classList.toggle('d-none', tipoVentaSeleccionado !== 'mesa');
    document.getElementById('vrGrupoLlevar').classList.toggle('d-none', tipoVentaSeleccionado !== 'llevar');
    document.getElementById('vrGrupoDelivery').classList.toggle('d-none', tipoVentaSeleccionado !== 'delivery');
  }

  // ===== TABS DE MODO (Servirse/Llevar/Delivery) =====
  const TIPO_LABELS_UI = { mesa: 'Servirse', llevar: 'Llevar', delivery: 'Delivery' };

  document.querySelectorAll('.vr-modo-tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      tipoVentaSeleccionado = this.dataset.tipo;
      document.querySelectorAll('.vr-modo-tab').forEach(t => t.classList.toggle('vr-modo-tab-active', t === this));
      actualizarPillTipo();
      actualizarGrupoClienteDatos();
      actualizarTextoContinuar();
      actualizarBotonesConfirmar();
      actualizarResumenSubheader();
    });
  });

  // ===== UBICACIÓN RESPONSIVE DE #vrTipoYDatos =====
  // En desktop vive inline dentro de #vrCart (posición original, barra
  // lateral siempre visible). En mobile/tablet (≤1023px) se muda dentro de
  // la hoja #vrTipoSheet, que el pill del subheader abre bajo demanda —
  // evita tener el mismo control repetido en dos sitios a la vez.
  (function () {
    const wrap = document.getElementById('vrTipoYDatos');
    const sheetBody = document.getElementById('vrTipoSheetBody');
    if (!wrap || !sheetBody) return;
    const originalParent = wrap.parentNode;
    const originalNext = wrap.nextSibling;
    let enHoja = false;

    function actualizarUbicacion() {
      const esAngosto = window.innerWidth <= 1023;
      if (esAngosto && !enHoja) { sheetBody.appendChild(wrap); enHoja = true; }
      else if (!esAngosto && enHoja) { originalParent.insertBefore(wrap, originalNext); enHoja = false; }
    }

    actualizarUbicacion();
    window.addEventListener('resize', actualizarUbicacion);
  })();

  // ===== PILL DE TIPO DE PEDIDO (subheader) =====
  // Ya no es clickeable: es solo un badge informativo (ver
  // pizzeria/handoff_pos_movil/README.md). Quien abre la hoja de modo es el
  // botón "⋯" (#pzshMasOpciones), no el pill. Solo existe cuando no hay
  // PEDIDO_ID: al agregar a un pedido abierto el tipo ya no se puede cambiar.
  const pillTipo = document.getElementById('pzshTipoPedido');
  const masOpciones = document.getElementById('pzshMasOpciones');
  const tipoSheet = document.getElementById('vrTipoSheet');
  const tipoSheetBackdrop = document.getElementById('vrTipoSheetBackdrop');
  const tipoSheetListo = document.getElementById('vrTipoSheetListo');
  if (window.pzMoverAlBodyEnMobile) {
    window.pzMoverAlBodyEnMobile(tipoSheet);
    window.pzMoverAlBodyEnMobile(tipoSheetBackdrop);
  }

  const cartTipoPill = document.getElementById('vrCartTipoPill');

  function actualizarPillTipo() {
    if (pillTipo) {
      const label = pillTipo.querySelector('.pzsh-pill-label');
      if (label) label.textContent = TIPO_LABELS_UI[tipoVentaSeleccionado] || '';
      pillTipo.classList.toggle('pzsh-pill-tono-delivery', tipoVentaSeleccionado === 'delivery');
      pillTipo.classList.toggle('pzsh-pill-tono-oscuro', tipoVentaSeleccionado !== 'delivery');
    }
    // Pill del carrito (handoff visual "Pedido #001 · Llevar ▾") — mismo
    // dato que el pill del subheader, sincronizados desde una sola fuente
    // (tipoVentaSeleccionado) para no repetir la lógica dos veces.
    if (cartTipoPill) {
      const icono = cartTipoPill.querySelector('i');
      cartTipoPill.textContent = (TIPO_LABELS_UI[tipoVentaSeleccionado] || '') + ' ';
      if (icono) cartTipoPill.appendChild(icono);
      cartTipoPill.classList.toggle('vr-cart-tipo-pill-delivery', tipoVentaSeleccionado === 'delivery');
    }
  }

  // El texto del botón "Continuar" confirma lo elegido (ver
  // handoff_pos_movil/README.md: "Continuar · Mesa 6", "Continuar · envío $2.50").
  function actualizarTextoContinuar() {
    if (!tipoSheetListo) return;
    let texto = 'Continuar';
    if (tipoVentaSeleccionado === 'mesa') {
      const mesa = mesaSeleccionada();
      if (mesa) texto = `Continuar · Mesa ${mesa.nombre || mesa.numero} · ${personasSeleccionadas}p`;
    } else if (tipoVentaSeleccionado === 'delivery') {
      const valor = document.getElementById('vrValorMoto').value;
      if (valor) texto = `Continuar · envío $${parseFloat(valor).toFixed(2)}`;
    }
    tipoSheetListo.textContent = texto;
  }

  function abrirTipoSheet() {
    if (!tipoSheet) return;
    tipoSheet.classList.add('pz-cart-sheet-open');
    if (tipoSheetBackdrop) tipoSheetBackdrop.classList.add('active');
    if (masOpciones) masOpciones.setAttribute('aria-expanded', 'true');
    actualizarTextoContinuar();
  }

  function cerrarTipoSheet() {
    if (!tipoSheet) return;
    tipoSheet.classList.remove('pz-cart-sheet-open');
    if (tipoSheetBackdrop) tipoSheetBackdrop.classList.remove('active');
    if (masOpciones) masOpciones.setAttribute('aria-expanded', 'false');
  }

  if (tipoSheetListo) tipoSheetListo.addEventListener('click', cerrarTipoSheet);
  if (tipoSheetBackdrop) tipoSheetBackdrop.addEventListener('click', cerrarTipoSheet);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') cerrarTipoSheet();
  });

  // ===== ACCIÓN DEL SUBHEADER "⋯" → abre la hoja de modo =====
  if (masOpciones) masOpciones.addEventListener('click', abrirTipoSheet);

  document.getElementById('vrPersonasMenos').addEventListener('click', function () { cambiarPersonas(-1); });
  document.getElementById('vrPersonasMas').addEventListener('click', function () { cambiarPersonas(1); });
  renderPersonas();

  ['vrMesaSelect', 'vrTelefonoDelivery'].forEach(function (id) {
    document.getElementById(id).addEventListener('input', function () {
      actualizarBotonesConfirmar();
      actualizarResumenSubheader();
    });
  });

  document.getElementById('vrNombreLlevar').addEventListener('input', actualizarResumenSubheader);

  // ===== DATOS DE ENTREGA (Delivery): forma de pago =====
  // Efectivo: el motorizado cobra el total directo al cliente. Transferencia:
  // ya se cobró (o se cobra) por transferencia, así que el motorizado no
  // cobra nada al entregar — solo le pagamos su valor de moto aparte.
  let pagoDeliverySeleccionado = null;

  document.querySelectorAll('#vrPagoDeliveryTabs .vr-modo-pago-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      pagoDeliverySeleccionado = this.dataset.valor;
      document.querySelectorAll('#vrPagoDeliveryTabs .vr-modo-pago-btn').forEach(function (b) {
        b.classList.toggle('vr-modo-pago-btn-active', b === btn);
      });
    });
  });

  // ===== DATOS DE ENTREGA (Delivery): costo de envío =====
  function marcarBotonCostoEnvio(valor) {
    document.querySelectorAll('#vrCostoEnvioTabs .vr-modo-envio-btn').forEach(function (btn) {
      btn.classList.toggle('vr-modo-envio-btn-active', valor !== null && btn.dataset.valor === valor);
    });
  }

  function seleccionarCostoEnvio(valor) {
    marcarBotonCostoEnvio(valor);
    document.getElementById('vrValorMoto').value = valor === null ? '' : valor;
    actualizarTextoContinuar();
    actualizarResumenSubheader();
  }

  document.querySelectorAll('#vrCostoEnvioTabs .vr-modo-envio-btn').forEach(function (btn) {
    btn.addEventListener('click', function () { seleccionarCostoEnvio(this.dataset.valor); });
  });

  document.getElementById('vrValorMoto').addEventListener('input', function () {
    marcarBotonCostoEnvio(null);
    actualizarTextoContinuar();
    actualizarResumenSubheader();
  });

  // ===== CONFIRMAR PEDIDO (el cobro se hace luego en Órdenes) =====
  let guardandoPedido = false;

  function datosClienteValidos() {
    if (PEDIDO_ID) return true;
    if (tipoVentaSeleccionado === 'mesa') {
      return !!document.getElementById('vrMesaSelect').value;
    }
    if (tipoVentaSeleccionado === 'delivery') {
      return !!document.getElementById('vrTelefonoDelivery').value.trim();
    }
    return true;
  }

  function actualizarBotonesConfirmar() {
    const deshabilitado = !carrito.length || guardandoPedido || !datosClienteValidos();
    document.getElementById('vrBtnConfirmarImprimir').disabled = deshabilitado;
  }

  window.vrGuardarPedido = function (conImpresion) {
    if (!carrito.length || guardandoPedido || !datosClienteValidos()) return;
    guardandoPedido = true;
    actualizarBotonesConfirmar();

    const body = new FormData();
    body.append('carrito', JSON.stringify(carrito));
    body.append('imprimir', conImpresion ? 'true' : 'false');

    let mesaIdUsada = null;

    if (PEDIDO_ID) {
      body.append('pedido_id', PEDIDO_ID);
    } else {
      body.append('tipo', tipoVentaSeleccionado);
      if (tipoVentaSeleccionado === 'mesa') {
        mesaIdUsada = document.getElementById('vrMesaSelect').value;
        body.append('mesa_id', mesaIdUsada);
        body.append('personas', String(personasSeleccionadas));
        body.append('nombre', document.getElementById('vrNombreMesa').value.trim());
      } else if (tipoVentaSeleccionado === 'llevar') {
        body.append('nombre', document.getElementById('vrNombreLlevar').value.trim());
      } else if (tipoVentaSeleccionado === 'delivery') {
        body.append('telefono', document.getElementById('vrTelefonoDelivery').value.trim());
        body.append('nombre', document.getElementById('vrNombreDelivery').value.trim());
        body.append('valor_moto', document.getElementById('vrValorMoto').value.trim());
        body.append('pago_delivery', pagoDeliverySeleccionado || '');
        body.append('observaciones', document.getElementById('vrNotasDelivery').value.trim());
      }
    }

    fetch(window.PZ_URLS.guardarPedido, { method: 'POST', body, headers: { 'X-CSRFToken': window.CSRF_TOKEN } })
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') { alert('Error al guardar el pedido: ' + data.message); return; }

        if (PEDIDO_ID) {
          window.location.href = window.PZ_URLS.detalleOrden;
          return;
        }

        carrito.length = 0;
        renderCarrito();
        if (mesaIdUsada) {
          const mesa = (catalogo.mesas || []).find(m => String(m.id) === String(mesaIdUsada));
          if (mesa) mesa.libre = false;
          document.getElementById('vrMesaSelect').value = '';
          renderMesaGrid();
        }
        personasSeleccionadas = 1;
        personasEditadasAMano = false;
        renderPersonas();
        document.getElementById('vrNombreMesa').value = '';
        document.getElementById('vrNombreLlevar').value = '';
        document.getElementById('vrTelefonoDelivery').value = '';
        document.getElementById('vrNombreDelivery').value = '';
        document.getElementById('vrValorMoto').value = '';
        document.getElementById('vrNotasDelivery').value = '';
        pagoDeliverySeleccionado = null;
        document.querySelectorAll('#vrPagoDeliveryTabs .vr-modo-pago-btn').forEach(function (b) {
          b.classList.remove('vr-modo-pago-btn-active');
        });
        seleccionarCostoEnvio(null);
        actualizarTextoContinuar();
        actualizarNumeroOrden(data.pedido.numero_dia + 1);
        actualizarResumenSubheader();
        mostrarToast(`Pedido #${data.pedido.numero_pedido_completo} confirmado`);
      })
      .catch(() => alert('Error inesperado al confirmar el pedido'))
      .finally(() => {
        guardandoPedido = false;
        actualizarBotonesConfirmar();
      });
  };

  // ===== BÚSQUEDA =====
  document.getElementById('vrBuscador').addEventListener('input', function () {
    busqueda = this.value.trim();
    renderGrid();
  });

  function preseleccionarMesa() {
    const mesaId = catalogo.mesa_preseleccionada;
    if (!mesaId || PEDIDO_ID) return;

    tipoVentaSeleccionado = 'mesa';
    document.querySelectorAll('.vr-modo-tab').forEach(t => t.classList.toggle('vr-modo-tab-active', t.dataset.tipo === 'mesa'));
    actualizarPillTipo();
    actualizarGrupoClienteDatos();

    seleccionarMesa(mesaId);
  }

  // ===== INIT =====
  document.addEventListener('DOMContentLoaded', function () {
    renderCategorias();
    renderGrid();
    renderCarrito();
    renderMesaGrid();
    renderClientesRecientes();
    actualizarGrupoClienteDatos();
    preseleccionarMesa();
    actualizarResumenSubheader();
  });
})();
