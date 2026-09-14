// Al abrir la app instalada se vuelve a la última pantalla, no a `/`.
//
// El sistema cierra la app cuando pasa un rato en segundo plano, y al volver
// la arranca de nuevo en el start_url del manifest (`/`, Pedidos de almuerzos).
// Cada pantalla guarda aquí su dirección; si la app acaba de arrancar y cayó en
// `/`, se reemplaza por la última guardada. Va en el <head>, antes de los
// estilos, para que no se alcance a pintar Pedidos.
//
// Solo en la app instalada: en una pestaña normal escribir la dirección `/`
// debe abrir `/`.
(function () {
  'use strict';

  const CLAVE = 'pz_ultima_pantalla';
  const MARCA_ARRANQUE = 'pz_app_abierta';

  const instalada = (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches)
    || window.navigator.standalone === true;

  try {
    // sessionStorage vive lo que dura la app abierta: vacío = acaba de arrancar.
    const recienAbierta = !sessionStorage.getItem(MARCA_ARRANQUE);
    sessionStorage.setItem(MARCA_ARRANQUE, '1');

    if (instalada && recienAbierta && window.location.pathname === '/' && !window.location.search) {
      const ultima = localStorage.getItem(CLAVE);
      // Solo rutas propias ("/x", nunca "//otro-sitio").
      if (ultima && ultima !== '/' && ultima.charAt(0) === '/' && ultima.charAt(1) !== '/') {
        window.location.replace(ultima);
        return;
      }
    }

    localStorage.setItem(CLAVE, window.location.pathname + window.location.search);
  } catch (e) {
    // Sin almacenamiento (modo privado): la app abre en `/` como siempre.
  }
})();
