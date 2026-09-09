(function () {
  const catalogo = window.PZ_CATALOGO;
  const IVA_RATE = 0.15;
  const PEDIDO_ID = window.PZ_PEDIDO_ID || null;

  const carrito = [];
  let categoriaActiva = 'Todas';
  let busqueda = '';

  // Estado del selector modal (pizza, combo o porción individual)
  const selector = {
    kind: null, // 'pizza' | 'combo' | 'porcion' | 'producto_alitas' | 'producto_bebida' | 'producto_michelada'
    comboId: null,
    productoId: null,
    tamanoId: null,
    sabor1Id: null,
    sabor2Id: null,
    mitad: false,
    cantidad: 1,
    alitas: [], // [{ saborId, cantidad }]
    saboresBebidaIds: [],
    saboresMicheladaIds: [],
    saboresPorcionIds: [],
  };
  let selectorModal;

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

  // ===== HELPERS DE SELECTOR (pizza / combo) =====
  function saborLabel(s) {
    return s.es_premium ? `${s.nombre} <span class="pz-badge-premium">Premium</span>` : s.nombre;
  }

  function comboSeleccionado() {
    return catalogo.combos.find(c => c.id === selector.comboId);
  }

  function comboTieneTamanos() {
    const c = comboSeleccionado();
    return !!(c && c.tamanos && c.tamanos.length);
  }

  function comboTienePizzaFija() {
    const c = comboSeleccionado();
    return !!(c && !comboTieneTamanos() && c.pizza_tamano_fijo_id);
  }

  function comboRequierePizza() {
    return selector.kind === 'combo' && (comboTieneTamanos() || comboTienePizzaFija());
  }

  function comboPorcionesCantidad() {
    const c = comboSeleccionado();
    return (selector.kind === 'combo' && c && c.porcion_pizza_cantidad) || 0;
  }

  function comboMicheladaCantidad() {
    const c = comboSeleccionado();
    return (selector.kind === 'combo' && c && c.michelada_cantidad) || 0;
  }

  // ===== SABOR DE ALITAS (combos y productos de alitas) =====
  function alitasRequeridas() {
    if (selector.kind === 'combo') {
      const combo = comboSeleccionado();
      return (combo && combo.alitas_cantidad) || 0;
    }
    if (selector.kind === 'producto_alitas') {
      const producto = catalogo.productos.find(p => p.id === selector.productoId);
      return (producto && producto.alitas_cantidad) || 0;
    }
    return 0;
  }

  function alitasAsignadas() {
    return selector.alitas.reduce((sum, a) => sum + a.cantidad, 0);
  }

  function actualizarBadgeAlitas() {
    const requerido = alitasRequeridas();
    const faltan = Math.max(0, requerido - alitasAsignadas());
    const totalEl = document.getElementById('vrSelectorAlitasTotal');
    totalEl.textContent = faltan > 0 ? `Falta${faltan > 1 ? 'n' : ''} ${faltan}` : 'Listo';
    totalEl.classList.toggle('pz-faltan-ok', faltan === 0);
  }

  function establecerCantidadAlitas(saborId, cantidadDeseada, inputEl) {
    const requerido = alitasRequeridas();
    let cantidad = Math.max(0, Math.min(Math.floor(cantidadDeseada) || 0, requerido));
    let entry = selector.alitas.find(a => a.saborId === saborId);

    if (cantidad > 0 && !entry && selector.alitas.length >= 3) {
      cantidad = 0;
      mostrarToast('Máximo 3 sabores de alitas');
    }

    if (cantidad <= 0) {
      selector.alitas = selector.alitas.filter(a => a.saborId !== saborId);
    } else if (entry) {
      entry.cantidad = cantidad;
    } else {
      selector.alitas.push({ saborId, cantidad });
    }

    inputEl.value = cantidad || '';
    actualizarBadgeAlitas();
  }

  function renderSelectorAlitas() {
    const wrap = document.getElementById('vrSelectorAlitasWrap');
    const requerido = alitasRequeridas();
    if (!requerido) {
      wrap.classList.add('d-none');
      return;
    }
    wrap.classList.remove('d-none');

    const cont = document.getElementById('vrSelectorAlitas');
    cont.innerHTML = '';
    (catalogo.sabores_alitas || []).forEach(s => {
      const actual = selector.alitas.find(a => a.saborId === s.id);
      const cantidad = actual ? actual.cantidad : 0;
      const row = document.createElement('div');
      row.className = 'pz-select-row';
      row.innerHTML = `
        <span class="pz-select-nombre">${s.nombre}</span>
        <input type="text" inputmode="numeric" pattern="[0-9]*" class="pz-alitas-input" value="${cantidad || ''}" placeholder="0">`;
      const input = row.querySelector('.pz-alitas-input');
      input.addEventListener('input', () => establecerCantidadAlitas(s.id, parseInt(input.value, 10), input));
      input.addEventListener('focus', () => input.select());
      cont.appendChild(row);
    });

    actualizarBadgeAlitas();
  }

  // ===== SELECCIÓN MÚLTIPLE INDEPENDIENTE (porciones, bebidas, micheladas) =====
  function renderSeleccionMultiple(wrapId, contId, cantidad, pool, seleccion, etiqueta, onSelect) {
    const wrap = document.getElementById(wrapId);
    if (!cantidad) { wrap.classList.add('d-none'); return; }
    wrap.classList.remove('d-none');

    const cont = document.getElementById(contId);
    cont.innerHTML = '';
    for (let i = 0; i < cantidad; i++) {
      const grupo = document.createElement('div');
      grupo.className = 'pz-multi-grupo';
      if (cantidad > 1) {
        const label = document.createElement('div');
        label.className = 'pz-multi-label';
        label.textContent = `${etiqueta} ${i + 1}`;
        grupo.appendChild(label);
      }
      const grid = document.createElement('div');
      grid.className = 'pz-sabor-grid';
      (pool || []).forEach(s => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'pz-chip' + (seleccion[i] === s.id ? ' pz-chip-active' : '');
        btn.textContent = s.nombre;
        btn.addEventListener('click', () => onSelect(i, s.id));
        grid.appendChild(btn);
      });
      grupo.appendChild(grid);
      cont.appendChild(grupo);
    }
  }

  function selectorBebidaCantidad() {
    if (selector.kind === 'producto_bebida') return 1;
    if (selector.kind === 'combo') {
      const c = comboSeleccionado();
      return (c && c.bebida_cantidad) || 0;
    }
    return 0;
  }

  function selectorMicheladaCantidad() {
    if (selector.kind === 'producto_michelada') return 1;
    return comboMicheladaCantidad();
  }

  function renderSelectorBebida() {
    renderSeleccionMultiple(
      'vrSelectorBebidaWrap', 'vrSelectorBebida', selectorBebidaCantidad(), catalogo.sabores_bebida,
      selector.saboresBebidaIds, 'Bebida',
      (i, id) => { selector.saboresBebidaIds[i] = id; renderSelectorBebida(); },
    );
  }

  function renderSelectorMichelada() {
    renderSeleccionMultiple(
      'vrSelectorMicheladaWrap', 'vrSelectorMichelada', selectorMicheladaCantidad(), catalogo.sabores_michelada,
      selector.saboresMicheladaIds, 'Michelada',
      (i, id) => { selector.saboresMicheladaIds[i] = id; renderSelectorMichelada(); },
    );
  }

  function renderSelectorPorciones() {
    renderSeleccionMultiple(
      'vrSelectorPorcionesWrap', 'vrSelectorPorciones', comboPorcionesCantidad(), catalogo.sabores,
      selector.saboresPorcionIds, 'Porción',
      (i, id) => { selector.saboresPorcionIds[i] = id; renderSelectorPorciones(); actualizarPrecioSelector(); },
    );
  }

  function toggleSaborSeleccionado(saborId) {
    if (!selector.mitad) {
      selector.sabor1Id = saborId;
      selector.sabor2Id = null;
      return;
    }
    if (selector.sabor1Id === saborId) {
      selector.sabor1Id = selector.sabor2Id;
      selector.sabor2Id = null;
    } else if (selector.sabor2Id === saborId) {
      selector.sabor2Id = null;
    } else if (!selector.sabor1Id) {
      selector.sabor1Id = saborId;
    } else {
      // ya hay 1 o 2 sabores elegidos: el nuevo clic ocupa/reemplaza la segunda mitad
      selector.sabor2Id = saborId;
    }
  }

  function renderSelectorSabor1() {
    const cont = document.getElementById('vrSelectorSabor1');
    cont.innerHTML = '';
    catalogo.sabores.forEach(s => {
      const esSabor1 = selector.sabor1Id === s.id;
      const esSabor2 = selector.sabor2Id === s.id;
      const seleccionado = esSabor1 || esSabor2;
      let nombre = saborLabel(s);
      if (selector.mitad && seleccionado) {
        nombre += ` <span class="pz-badge-mitad">${esSabor1 ? '1/2' : '2/2'}</span>`;
      }
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pz-chip' + (seleccionado ? ' pz-chip-active' : '');
      btn.innerHTML = nombre;
      btn.addEventListener('click', () => {
        toggleSaborSeleccionado(s.id);
        renderSelectorSabor1();
        actualizarPrecioSelector();
      });
      cont.appendChild(btn);
    });
    actualizarFaltanSabor();
  }

  function actualizarFaltanSabor() {
    const el = document.getElementById('vrSelectorSaborFaltan');
    if (!el) return;
    const requerido = selector.mitad ? 2 : 1;
    const asignado = (selector.sabor1Id ? 1 : 0) + (selector.sabor2Id ? 1 : 0);
    const faltan = Math.max(0, requerido - asignado);
    el.textContent = faltan > 0 ? `Falta${faltan > 1 ? 'n' : ''} ${faltan}` : 'Listo';
    el.classList.toggle('pz-faltan-ok', faltan === 0);
  }

  function actualizarPrecioSelector() {
    const el = document.getElementById('vrSelectorPrecio');

    if (selector.kind === 'porcion') {
      if (!selector.sabor1Id) { el.textContent = '$0.00'; return; }
      const producto = productoPorcionIndividual();
      const precio = parseFloat(producto.precio);
      el.textContent = `$${(precio * selector.cantidad).toFixed(2)}`;
      el.dataset.unitario = precio;
      return;
    }

    if (selector.kind === 'producto_alitas' || selector.kind === 'producto_bebida' || selector.kind === 'producto_michelada') {
      const producto = catalogo.productos.find(p => p.id === selector.productoId);
      const precio = parseFloat(producto.precio);
      el.textContent = `$${(precio * selector.cantidad).toFixed(2)}`;
      el.dataset.unitario = precio;
      return;
    }

    if (selector.kind === 'combo' && !comboTieneTamanos()) {
      // Combo de precio fijo: se muestra el precio base; el recargo por sabor
      // premium (pizza fija o porciones) se calcula al confirmar el pedido.
      const c = comboSeleccionado();
      if (comboTienePizzaFija() && (!selector.sabor1Id || (selector.mitad && !selector.sabor2Id))) {
        el.textContent = '$0.00';
        return;
      }
      const requeridoPorciones = comboPorcionesCantidad();
      if (requeridoPorciones > 0 && selector.saboresPorcionIds.filter(Boolean).length !== requeridoPorciones) {
        el.textContent = '$0.00';
        return;
      }
      const precio = parseFloat((c && c.precio_fijo) || 0);
      el.textContent = `$${(precio * selector.cantidad).toFixed(2)}`;
      el.dataset.unitario = precio;
      return;
    }

    if (!selector.tamanoId || !selector.sabor1Id || (selector.mitad && !selector.sabor2Id)) {
      el.textContent = '$0.00';
      return;
    }
    const body = new FormData();
    body.append('tamano_id', selector.tamanoId);
    body.append('sabor_1_id', selector.sabor1Id);
    body.append('sabor_2_id', selector.mitad ? selector.sabor2Id : '');
    if (selector.kind === 'combo') body.append('combo_id', selector.comboId);

    fetch(window.PZ_URLS.calcularPrecio, { method: 'POST', body, headers: { 'X-CSRFToken': window.CSRF_TOKEN } })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          const precio = parseFloat(data.precio);
          el.textContent = `$${(precio * selector.cantidad).toFixed(2)}`;
          el.dataset.unitario = precio;
        }
      });
  }

  window.vrCambiarCantidad = function (delta) {
    selector.cantidad = Math.max(1, selector.cantidad + delta);
    document.getElementById('vrSelectorCantidad').textContent = selector.cantidad;
    actualizarPrecioSelector();
  };

  function resetSelectorComun() {
    selector.sabor1Id = null;
    selector.sabor2Id = null;
    selector.mitad = false;
    selector.cantidad = 1;
    selector.alitas = [];
    selector.saboresBebidaIds = [];
    selector.saboresMicheladaIds = [];
    selector.saboresPorcionIds = [];
    document.getElementById('vrSelectorMitad').checked = false;
    document.getElementById('vrSelectorCantidad').textContent = '1';
  }

  function abrirSelectorTamanoPizza(tamano) {
    selector.kind = 'pizza';
    selector.comboId = null;
    selector.productoId = null;
    selector.tamanoId = tamano.id;
    resetSelectorComun();

    // La "Porción" es una sola porción de pizza: no admite mitad y mitad
    // (no tiene sentido partir una porción individual en dos sabores).
    const permiteMitad = tamano.nombre !== 'Porción';

    document.getElementById('vrModalTitulo').textContent = `Pizza ${tamano.nombre}`;
    document.getElementById('vrSelectorTamanoWrap').style.display = 'none';
    document.getElementById('vrSelectorMitadWrap').style.display = permiteMitad ? 'block' : 'none';
    document.getElementById('vrSelectorSaborWrap').style.display = 'block';

    renderSelectorSabor1();
    renderSelectorPorciones();
    renderSelectorAlitas();
    renderSelectorBebida();
    renderSelectorMichelada();
    actualizarPrecioSelector();
    selectorModal.show();
  }

  // Los combos usan su propio configurador por pasos (handoff_combo): el modal
  // genérico se queda para pizzas, porciones y productos sueltos.
  const configuradorCombo = window.pzCrearConfiguradorCombo
    ? window.pzCrearConfiguradorCombo({
      catalogo: catalogo,
      calcularPrecioUrl: window.PZ_URLS.calcularPrecio,
      csrfToken: window.CSRF_TOKEN,
      mostrarToast: mostrarToast,
      onAgregar: function (item) {
        carrito.push(item);
        mostrarToast(`Agregado: ${item._label}`);
        renderCarrito();
      },
    })
    : null;

  function abrirSelectorCombo(combo) {
    configuradorCombo.abrir(combo);
  }

  function abrirSelectorPorcion(producto) {
    selector.kind = 'porcion';
    selector.comboId = null;
    selector.productoId = producto.id;
    selector.tamanoId = null;
    resetSelectorComun();

    document.getElementById('vrModalTitulo').textContent = producto.nombre;
    document.getElementById('vrSelectorTamanoWrap').style.display = 'none';
    document.getElementById('vrSelectorMitadWrap').style.display = 'none';
    document.getElementById('vrSelectorSaborWrap').style.display = 'block';

    renderSelectorSabor1();
    renderSelectorPorciones();
    renderSelectorAlitas();
    renderSelectorBebida();
    renderSelectorMichelada();
    actualizarPrecioSelector();
    selectorModal.show();
  }

  function abrirSelectorProductoAlitas(producto) {
    selector.kind = 'producto_alitas';
    selector.comboId = null;
    selector.productoId = producto.id;
    selector.tamanoId = null;
    resetSelectorComun();

    document.getElementById('vrModalTitulo').textContent = producto.nombre;
    document.getElementById('vrSelectorTamanoWrap').style.display = 'none';
    document.getElementById('vrSelectorMitadWrap').style.display = 'none';
    document.getElementById('vrSelectorSaborWrap').style.display = 'none';

    renderSelectorPorciones();
    renderSelectorAlitas();
    renderSelectorBebida();
    renderSelectorMichelada();
    actualizarPrecioSelector();
    selectorModal.show();
  }

  function abrirSelectorProductoBebida(producto) {
    selector.kind = 'producto_bebida';
    selector.comboId = null;
    selector.productoId = producto.id;
    selector.tamanoId = null;
    resetSelectorComun();

    document.getElementById('vrModalTitulo').textContent = producto.nombre;
    document.getElementById('vrSelectorTamanoWrap').style.display = 'none';
    document.getElementById('vrSelectorMitadWrap').style.display = 'none';
    document.getElementById('vrSelectorSaborWrap').style.display = 'none';

    renderSelectorPorciones();
    renderSelectorAlitas();
    renderSelectorBebida();
    renderSelectorMichelada();
    actualizarPrecioSelector();
    selectorModal.show();
  }

  function abrirSelectorProductoMichelada(producto) {
    selector.kind = 'producto_michelada';
    selector.comboId = null;
    selector.productoId = producto.id;
    selector.tamanoId = null;
    resetSelectorComun();

    document.getElementById('vrModalTitulo').textContent = producto.nombre;
    document.getElementById('vrSelectorTamanoWrap').style.display = 'none';
    document.getElementById('vrSelectorMitadWrap').style.display = 'none';
    document.getElementById('vrSelectorSaborWrap').style.display = 'none';

    renderSelectorPorciones();
    renderSelectorAlitas();
    renderSelectorBebida();
    renderSelectorMichelada();
    actualizarPrecioSelector();
    selectorModal.show();
  }

  document.getElementById('vrSelectorMitad').addEventListener('change', function () {
    selector.mitad = this.checked;
    if (!selector.mitad) selector.sabor2Id = null;
    renderSelectorSabor1();
    actualizarPrecioSelector();
  });

  document.getElementById('vrBtnAgregarSelector').addEventListener('click', function () {
    if (selector.kind === 'porcion') {
      if (!selector.sabor1Id) {
        alert('Selecciona un sabor antes de agregar.');
        return;
      }
      const producto = productoPorcionIndividual();
      const sabor1 = catalogo.sabores.find(s => s.id === selector.sabor1Id);
      const precioUnitario = parseFloat(document.getElementById('vrSelectorPrecio').dataset.unitario || 0);

      carrito.push({
        kind: 'producto', cantidad: selector.cantidad, observacion: `Sabor: ${sabor1.nombre}`,
        producto_id: producto.id,
        _label: `${producto.nombre} - ${sabor1.nombre}`, _precio_unitario: precioUnitario,
      });

      selectorModal.hide();
      mostrarToast(`Agregado: ${carrito[carrito.length - 1]._label}`);
      renderCarrito();
      return;
    }

    if (selector.kind === 'producto_alitas') {
      const requeridoAlitasProd = alitasRequeridas();
      if (requeridoAlitasProd > 0 && alitasAsignadas() !== requeridoAlitasProd) {
        alert(`Asigna ${requeridoAlitasProd} alitas entre 1 y 3 sabores antes de agregar.`);
        return;
      }
      const producto = catalogo.productos.find(p => p.id === selector.productoId);
      const precioUnitario = parseFloat(document.getElementById('vrSelectorPrecio').dataset.unitario || 0);
      const alitasTexto = selector.alitas.map(a => {
        const sabor = catalogo.sabores_alitas.find(s => s.id === a.saborId);
        return `${a.cantidad} ${sabor.nombre}`;
      }).join(', ');

      carrito.push({
        kind: 'producto', cantidad: selector.cantidad, observacion: '',
        producto_id: producto.id,
        alitas_sabores: selector.alitas.map(a => ({ sabor_id: a.saborId, cantidad: a.cantidad })),
        _label: `${producto.nombre}${alitasTexto ? ' - ' + alitasTexto : ''}`,
        _precio_unitario: precioUnitario,
      });

      selectorModal.hide();
      mostrarToast(`Agregado: ${carrito[carrito.length - 1]._label}`);
      renderCarrito();
      return;
    }

    if (selector.kind === 'producto_bebida') {
      if (!selector.saboresBebidaIds[0]) {
        alert('Selecciona el sabor de la bebida.');
        return;
      }
      const producto = catalogo.productos.find(p => p.id === selector.productoId);
      const sabor = catalogo.sabores_bebida.find(s => s.id === selector.saboresBebidaIds[0]);
      const precioUnitario = parseFloat(document.getElementById('vrSelectorPrecio').dataset.unitario || 0);

      carrito.push({
        kind: 'producto', cantidad: selector.cantidad, observacion: '',
        producto_id: producto.id,
        sabor_bebida_id: selector.saboresBebidaIds[0],
        _label: `${producto.nombre} - ${sabor.nombre}`,
        _precio_unitario: precioUnitario,
      });

      selectorModal.hide();
      mostrarToast(`Agregado: ${carrito[carrito.length - 1]._label}`);
      renderCarrito();
      return;
    }

    if (selector.kind === 'producto_michelada') {
      if (!selector.saboresMicheladaIds[0]) {
        alert('Selecciona el sabor de la michelada.');
        return;
      }
      const producto = catalogo.productos.find(p => p.id === selector.productoId);
      const sabor = catalogo.sabores_michelada.find(s => s.id === selector.saboresMicheladaIds[0]);
      const precioUnitario = parseFloat(document.getElementById('vrSelectorPrecio').dataset.unitario || 0);

      carrito.push({
        kind: 'producto', cantidad: selector.cantidad, observacion: '',
        producto_id: producto.id,
        sabor_bebida_id: selector.saboresMicheladaIds[0],
        _label: `${producto.nombre} - ${sabor.nombre}`,
        _precio_unitario: precioUnitario,
      });

      selectorModal.hide();
      mostrarToast(`Agregado: ${carrito[carrito.length - 1]._label}`);
      renderCarrito();
      return;
    }

    if (selector.kind === 'combo' && !comboTieneTamanos()) {
      const c = comboSeleccionado();
      if (comboTienePizzaFija() && (!selector.sabor1Id || (selector.mitad && !selector.sabor2Id))) {
        alert('Selecciona el sabor de la pizza antes de agregar.');
        return;
      }
      const requeridoAlitasFijo = alitasRequeridas();
      if (requeridoAlitasFijo > 0 && alitasAsignadas() !== requeridoAlitasFijo) {
        alert(`Asigna ${requeridoAlitasFijo} alitas entre 1 y 3 sabores antes de agregar.`);
        return;
      }
      const requeridoPorciones = comboPorcionesCantidad();
      if (requeridoPorciones > 0 && selector.saboresPorcionIds.filter(Boolean).length !== requeridoPorciones) {
        alert('Selecciona el sabor de cada porción de pizza antes de agregar.');
        return;
      }
      const requeridoBebidaFijo = selectorBebidaCantidad();
      if (requeridoBebidaFijo > 0 && selector.saboresBebidaIds.filter(Boolean).length !== requeridoBebidaFijo) {
        alert('Selecciona el sabor de cada bebida antes de agregar.');
        return;
      }
      const requeridoMicheladaFijo = selectorMicheladaCantidad();
      if (requeridoMicheladaFijo > 0 && selector.saboresMicheladaIds.filter(Boolean).length !== requeridoMicheladaFijo) {
        alert('Selecciona el sabor de cada michelada antes de agregar.');
        return;
      }

      const precioUnitario = parseFloat(document.getElementById('vrSelectorPrecio').dataset.unitario || 0);
      const alitasTexto = selector.alitas.map(a => {
        const sabor = catalogo.sabores_alitas.find(s => s.id === a.saborId);
        return `${a.cantidad} ${sabor.nombre}`;
      }).join(', ');
      let saborTexto = '';
      if (selector.sabor1Id) {
        const sabor1 = catalogo.sabores.find(s => s.id === selector.sabor1Id);
        const sabor2 = selector.mitad ? catalogo.sabores.find(s => s.id === selector.sabor2Id) : null;
        saborTexto = sabor1.nombre + (sabor2 ? ' / ' + sabor2.nombre : '');
      }
      const porcionesTexto = selector.saboresPorcionIds.map(id => catalogo.sabores.find(s => s.id === id).nombre).join(', ');
      const bebidaTexto = selector.saboresBebidaIds.map(id => catalogo.sabores_bebida.find(s => s.id === id).nombre).join(', ');
      const micheladaTexto = selector.saboresMicheladaIds.map(id => catalogo.sabores_michelada.find(s => s.id === id).nombre).join(', ');

      let label = c.nombre;
      if (saborTexto) label += ' - ' + saborTexto;
      if (porcionesTexto) label += ' | Porciones: ' + porcionesTexto;
      if (alitasTexto) label += ' | Alitas: ' + alitasTexto;
      if (bebidaTexto) label += ' | Bebida: ' + bebidaTexto;
      if (micheladaTexto) label += ' | Michelada: ' + micheladaTexto;

      carrito.push({
        kind: 'combo', cantidad: selector.cantidad, observacion: '',
        combo_id: selector.comboId,
        sabor_1_id: selector.sabor1Id, sabor_2_id: selector.mitad ? selector.sabor2Id : null,
        alitas_sabores: selector.alitas.map(a => ({ sabor_id: a.saborId, cantidad: a.cantidad })),
        sabores_bebida_ids: selector.saboresBebidaIds.slice(),
        sabores_michelada_ids: selector.saboresMicheladaIds.slice(),
        sabores_porcion_ids: selector.saboresPorcionIds.slice(),
        _label: label,
        _precio_unitario: precioUnitario,
      });

      selectorModal.hide();
      mostrarToast(`Agregado: ${carrito[carrito.length - 1]._label}`);
      renderCarrito();
      return;
    }

    if (!selector.tamanoId || !selector.sabor1Id || (selector.mitad && !selector.sabor2Id)) {
      alert('Selecciona tamaño y sabor(es) antes de agregar.');
      return;
    }
    const requeridoAlitas = alitasRequeridas();
    if (requeridoAlitas > 0 && alitasAsignadas() !== requeridoAlitas) {
      alert(`Asigna ${requeridoAlitas} alitas entre 1 y 3 sabores antes de agregar.`);
      return;
    }
    const requeridoBebida = selectorBebidaCantidad();
    if (requeridoBebida > 0 && selector.saboresBebidaIds.filter(Boolean).length !== requeridoBebida) {
      alert('Selecciona el sabor de cada bebida antes de agregar.');
      return;
    }
    const tamano = catalogo.tamanos.find(t => t.id === selector.tamanoId);
    const sabor1 = catalogo.sabores.find(s => s.id === selector.sabor1Id);
    const sabor2 = selector.mitad ? catalogo.sabores.find(s => s.id === selector.sabor2Id) : null;
    const precioUnitario = parseFloat(document.getElementById('vrSelectorPrecio').dataset.unitario || 0);
    const saborTexto = sabor1.nombre + (sabor2 ? ' / ' + sabor2.nombre : '');

    if (selector.kind === 'pizza') {
      carrito.push({
        kind: 'pizza', cantidad: selector.cantidad, observacion: '',
        tamano_id: selector.tamanoId, sabor_1_id: selector.sabor1Id, sabor_2_id: selector.mitad ? selector.sabor2Id : null,
        _label: `Pizza ${tamano.nombre} - ${saborTexto}`, _precio_unitario: precioUnitario,
      });
    } else {
      const combo = comboSeleccionado();
      const alitasTexto = selector.alitas.map(a => {
        const sabor = catalogo.sabores_alitas.find(s => s.id === a.saborId);
        return `${a.cantidad} ${sabor.nombre}`;
      }).join(', ');
      const bebidaTexto = selector.saboresBebidaIds.map(id => catalogo.sabores_bebida.find(s => s.id === id).nombre).join(', ');
      carrito.push({
        kind: 'combo', cantidad: selector.cantidad, observacion: '',
        combo_id: selector.comboId, tamano_id: selector.tamanoId,
        sabor_1_id: selector.sabor1Id, sabor_2_id: selector.mitad ? selector.sabor2Id : null,
        alitas_sabores: selector.alitas.map(a => ({ sabor_id: a.saborId, cantidad: a.cantidad })),
        sabores_bebida_ids: selector.saboresBebidaIds.slice(),
        _label: `${combo.nombre} (${tamano.nombre}) - ${saborTexto}${alitasTexto ? ' | Alitas: ' + alitasTexto : ''}${bebidaTexto ? ' | Bebida: ' + bebidaTexto : ''}`,
        _precio_unitario: precioUnitario,
      });
    }

    selectorModal.hide();
    mostrarToast(`Agregado: ${carrito[carrito.length - 1]._label}`);
    renderCarrito();
  });

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
    selectorModal = new bootstrap.Modal(document.getElementById('vrModalSelector'));
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
