(function () {
  const catalogo = window.PZ_CATALOGO;
  const ctx = window.PZ_CONTEXT;

  const pizza = { tamanoId: null, sabor1Id: null, sabor2Id: null, mitad: false, cantidad: 1 };
  const combo = { comboId: null, tamanoId: null, sabor1Id: null, sabor2Id: null, mitad: false, cantidad: 1 };
  const carrito = [];
  let categoriaActiva = null;

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
  function renderPizzaTamanos() {
    renderGrid(document.getElementById('pzPizzaTamanos'), catalogo.tamanos, {
      getId: t => t.id,
      getLabel: t => `${t.nombre}<br><small>$${parseFloat(t.precio_base).toFixed(2)}</small>`,
      selectedId: pizza.tamanoId,
      onSelect: t => { pizza.tamanoId = t.id; renderPizzaTamanos(); actualizarPrecioPizza(); },
    });
  }

  function renderPizzaSabores() {
    renderGrid(document.getElementById('pzPizzaSabor1'), catalogo.sabores, {
      getId: s => s.id,
      getLabel: saborLabel,
      selectedId: pizza.sabor1Id,
      onSelect: s => { pizza.sabor1Id = s.id; renderPizzaSabores(); renderPizzaSabor2(); actualizarPrecioPizza(); },
    });
  }

  function renderPizzaSabor2() {
    const opciones = catalogo.sabores.filter(s => s.id !== pizza.sabor1Id);
    renderGrid(document.getElementById('pzPizzaSabor2'), opciones, {
      getId: s => s.id,
      getLabel: saborLabel,
      selectedId: pizza.sabor2Id,
      onSelect: s => { pizza.sabor2Id = s.id; renderPizzaSabor2(); actualizarPrecioPizza(); },
    });
  }

  document.getElementById('pzPizzaMitad').addEventListener('change', function () {
    pizza.mitad = this.checked;
    document.getElementById('pzPizzaSabor2Wrap').classList.toggle('d-none', !pizza.mitad);
    if (!pizza.mitad) pizza.sabor2Id = null;
    else renderPizzaSabor2();
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
    document.getElementById('pzPizzaSabor2Wrap').classList.add('d-none');
    document.getElementById('pzPizzaObs').value = '';
    document.getElementById('pzPizzaCantidad').textContent = '1';
    renderPizzaTamanos(); renderPizzaSabores();
    document.getElementById('pzPizzaPrecio').textContent = '$0.00';
    renderCarrito();
  };

  // ===== COMBOS =====
  function renderCombos() {
    renderGrid(document.getElementById('pzComboLista'), catalogo.combos, {
      getId: c => c.id,
      getLabel: c => c.nombre,
      selectedId: combo.comboId,
      onSelect: c => {
        combo.comboId = c.id; combo.tamanoId = null;
        renderCombos(); renderComboTamanos(); renderComboComponentes(); actualizarPrecioCombo();
      },
    });
  }

  function comboSeleccionado() {
    return catalogo.combos.find(c => c.id === combo.comboId);
  }

  function renderComboTamanos() {
    const c = comboSeleccionado();
    const opciones = c ? c.tamanos : [];
    renderGrid(document.getElementById('pzComboTamanos'), opciones, {
      getId: t => t.tamano_id,
      getLabel: t => `${t.tamano_nombre}<br><small>$${parseFloat(t.precio).toFixed(2)}</small>`,
      selectedId: combo.tamanoId,
      onSelect: t => { combo.tamanoId = t.tamano_id; renderComboTamanos(); actualizarPrecioCombo(); },
    });
  }

  function renderComboComponentes() {
    const c = comboSeleccionado();
    const wrap = document.getElementById('pzComboComponentesWrap');
    const list = document.getElementById('pzComboComponentes');
    if (!c) { wrap.style.display = 'none'; return; }
    wrap.style.display = 'block';
    list.innerHTML = c.componentes.map(comp => `<li>${comp.cantidad}x ${comp.tipo}${comp.detalle ? ' - ' + comp.detalle : ''}</li>`).join('');
  }

  function renderComboSabores() {
    renderGrid(document.getElementById('pzComboSabor1'), catalogo.sabores, {
      getId: s => s.id,
      getLabel: saborLabel,
      selectedId: combo.sabor1Id,
      onSelect: s => { combo.sabor1Id = s.id; renderComboSabores(); renderComboSabor2(); actualizarPrecioCombo(); },
    });
  }

  function renderComboSabor2() {
    const opciones = catalogo.sabores.filter(s => s.id !== combo.sabor1Id);
    renderGrid(document.getElementById('pzComboSabor2'), opciones, {
      getId: s => s.id,
      getLabel: saborLabel,
      selectedId: combo.sabor2Id,
      onSelect: s => { combo.sabor2Id = s.id; renderComboSabor2(); actualizarPrecioCombo(); },
    });
  }

  document.getElementById('pzComboMitad').addEventListener('change', function () {
    combo.mitad = this.checked;
    document.getElementById('pzComboSabor2Wrap').classList.toggle('d-none', !combo.mitad);
    if (!combo.mitad) combo.sabor2Id = null;
    else renderComboSabor2();
    actualizarPrecioCombo();
  });

  function actualizarPrecioCombo() {
    const el = document.getElementById('pzComboPrecio');
    if (!combo.comboId || !combo.tamanoId || !combo.sabor1Id || (combo.mitad && !combo.sabor2Id)) {
      el.textContent = '$0.00';
      return;
    }
    pedirPrecio({
      combo_id: combo.comboId, tamano_id: combo.tamanoId,
      sabor_1_id: combo.sabor1Id, sabor_2_id: combo.mitad ? combo.sabor2Id : '',
    }).then(precio => { el.textContent = `$${(precio * combo.cantidad).toFixed(2)}`; el.dataset.unitario = precio; });
  }

  window.pzAgregarCombo = function () {
    if (!combo.comboId || !combo.tamanoId || !combo.sabor1Id || (combo.mitad && !combo.sabor2Id)) {
      alert('Selecciona combo, tamaño y sabor(es) antes de agregar.');
      return;
    }
    const c = comboSeleccionado();
    const tamanoInfo = c.tamanos.find(t => t.tamano_id === combo.tamanoId);
    const sabor1 = catalogo.sabores.find(s => s.id === combo.sabor1Id);
    const sabor2 = combo.mitad ? catalogo.sabores.find(s => s.id === combo.sabor2Id) : null;
    const precioUnitario = parseFloat(document.getElementById('pzComboPrecio').dataset.unitario || 0);
    const obs = document.getElementById('pzComboObs').value.trim();

    carrito.push({
      kind: 'combo',
      cantidad: combo.cantidad,
      observacion: obs,
      combo_id: combo.comboId,
      tamano_id: combo.tamanoId,
      sabor_1_id: combo.sabor1Id,
      sabor_2_id: combo.mitad ? combo.sabor2Id : null,
      _label: `${c.nombre} (${tamanoInfo.tamano_nombre}) - ${sabor1.nombre}${sabor2 ? ' / ' + sabor2.nombre : ''}`,
      _precio_unitario: precioUnitario,
    });

    combo.comboId = null; combo.tamanoId = null; combo.sabor1Id = null; combo.sabor2Id = null; combo.mitad = false; combo.cantidad = 1;
    document.getElementById('pzComboMitad').checked = false;
    document.getElementById('pzComboSabor2Wrap').classList.add('d-none');
    document.getElementById('pzComboObs').value = '';
    document.getElementById('pzComboCantidad').textContent = '1';
    renderCombos(); renderComboTamanos(); renderComboComponentes(); renderComboSabores();
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
      btn.addEventListener('click', () => {
        carrito.push({
          kind: 'producto', cantidad: 1, observacion: '', producto_id: p.id,
          _label: p.nombre, _precio_unitario: parseFloat(p.precio),
        });
        renderCarrito();
      });
      container.appendChild(btn);
    });
  }

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
          <span>${item.cantidad}x ${item._label}</span>
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
  renderPizzaTamanos();
  renderPizzaSabores();
  renderCombos();
  renderComboTamanos();
  renderComboComponentes();
  renderComboSabores();
  renderCategoriaChips();
  renderProductos();
  renderCarrito();
})();
