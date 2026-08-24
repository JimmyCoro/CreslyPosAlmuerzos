(function () {
  const DRAG_THRESHOLD_PX = 6;
  let modal = null;
  let mesaEnEdicion = null; // elemento .pzg-mesa siendo editado, o null si es alta

  function csrfHeaders() {
    return { 'X-CSRFToken': window.CSRF_TOKEN };
  }

  function mostrarError(mensaje) {
    const el = document.getElementById('pzgFormError');
    el.textContent = mensaje;
    el.classList.remove('d-none');
  }

  function ocultarError() {
    document.getElementById('pzgFormError').classList.add('d-none');
  }

  function pzgAbrirCrear() {
    mesaEnEdicion = null;
    document.getElementById('pzgModalTitulo').textContent = 'Nueva mesa';
    document.getElementById('pzgFormMesa').reset();
    document.getElementById('pzgNumero').disabled = false;
    document.getElementById('pzgActivaWrap').classList.add('d-none');
    ocultarError();
    if (!modal) modal = new bootstrap.Modal(document.getElementById('pzgModalMesa'));
    modal.show();
  }

  function pzgAbrirEditar(mesaEl) {
    mesaEnEdicion = mesaEl;
    document.getElementById('pzgModalTitulo').textContent = `Mesa ${mesaEl.dataset.numero}`;
    document.getElementById('pzgNumero').value = mesaEl.dataset.numero;
    document.getElementById('pzgNombre').value = mesaEl.dataset.nombre || '';
    document.getElementById('pzgZona').value = mesaEl.dataset.zona || '';
    document.getElementById('pzgForma').value = mesaEl.dataset.forma;
    document.getElementById('pzgCapacidad').value = mesaEl.dataset.capacidad;
    document.getElementById('pzgActiva').checked = mesaEl.dataset.activa === 'true';
    document.getElementById('pzgActivaWrap').classList.remove('d-none');
    ocultarError();
    if (!modal) modal = new bootstrap.Modal(document.getElementById('pzgModalMesa'));
    modal.show();
  }

  function actualizarBotonMesa(mesaEl, mesa) {
    mesaEl.dataset.numero = mesa.numero;
    mesaEl.dataset.nombre = mesa.nombre || '';
    mesaEl.dataset.zona = mesa.zona || '';
    mesaEl.dataset.forma = mesa.forma;
    mesaEl.dataset.capacidad = mesa.capacidad;
    mesaEl.dataset.activa = mesa.activa ? 'true' : 'false';
    mesaEl.classList.remove('pzg-mesa-cuadrada', 'pzg-mesa-redonda');
    mesaEl.classList.add(`pzg-mesa-${mesa.forma}`);
    mesaEl.classList.toggle('pzg-mesa-inactiva', !mesa.activa);
    mesaEl.querySelector('.pzg-mesa-numero').textContent = mesa.nombre || mesa.numero;
    mesaEl.querySelector('.pzg-mesa-cap').innerHTML = `<i class="fas fa-user"></i>${mesa.capacidad}`;
  }

  function agregarMesaAlDom(mesa) {
    const floor = document.getElementById('pzFloor');
    const vacio = floor.querySelector('.pzg-floor-empty');
    if (vacio) vacio.remove();

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `pzg-mesa pzg-mesa-${mesa.forma} pzg-estado-${mesa.estado}`;
    btn.style.left = `${mesa.pos_x}%`;
    btn.style.top = `${mesa.pos_y}%`;
    btn.dataset.mesaId = mesa.id;
    btn.dataset.numero = mesa.numero;
    btn.dataset.nombre = mesa.nombre || '';
    btn.dataset.zona = mesa.zona || '';
    btn.dataset.forma = mesa.forma;
    btn.dataset.capacidad = mesa.capacidad;
    btn.dataset.activa = mesa.activa ? 'true' : 'false';
    btn.dataset.posX = mesa.pos_x;
    btn.dataset.posY = mesa.pos_y;
    btn.innerHTML = `<span class="pzg-mesa-numero">${mesa.nombre || mesa.numero}</span><span class="pzg-mesa-cap"><i class="fas fa-user"></i>${mesa.capacidad}</span>`;
    floor.appendChild(btn);
    activarDrag(btn);
  }

  function pzgGuardarMesa(ev) {
    ev.preventDefault();
    ocultarError();

    const body = new URLSearchParams({
      numero: document.getElementById('pzgNumero').value,
      nombre: document.getElementById('pzgNombre').value,
      zona: document.getElementById('pzgZona').value,
      forma: document.getElementById('pzgForma').value,
      capacidad: document.getElementById('pzgCapacidad').value,
    });

    let url = window.PZG_URLS.crearMesa;
    if (mesaEnEdicion) {
      url = window.PZG_URLS.actualizarMesa.replace('/0/', `/${mesaEnEdicion.dataset.mesaId}/`);
      body.set('activa', document.getElementById('pzgActiva').checked ? 'true' : 'false');
    }

    fetch(url, { method: 'POST', headers: csrfHeaders(), body })
      .then(r => r.json())
      .then(data => {
        if (data.status !== 'ok') {
          mostrarError(data.message || 'No se pudo guardar la mesa');
          return;
        }
        if (mesaEnEdicion) {
          actualizarBotonMesa(mesaEnEdicion, data.mesa);
        } else {
          agregarMesaAlDom(data.mesa);
        }
        modal.hide();
      })
      .catch(() => mostrarError('Error inesperado al guardar la mesa'));
  }

  function moverMesaEnServidor(mesaEl, posX, posY) {
    const url = window.PZG_URLS.moverMesa.replace('/0/', `/${mesaEl.dataset.mesaId}/`);
    const body = new URLSearchParams({ pos_x: posX, pos_y: posY });
    fetch(url, { method: 'POST', headers: csrfHeaders(), body })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          mesaEl.dataset.posX = data.mesa.pos_x;
          mesaEl.dataset.posY = data.mesa.pos_y;
        }
      });
  }

  function activarDrag(mesaEl) {
    mesaEl.addEventListener('pointerdown', function (ev) {
      ev.preventDefault();
      const floor = document.getElementById('pzFloor');
      const floorRect = floor.getBoundingClientRect();
      const startX = ev.clientX;
      const startY = ev.clientY;
      let moved = false;
      mesaEl.setPointerCapture(ev.pointerId);

      function onMove(moveEv) {
        const dx = moveEv.clientX - startX;
        const dy = moveEv.clientY - startY;
        if (!moved && Math.hypot(dx, dy) > DRAG_THRESHOLD_PX) {
          moved = true;
          mesaEl.classList.add('pzg-dragging');
        }
        if (!moved) return;

        let posX = ((moveEv.clientX - floorRect.left) / floorRect.width) * 100;
        let posY = ((moveEv.clientY - floorRect.top) / floorRect.height) * 100;
        posX = Math.max(0, Math.min(100, posX));
        posY = Math.max(0, Math.min(100, posY));
        mesaEl.style.left = `${posX}%`;
        mesaEl.style.top = `${posY}%`;
      }

      function onUp() {
        mesaEl.removeEventListener('pointermove', onMove);
        mesaEl.removeEventListener('pointerup', onUp);
        mesaEl.classList.remove('pzg-dragging');

        if (moved) {
          const posX = parseFloat(mesaEl.style.left);
          const posY = parseFloat(mesaEl.style.top);
          moverMesaEnServidor(mesaEl, posX, posY);
        } else {
          pzgAbrirEditar(mesaEl);
        }
      }

      mesaEl.addEventListener('pointermove', onMove);
      mesaEl.addEventListener('pointerup', onUp, { once: true });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('#pzFloor .pzg-mesa').forEach(activarDrag);
    document.getElementById('pzgFormMesa').addEventListener('submit', pzgGuardarMesa);
  });

  window.pzgAbrirCrear = pzgAbrirCrear;
})();
