// Cerrar una orden pagada por adelantado (botones con data-cerrar-orden="<url>").
// Lo usan la lista de Órdenes y el detalle de la orden. Delegado en document
// porque la lista se reemplaza entera en cada refresco en vivo.
(function () {
  'use strict';

  function csrfToken() {
    if (window.CSRF_TOKEN) return window.CSRF_TOKEN;
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  document.addEventListener('click', function (ev) {
    const boton = ev.target.closest('[data-cerrar-orden]');
    if (!boton || boton.disabled) return;
    ev.preventDefault();
    ev.stopPropagation();

    // Cerrar saca la orden de la lista y libera la mesa: no se deshace.
    if (!window.confirm('¿Cerrar la orden? Ya está pagada y servida; saldrá de la lista de órdenes.')) return;

    boton.disabled = true;
    fetch(boton.dataset.cerrarOrden, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken() },
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.status !== 'ok') {
          alert(data.message || 'No se pudo cerrar la orden');
          boton.disabled = false;
          return;
        }
        const card = boton.closest('.or-card');
        if (card) {
          // La tarjeta sale ya; la lista pide los grupos de nuevo para que
          // cuadren los conteos de cada grupo.
          card.remove();
          document.dispatchEvent(new CustomEvent('pz:orden-cerrada'));
        } else if (window.PZ_URLS && window.PZ_URLS.ordenes) {
          window.location.href = window.PZ_URLS.ordenes;
        } else {
          window.location.reload();
        }
      })
      .catch(function () {
        alert('Error inesperado al cerrar la orden');
        boton.disabled = false;
      });
  });
})();
