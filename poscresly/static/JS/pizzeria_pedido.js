(function () {
  const catalogo = window.PZ_CATALOGO;
  const ctx = window.PZ_CONTEXT;

  const pizza = { tamanoId: null, sabor1Id: null, sabor2Id: null, mitad: false, cantidad: 1 };
  const combo = {
    comboId: null, tamanoId: null, sabor1Id: null, sabor2Id: null, mitad: false, cantidad: 1, alitas: [],
    saboresBebidaIds: [], saboresMicheladaIds: [], saboresPorcionIds: [],
  };
  const alitasProducto = { productoId: null, cantidad: 1, alitas: [] };
  const bebidaProducto = { productoId: null, cantidad: 1, saborBebidaId: null };
  const micheladaProducto = { productoId: null, cantidad: 1, saborMicheladaId: null };
  const carrito = [];
  let categoriaActiva = null;
  let modalAlitasProducto;
  let modalBebidaProducto;
  let modalMicheladaProducto;

  // ===== TABS =====
  document.querySelectorAll('#pzTabs .nav-link').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#pzTabs .nav-link').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.dataset.tab;
      document.querySelectorAll('.pz-tab-pane').forEach(pane => {
        pane.classList.toggle('d-none', pane.dataset.pane !== tab);
      });
    });
  });

  // ===== HELPERS DE RENDER =====
  function renderGrid(container, items, opts) {
    container.innerHTML = '';
    items.forEach(item => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pz-chip';
      if (opts.selectedId != null && opts.selectedId === opts.getId(item)) btn.classList.add('pz-chip-active');
      btn.innerHTML = opts.getLabel(item);
      btn.addEventListener('click', () => opts.onSelect(item));
      container.appendChild(btn);
    });
  }

  function saborLabel(s) {
    return s.es_premium ? `${s.nombre} <span class="pz-badge-premium">Premium</span>` : s.nombre;
  }

  // ===== PIZZA =====
  function renderTamanoRadio(container, opciones, selectedId, onSelect) {
    container.innerHTML = '';
    opciones.forEach(t => {
      const activo = selectedId === t.id;
      const row = document.createElement('button');
      row.type = 'button';
      row.className = 'pz-radio-row' + (activo ? ' pz-radio-row-active' : '');
      row.innerHTML = `
        <span class="pz-radio-left"><span class="pz-radio-dot"></span>${t.nombre}</span>
        <span class="pz-radio-precio">$${parseFloat(t.precio).toFixed(2)}</span>`;
      row.addEventListener('click', () => onSelect(t.id));
      container.appendChild(row);
    });
  }

  function renderPizzaTamanos() {
    renderTamanoRadio(
      document.getElementById('pzPizzaTamanos'),
      catalogo.tamanos.map(t => ({ id: t.id, nombre: t.nombre, precio: t.precio_base })),
      pizza.tamanoId,
      id => { pizza.tamanoId = id; renderPizzaTamanos(); actualizarPrecioPizza(); },
    );
  }

  function toggleSaborSeleccionado(state, saborId) {
    if (!state.mitad) {
      state.sabor1Id = saborId;
      state.sabor2Id = null;
      return;
    }
    if (state.sabor1Id === saborId) {
      state.sabor1Id = state.sabor2Id;
      state.sabor2Id = null;
    } else if (state.sabor2Id === saborId) {
      state.sabor2Id = null;
    } else if (!state.sabor1Id) {
      state.sabor1Id = saborId;
    } else {
      // ya hay 1 o 2 sabores elegidos: el nuevo clic ocupa/reemplaza la segunda mitad
      state.sabor2Id = saborId;
    }
  }

  function renderSaboresConMitad(container, state, faltanElId, onChange) {
    container.innerHTML = '';
    catalogo.sabores.forEach(s => {
      const esSabor1 = state.sabor1Id === s.id;
      const esSabor2 = state.sabor2Id === s.id;
      const seleccionado = esSabor1 || esSabor2;
      let nombre = saborLabel(s);
      if (state.mitad && seleccionado) {
        nombre += ` <span class="pz-badge-mitad">${esSabor1 ? '1/2' : '2/2'}</span>`;
      }
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pz-chip' + (seleccionado ? ' pz-chip-active' : '');
      btn.innerHTML = nombre;
      btn.addEventListener('click', () => { toggleSaborSeleccionado(state, s.id); onChange(); });
      container.appendChild(btn);
    });

    const el = document.getElementById(faltanElId);
    if (el) {
      const requerido = state.mitad ? 2 : 1;
      const asignado = (state.sabor1Id ? 1 : 0) + (state.sabor2Id ? 1 : 0);
      const faltan = Math.max(0, requerido - asignado);
      el.textContent = faltan > 0 ? `Falta${faltan > 1 ? 'n' : ''} ${faltan}` : 'Listo';
      el.classList.toggle('pz-faltan-ok', faltan === 0);
    }
  }

  function renderPizzaSabores() {
    renderSaboresConMitad(document.getElementById('pzPizzaSabor1'), pizza, 'pzPizzaSaborFaltan', () => {
      renderPizzaSabores();
      actualizarPrecioPizza();
    });
  }

  document.getElementById('pzPizzaMitad').addEventListener('change', function () {
    pizza.mitad = this.checked;
    if (!pizza.mitad) pizza.sabor2Id = null;
    renderPizzaSabores();
    actualizarPrecioPizza();
  });

  function actualizarPrecioPizza() {
    const el = document.getElementById('pzPizzaPrecio');
    if (!pizza.tamanoId || !pizza.sabor1Id || (pizza.mitad && !pizza.sabor2Id)) {
      el.textContent = '$0.00';
      return;
    }
    pedirPrecio({ tamano_id: pizza.tamanoId, sabor_1_id: pizza.sabor1Id, sabor_2_id: pizza.mitad ? pizza.sabor2Id : '' })
      .then(precio => { el.textContent = `$${(precio * pizza.cantidad).toFixed(2)}`; el.dataset.unitario = precio; });
  }

  window.pzAgregarPizza = function () {
    if (!pizza.tamanoId || !pizza.sabor1Id || (pizza.mitad && !pizza.sabor2Id)) {
      alert('Selecciona tamaño y sabor(es) antes de agregar.');
      return;
    }
    const tamano = catalogo.tamanos.find(t => t.id === pizza.tamanoId);
    const sabor1 = catalogo.sabores.find(s => s.id === pizza.sabor1Id);
    const sabor2 = pizza.mitad ? catalogo.sabores.find(s => s.id === pizza.sabor2Id) : null;
    const precioUnitario = parseFloat(document.getElementById('pzPizzaPrecio').dataset.unitario || 0);
    const obs = document.getElementById('pzPizzaObs').value.trim();

    carrito.push({
      kind: 'pizza',
      cantidad: pizza.cantidad,
      observacion: obs,
      tamano_id: pizza.tamanoId,
      sabor_1_id: pizza.sabor1Id,
      sabor_2_id: pizza.mitad ? pizza.sabor2Id : null,
      _label: `Pizza ${tamano.nombre} - ${sabor1.nombre}${sabor2 ? ' / ' + sabor2.nombre : ''}`,
      _precio_unitario: precioUnitario,
    });

    pizza.tamanoId = null; pizza.sabor1Id = null; pizza.sabor2Id = null; pizza.mitad = false; pizza.cantidad = 1;
    document.getElementById('pzPizzaMitad').checked = false;
    document.getElementById('pzPizzaObs').value = '';
    document.getElementById('pzPizzaCantidad').textContent = '1';
    renderPizzaTamanos(); renderPizzaSabores();
    document.getElementById('pzPizzaPrecio').textContent = '$0.00';
    renderCarrito();
  };

  // ===== COMBOS =====
  function renderCombos() {
    const cont = document.getElementById('pzComboLista');
    cont.innerHTML = '';
    catalogo.combos.forEach(c => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pz-chip pz-chip-combo' + (combo.comboId === c.id ? ' pz-chip-active' : '');
      btn.innerHTML = `
        <span class="pz-chip-combo-nombre">${c.nombre}</span>
        ${c.descripcion ? `<span class="pz-chip-combo-desc">${c.descripcion}</span>` : ''}`;
      btn.addEventListener('click', () => {
        combo.comboId = c.id; combo.tamanoId = null; combo.sabor1Id = null; combo.sabor2Id = null;
        combo.mitad = false; combo.alitas = [];
        combo.saboresBebidaIds = []; combo.saboresMicheladaIds = []; combo.saboresPorcionIds = [];
        document.getElementById('pzComboMitad').checked = false;
        renderCombos(); renderComboTamanos(); renderComboSabores(); renderComboAlitas();
        renderComboBebida(); renderComboMichelada(); renderComboPorciones();
        actualizarVisibilidadCombo();
        actualizarPrecioCombo();
      });
      cont.appendChild(btn);
    });
  }

  function comboSeleccionado() {
    return catalogo.combos.find(c => c.id === combo.comboId);
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
    return comboTieneTamanos() || comboTienePizzaFija();
  }

  function comboPorcionesCantidad() {
    const c = comboSeleccionado();
    return (c && c.porcion_pizza_cantidad) || 0;
  }

  function comboBebidaCantidad() {
    const c = comboSeleccionado();
    return (c && c.bebida_cantidad) || 0;
  }

  function comboMicheladaCantidad() {
    const c = comboSeleccionado();
    return (c && c.michelada_cantidad) || 0;
  }

  function actualizarVisibilidadCombo() {
    const tienePizza = comboRequierePizza();
    document.getElementById('pzComboTamanoWrap').classList.toggle('d-none', !comboTieneTamanos());
    document.getElementById('pzComboMitadWrap').classList.toggle('d-none', !tienePizza);
    document.getElementById('pzComboSaborWrap').classList.toggle('d-none', !tienePizza);
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

  function renderComboPorciones() {
    renderSeleccionMultiple(
      'pzComboPorcionesWrap', 'pzComboPorciones', comboPorcionesCantidad(), catalogo.sabores,
      combo.saboresPorcionIds, 'Porción',
      (i, id) => { combo.saboresPorcionIds[i] = id; renderComboPorciones(); actualizarPrecioCombo(); },
    );
  }

  function renderComboBebida() {
    renderSeleccionMultiple(
      'pzComboBebidaWrap', 'pzComboBebida', comboBebidaCantidad(), catalogo.sabores_bebida,
      combo.saboresBebidaIds, 'Bebida',
      (i, id) => { combo.saboresBebidaIds[i] = id; renderComboBebida(); },
    );
  }

  function renderComboMichelada() {
    renderSeleccionMultiple(
      'pzComboMicheladaWrap', 'pzComboMichelada', comboMicheladaCantidad(), catalogo.sabores_michelada,
      combo.saboresMicheladaIds, 'Michelada',
      (i, id) => { combo.saboresMicheladaIds[i] = id; renderComboMichelada(); },
    );
  }

  function renderComboTamanos() {
    const c = comboSeleccionado();
    const opciones = (c ? c.tamanos : []).map(t => ({ id: t.tamano_id, nombre: t.tamano_nombre, precio: t.precio }));
    renderTamanoRadio(
      document.getElementById('pzComboTamanos'),
      opciones,
      combo.tamanoId,
      id => { combo.tamanoId = id; renderComboTamanos(); actualizarPrecioCombo(); },
    );
  }

  // ===== SABOR DE ALITAS (combos con componente de alitas) =====
  function alitasRequeridas() {
    const c = comboSeleccionado();
    return (c && c.alitas_cantidad) || 0;
  }

  function alitasAsignadas() {
    return combo.alitas.reduce((sum, a) => sum + a.cantidad, 0);
  }

  function actualizarBadgeAlitasCombo() {
    const requerido = alitasRequeridas();
    const faltan = Math.max(0, requerido - alitasAsignadas());
    const totalEl = document.getElementById('pzComboAlitasTotal');
    totalEl.textContent = faltan > 0 ? `Falta${faltan > 1 ? 'n' : ''} ${faltan}` : 'Listo';
    totalEl.classList.toggle('pz-faltan-ok', faltan === 0);
  }

  function establecerCantidadAlitasCombo(saborId, cantidadDeseada, inputEl) {
    const requerido = alitasRequeridas();
    let cantidad = Math.max(0, Math.min(Math.floor(cantidadDeseada) || 0, requerido));
    let entry = combo.alitas.find(a => a.saborId === saborId);

    if (cantidad > 0 && !entry && combo.alitas.length >= 3) {
      cantidad = 0;
      alert('Máximo 3 sabores de alitas.');
    }

    if (cantidad <= 0) {
      combo.alitas = combo.alitas.filter(a => a.saborId !== saborId);
    } else if (entry) {
      entry.cantidad = cantidad;
    } else {
      combo.alitas.push({ saborId, cantidad });
    }

    inputEl.value = cantidad || '';
    actualizarBadgeAlitasCombo();
  }

  function renderComboAlitas() {
    const wrap = document.getElementById('pzComboAlitasWrap');
    const requerido = alitasRequeridas();
    if (!requerido) {
      wrap.classList.add('d-none');
      return;
    }
    wrap.classList.remove('d-none');

    const cont = document.getElementById('pzComboAlitas');
    cont.innerHTML = '';
    (catalogo.sabores_alitas || []).forEach(s => {
      const actual = combo.alitas.find(a => a.saborId === s.id);
      const cantidad = actual ? actual.cantidad : 0;
      const row = document.createElement('div');
      row.className = 'pz-select-row';
      row.innerHTML = `
        <span class="pz-select-nombre">${s.nombre}</span>
        <input type="text" inputmode="numeric" pattern="[0-9]*" class="pz-alitas-input" value="${cantidad || ''}" placeholder="0">`;
      const input = row.querySelector('.pz-alitas-input');
      input.addEventListener('input', () => establecerCantidadAlitasCombo(s.id, parseInt(input.value, 10), input));
      input.addEventListener('focus', () => input.select());
      cont.appendChild(row);
    });

    actualizarBadgeAlitasCombo();
  }

  function renderComboSabores() {
    renderSaboresConMitad(document.getElementById('pzComboSabor1'), combo, 'pzComboSaborFaltan', () => {
      renderComboSabores();
      actualizarPrecioCombo();
    });
  }

  document.getElementById('pzComboMitad').addEventListener('change', function () {
    combo.mitad = this.checked;
    if (!combo.mitad) combo.sabor2Id = null;
    renderComboSabores();
    actualizarPrecioCombo();
  });

  function actualizarPrecioCombo() {
    const el = document.getElementById('pzComboPrecio');
    const c = comboSeleccionado();
    if (!c) { el.textContent = '$0.00'; return; }

    if (comboTieneTamanos()) {
      if (!combo.tamanoId || !combo.sabor1Id || (combo.mitad && !combo.sabor2Id)) {
        el.textContent = '$0.00';
        return;
      }
      pedirPrecio({
        combo_id: combo.comboId, tamano_id: combo.tamanoId,
        sabor_1_id: combo.sabor1Id, sabor_2_id: combo.mitad ? combo.sabor2Id : '',
      }).then(precio => { el.textContent = `$${(precio * combo.cantidad).toFixed(2)}`; el.dataset.unitario = precio; });
      return;
    }

    // Combo de precio fijo: se muestra el precio base; el recargo por sabor
    // premium (pizza fija o porciones) se calcula al confirmar el pedido.
    if (comboTienePizzaFija() && (!combo.sabor1Id || (combo.mitad && !combo.sabor2Id))) {
      el.textContent = '$0.00';
      return;
    }
    const requeridoPorciones = comboPorcionesCantidad();
    if (requeridoPorciones > 0 && combo.saboresPorcionIds.filter(Boolean).length !== requeridoPorciones) {
      el.textContent = '$0.00';
      return;
    }
    const precio = parseFloat(c.precio_fijo || 0);
    el.textContent = `$${(precio * combo.cantidad).toFixed(2)}`;
    el.dataset.unitario = precio;
  }

  window.pzAgregarCombo = function () {
    const c = comboSeleccionado();
    if (!c) { alert('Selecciona un combo.'); return; }

    if (comboTieneTamanos()) {
      if (!combo.tamanoId || !combo.sabor1Id || (combo.mitad && !combo.sabor2Id)) {
        alert('Selecciona tamaño y sabor(es) antes de agregar.');
        return;
      }
    } else if (comboTienePizzaFija() && (!combo.sabor1Id || (combo.mitad && !combo.sabor2Id))) {
      alert('Selecciona el sabor de la pizza antes de agregar.');
      return;
    }

    const requeridoAlitas = alitasRequeridas();
    if (requeridoAlitas > 0 && alitasAsignadas() !== requeridoAlitas) {
      alert(`Asigna ${requeridoAlitas} alitas entre 1 y 3 sabores antes de agregar.`);
      return;
    }
    const requeridoPorciones = comboPorcionesCantidad();
    if (requeridoPorciones > 0 && combo.saboresPorcionIds.filter(Boolean).length !== requeridoPorciones) {
      alert('Selecciona el sabor de cada porción de pizza antes de agregar.');
      return;
    }
    const requeridoBebida = comboBebidaCantidad();
    if (requeridoBebida > 0 && combo.saboresBebidaIds.filter(Boolean).length !== requeridoBebida) {
      alert('Selecciona el sabor de cada bebida antes de agregar.');
      return;
    }
    const requeridoMichelada = comboMicheladaCantidad();
    if (requeridoMichelada > 0 && combo.saboresMicheladaIds.filter(Boolean).length !== requeridoMichelada) {
      alert('Selecciona el sabor de cada michelada antes de agregar.');
      return;
    }

    const tamanoInfo = comboTieneTamanos() ? c.tamanos.find(t => t.tamano_id === combo.tamanoId) : null;
    const precioUnitario = parseFloat(document.getElementById('pzComboPrecio').dataset.unitario || 0);
    const obs = document.getElementById('pzComboObs').value.trim();
    const alitasTexto = combo.alitas.map(a => {
      const sabor = catalogo.sabores_alitas.find(s => s.id === a.saborId);
      return `${a.cantidad} ${sabor.nombre}`;
    }).join(', ');

    let saborTexto = '';
    if (combo.sabor1Id) {
      const sabor1 = catalogo.sabores.find(s => s.id === combo.sabor1Id);
      const sabor2 = combo.mitad ? catalogo.sabores.find(s => s.id === combo.sabor2Id) : null;
      saborTexto = sabor1.nombre + (sabor2 ? ' / ' + sabor2.nombre : '');
    }
    const porcionesTexto = combo.saboresPorcionIds.map(id => catalogo.sabores.find(s => s.id === id).nombre).join(', ');
    const bebidaTexto = combo.saboresBebidaIds.map(id => catalogo.sabores_bebida.find(s => s.id === id).nombre).join(', ');
    const micheladaTexto = combo.saboresMicheladaIds.map(id => catalogo.sabores_michelada.find(s => s.id === id).nombre).join(', ');

    let label = c.nombre + (tamanoInfo ? ` (${tamanoInfo.tamano_nombre})` : '');
    if (saborTexto) label += ' - ' + saborTexto;
    if (porcionesTexto) label += ' | Porciones: ' + porcionesTexto;
    if (alitasTexto) label += ' | Alitas: ' + alitasTexto;
    if (bebidaTexto) label += ' | Bebida: ' + bebidaTexto;
    if (micheladaTexto) label += ' | Michelada: ' + micheladaTexto;

    carrito.push({
      kind: 'combo',
      cantidad: combo.cantidad,
      observacion: obs,
      combo_id: combo.comboId,
      tamano_id: combo.tamanoId,
      sabor_1_id: combo.sabor1Id,
      sabor_2_id: combo.mitad ? combo.sabor2Id : null,
      alitas_sabores: combo.alitas.map(a => ({ sabor_id: a.saborId, cantidad: a.cantidad })),
      sabores_bebida_ids: combo.saboresBebidaIds.slice(),
      sabores_michelada_ids: combo.saboresMicheladaIds.slice(),
      sabores_porcion_ids: combo.saboresPorcionIds.slice(),
      _label: label,
      _precio_unitario: precioUnitario,
    });

    combo.comboId = null; combo.tamanoId = null; combo.sabor1Id = null; combo.sabor2Id = null;
    combo.mitad = false; combo.cantidad = 1; combo.alitas = [];
    combo.saboresBebidaIds = []; combo.saboresMicheladaIds = []; combo.saboresPorcionIds = [];
    document.getElementById('pzComboMitad').checked = false;
    document.getElementById('pzComboObs').value = '';
    document.getElementById('pzComboCantidad').textContent = '1';
    renderCombos(); renderComboTamanos(); renderComboSabores(); renderComboAlitas();
    renderComboBebida(); renderComboMichelada(); renderComboPorciones();
    actualizarVisibilidadCombo();
    document.getElementById('pzComboPrecio').textContent = '$0.00';
    renderCarrito();
  };

  // ===== PRODUCTOS SIMPLES =====
  function renderCategoriaChips() {
    const categorias = [...new Set(catalogo.productos.map(p => p.categoria))];
    const container = document.getElementById('pzCategoriaChips');
    container.innerHTML = '';
    categorias.forEach(cat => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'pz-chip pz-chip-small' + (categoriaActiva === cat ? ' pz-chip-active' : '');
      chip.textContent = cat;
      chip.addEventListener('click', () => { categoriaActiva = cat; renderCategoriaChips(); renderProductos(); });
      container.appendChild(chip);
    });
    if (!categoriaActiva && categorias.length) categoriaActiva = categorias[0];
  }

  function renderProductos() {
    const lista = catalogo.productos.filter(p => p.categoria === categoriaActiva);
    const container = document.getElementById('pzProductosLista');
    container.innerHTML = '';
    lista.forEach(p => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'pz-chip pz-chip-producto';
      btn.innerHTML = `${p.nombre}<br><small>$${parseFloat(p.precio).toFixed(2)}</small>`;
      if (p.alitas_cantidad > 0) {
        btn.addEventListener('click', () => abrirModalAlitasProducto(p));
      } else if (p.tipo_sabor_bebida === 'bebida') {
        btn.addEventListener('click', () => abrirModalBebidaProducto(p));
      } else if (p.tipo_sabor_bebida === 'michelada') {
        btn.addEventListener('click', () => abrirModalMicheladaProducto(p));
      } else {
        btn.addEventListener('click', () => {
          carrito.push({
            kind: 'producto', cantidad: 1, observacion: '', producto_id: p.id,
            _label: p.nombre, _precio_unitario: parseFloat(p.precio),
          });
          renderCarrito();
        });
      }
      container.appendChild(btn);
    });
  }

  // ===== PRODUCTO DE ALITAS (sabor requerido) =====
  function productoAlitasSeleccionado() {
    return catalogo.productos.find(p => p.id === alitasProducto.productoId);
  }

  function alitasProductoRequeridas() {
    const p = productoAlitasSeleccionado();
    return (p && p.alitas_cantidad) || 0;
  }

  function alitasProductoAsignadas() {
    return alitasProducto.alitas.reduce((sum, a) => sum + a.cantidad, 0);
  }

  function actualizarBadgeAlitasProducto() {
    const requerido = alitasProductoRequeridas();
    const faltan = Math.max(0, requerido - alitasProductoAsignadas());
    const totalEl = document.getElementById('pzModalAlitasProductoFaltan');
    totalEl.textContent = faltan > 0 ? `Falta${faltan > 1 ? 'n' : ''} ${faltan}` : 'Listo';
    totalEl.classList.toggle('pz-faltan-ok', faltan === 0);
  }

  function establecerCantidadAlitasProducto(saborId, cantidadDeseada, inputEl) {
    const requerido = alitasProductoRequeridas();
    let cantidad = Math.max(0, Math.min(Math.floor(cantidadDeseada) || 0, requerido));
    let entry = alitasProducto.alitas.find(a => a.saborId === saborId);

    if (cantidad > 0 && !entry && alitasProducto.alitas.length >= 3) {
      cantidad = 0;
      alert('Máximo 3 sabores de alitas.');
    }

    if (cantidad <= 0) {
      alitasProducto.alitas = alitasProducto.alitas.filter(a => a.saborId !== saborId);
    } else if (entry) {
      entry.cantidad = cantidad;
    } else {
      alitasProducto.alitas.push({ saborId, cantidad });
    }

    inputEl.value = cantidad || '';
    actualizarBadgeAlitasProducto();
  }

  function renderAlitasProductoGrid() {
    const requerido = alitasProductoRequeridas();
    const cont = document.getElementById('pzModalAlitasProductoGrid');
    cont.innerHTML = '';
    (catalogo.sabores_alitas || []).forEach(s => {
      const actual = alitasProducto.alitas.find(a => a.saborId === s.id);
      const cantidad = actual ? actual.cantidad : 0;
      const row = document.createElement('div');
      row.className = 'pz-select-row';
      row.innerHTML = `
        <span class="pz-select-nombre">${s.nombre}</span>
        <input type="text" inputmode="numeric" pattern="[0-9]*" class="pz-alitas-input" value="${cantidad || ''}" placeholder="0">`;
      const input = row.querySelector('.pz-alitas-input');
      input.addEventListener('input', () => establecerCantidadAlitasProducto(s.id, parseInt(input.value, 10), input));
      input.addEventListener('focus', () => input.select());
      cont.appendChild(row);
    });

    actualizarBadgeAlitasProducto();
  }

  function actualizarPrecioAlitasProducto() {
    const p = productoAlitasSeleccionado();
    const el = document.getElementById('pzModalAlitasProductoPrecio');
    if (!p) { el.textContent = '$0.00'; return; }
    const precio = parseFloat(p.precio);
    el.textContent = `$${(precio * alitasProducto.cantidad).toFixed(2)}`;
    el.dataset.unitario = precio;
  }

  window.pzCambiarCantidadProductoAlitas = function (delta) {
    alitasProducto.cantidad = Math.max(1, alitasProducto.cantidad + delta);
    document.getElementById('pzModalAlitasProductoCantidad').textContent = alitasProducto.cantidad;
    actualizarPrecioAlitasProducto();
  };

  function abrirModalAlitasProducto(producto) {
    alitasProducto.productoId = producto.id;
    alitasProducto.cantidad = 1;
    alitasProducto.alitas = [];
    document.getElementById('pzModalAlitasProductoTitulo').textContent = producto.nombre;
    document.getElementById('pzModalAlitasProductoCantidad').textContent = '1';
    renderAlitasProductoGrid();
    actualizarPrecioAlitasProducto();
    modalAlitasProducto.show();
  }

  document.getElementById('pzBtnAgregarAlitasProducto').addEventListener('click', function () {
    const requerido = alitasProductoRequeridas();
    if (requerido > 0 && alitasProductoAsignadas() !== requerido) {
      alert(`Asigna ${requerido} alitas entre 1 y 3 sabores antes de agregar.`);
      return;
    }
    const producto = productoAlitasSeleccionado();
    const precioUnitario = parseFloat(document.getElementById('pzModalAlitasProductoPrecio').dataset.unitario || 0);
    const alitasTexto = alitasProducto.alitas.map(a => {
      const sabor = catalogo.sabores_alitas.find(s => s.id === a.saborId);
      return `${a.cantidad} ${sabor.nombre}`;
    }).join(', ');

    carrito.push({
      kind: 'producto', cantidad: alitasProducto.cantidad, observacion: '',
      producto_id: producto.id,
      alitas_sabores: alitasProducto.alitas.map(a => ({ sabor_id: a.saborId, cantidad: a.cantidad })),
      _label: `${producto.nombre}${alitasTexto ? ' - ' + alitasTexto : ''}`,
      _precio_unitario: precioUnitario,
    });

    modalAlitasProducto.hide();
    renderCarrito();
  });

  // ===== PRODUCTO DE BEBIDA (sabor de cola requerido) =====
  function productoBebidaSeleccionado() {
    return catalogo.productos.find(p => p.id === bebidaProducto.productoId);
  }

  function renderBebidaProductoGrid() {
    renderGrid(document.getElementById('pzModalBebidaProductoGrid'), catalogo.sabores_bebida || [], {
      getId: s => s.id,
      getLabel: s => s.nombre,
      selectedId: bebidaProducto.saborBebidaId,
      onSelect: s => { bebidaProducto.saborBebidaId = s.id; renderBebidaProductoGrid(); },
    });
  }

  function actualizarPrecioBebidaProducto() {
    const p = productoBebidaSeleccionado();
    const el = document.getElementById('pzModalBebidaProductoPrecio');
    if (!p) { el.textContent = '$0.00'; return; }
    const precio = parseFloat(p.precio);
    el.textContent = `$${(precio * bebidaProducto.cantidad).toFixed(2)}`;
    el.dataset.unitario = precio;
  }

  window.pzCambiarCantidadProductoBebida = function (delta) {
    bebidaProducto.cantidad = Math.max(1, bebidaProducto.cantidad + delta);
    document.getElementById('pzModalBebidaProductoCantidad').textContent = bebidaProducto.cantidad;
    actualizarPrecioBebidaProducto();
  };

  function abrirModalBebidaProducto(producto) {
    bebidaProducto.productoId = producto.id;
    bebidaProducto.cantidad = 1;
    bebidaProducto.saborBebidaId = null;
    document.getElementById('pzModalBebidaProductoTitulo').textContent = producto.nombre;
    document.getElementById('pzModalBebidaProductoCantidad').textContent = '1';
    renderBebidaProductoGrid();
    actualizarPrecioBebidaProducto();
    modalBebidaProducto.show();
  }

  document.getElementById('pzBtnAgregarBebidaProducto').addEventListener('click', function () {
    if (!bebidaProducto.saborBebidaId) {
      alert('Selecciona el sabor de la bebida.');
      return;
    }
    const producto = productoBebidaSeleccionado();
    const sabor = catalogo.sabores_bebida.find(s => s.id === bebidaProducto.saborBebidaId);
    const precioUnitario = parseFloat(document.getElementById('pzModalBebidaProductoPrecio').dataset.unitario || 0);

    carrito.push({
      kind: 'producto', cantidad: bebidaProducto.cantidad, observacion: '',
      producto_id: producto.id,
      sabor_bebida_id: bebidaProducto.saborBebidaId,
      _label: `${producto.nombre} - ${sabor.nombre}`,
      _precio_unitario: precioUnitario,
    });

    modalBebidaProducto.hide();
    renderCarrito();
  });

  // ===== PRODUCTO DE MICHELADA (sabor requerido) =====
  function productoMicheladaSeleccionado() {
    return catalogo.productos.find(p => p.id === micheladaProducto.productoId);
  }

  function renderMicheladaProductoGrid() {
    renderGrid(document.getElementById('pzModalMicheladaProductoGrid'), catalogo.sabores_michelada || [], {
      getId: s => s.id,
      getLabel: s => s.nombre,
      selectedId: micheladaProducto.saborMicheladaId,
      onSelect: s => { micheladaProducto.saborMicheladaId = s.id; renderMicheladaProductoGrid(); },
    });
  }

  function actualizarPrecioMicheladaProducto() {
    const p = productoMicheladaSeleccionado();
    const el = document.getElementById('pzModalMicheladaProductoPrecio');
    if (!p) { el.textContent = '$0.00'; return; }
    const precio = parseFloat(p.precio);
    el.textContent = `$${(precio * micheladaProducto.cantidad).toFixed(2)}`;
    el.dataset.unitario = precio;
  }

  window.pzCambiarCantidadProductoMichelada = function (delta) {
    micheladaProducto.cantidad = Math.max(1, micheladaProducto.cantidad + delta);
    document.getElementById('pzModalMicheladaProductoCantidad').textContent = micheladaProducto.cantidad;
    actualizarPrecioMicheladaProducto();
  };

  function abrirModalMicheladaProducto(producto) {
    micheladaProducto.productoId = producto.id;
    micheladaProducto.cantidad = 1;
    micheladaProducto.saborMicheladaId = null;
    document.getElementById('pzModalMicheladaProductoTitulo').textContent = producto.nombre;
    document.getElementById('pzModalMicheladaProductoCantidad').textContent = '1';
    renderMicheladaProductoGrid();
    actualizarPrecioMicheladaProducto();
    modalMicheladaProducto.show();
  }

  document.getElementById('pzBtnAgregarMicheladaProducto').addEventListener('click', function () {
    if (!micheladaProducto.saborMicheladaId) {
      alert('Selecciona el sabor de la michelada.');
      return;
    }
    const producto = productoMicheladaSeleccionado();
    const sabor = catalogo.sabores_michelada.find(s => s.id === micheladaProducto.saborMicheladaId);
    const precioUnitario = parseFloat(document.getElementById('pzModalMicheladaProductoPrecio').dataset.unitario || 0);

    carrito.push({
      kind: 'producto', cantidad: micheladaProducto.cantidad, observacion: '',
      producto_id: producto.id,
      sabor_bebida_id: micheladaProducto.saborMicheladaId,
      _label: `${producto.nombre} - ${sabor.nombre}`,
      _precio_unitario: precioUnitario,
    });

    modalMicheladaProducto.hide();
    renderCarrito();
  });

  // ===== CANTIDAD =====
  window.pzCambiarCantidad = function (tipo, delta) {
    const state = tipo === 'pizza' ? pizza : combo;
    state.cantidad = Math.max(1, state.cantidad + delta);
    document.getElementById(tipo === 'pizza' ? 'pzPizzaCantidad' : 'pzComboCantidad').textContent = state.cantidad;
    if (tipo === 'pizza') actualizarPrecioPizza(); else actualizarPrecioCombo();
  };

  // ===== PRECIO VÍA AJAX =====
  function pedirPrecio(params) {
    const body = new FormData();
    Object.entries(params).forEach(([k, v]) => body.append(k, v));
    return fetch(window.PZ_URLS.calcularPrecio, {
      method: 'POST', body, headers: { 'X-CSRFToken': window.CSRF_TOKEN },
    })
      .then(r => r.json())
      .then(data => (data.status === 'ok' ? parseFloat(data.precio) : 0));
  }

  // ===== CARRITO =====
  function renderCarrito() {
    const container = document.getElementById('pzCarritoItems');
    const totalEl = document.getElementById('pzCarritoTotal');
    const btnConfirmar = document.getElementById('pzBtnConfirmar');

    if (!carrito.length) {
      container.innerHTML = '<p class="text-muted">Aún no has agregado productos</p>';
      totalEl.textContent = '$0.00';
      btnConfirmar.disabled = true;
      return;
    }

    let total = 0;
    container.innerHTML = carrito.map((item, idx) => {
      const subtotal = item._precio_unitario * item.cantidad;
      total += subtotal;
      return `
        <div class="pz-carrito-item">
          <span class="pz-item-qty">${item.cantidad}</span>
          <span class="pz-carrito-item-label">${item._label}</span>
          <span>$${subtotal.toFixed(2)}</span>
          <button type="button" class="pz-carrito-remove" onclick="pzQuitarItem(${idx})"><i class="fas fa-times"></i></button>
        </div>`;
    }).join('');
    totalEl.textContent = `$${total.toFixed(2)}`;
    btnConfirmar.disabled = false;
  }

  window.pzQuitarItem = function (idx) {
    carrito.splice(idx, 1);
    renderCarrito();
  };

  window.pzConfirmarPedido = function () {
    if (!carrito.length) return;

    const contactoInput = document.getElementById('pzContacto');
    if (ctx.tipo === 'llevar' && !ctx.pedidoId && contactoInput && !contactoInput.value.trim()) {
      alert('Ingresa el nombre o teléfono del cliente.');
      return;
    }

    const body = new FormData();
    body.append('tipo', ctx.tipo);
    if (ctx.mesaId) body.append('mesa_id', ctx.mesaId);
    if (contactoInput) body.append('contacto', contactoInput.value.trim());
    if (ctx.pedidoId) body.append('pedido_id', ctx.pedidoId);
    body.append('carrito', JSON.stringify(carrito));

    const btn = document.getElementById('pzBtnConfirmar');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Guardando...';

    fetch(window.PZ_URLS.guardarPedido, {
      method: 'POST', body, headers: { 'X-CSRFToken': window.CSRF_TOKEN },
    })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          window.location.href = window.PZ_URLS.mapaMesas;
        } else {
          alert('Error: ' + data.message);
          btn.disabled = false;
          btn.innerHTML = '<i class="fas fa-check me-2"></i>Confirmar pedido';
        }
      })
      .catch(() => {
        alert('Error inesperado al guardar el pedido');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check me-2"></i>Confirmar pedido';
      });
  };

  // ===== INIT =====
  modalAlitasProducto = new bootstrap.Modal(document.getElementById('pzModalAlitasProducto'));
  modalBebidaProducto = new bootstrap.Modal(document.getElementById('pzModalBebidaProducto'));
  modalMicheladaProducto = new bootstrap.Modal(document.getElementById('pzModalMicheladaProducto'));
  renderPizzaTamanos();
  renderPizzaSabores();
  renderCombos();
  renderComboTamanos();
  renderComboSabores();
  renderComboAlitas();
  renderComboBebida();
  renderComboMichelada();
  renderComboPorciones();
  actualizarVisibilidadCombo();
  renderCategoriaChips();
  renderProductos();
  renderCarrito();
})();
