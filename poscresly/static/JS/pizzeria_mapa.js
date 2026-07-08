(function () {
  function pzMesaClick(el) {
    const estado = el.dataset.estado;
    const mesaId = el.dataset.mesaId;

    if (estado === 'libre') {
      window.location.href = window.PZ_URLS.tomarPedidoMesa + mesaId + '/';
      return;
    }

    const pedidoId = el.dataset.pedidoId;
    if (pedidoId) {
      pzVerPedido(pedidoId, mesaId);
    }
  }

  function formatearItems(pedido) {
    let filas = '';
    (pedido.pizzas || []).forEach(p => {
      const sabor = p.sabor_2 ? `1/2 ${p.sabor_1} / 1/2 ${p.sabor_2}` : p.sabor_1;
      filas += `<div class="pz-item-row"><span>${p.cantidad}x Pizza ${p.tamano} - ${sabor}</span><span>$${(p.precio_unitario * p.cantidad).toFixed(2)}</span></div>`;
    });
    (pedido.combos || []).forEach(c => {
      const sabor = c.sabor_2 ? `1/2 ${c.sabor_1} / 1/2 ${c.sabor_2}` : c.sabor_1;
      filas += `<div class="pz-item-row"><span>${c.cantidad}x ${c.combo} (${c.tamano}) - ${sabor}</span><span>$${(c.precio_unitario * c.cantidad).toFixed(2)}</span></div>`;
    });
    (pedido.productos_simples || []).forEach(ps => {
      filas += `<div class="pz-item-row"><span>${ps.cantidad}x ${ps.producto}</span><span>$${(ps.precio_unitario * ps.cantidad).toFixed(2)}</span></div>`;
    });
    return filas || '<p class="text-muted">Sin productos</p>';
  }

  function pzVerPedido(pedidoId) {
    const modalEl = document.getElementById('pzModalPedido');
    const modal = new bootstrap.Modal(modalEl);
    document.getElementById('pzModalBody').innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin"></i></div>';
    document.getElementById('pzModalFooter').innerHTML = '';
    modal.show();

    fetch(window.PZ_URLS.obtenerPedido + pedidoId + '/')
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') {
          document.getElementById('pzModalBody').innerHTML = '<p class="text-danger">No se pudo cargar el pedido.</p>';
          return;
        }
        const pedido = data.pedido;
        document.getElementById('pzModalTitulo').textContent =
          pedido.tipo === 'mesa' ? `Mesa ${pedido.mesa_numero} - Pedido #${pedido.numero_pedido_completo}` : `Para llevar - Pedido #${pedido.numero_pedido_completo}`;

        document.getElementById('pzModalBody').innerHTML = `
          <div class="pz-items-list">${formatearItems(pedido)}</div>
          <div class="pz-total-row"><strong>Total</strong><strong>$${pedido.total.toFixed(2)}</strong></div>
        `;

        const agregarUrl = pedido.tipo === 'mesa'
          ? `${window.PZ_URLS.tomarPedidoMesa}${pedido.mesa_id}/?pedido_id=${pedido.id}`
          : `/pizzeria/pedido/llevar/?pedido_id=${pedido.id}`;

        document.getElementById('pzModalFooter').innerHTML = `
          <a href="${agregarUrl}" class="btn btn-pz-outline"><i class="fas fa-plus me-2"></i>Agregar productos</a>
          <button type="button" class="btn btn-pz-primary" onclick="pzCobrar(${pedido.id})"><i class="fas fa-cash-register me-2"></i>Cobrar</button>
        `;
      });
  }

  function pzCobrar(pedidoId) {
    document.getElementById('pzModalFooter').innerHTML = `
      <span class="me-auto">Forma de pago:</span>
      <button type="button" class="btn btn-outline-success" onclick="pzConfirmarCobro(${pedidoId}, 'Efectivo')"><i class="fas fa-money-bill me-1"></i>Efectivo</button>
      <button type="button" class="btn btn-outline-primary" onclick="pzConfirmarCobro(${pedidoId}, 'Transferencia')"><i class="fas fa-mobile-alt me-1"></i>Transferencia</button>
    `;
  }

  function pzConfirmarCobro(pedidoId, formaPago) {
    const body = new FormData();
    body.append('pedido_id', pedidoId);
    body.append('forma_pago', formaPago);

    fetch(window.PZ_URLS.cerrarCobrar, {
      method: 'POST',
      body,
      headers: { 'X-CSRFToken': window.CSRF_TOKEN },
    })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          window.location.reload();
        } else {
          alert('Error: ' + data.message);
        }
      })
      .catch(() => alert('Error inesperado al cobrar el pedido'));
  }

  function conectarWebSocketMesas() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/pizzeria/mesas/`);

    ws.onmessage = function (event) {
      const data = JSON.parse(event.data);
      if (data.type === 'mesa_actualizada') {
        const mesaEl = document.querySelector(`.pz-mesa[data-mesa-id="${data.payload.mesa_id}"]`);
        if (!mesaEl) return;
        mesaEl.classList.remove('pz-estado-libre', 'pz-estado-ocupada', 'pz-estado-por_cobrar');
        mesaEl.classList.add(`pz-estado-${data.payload.estado}`);
        mesaEl.dataset.estado = data.payload.estado;
        if (data.payload.pedido_id) {
          mesaEl.dataset.pedidoId = data.payload.pedido_id;
        } else {
          delete mesaEl.dataset.pedidoId;
          const totalEl = mesaEl.querySelector('.pz-mesa-total');
          if (totalEl) totalEl.remove();
        }
      } else if (data.type === 'pedido_pizzeria_actualizado') {
        const mesaId = data.payload.mesa_id;
        if (!mesaId) return;
        const mesaEl = document.querySelector(`.pz-mesa[data-mesa-id="${mesaId}"]`);
        if (!mesaEl) return;
        let totalEl = mesaEl.querySelector('.pz-mesa-total');
        if (!totalEl) {
          totalEl = document.createElement('span');
          totalEl.className = 'pz-mesa-total';
          mesaEl.appendChild(totalEl);
        }
        totalEl.textContent = `$${data.payload.total.toFixed(2)}`;
      }
    };

    ws.onclose = function () {
      setTimeout(conectarWebSocketMesas, 3000);
    };
  }

  window.pzMesaClick = pzMesaClick;
  window.pzVerPedido = pzVerPedido;
  window.pzCobrar = pzCobrar;
  window.pzConfirmarCobro = pzConfirmarCobro;

  document.addEventListener('DOMContentLoaded', conectarWebSocketMesas);
})();
