// Cada pantalla recuerda dónde se dejó: al volver a ella (flecha atrás, barra
// inferior, menú lateral) aparece en la misma posición de scroll. Se guarda por
// ruta, sin la querystring, para que entrar a Órdenes desde la barra inferior
// devuelva la misma lista que se dejó (la pestaña ya la recuerda la sesión).
//
// En las páginas con sidebar el que scrollea es .col-der (overflow-y:auto),
// no la ventana; se guardan los dos porque según el ancho puede ser uno u otro.
(function () {
  'use strict';

  const PREFIJO = 'pz_posicion:';
  const clave = PREFIJO + window.location.pathname;

  function leer() {
    try {
      return JSON.parse(localStorage.getItem(clave)) || null;
    } catch (e) {
      return null;
    }
  }

  function contenedor() {
    return document.querySelector('.col-der');
  }

  function guardar() {
    const col = contenedor();
    try {
      localStorage.setItem(clave, JSON.stringify({
        ventana: window.scrollY,
        columna: col ? col.scrollTop : 0,
      }));
    } catch (e) { /* sin almacenamiento (modo privado): no se recuerda */ }
  }

  function restaurar() {
    const posicion = leer();
    if (!posicion) return;
    const col = contenedor();
    if (col && posicion.columna) col.scrollTop = posicion.columna;
    if (posicion.ventana) window.scrollTo(0, posicion.ventana);
  }

  // Que el navegador no pelee con la restauración propia.
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';

  // Las pantallas que cambian su contenido antes (p. ej. Órdenes, que vuelve a
  // desplegar las tarjetas) cargan su JS antes que este, así que al llegar aquí
  // el alto ya es el definitivo. Se repite en load por fuentes e imágenes.
  restaurar();
  window.addEventListener('load', restaurar);

  let pendiente = false;
  document.addEventListener('scroll', function () {
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(function () {
      pendiente = false;
      guardar();
    });
  }, { capture: true, passive: true });
  window.addEventListener('pagehide', guardar);

  // Para pantallas que quieren empezar arriba en un caso concreto
  // (p. ej. al cambiar de pestaña en Órdenes).
  window.pzOlvidarPosicion = function () {
    try { localStorage.removeItem(clave); } catch (e) { /* nada que borrar */ }
  };
})();
