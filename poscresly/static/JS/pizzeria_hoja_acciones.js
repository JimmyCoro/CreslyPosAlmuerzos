(function () {
  const accHoja = document.getElementById('accHoja');
  const accBackdrop = document.getElementById('accSheetBackdrop');
  const btnAbrir = document.getElementById('accBtnAbrir');
  const confirmHoja = document.getElementById('accConfirmHoja');
  const confirmBackdrop = document.getElementById('accConfirmBackdrop');

  if (!accHoja || !accBackdrop || !confirmHoja || !confirmBackdrop) return;

  // Mismo mecanismo que la hoja del platillo (pizzeria_detalle_orden.js):
  // escapar el overflow:hidden de .main-content en móvil.
  if (window.pzMoverAlBodyEnMobile) {
    window.pzMoverAlBodyEnMobile(accHoja);
    window.pzMoverAlBodyEnMobile(accBackdrop);
    window.pzMoverAlBodyEnMobile(confirmHoja);
    window.pzMoverAlBodyEnMobile(confirmBackdrop);
  }

  function abrirAcciones() {
    accHoja.classList.add('pz-cart-sheet-open');
    accBackdrop.classList.add('active');
  }
  function cerrarAcciones() {
    accHoja.classList.remove('pz-cart-sheet-open');
    accBackdrop.classList.remove('active');
  }

  let motivoElegido = null;

  function resetMotivo() {
    motivoElegido = null;
    document.querySelectorAll('.acc-chip').forEach((c) => c.classList.remove('acc-chip-active'));
    const otro = document.getElementById('accMotivoOtro');
    if (otro) { otro.hidden = true; otro.value = ''; }
    const btn = document.getElementById('accBtnAnular');
    if (btn) btn.disabled = true;
  }

  function abrirConfirmacion() {
    resetMotivo();
    confirmHoja.classList.add('pz-cart-sheet-open');
    confirmBackdrop.classList.add('active');
  }
  function cerrarConfirmacion() {
    confirmHoja.classList.remove('pz-cart-sheet-open');
    confirmBackdrop.classList.remove('active');
  }

  if (btnAbrir) btnAbrir.addEventListener('click', abrirAcciones);
  accBackdrop.addEventListener('click', cerrarAcciones);
  confirmBackdrop.addEventListener('click', cerrarConfirmacion);

  // ===== Tap en una fila de la hoja de acciones =====
  function clickFila(el) {
    const disponible = el.dataset.disponible === '1';
    const clave = el.dataset.clave;

    if (!disponible) {
      cerrarAcciones();
      alert('Esta función todavía no está disponible.');
      return;
    }

    if (clave === 'llamar' && el.dataset.url) {
      cerrarAcciones();
      window.location.href = el.dataset.url;
      return;
    }

    if (clave === 'anular') {
      cerrarAcciones();
      abrirConfirmacion();
      return;
    }

    if (el.dataset.url) {
      cerrarAcciones();
      window.location.href = el.dataset.url;
      return;
    }
  }

  // ===== Confirmación de anulación: chips de motivo =====
  function actualizarBotonAnular() {
    const otro = document.getElementById('accMotivoOtro');
    const btn = document.getElementById('accBtnAnular');
    const hayOtro = otro && !otro.hidden && otro.value.trim();
    btn.disabled = !(motivoElegido || hayOtro);
  }

  function elegirMotivo(chip) {
    document.querySelectorAll('.acc-chip').forEach((c) => c.classList.remove('acc-chip-active'));
    chip.classList.add('acc-chip-active');
    const otro = document.getElementById('accMotivoOtro');
    if (chip.dataset.motivo === 'Otro') {
      motivoElegido = null;
      otro.hidden = false;
      otro.focus();
    } else {
      motivoElegido = chip.dataset.motivo;
      otro.hidden = true;
      otro.value = '';
    }
    actualizarBotonAnular();
  }

  document.addEventListener('input', function (ev) {
    if (ev.target && ev.target.id === 'accMotivoOtro') actualizarBotonAnular();
  });

  function confirmarAnular() {
    const otro = document.getElementById('accMotivoOtro');
    const motivo = motivoElegido || (otro && otro.value.trim() ? `Otro: ${otro.value.trim()}` : '');
    if (!motivo) return;

    const btn = document.getElementById('accBtnAnular');
    btn.disabled = true;

    const body = new FormData();
    body.append('motivo', motivo);
    fetch(window.PZ_URLS.cancelarPedido, {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN },
      body,
    })
      .then((r) => r.json().catch(() => { throw new Error(`Respuesta inválida del servidor (HTTP ${r.status})`); }))
      .then((data) => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); btn.disabled = false; return; }
        window.location.reload();
      })
      .catch((err) => {
        alert(err && err.message ? err.message : 'Error inesperado al anular el pedido');
        btn.disabled = false;
      });
  }

  window.accClickFila = clickFila;
  window.accElegirMotivo = elegirMotivo;
  window.accConfirmarAnular = confirmarAnular;
  window.accCerrarConfirmacion = cerrarConfirmacion;
})();
