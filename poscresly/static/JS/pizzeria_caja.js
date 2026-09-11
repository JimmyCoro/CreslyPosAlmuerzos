(function () {
  'use strict';

  // Montos siempre en centavos enteros para no arrastrar errores de coma flotante.
  function aCentavos(texto) {
    const limpio = String(texto || '').trim().replace(',', '.');
    if (!/^\d+(\.\d{0,2})?$/.test(limpio)) return null;
    return Math.round(parseFloat(limpio) * 100);
  }
  function dinero(centavos) {
    return '$' + (centavos / 100).toFixed(2);
  }
  // Solo dígitos y un punto con hasta 2 decimales mientras se escribe.
  function sanearMonto(input) {
    let v = input.value.replace(',', '.').replace(/[^\d.]/g, '');
    const partes = v.split('.');
    if (partes.length > 2) v = partes[0] + '.' + partes.slice(1).join('');
    const [entero, dec] = v.split('.');
    input.value = dec !== undefined ? entero + '.' + dec.slice(0, 2) : entero;
  }
  function faltan(lista) {
    return lista.length ? 'Falta ' + lista.join(' y ') : '';
  }

  // ===== Aviso breve (sobrevive a la recarga vía sessionStorage) =====
  function mostrarAviso(texto) {
    const aviso = document.getElementById('cjAviso');
    if (!aviso || !texto) return;
    aviso.textContent = texto;
    aviso.classList.add('cj-aviso-visible');
    setTimeout(() => aviso.classList.remove('cj-aviso-visible'), 2600);
  }
  try {
    const pendiente = sessionStorage.getItem('cjAviso');
    if (pendiente) {
      sessionStorage.removeItem('cjAviso');
      mostrarAviso(pendiente);
    }
  } catch (e) { /* almacenamiento bloqueado: el aviso es solo cortesía */ }

  function enviar(url, datos) {
    return fetch(url, {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN, 'Content-Type': 'application/json' },
      body: JSON.stringify(datos),
    }).then((r) => r.json().catch(() => { throw new Error(`Respuesta inválida del servidor (HTTP ${r.status})`); }));
  }
  function exitoYRecargar(mensaje) {
    try { sessionStorage.setItem('cjAviso', mensaje); } catch (e) { /* sin aviso */ }
    window.location.reload();
  }

  // ===== Abrir caja =====
  const formAbrir = document.getElementById('cjFormAbrir');
  if (formAbrir) {
    const input = document.getElementById('cjFondo');
    const boton = document.getElementById('cjBtnAbrir');
    const linea = document.getElementById('cjAbrirFalta');
    const atajos = formAbrir.querySelectorAll('.cj-atajo');

    function actualizarAbrir() {
      const centavos = aCentavos(input.value);
      boton.disabled = centavos === null;
      boton.textContent = centavos === null ? 'Abrir caja' : `Abrir caja con ${dinero(centavos)}`;
      linea.hidden = false;
      linea.textContent = centavos === null ? faltan(['el fondo inicial']) : '';
      atajos.forEach((a) => a.classList.toggle('cj-atajo-activo', aCentavos(a.dataset.monto) === centavos));
    }
    input.addEventListener('input', () => { sanearMonto(input); actualizarAbrir(); });
    atajos.forEach((a) => a.addEventListener('click', () => {
      input.value = a.dataset.monto;
      actualizarAbrir();
    }));
    formAbrir.addEventListener('submit', (ev) => {
      if (aCentavos(input.value) === null) { ev.preventDefault(); actualizarAbrir(); return; }
      setTimeout(() => { boton.disabled = true; }, 0);
    });
    actualizarAbrir();
  }

  // ===== Hojas inferiores: cerrar deslizando hacia abajo =====
  document.querySelectorAll('.cj-hoja').forEach((hoja) => {
    const cuerpo = hoja.querySelector('.offcanvas-body');
    let inicioY = null;
    let dy = 0;
    hoja.addEventListener('touchstart', (ev) => {
      inicioY = cuerpo.scrollTop <= 0 ? ev.touches[0].clientY : null;
      dy = 0;
    }, { passive: true });
    hoja.addEventListener('touchmove', (ev) => {
      if (inicioY === null) return;
      dy = Math.max(0, ev.touches[0].clientY - inicioY);
      if (dy > 8) {
        hoja.style.transition = 'none';
        hoja.style.transform = `translateY(${dy}px)`;
      }
    }, { passive: true });
    hoja.addEventListener('touchend', () => {
      if (inicioY === null) return;
      inicioY = null;
      hoja.style.transition = 'transform .2s ease';
      if (dy > 90) {
        hoja.style.transform = 'translateY(100%)';
        setTimeout(() => bootstrap.Offcanvas.getOrCreateInstance(hoja).hide(), 180);
      } else {
        hoja.style.transform = '';
      }
    });
    hoja.addEventListener('hidden.bs.offcanvas', () => {
      hoja.style.transition = '';
      hoja.style.transform = '';
    });
  });

  // ===== Conteo por denominación (reutilizable) =====
  function iniciarConteo(raiz, alCambiar) {
    const cantidades = {};
    raiz.querySelectorAll('.cj-conteo-fila').forEach((fila) => {
      const clave = fila.dataset.clave;
      const valorCentavos = aCentavos(fila.dataset.valor);
      const menos = fila.querySelector('[data-cj-menos]');
      const cant = fila.querySelector('[data-cj-cant]');
      const sub = fila.querySelector('[data-cj-sub]');
      cantidades[clave] = 0;

      function pintar() {
        const n = cantidades[clave];
        cant.textContent = n;
        sub.textContent = dinero(n * valorCentavos);
        menos.disabled = n === 0;
        fila.classList.toggle('cj-conteo-cero', n === 0);
        alCambiar(total());
      }
      menos.addEventListener('click', () => { if (cantidades[clave] > 0) { cantidades[clave] -= 1; pintar(); } });
      fila.querySelector('[data-cj-mas]').addEventListener('click', () => { cantidades[clave] += 1; pintar(); });
      fila.dataset.valorCentavos = valorCentavos;
    });

    function total() {
      let suma = 0;
      raiz.querySelectorAll('.cj-conteo-fila').forEach((f) => {
        suma += cantidades[f.dataset.clave] * Number(f.dataset.valorCentavos);
      });
      return suma;
    }
    return { conteo: () => ({ ...cantidades }), total };
  }

  const CJ = window.CJ;

  // ===== Retirar a bóveda =====
  const conteoRetiro = document.getElementById('cjConteoRetiro');
  if (conteoRetiro && CJ) {
    const boton = document.getElementById('cjBtnRetirar');
    const linea = document.getElementById('cjRetiroFalta');
    const totalEl = document.getElementById('cjRetiroTotal');
    const quedanEl = document.getElementById('cjRetiroQuedan');
    let enviando = false;

    function actualizarRetiro(total) {
      const quedan = CJ.esperadoCentavos - total;
      totalEl.textContent = dinero(total);
      quedanEl.textContent = dinero(quedan);
      quedanEl.parentElement.classList.toggle('cj-quedan-negativo', quedan < 0);
      let mensaje = '';
      if (total === 0) mensaje = 'Cuenta lo que vas a retirar';
      else if (quedan < 0) mensaje = 'Estás retirando más de lo que hay en el cajón';
      linea.textContent = mensaje;
      boton.disabled = Boolean(mensaje) || enviando;
      boton.textContent = `Retirar ${dinero(total)}`;
    }
    const conteo = iniciarConteo(conteoRetiro, actualizarRetiro);

    boton.addEventListener('click', () => {
      if (boton.disabled) return;
      enviando = true;
      boton.disabled = true;
      enviar(CJ.urls.retiro, {
        turno_id: CJ.turnoId,
        conteo: conteo.conteo(),
        motivo: document.getElementById('cjRetiroMotivo').value,
      })
        .then((data) => {
          if (data.status !== 'ok') throw new Error(data.message);
          exitoYRecargar(data.message);
        })
        .catch((err) => {
          enviando = false;
          linea.textContent = err.message || 'No se pudo registrar el retiro';
          boton.disabled = false;
        });
    });
  }

  // ===== Ingreso o gasto =====
  const hojaMov = document.getElementById('cjHojaMovimiento');
  if (hojaMov && CJ) {
    const input = document.getElementById('cjMovMonto');
    const boton = document.getElementById('cjBtnMovimiento');
    const linea = document.getElementById('cjMovFalta');
    const segmentos = hojaMov.querySelectorAll('.cj-seg');
    const chips = hojaMov.querySelectorAll('.cj-chip');
    let tipo = 'gasto';
    let categoria = '';
    let enviando = false;

    function actualizarMov() {
      const centavos = aCentavos(input.value);
      const monto = centavos && centavos > 0 ? centavos : null;
      const lista = [];
      if (monto === null) lista.push('el monto');
      if (!categoria) lista.push('la categoría');
      let mensaje = faltan(lista);
      if (!mensaje && tipo === 'gasto' && monto > CJ.esperadoCentavos) mensaje = 'El gasto deja el cajón en negativo';
      linea.textContent = mensaje;
      boton.disabled = Boolean(mensaje) || enviando;
      boton.textContent = tipo === 'gasto' ? 'Registrar gasto' : 'Registrar ingreso';
      return monto;
    }

    segmentos.forEach((s) => s.addEventListener('click', () => {
      tipo = s.dataset.tipo;
      segmentos.forEach((o) => {
        const activo = o === s;
        o.classList.toggle('cj-seg-activo', activo);
        o.setAttribute('aria-checked', String(activo));
      });
      actualizarMov();
    }));
    chips.forEach((c) => c.addEventListener('click', () => {
      categoria = c.dataset.categoria;
      chips.forEach((o) => o.setAttribute('aria-checked', String(o === c)));
      actualizarMov();
    }));
    input.addEventListener('input', () => { sanearMonto(input); actualizarMov(); });

    boton.addEventListener('click', () => {
      const monto = actualizarMov();
      if (boton.disabled || monto === null) return;
      enviando = true;
      boton.disabled = true;
      enviar(CJ.urls.movimiento, {
        turno_id: CJ.turnoId,
        tipo,
        monto: (monto / 100).toFixed(2),
        categoria,
        detalle: document.getElementById('cjMovDetalle').value,
      })
        .then((data) => {
          if (data.status !== 'ok') throw new Error(data.message);
          exitoYRecargar(data.message);
        })
        .catch((err) => {
          enviando = false;
          linea.textContent = err.message || 'No se pudo registrar el movimiento';
          boton.disabled = false;
        });
    });
    actualizarMov();
  }
})();
