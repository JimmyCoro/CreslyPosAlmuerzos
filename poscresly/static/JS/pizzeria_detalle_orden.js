(function () {
  let currentItem = null;

  const ESTADO_ICONOS = {
    en_proceso: 'fa-hourglass-half',
    cocinando: 'fa-fire-burner',
    listo: 'fa-check',
    completo: 'fa-check-double',
  };

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

  // ===== MODAL DE GESTIÓN DE PLATILLO =====

  function abrirModalItem(el) {
    const itemId = el.dataset.itemId;
    if (!itemId) return;

    const modalEl = document.getElementById('doModalItem');
    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    document.getElementById('diModalTitulo').textContent = 'Platillo';
    document.getElementById('diModalBody').innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i></div>';
    modal.show();

    fetch(urlParaItem(window.PZ_URLS.detalleItemPreparacion, itemId))
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') {
          document.getElementById('diModalBody').innerHTML = '<p class="text-danger">No se pudo cargar el platillo.</p>';
          return;
        }
        currentItem = data.item;
        renderAcciones();
      })
      .catch(() => {
        document.getElementById('diModalBody').innerHTML = '<p class="text-danger">Error inesperado.</p>';
      });
  }

  function iconoEstado(estado) {
    return ESTADO_ICONOS[estado] || 'fa-hourglass-half';
  }

  function renderEstadoDropdown(d) {
    const opciones = d.estados.map((op) => `
        <button type="button" class="di-estado-opcion di-icon-estado-${op.value}${op.value === d.estado ? ' di-estado-opcion-actual' : ''}" onclick="doSeleccionarEstado('${op.value}')">
          <span class="di-action-icon di-icon-estado-${op.value}"><i class="fas ${iconoEstado(op.value)}"></i></span>
          <span class="di-action-title">${escapeHtml(op.display)}</span>
          ${op.value === d.estado ? '<i class="fas fa-check di-estado-check"></i>' : ''}
        </button>`).join('');

    return `
      <div class="di-section-label">ESTADO</div>
      <div class="di-estado-select">
        <button type="button" class="di-estado-trigger" onclick="doToggleEstadoOpciones()">
          <span class="di-action-icon di-icon-estado-${d.estado}"><i class="fas ${iconoEstado(d.estado)}"></i></span>
          <span class="di-action-text">
            <span class="di-action-title">${escapeHtml(d.estado_display)}</span>
            <span class="di-action-desc">Toca para elegir cualquier estado</span>
          </span>
          <i class="fas fa-chevron-down di-estado-chevron" id="diEstadoChevron"></i>
        </button>
        <div class="di-estado-opciones" id="diEstadoOpciones" hidden>${opciones}</div>
      </div>`;
  }

  function renderAcciones() {
    const d = currentItem;
    document.getElementById('diModalTitulo').textContent = `${d.cantidad}× ${d.descripcion}`;

    let html = '<p class="di-subtitle">Mueve el estado o gestiona el platillo</p>';
    html += renderEstadoDropdown(d);

    if (d.puede_gestionar) {
      html += '<div class="di-section-label">ACCIONES</div>';
      html += `
        <button type="button" class="di-action" onclick="doMostrarFormEditar()">
          <span class="di-action-icon di-icon-edit"><i class="fas fa-pencil"></i></span>
          <span class="di-action-text">
            <span class="di-action-title">Editar platillo</span>
            <span class="di-action-desc">Modifique cantidad, notas o personalización</span>
          </span>
        </button>
        <button type="button" class="di-action" onclick="doPedirOtroIgual()">
          <span class="di-action-icon di-icon-copy"><i class="fas fa-copy"></i></span>
          <span class="di-action-text">
            <span class="di-action-title">Pedir otro igual</span>
            <span class="di-action-desc">Agrega una nueva línea con la misma personalización</span>
          </span>
        </button>
        <button type="button" class="di-action" onclick="doReimprimirPlatillo()">
          <span class="di-action-icon di-icon-print"><i class="fas fa-print"></i></span>
          <span class="di-action-text">
            <span class="di-action-title">Reimprimir este platillo</span>
            <span class="di-action-desc">Envía un ticket nuevo a cocina solo con este platillo</span>
          </span>
        </button>`;
      if (d.puede_quitar) {
        html += `
        <button type="button" class="di-action di-action-danger" onclick="doQuitarDelPedido()">
          <span class="di-action-icon di-icon-trash"><i class="fas fa-trash"></i></span>
          <span class="di-action-text">
            <span class="di-action-title">Quitar del pedido</span>
            <span class="di-action-desc">Solo si todavía no fue preparado ni servido</span>
          </span>
        </button>`;
      }
    }

    document.getElementById('diModalBody').innerHTML = html;
  }

  function mostrarFormEditar() {
    const d = currentItem;
    document.getElementById('diModalBody').innerHTML = `
      <div class="di-edit-form">
        <label class="di-edit-label">Cantidad</label>
        <input type="number" min="1" class="di-edit-input" id="diEditCantidad" value="${d.cantidad}">
        <label class="di-edit-label">Nota / observación</label>
        <textarea class="di-edit-textarea" id="diEditObservacion" rows="3" placeholder="Ej: sin cebolla, extra picante">${escapeHtml(d.observacion)}</textarea>
        <div class="di-edit-actions">
          <button type="button" class="di-btn-cancelar" onclick="doRenderAccionesItem()">Cancelar</button>
          <button type="button" class="di-btn-guardar" id="diBtnGuardarEdit" onclick="doGuardarEdicionItem()">Guardar</button>
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

  function toggleEstadoOpciones() {
    const opciones = document.getElementById('diEstadoOpciones');
    const chevron = document.getElementById('diEstadoChevron');
    if (!opciones) return;
    opciones.hidden = !opciones.hidden;
    chevron.classList.toggle('di-estado-chevron-abierto', !opciones.hidden);
  }

  function seleccionarEstado(estado) {
    if (estado === currentItem.estado) { toggleEstadoOpciones(); return; }
    postItem(window.PZ_URLS.establecerEstadoItemPreparacion, currentItem.id, { estado })
      .then(data => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); return; }
        window.location.reload();
      })
      .catch((err) => alert(err && err.message ? err.message : 'Error inesperado al actualizar el estado'));
  }

  window.doAbrirModalItem = abrirModalItem;
  window.doRenderAccionesItem = renderAcciones;
  window.doMostrarFormEditar = mostrarFormEditar;
  window.doGuardarEdicionItem = guardarEdicion;
  window.doPedirOtroIgual = pedirOtroIgual;
  window.doReimprimirPlatillo = reimprimirPlatillo;
  window.doQuitarDelPedido = quitarDelPedido;
  window.doToggleEstadoOpciones = toggleEstadoOpciones;
  window.doSeleccionarEstado = seleccionarEstado;
})();
