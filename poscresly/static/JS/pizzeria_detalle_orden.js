(function () {
  let currentItem = null;

  function urlParaItem(base, itemId) {
    return base.replace('/0/', '/' + itemId + '/');
  }

  function escapeHtml(texto) {
    const div = document.createElement('div');
    div.textContent = texto == null ? '' : texto;
    return div.innerHTML;
  }

  function postItem(base, itemId, params) {
    const entries = Object.entries(params || {});
    const options = {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN },
    };
    // Daphne rechaza a nivel de protocolo un POST con multipart/form-data
    // sin partes (FormData vacío), así que solo adjuntamos body si hay campos.
    if (entries.length) {
      const body = new FormData();
      entries.forEach(([k, v]) => body.append(k, v));
      options.body = body;
    }
    return fetch(urlParaItem(base, itemId), options).then(r => r.json().catch(() => {
      throw new Error(`Respuesta inválida del servidor (HTTP ${r.status})`);
    }));
  }

  // ===== HOJA DEL PLATILLO =====
  // Reutiliza .pz-cart-sheet / .pz-sheet-backdrop (pizzeria-cart-bar.css) y
  // el helper pzMoverAlBodyEnMobile (pizzeria_cart_bar.js) — mismo mecanismo
  // que ya usa el carrito de Punto de venta para escapar el overflow:hidden
  // de .col-der y quedar siempre por encima de la bottom nav.
  const hojaEl = document.getElementById('diHoja');
  const backdropEl = document.getElementById('diSheetBackdrop');
  const bodyEl = document.getElementById('diHojaBody');
  const barraAccionesEl = document.getElementById('diBarraAcciones');

  if (!hojaEl || !backdropEl || !bodyEl) return;

  if (window.pzMoverAlBodyEnMobile) {
    window.pzMoverAlBodyEnMobile(hojaEl);
    window.pzMoverAlBodyEnMobile(backdropEl);
    // .do-barra-acciones es position:fixed igual que la hoja, y vive
    // dentro de .main-content (overflow:hidden) — sin moverla a <body>
    // queda recortada por ese overflow en vez de flotar de verdad sobre
    // la bottom nav. Mismo motivo por el que pizzeria_bottom_nav.html y
    // el carrito de Punto de venta hacen lo mismo con sus propios fixed.
    if (barraAccionesEl) window.pzMoverAlBodyEnMobile(barraAccionesEl);
  }

  function abrirHoja() {
    hojaEl.classList.add('pz-cart-sheet-open');
    backdropEl.classList.add('active');
  }

  function cerrarHoja() {
    hojaEl.classList.remove('pz-cart-sheet-open');
    backdropEl.classList.remove('active');
  }

  backdropEl.addEventListener('click', cerrarHoja);

  // ===== Tap en el pill de estado de una fila: avanza sin abrir nada =====
  function avanzarItem(ev, boton) {
    ev.stopPropagation();
    if (boton.disabled) return;
    const itemId = boton.dataset.itemId;
    boton.disabled = true;
    postItem(window.PZ_URLS.avanzarItemPreparacion, itemId, {})
      .then(data => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); boton.disabled = false; return; }
        window.location.reload();
      })
      .catch((err) => {
        alert(err && err.message ? err.message : 'Error inesperado al avanzar el estado');
        boton.disabled = false;
      });
  }

  // ===== Tap en el resto de la fila: abre la hoja completa =====
  function abrirHojaItem(el) {
    const itemId = el.dataset.itemId;
    if (!itemId) return;

    bodyEl.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i></div>';
    abrirHoja();

    fetch(urlParaItem(window.PZ_URLS.detalleItemPreparacion, itemId))
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') {
          bodyEl.innerHTML = '<p class="text-danger">No se pudo cargar el platillo.</p>';
          return;
        }
        currentItem = data.item;
        renderHoja();
      })
      .catch(() => {
        bodyEl.innerHTML = '<p class="text-danger">Error inesperado.</p>';
      });
  }

  function renderEstados(d) {
    return d.estados.map((op) => `
        <button type="button" class="do-hoja-estado-opcion${op.value === d.estado ? ' do-hoja-estado-opcion-activa' : ''}" data-estado="${op.value}" onclick="doSeleccionarEstado('${op.value}')">
          <span class="do-hoja-estado-dot"></span>
          <span class="do-hoja-estado-label">${escapeHtml(op.display)}</span>
        </button>`).join('');
  }

  function renderHoja() {
    const d = currentItem;

    let html = `
      <div class="do-hoja-header">
        <span class="do-hoja-badge">${d.cantidad}</span>
        <div class="do-hoja-info">
          <span class="do-hoja-nombre">${escapeHtml(d.nombre)}</span>
          ${d.modificadores ? `<span class="do-hoja-mods">${escapeHtml(d.modificadores)}</span>` : ''}
        </div>
        <span class="do-hoja-importe">$${Number(d.importe).toFixed(2)}</span>
      </div>

      <div class="do-hoja-section">
        <span class="do-hoja-section-label">ESTADO</span>
        <div class="do-hoja-estados">${renderEstados(d)}</div>
        ${d.siguiente_estado ? `
        <button type="button" class="do-hoja-siguiente-btn" onclick="doSeleccionarEstado('${d.siguiente_estado}')">
          <i class="bi bi-check-lg"></i><span>${escapeHtml(d.siguiente_etiqueta)}</span>
        </button>` : ''}
      </div>`;

    if (d.puede_gestionar) {
      html += `
      <div class="do-hoja-divider"></div>

      <div class="do-hoja-section">
        <span class="do-hoja-section-label">CANTIDAD</span>
        <div class="do-hoja-cantidad-row">
          <div class="do-hoja-stepper">
            <button type="button" class="do-hoja-stepper-btn" id="diStepperMenos" onclick="doCambiarCantidad(-1)"${d.cantidad <= 1 ? ' disabled' : ''}>−</button>
            <span class="do-hoja-cantidad-valor" id="diHojaCantidadValor">${d.cantidad}</span>
            <button type="button" class="do-hoja-stepper-btn" onclick="doCambiarCantidad(1)">＋</button>
          </div>
          <span class="do-hoja-precio-unit" id="diHojaPrecioUnit">$${Number(d.precio_unitario).toFixed(2)} c/u</span>
        </div>
      </div>

      <div class="do-hoja-divider"></div>

      <div class="do-hoja-section">
        <span class="do-hoja-section-label">ACCIONES</span>
        <div class="do-hoja-acciones">
          <button type="button" class="do-hoja-accion" onclick="doMostrarFormEditar()">
            <i class="bi bi-pencil do-hoja-accion-icono"></i>
            <span class="do-hoja-accion-texto">Editar personalización</span>
            <i class="bi bi-chevron-right do-hoja-accion-chevron"></i>
          </button>
          <button type="button" class="do-hoja-accion" onclick="doPedirOtroIgual()">
            <i class="bi bi-copy do-hoja-accion-icono"></i>
            <span class="do-hoja-accion-texto">Pedir otro igual</span>
            <i class="bi bi-chevron-right do-hoja-accion-chevron"></i>
          </button>
          <button type="button" class="do-hoja-accion" onclick="doReimprimirPlatillo()">
            <i class="bi bi-printer do-hoja-accion-icono"></i>
            <span class="do-hoja-accion-texto">Reimprimir en cocina</span>
            <i class="bi bi-chevron-right do-hoja-accion-chevron"></i>
          </button>`;
      if (d.puede_quitar) {
        html += `
          <button type="button" class="do-hoja-accion do-hoja-accion-danger" onclick="doQuitarDelPedido()">
            <i class="bi bi-x-lg do-hoja-accion-icono"></i>
            <span class="do-hoja-accion-texto">Quitar de la orden</span>
            <i class="bi bi-chevron-right do-hoja-accion-chevron"></i>
          </button>`;
      }
      html += `
        </div>
      </div>`;
    }

    bodyEl.innerHTML = html;
  }

  // ===== Cantidad: la hoja se actualiza al toque, sin recargar la página
  // (a diferencia del resto de acciones) para que +/- se sienta inmediato. =====
  function cambiarCantidad(delta) {
    const nueva = currentItem.cantidad + delta;
    if (nueva < 1) return;
    currentItem.cantidad = nueva;

    document.getElementById('diHojaCantidadValor').textContent = nueva;
    document.getElementById('diStepperMenos').disabled = nueva <= 1;

    postItem(window.PZ_URLS.editarItemPreparacion, currentItem.id, {
      cantidad: nueva,
      observacion: currentItem.observacion || '',
    }).then(data => {
      if (data.status !== 'ok') { alert('Error: ' + data.message); return; }
      currentItem.importe = currentItem.precio_unitario * nueva;
      const importeEl = document.querySelector('.do-hoja-importe');
      if (importeEl) importeEl.textContent = '$' + currentItem.importe.toFixed(2);
      const badgeEl = document.querySelector(`.do-linea[data-item-id="${currentItem.id}"] .do-linea-badge`);
      if (badgeEl) badgeEl.textContent = nueva;
    }).catch((err) => alert(err && err.message ? err.message : 'Error inesperado al actualizar la cantidad'));
  }

  function mostrarFormEditar() {
    const d = currentItem;
    bodyEl.innerHTML = `
      <div class="do-hoja-edit-form">
        <label class="do-hoja-edit-label">Cantidad</label>
        <input type="number" min="1" class="do-hoja-edit-input" id="diEditCantidad" value="${d.cantidad}">
        <label class="do-hoja-edit-label">Nota / observación</label>
        <textarea class="do-hoja-edit-textarea" id="diEditObservacion" rows="3" placeholder="Ej: sin cebolla, extra picante">${escapeHtml(d.observacion)}</textarea>
        <div class="do-hoja-edit-actions">
          <button type="button" class="do-hoja-btn-cancelar" onclick="doRenderHojaItem()">Cancelar</button>
          <button type="button" class="do-hoja-btn-guardar" id="diBtnGuardarEdit" onclick="doGuardarEdicionItem()">Guardar</button>
        </div>
      </div>`;
  }

  function guardarEdicion() {
    const cantidad = parseInt(document.getElementById('diEditCantidad').value, 10);
    const observacion = document.getElementById('diEditObservacion').value.trim();
    if (!cantidad || cantidad < 1) { alert('Ingresa una cantidad válida'); return; }

    const boton = document.getElementById('diBtnGuardarEdit');
    boton.disabled = true;
    postItem(window.PZ_URLS.editarItemPreparacion, currentItem.id, { cantidad, observacion })
      .then(data => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); boton.disabled = false; return; }
        window.location.reload();
      })
      .catch((err) => { alert(err && err.message ? err.message : 'Error inesperado al editar el platillo'); boton.disabled = false; });
  }

  function pedirOtroIgual() {
    postItem(window.PZ_URLS.duplicarItemPreparacion, currentItem.id)
      .then(data => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); return; }
        window.location.reload();
      })
      .catch((err) => alert(err && err.message ? err.message : 'Error inesperado al duplicar el platillo'));
  }

  function reimprimirPlatillo() {
    postItem(window.PZ_URLS.reimprimirItemPreparacion, currentItem.id)
      .then(data => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); return; }
        alert('Ticket enviado a cocina');
      })
      .catch((err) => alert(err && err.message ? err.message : 'Error inesperado al reimprimir el platillo'));
  }

  function quitarDelPedido() {
    if (!confirm('¿Quitar este platillo del pedido?')) return;
    postItem(window.PZ_URLS.quitarItemPreparacion, currentItem.id)
      .then(data => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); return; }
        window.location.reload();
      })
      .catch((err) => alert(err && err.message ? err.message : 'Error inesperado al quitar el platillo'));
  }

  // ===== Tap en un estado de la fila de cuatro: salta directo, incluso
  // hacia atrás (corregir un error de marcado). =====
  function seleccionarEstado(estado) {
    if (estado === currentItem.estado) return;
    postItem(window.PZ_URLS.establecerEstadoItemPreparacion, currentItem.id, { estado })
      .then(data => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); return; }
        window.location.reload();
      })
      .catch((err) => alert(err && err.message ? err.message : 'Error inesperado al actualizar el estado'));
  }

  window.doAbrirHojaItem = abrirHojaItem;
  window.doAvanzarItem = avanzarItem;
  window.doRenderHojaItem = renderHoja;
  window.doCambiarCantidad = cambiarCantidad;
  window.doMostrarFormEditar = mostrarFormEditar;
  window.doGuardarEdicionItem = guardarEdicion;
  window.doPedirOtroIgual = pedirOtroIgual;
  window.doReimprimirPlatillo = reimprimirPlatillo;
  window.doQuitarDelPedido = quitarDelPedido;
  window.doSeleccionarEstado = seleccionarEstado;
})();
