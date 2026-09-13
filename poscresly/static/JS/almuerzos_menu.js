// Menú del día (1A/1B) · handoff_menu_del_dia. La pantalla cambia sola
// mientras se venden almuerzos: cada 20 s pide el parcial de secciones y la
// sub-línea del subheader. Sin websocket, a propósito (README §8).
(function () {
  var main = document.getElementById('almMenu');
  var secciones = document.getElementById('almSecciones');
  var sub = document.getElementById('almMenuSub');
  if (!main || !secciones) return;

  var url = main.dataset.parcialUrl;
  var publicadoInicial = !document.getElementById('almBarraConfigurar');
  var INTERVALO = 20000;
  var timer = null;

  function refrescar() {
    if (document.hidden) return;
    fetch(url, { headers: { 'X-Requested-With': 'fetch' }, cache: 'no-store' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data) return;
        // Otro dispositivo publicó (o vació) el menú: cambia la estructura
        // de la pantalla (barra de acción), así que se recarga entera.
        if (data.publicado !== publicadoInicial) {
          window.location.reload();
          return;
        }
        secciones.innerHTML = data.secciones;
        if (sub) sub.innerHTML = data.sub;
      })
      .catch(function () { /* sin red: se reintenta en el siguiente ciclo */ });
  }

  function iniciar() {
    if (timer) clearInterval(timer);
    timer = setInterval(refrescar, INTERVALO);
  }

  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) { refrescar(); iniciar(); }
  });
  iniciar();
})();
