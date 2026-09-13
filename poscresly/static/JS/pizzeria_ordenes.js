// Órdenes (handoff_ordenes): tarjetas desplegables, buscador y refresco en vivo.
// Qué órdenes están desplegadas se recuerda entre visitas; la posición del
// scroll la recuerda recordar_posicion.js y la pestaña, la sesión (vista).
(function () {
  'use strict';

  const REFRESCO_MS = 12000;
  const CLAVE_DESPLEGADAS = 'pz_ordenes_desplegadas';
  const lista = document.getElementById('orLista');
  const busqueda = document.getElementById('orBusqueda');
  const busquedaInput = document.getElementById('orBusquedaInput');
  if (!lista) return;

  // ===== Órdenes desplegadas (varias a la vez, recordadas) =====
  function leerDesplegadas() {
    try {
      return new Set(JSON.parse(localStorage.getItem(CLAVE_DESPLEGADAS)) || []);
    } catch (e) {
      return new Set();
    }
  }

  function guardarDesplegadas(ids) {
    // Las órdenes cobradas se quedan en la lista guardada; se conservan solo
    // las últimas para que no crezca sin fin.
    const recientes = Array.from(ids).slice(-100);
    try {
      localStorage.setItem(CLAVE_DESPLEGADAS, JSON.stringify(recientes));
    } catch (e) { /* sin almacenamiento: no se recuerda */ }
  }

  function marcar(card, abierta) {
    card.classList.toggle('or-card-abierta', abierta);
    card.querySelector('.or-card-cabecera').setAttribute('aria-expanded', String(abierta));
    card.querySelector('.or-card-detalle').hidden = !abierta;
  }

  function aplicarDesplegadas() {
    const ids = leerDesplegadas();
    lista.querySelectorAll('.or-card').forEach(function (card) {
      marcar(card, ids.has(card.dataset.pedidoId));
    });
  }

  lista.addEventListener('click', function (ev) {
    const cabecera = ev.target.closest('.or-card-cabecera');
    if (!cabecera) return;
    // La cabecera solo despliega y pliega; se entra a la orden tocando el
    // cuerpo con los productos (un enlace normal).
    const card = cabecera.closest('.or-card');
    const abierta = !card.classList.contains('or-card-abierta');
    marcar(card, abierta);

    const ids = leerDesplegadas();
    if (abierta) ids.add(card.dataset.pedidoId); else ids.delete(card.dataset.pedidoId);
    guardarDesplegadas(ids);
  });

  aplicarDesplegadas();

  // Cambiar de pestaña es ir a otra lista: empieza arriba, no donde quedó la anterior.
  document.querySelectorAll('.or-tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      if (window.pzOlvidarPosicion) window.pzOlvidarPosicion();
    });
  });

  // ===== Buscador: detrás del ⌕ para no gastar alto de pantalla =====
  function alternarBusqueda() {
    if (!busqueda) return;
    busqueda.hidden = !busqueda.hidden;
    if (!busqueda.hidden) busquedaInput.focus();
  }
  ['orBuscarToggle', 'orBuscarToggleDesktop'].forEach(function (id) {
    const boton = document.getElementById(id);
    if (boton) boton.addEventListener('click', alternarBusqueda);
  });

  if (busquedaInput) {
    if (busquedaInput.value) {
      const largo = busquedaInput.value.length;
      busquedaInput.focus({ preventScroll: true });
      busquedaInput.setSelectionRange(largo, largo);
    }
    let espera = null;
    busquedaInput.addEventListener('input', function () {
      clearTimeout(espera);
      espera = setTimeout(function () { busqueda.requestSubmit(); }, 450);
    });
  }

  // ===== Refresco en vivo =====
  // La cocina marca platillos mientras el mesero mira la lista. Se reemplazan
  // los grupos y se vuelven a desplegar las mismas órdenes, así que lo que el
  // usuario está leyendo sigue abierto. No se refresca mientras escribe.
  function refrescar() {
    if (document.hidden) return;
    if (busquedaInput && document.activeElement === busquedaInput) return;

    const url = new URL(window.location.href);
    url.searchParams.set('parcial', '1');
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (html) {
        if (html === null) return;
        lista.innerHTML = html;
        aplicarDesplegadas();
      })
      .catch(function () { /* sin red: se reintenta en el próximo ciclo */ });
  }

  setInterval(refrescar, REFRESCO_MS);
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) refrescar();
  });
})();
