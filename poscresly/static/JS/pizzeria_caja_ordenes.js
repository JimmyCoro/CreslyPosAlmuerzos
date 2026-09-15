// Órdenes del turno (pizzeria/handoff_ordenes_turno): hoja ⋯ y corrección del
// método de pago. El acordeón es el collapse de Bootstrap (sin JS propio) y el
// cerrar deslizando las hojas ya lo da pizzeria_caja.js.
(function () {
  'use strict';

  const CJ = window.CJ;
  const hojaAcc = document.getElementById('otHojaAcciones');
  const hojaCor = document.getElementById('otHojaCorregir');
  if (!CJ || !hojaAcc || !hojaCor) return;

  const acc = bootstrap.Offcanvas.getOrCreateInstance(hojaAcc);
  const cor = bootstrap.Offcanvas.getOrCreateInstance(hojaCor);
  const radios = hojaCor.querySelectorAll('.ot-radio:not([disabled])');
  const motivo = document.getElementById('otCorMotivo');
  const boton = document.getElementById('otBtnCorregir');
  const linea = document.getElementById('otCorFalta');
  const previa = document.getElementById('otCorPrevia');
  const subtotales = window.OT_SUBTOTALES || {};

  let orden = null;
  let elegido = '';
  let enviando = false;

  function dinero(centavos) {
    return '$' + (centavos / 100).toFixed(2);
  }

  // Misma regla que campos_faltantes_correccion() en la vista.
  function faltantes() {
    const faltan = [];
    if (!motivo.value.trim()) faltan.push('Falta escribir el motivo');
    if (!elegido || elegido === orden.metodo) faltan.push('Elige un método distinto al actual');
    return faltan;
  }

  function pintarPrevia() {
    if (!elegido || elegido === orden.metodo) {
      previa.hidden = true;
      return;
    }
    const monto = Number(orden.centavos);
    const desde = (subtotales[orden.metodo] || 0) - monto;
    const hacia = (subtotales[elegido] || 0) + monto;
    previa.hidden = false;
    previa.innerHTML =
      `<span class="ot-previa-fila"><span>${orden.metodo}</span><strong>${dinero(desde)}</strong></span>` +
      `<span class="ot-previa-fila"><span>${elegido}</span><strong>${dinero(hacia)}</strong></span>` +
      '<span class="ot-previa-nota">El total del turno no cambia.</span>';
  }

  function actualizar() {
    const faltan = faltantes();
    linea.textContent = faltan[0] || '';
    boton.disabled = faltan.length > 0 || enviando;
    pintarPrevia();
  }

  // ⋯ de una fila: abre la hoja sin desplegar la fila.
  document.querySelectorAll('[data-ot-orden]').forEach((el) => el.addEventListener('click', (ev) => {
    ev.stopPropagation();
    orden = { ...el.dataset };
    document.getElementById('otAccTitulo').textContent = orden.titulo;
    document.getElementById('otAccSub').textContent = orden.sub;
    document.getElementById('otAccMetodo').textContent = `Ahora: ${orden.metodo.toLowerCase()}`;
    const historial = document.getElementById('otAccHistorial');
    historial.hidden = !orden.aviso;
    document.getElementById('otAccHistorialTexto').textContent = orden.aviso || '';
    acc.show();
  }));

  // Una hoja a la vez: la de corrección se abre cuando la de acciones terminó de cerrarse.
  document.getElementById('otAccCorregir').addEventListener('click', () => {
    hojaAcc.addEventListener('hidden.bs.offcanvas', () => {
      elegido = '';
      motivo.value = '';
      document.getElementById('otCorSub').innerHTML =
        `${orden.titulo} · <strong>${dinero(Number(orden.centavos))}</strong>. El monto no cambia.`;
      radios.forEach((r) => {
        r.setAttribute('aria-checked', 'false');
        r.classList.toggle('ot-radio-es-actual', r.dataset.metodo === orden.metodo);
      });
      actualizar();
      cor.show();
    }, { once: true });
    acc.hide();
  });

  radios.forEach((r) => r.addEventListener('click', () => {
    elegido = r.dataset.metodo;
    radios.forEach((o) => o.setAttribute('aria-checked', String(o === r)));
    actualizar();
  }));
  motivo.addEventListener('input', actualizar);

  boton.addEventListener('click', () => {
    if (boton.disabled || !orden) return;
    enviando = true;
    boton.disabled = true;
    fetch(CJ.urls.corregir.replace('/0/', `/${orden.otOrden}/`), {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify({ turno_id: CJ.turnoId, metodo: elegido, motivo: motivo.value }),
    })
      .then((r) => r.json().catch(() => { throw new Error(`Respuesta inválida del servidor (HTTP ${r.status})`); }))
      .then((data) => {
        if (data.status !== 'ok') throw new Error(data.message);
        try { sessionStorage.setItem('cjAviso', data.message); } catch (e) { /* sin aviso */ }
        window.location.reload();
      })
      .catch((err) => {
        enviando = false;
        linea.textContent = err.message || 'No se pudo corregir el método';
        boton.disabled = false;
      });
  });
})();
