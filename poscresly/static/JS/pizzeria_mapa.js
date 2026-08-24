(function () {
  function pzMesaClick(el) {
    const pedidoId = el.dataset.pedidoId;
    if (pedidoId) {
      pzVerPedido(pedidoId, el.dataset.mesaId);
      return;
    }
    pzAbrirAccionesMesa(el);
  }

  const PZMA_DOT_COLOR = { libre: '#23a05f', reservada: '#3b6fd6', ocupada: '#c8102e', por_cobrar: '#d99000' };
  const PZM_ESTADO_LABEL_LARGO = { libre: 'Libre', reservada: 'Reservada', ocupada: 'Ocupada', por_cobrar: 'Por cobrar' };
  let pzmaMesaActual = null;

  function pzAbrirAccionesMesa(el) {
    pzmaMesaActual = el;
    const numero = el.querySelector('.pzm-table-num').textContent.trim();
    const estado = el.dataset.estado;
    const cap = el.dataset.capacidad;

    document.getElementById('pzmaTitulo').textContent = `Mesa ${numero}`;
    document.getElementById('pzmaStatusTexto').textContent =
      `${PZM_ESTADO_LABEL_LARGO[estado] || estado} · Cap. ${cap} persona${cap === '1' ? '' : 's'}`;
    document.getElementById('pzmaStatusDot').style.background = PZMA_DOT_COLOR[estado] || '#9ca3af';

    const reservaTexto = document.getElementById('pzmaReservaTexto');
    const reservaBtn = document.getElementById('pzmaReserva');
    if (estado === 'reservada') {
      reservaTexto.textContent = 'Quitar reserva';
      reservaBtn.dataset.accion = 'quitar';
    } else {
      reservaTexto.textContent = 'Marcar como reservada';
      reservaBtn.dataset.accion = 'reservar';
    }

    const modal = new bootstrap.Modal(document.getElementById('pzModalMesaAcciones'));
    modal.show();
  }

  function pzCambiarEstadoMesa(mesaId, estado) {
    const url = window.PZ_URLS.cambiarEstadoMesa.replace('/0/', '/' + mesaId + '/');
    fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN },
      body: new URLSearchParams({ estado }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') {
          alert(data.message || 'No se pudo cambiar el estado de la mesa');
          return;
        }
        const modalEl = document.getElementById('pzModalMesaAcciones');
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      })
      .catch(() => alert('Error inesperado al cambiar el estado de la mesa'));
  }

  function filaItem(cantidad, nombre, subtotal) {
    return `<div class="pz-item-row">
      <span class="pz-item-left">
        <span class="pz-item-qty">${cantidad}</span>
        <span class="pz-item-nombre">${nombre}</span>
      </span>
      <span class="pz-item-precio">$${subtotal.toFixed(2)}</span>
    </div>`;
  }

  function formatearItems(pedido) {
    let filas = '';
    (pedido.pizzas || []).forEach(p => {
      const sabor = p.sabor_2 ? `1/2 ${p.sabor_1} / 1/2 ${p.sabor_2}` : p.sabor_1;
      filas += filaItem(p.cantidad, `Pizza ${p.tamano} - ${sabor}`, p.precio_unitario * p.cantidad);
    });
    (pedido.combos || []).forEach(c => {
      let nombre = c.combo + (c.tamano ? ` (${c.tamano})` : '');
      if (c.sabor_1) {
        nombre += ' - ' + (c.sabor_2 ? `1/2 ${c.sabor_1} / 1/2 ${c.sabor_2}` : c.sabor_1);
      }
      if (c.sabores_porcion && c.sabores_porcion.length) {
        nombre += ' | Porciones: ' + c.sabores_porcion.join(', ');
      }
      if (c.sabores_bebida && c.sabores_bebida.length) {
        nombre += ' | Bebida: ' + c.sabores_bebida.join(', ');
      }
      if (c.sabores_michelada && c.sabores_michelada.length) {
        nombre += ' | Michelada: ' + c.sabores_michelada.join(', ');
      }
      filas += filaItem(c.cantidad, nombre, c.precio_unitario * c.cantidad);
    });
    (pedido.productos_simples || []).forEach(ps => {
      const nombre = ps.sabor_bebida ? `${ps.producto} - ${ps.sabor_bebida}` : ps.producto;
      filas += filaItem(ps.cantidad, nombre, ps.precio_unitario * ps.cantidad);
    });
    return filas || '<p class="text-muted">Sin productos</p>';
  }

  function pzVerPedido(pedidoId, mesaId, irACobro) {
    const modalEl = document.getElementById('pzModalPedido');
    const modal = new bootstrap.Modal(modalEl);
    document.getElementById('pzModalBody').innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i></div>';
    document.getElementById('pzModalFooter').innerHTML = '';
    modal.show();

    fetch(window.PZ_URLS.obtenerPedido.replace('/0/', '/' + pedidoId + '/'))
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') {
          document.getElementById('pzModalBody').innerHTML = '<p class="text-danger">No se pudo cargar el pedido.</p>';
          return;
        }
        const pedido = data.pedido;
        let tituloTipo = 'Para llevar';
        if (pedido.tipo === 'mesa') tituloTipo = `Mesa ${pedido.mesa_numero}`;
        else if (pedido.tipo === 'delivery') tituloTipo = 'Delivery';
        document.getElementById('pzModalTitulo').textContent = `${tituloTipo} - Pedido #${pedido.numero_pedido_completo}`;

        const contactoHtml = pedido.contacto
          ? `<div class="pz-item-row"><span>${pedido.tipo === 'delivery' ? 'Tel/Nombre' : 'Nombre'}</span><span>${pedido.contacto}</span></div>`
          : '';
        const valorMotoHtml = pedido.valor_moto
          ? `<div class="pz-item-row"><span>Valor moto</span><span>$${pedido.valor_moto.toFixed(2)}</span></div>`
          : '';

        document.getElementById('pzModalBody').innerHTML = `
          ${contactoHtml}${valorMotoHtml}
          <div class="pz-items-list">${formatearItems(pedido)}</div>
          <div class="pz-total-row"><strong>Total</strong><strong>$${pedido.total.toFixed(2)}</strong></div>
        `;

        if (irACobro) {
          pzCobrar(pedido.id);
          return;
        }

        const agregarUrl = pedido.tipo === 'mesa'
          ? `${window.PZ_URLS.tomarPedidoMesa.replace('/0/', '/' + pedido.mesa_id + '/')}?pedido_id=${pedido.id}`
          : `/pizzeria/pedido/llevar/?pedido_id=${pedido.id}`;

        document.getElementById('pzModalFooter').innerHTML = `
          <a href="${agregarUrl}" class="btn btn-pz-outline"><i class="fas fa-plus me-2"></i>Agregar productos</a>
          <button type="button" class="btn btn-pz-primary" onclick="pzCobrar(${pedido.id})"><i class="fas fa-cash-register me-2"></i>Cobrar</button>
        `;
      });
  }

  function pzCobrar(pedidoId) {
    window.location.href = window.PZ_URLS.cobrarOrden.replace('/0/', '/' + pedidoId + '/');
  }

  const PZM_ESTADO_LABEL = { libre: 'Libre', reservada: 'Reservada', ocupada: 'Ocupada', por_cobrar: 'Por cobrar' };

  function actualizarTarjetaMesa(mesaEl, estado) {
    mesaEl.classList.remove('pzm-table-libre', 'pzm-table-reservada', 'pzm-table-ocupada', 'pzm-table-por_cobrar');
    mesaEl.classList.add(`pzm-table-${estado}`);
    mesaEl.dataset.estado = estado;

    const statusEl = mesaEl.querySelector('.pzm-table-status');
    if (statusEl) statusEl.textContent = PZM_ESTADO_LABEL[estado] || estado;

    const amountEl = mesaEl.querySelector('.pzm-table-amount');
    const subEl = mesaEl.querySelector('.pzm-table-sub');
    const cap = mesaEl.dataset.capacidad;

    if (estado === 'libre' || estado === 'reservada') {
      if (amountEl) amountEl.textContent = estado === 'libre' ? 'Disponible' : 'Reservada';
      if (subEl && cap) subEl.textContent = `${cap} persona${cap === '1' ? '' : 's'}`;
    } else {
      if (amountEl && ['Disponible', 'Reservada'].includes(amountEl.textContent.trim())) amountEl.textContent = 'En cuenta';
      if (subEl && cap) subEl.textContent = `${cap}p`;
    }
  }

  function conectarWebSocketMesas() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/pizzeria/mesas/`);

    ws.onmessage = function (event) {
      const data = JSON.parse(event.data);
      if (data.type === 'mesa_actualizada') {
        const mesaEl = document.querySelector(`.pzm-table[data-mesa-id="${data.payload.mesa_id}"]`);
        if (!mesaEl) return;
        if (data.payload.pedido_id) {
          mesaEl.dataset.pedidoId = data.payload.pedido_id;
        } else {
          delete mesaEl.dataset.pedidoId;
        }
        actualizarTarjetaMesa(mesaEl, data.payload.estado);
      } else if (data.type === 'pedido_pizzeria_actualizado') {
        const mesaId = data.payload.mesa_id;
        if (!mesaId) return;
        const mesaEl = document.querySelector(`.pzm-table[data-mesa-id="${mesaId}"]`);
        if (!mesaEl) return;
        const amountEl = mesaEl.querySelector('.pzm-table-amount');
        if (amountEl) amountEl.textContent = `$${data.payload.total.toFixed(2)}`;
      }
    };

    ws.onclose = function () {
      setTimeout(conectarWebSocketMesas, 3000);
    };
  }

  // ===== ÓRDENES EN CURSO: estado de preparación por ítem =====
  const ESTADO_ICONOS = {
    en_proceso: 'fa-hourglass-half',
    cocinando: 'fa-fire-burner',
    listo: 'fa-check',
    completo: 'fa-check-double',
  };

  function pzAvanzarEstadoItem(boton) {
    const itemEl = boton.closest('.oc-item');
    const itemId = itemEl.dataset.itemId;
    if (!itemId) return;

    boton.disabled = true;
    fetch(window.PZ_URLS.avanzarItemPreparacion + itemId + '/avanzar/', {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN },
    })
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') { alert('Error: ' + data.message); return; }
        Object.keys(ESTADO_ICONOS).forEach(estado => boton.classList.remove(`oc-pill-${estado}`));
        boton.classList.add(`oc-pill-${data.estado}`);
        const icono = ESTADO_ICONOS[data.estado] || 'fa-hourglass-half';
        boton.innerHTML = `<i class="fas ${icono}"></i> ${data.estado_display}`;
      })
      .catch(() => alert('Error inesperado al actualizar el estado'))
      .finally(() => { boton.disabled = false; });
  }

  function pzToggleVerMas(boton) {
    const card = boton.closest('.oc-card');
    const items = card.querySelector('.oc-items');
    const expandido = items.classList.toggle('oc-items-expandida');
    boton.querySelector('span').textContent = expandido ? 'Ver menos' : 'Ver más';
    boton.querySelector('i').classList.toggle('fa-chevron-down', !expandido);
    boton.querySelector('i').classList.toggle('fa-chevron-up', expandido);
  }

  function inicializarModalAccionesMesa() {
    const tomarOrdenBtn = document.getElementById('pzmaTomarOrden');
    const reservaBtn = document.getElementById('pzmaReserva');
    const opcionesEstado = document.querySelectorAll('.pzma-estado-opcion');
    if (!tomarOrdenBtn || !reservaBtn || !opcionesEstado.length) return;

    tomarOrdenBtn.addEventListener('click', function () {
      if (!pzmaMesaActual) return;
      window.location.href = `${window.PZ_URLS.nuevaOrden}?mesa_id=${pzmaMesaActual.dataset.mesaId}`;
    });

    reservaBtn.addEventListener('click', function () {
      if (!pzmaMesaActual) return;
      const nuevoEstado = this.dataset.accion === 'quitar' ? 'libre' : 'reservada';
      pzCambiarEstadoMesa(pzmaMesaActual.dataset.mesaId, nuevoEstado);
    });

    opcionesEstado.forEach(function (boton) {
      boton.addEventListener('click', function () {
        if (!pzmaMesaActual) return;
        pzCambiarEstadoMesa(pzmaMesaActual.dataset.mesaId, this.dataset.estado);
      });
    });
  }

  window.pzMesaClick = pzMesaClick;
  window.pzVerPedido = pzVerPedido;
  window.pzCobrar = pzCobrar;
  window.pzAvanzarEstadoItem = pzAvanzarEstadoItem;
  window.pzToggleVerMas = pzToggleVerMas;

  document.addEventListener('DOMContentLoaded', function () {
    conectarWebSocketMesas();
    inicializarModalAccionesMesa();
  });
})();
