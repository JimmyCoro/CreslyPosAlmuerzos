/* Cobro simple + pago mixto (handoff_cobrar §2-3), y reutilizado por
   Cobrar a una persona (misma tarjeta de método, otro objetivo). Un solo
   puedeConfirmar() maneja el botón, la línea roja y el resaltado del
   subtítulo — no hay tres comprobaciones repetidas. */
(function () {
  const METODOS = [
    { valor: 'Efectivo', icono: 'bi-cash' },
    { valor: 'Transferencia', icono: 'bi-arrow-left-right' },
    { valor: 'Tarjeta', icono: 'bi-credit-card' },
  ];
  const TOLERANCIA = 0.01;

  function fmt(n) { return (Math.round((n || 0) * 100) / 100).toFixed(2); }

  function crearWidget(cfg) {
    // cfg: { objetivo, modo:'pedido'|'persona', urlProcesar|onConfirmar,
    //        subLineaTemplate(motivo) -> string, nombreEtiqueta }
    let metodo = 'Efectivo';
    let montoRecibido = '';
    let mixto = false;
    let lineasMixto = [
      { metodo: 'Efectivo', monto: '' },
      { metodo: 'Transferencia', monto: '' },
    ];
    let lineaEnfocada = 0;

    const elMetodos = document.getElementById(cfg.idMetodos || 'cbmMetodos');
    const elBloque = document.getElementById(cfg.idBloque || 'cbmBloqueMetodo');
    const elBtn = document.getElementById(cfg.idBtn || 'cbmBtnConfirmar');
    const elBtnTexto = document.getElementById(cfg.idBtnTexto || 'cbmBtnConfirmarTexto');
    const elLineaBloqueo = document.getElementById(cfg.idLineaBloqueo || 'cbmLineaBloqueo');
    const elSubLinea = cfg.idSubLinea ? document.getElementById(cfg.idSubLinea) : null;

    function montosRapidos(objetivo) {
      const exacto = Math.round(objetivo * 100) / 100;
      const siguienteMultiploDe5 = Math.ceil(objetivo / 5) * 5;
      const billetes = [10, 20, 50, 100].filter((b) => b > exacto);
      const set = [exacto, siguienteMultiploDe5, ...billetes];
      return [...new Set(set.map((n) => Math.round(n * 100) / 100))].slice(0, 4);
    }

    function sumaMixto() {
      return lineasMixto.reduce((acc, l) => acc + (parseFloat(l.monto) || 0), 0);
    }

    // ===== Única fuente de verdad =====
    function puedeConfirmar() {
      if (!mixto) {
        const recibido = parseFloat(montoRecibido) || 0;
        if (metodo !== 'Efectivo') {
          // Transferencia/Tarjeta: se asume el monto exacto (no hay vuelto).
          return { ok: true, motivo: '' };
        }
        const falta = cfg.objetivo - recibido;
        if (falta > TOLERANCIA) return { ok: false, motivo: `Ingresa al menos $${fmt(cfg.objetivo)} para cubrir el total` };
        return { ok: true, motivo: '' };
      }
      const suma = sumaMixto();
      const diff = cfg.objetivo - suma;
      if (diff > TOLERANCIA) return { ok: false, motivo: `Asigna los $${fmt(diff)} restantes para continuar` };
      if (diff < -TOLERANCIA) return { ok: false, motivo: `Sobran $${fmt(-diff)} entre los métodos — ajusta los montos` };
      return { ok: true, motivo: '' };
    }

    function renderResultado() {
      const recibido = parseFloat(montoRecibido) || 0;
      const diff = mixto ? (sumaMixto() - cfg.objetivo) : (recibido - cfg.objetivo);
      let clase = 'cbm-resultado-ok';
      let label = mixto ? 'CUBIERTO' : 'VUELTO';
      let sub = mixto ? `Asignado $${fmt(sumaMixto())} de $${fmt(cfg.objetivo)}` : `Recibido $${fmt(recibido)}`;
      let valor = diff;
      if (mixto && diff > TOLERANCIA) {
        clase = 'cbm-resultado-sobra'; label = 'SOBRA';
      } else if (diff < -TOLERANCIA) {
        clase = 'cbm-resultado-falta'; label = mixto ? 'FALTA CUBRIR' : 'FALTA CUBRIR';
        valor = -diff;
        sub = mixto ? `Asignado $${fmt(sumaMixto())} de $${fmt(cfg.objetivo)}` : sub;
      }
      return `
        <div class="cbm-resultado ${clase}">
          <div class="cbm-resultado-info">
            <span class="cbm-resultado-label">${label}</span>
            <span class="cbm-resultado-sub">${sub}</span>
          </div>
          <span class="cbm-resultado-valor">$${fmt(Math.abs(valor))}</span>
        </div>`;
    }

    function renderSimple() {
      const recibido = parseFloat(montoRecibido) || 0;
      const falta = cfg.objetivo - recibido;
      const nota = falta > TOLERANCIA ? `<span class="cbm-recibido-nota cbm-recibido-nota-falta">faltan $${fmt(falta)}</span>` : `<span class="cbm-recibido-nota cbm-recibido-nota-ok">cubre el total</span>`;
      elBloque.innerHTML = `
        <div class="cbm-divisor"></div>
        <div>
          <div class="cbm-recibido-header">
            <span class="cbm-metodo-label" style="margin:0">MONTO RECIBIDO</span>
            ${nota}
          </div>
          <div class="cbm-recibido-input-wrap">
            <span>$</span>
            <input type="text" inputmode="decimal" class="cbm-recibido-input" id="cbmRecibidoInput" placeholder="0.00" value="${montoRecibido}">
          </div>
          <div class="cbm-atajos" id="cbmAtajos"></div>
          ${renderResultado()}
        </div>`;

      const input = document.getElementById('cbmRecibidoInput');
      input.addEventListener('input', function () {
        const cursor = this.selectionStart;
        montoRecibido = this.value;
        renderSimple();
        actualizarConfirmar();
        // renderSimple() reconstruye el bloque — el <input> de arriba ya
        // no está en el documento, hay que volver a buscarlo por id antes
        // de reenfocar (si no, el foco no vuelve y el teclado deja de
        // escribir después del primer carácter).
        const nuevo = document.getElementById('cbmRecibidoInput');
        if (nuevo) { nuevo.focus(); nuevo.setSelectionRange(cursor, cursor); }
      });

      const atajos = montosRapidos(cfg.objetivo);
      document.getElementById('cbmAtajos').innerHTML = atajos.map((m, i) => `
        <button type="button" class="cbm-atajo${i === 0 ? ' cbm-atajo-exacto' : ''}${parseFloat(montoRecibido) === m ? ' cbm-atajo-activo' : ''}" data-monto="${m}">$${fmt(m)}</button>
      `).join('');
      document.getElementById('cbmAtajos').querySelectorAll('.cbm-atajo').forEach((btn) => {
        btn.addEventListener('click', function () {
          montoRecibido = this.dataset.monto;
          renderSimple();
          actualizarConfirmar();
        });
      });
    }

    function renderMixto() {
      const suma = sumaMixto();
      const activas = lineasMixto.filter((l) => parseFloat(l.monto) > 0).length;
      elBloque.innerHTML = `
        <div class="cbm-divisor"></div>
        <div>
          <div class="cbm-mixto-header">
            <span class="cbm-metodo-label" style="margin:0">REPARTIR ENTRE MÉTODOS</span>
            <span class="cbm-mixto-contador">${activas} de ${lineasMixto.length}</span>
          </div>
          <div class="cbm-mixto-lineas" id="cbmMixtoLineas"></div>
          ${lineasMixto.length < 3 ? `
          <button type="button" class="cbm-mixto-agregar" id="cbmMixtoAgregar">
            <span class="cbm-mixto-agregar-icono"><i class="bi bi-credit-card"></i></span>
            <span>Agregar tarjeta</span>
            <i class="bi bi-plus-lg"></i>
          </button>` : ''}
          ${renderResultado()}
        </div>`;

      const iconos = { Efectivo: 'bi-cash', Transferencia: 'bi-arrow-left-right', Tarjeta: 'bi-credit-card' };
      const claseIcono = { Efectivo: 'cbm-mixto-icono-efectivo', Transferencia: 'cbm-mixto-icono-transferencia', Tarjeta: 'cbm-mixto-icono-tarjeta' };

      document.getElementById('cbmMixtoLineas').innerHTML = lineasMixto.map((l, idx) => `
        <div class="cbm-mixto-linea${idx === lineaEnfocada ? ' cbm-mixto-linea-activa' : ''}" data-idx="${idx}">
          <span class="cbm-mixto-icono ${claseIcono[l.metodo]}"><i class="bi ${iconos[l.metodo]}"></i></span>
          <div class="cbm-mixto-info">
            <span class="cbm-mixto-nombre">${l.metodo}</span>
            <input type="text" inputmode="decimal" class="cbm-mixto-input" data-idx="${idx}" placeholder="$0.00" value="${l.monto}">
          </div>
          <button type="button" class="cbm-mixto-resto" data-idx="${idx}">Resto</button>
        </div>
      `).join('');

      document.getElementById('cbmMixtoLineas').querySelectorAll('.cbm-mixto-input').forEach((input) => {
        // OJO: nada de re-render acá. Reconstruir el HTML mientras el
        // input tiene el foco (aunque sea solo para resaltar la fila
        // activa) destruye el <input> y el foco se pierde — el teclado
        // deja de escribir. Solo se togglea la clase en el DOM existente.
        input.addEventListener('focus', function () {
          lineaEnfocada = parseInt(this.dataset.idx, 10);
          document.querySelectorAll('.cbm-mixto-linea').forEach((el) => {
            el.classList.toggle('cbm-mixto-linea-activa', parseInt(el.dataset.idx, 10) === lineaEnfocada);
          });
        });
        input.addEventListener('input', function () {
          const idx = this.dataset.idx;
          const cursor = this.selectionStart;
          lineasMixto[parseInt(idx, 10)].monto = this.value;
          renderMixto();
          actualizarConfirmar();
          const nuevo = document.querySelector(`.cbm-mixto-input[data-idx="${idx}"]`);
          if (nuevo) { nuevo.focus(); nuevo.setSelectionRange(cursor, cursor); }
        });
      });
      document.getElementById('cbmMixtoLineas').querySelectorAll('.cbm-mixto-resto').forEach((btn) => {
        btn.addEventListener('click', function () {
          const idx = parseInt(this.dataset.idx, 10);
          const restoOtros = lineasMixto.reduce((acc, l, i) => acc + (i === idx ? 0 : (parseFloat(l.monto) || 0)), 0);
          const resto = Math.max(0, cfg.objetivo - restoOtros);
          lineasMixto[idx].monto = fmt(resto);
          lineaEnfocada = idx;
          renderMixto();
          actualizarConfirmar();
        });
      });
      const agregar = document.getElementById('cbmMixtoAgregar');
      if (agregar) {
        agregar.addEventListener('click', function () {
          lineasMixto.push({ metodo: 'Tarjeta', monto: '' });
          lineaEnfocada = lineasMixto.length - 1;
          renderMixto();
          actualizarConfirmar();
        });
      }
    }

    function renderBloque() {
      if (mixto) { renderMixto(); return; }
      if (metodo === 'Efectivo') { renderSimple(); return; }
      elBloque.innerHTML = `<div class="cbm-divisor"></div>${renderResultado()}`;
    }

    function actualizarConfirmar() {
      const r = puedeConfirmar();
      elBtn.disabled = !r.ok;
      elBtn.classList.toggle('cbm-btn-confirmar-on', r.ok);
      elBtn.classList.toggle('cbm-btn-confirmar-off', !r.ok);
      elBtnTexto.innerHTML = r.ok
        ? `<i class="bi bi-check-lg"></i> ${cfg.textoConfirmar || 'Confirmar cobro'} · $${fmt(cfg.objetivo)}`
        : (cfg.textoConfirmar || 'Confirmar cobro');
      elLineaBloqueo.hidden = r.ok;
      elLineaBloqueo.textContent = r.motivo;
      if (elSubLinea && cfg.subLineaBase) {
        elSubLinea.innerHTML = r.ok
          ? cfg.subLineaBase
          : `${cfg.subLineaBase} · <strong style="color:#c8102e">${r.motivo}</strong>`;
      }
      return r;
    }

    elMetodos.querySelectorAll('.cbm-metodo').forEach((btn) => {
      btn.addEventListener('click', function () {
        const val = this.dataset.metodo;
        mixto = val === 'Mixto';
        if (!mixto) metodo = val;
        elMetodos.querySelectorAll('.cbm-metodo').forEach((b) => b.classList.toggle('cbm-metodo-activo', b.dataset.metodo === (mixto ? 'Mixto' : metodo)));
        renderBloque();
        actualizarConfirmar();
      });
    });
    elMetodos.querySelector('[data-metodo="Efectivo"]').classList.add('cbm-metodo-activo');
    renderBloque();
    actualizarConfirmar();

    return {
      puedeConfirmar: actualizarConfirmar,
      obtenerPagos() {
        if (mixto) return lineasMixto.filter((l) => parseFloat(l.monto) > 0).map((l) => ({ metodo: l.metodo, monto: parseFloat(l.monto) }));
        const monto = metodo === 'Efectivo' ? (parseFloat(montoRecibido) || 0) : cfg.objetivo;
        return [{ metodo, monto: metodo === 'Efectivo' ? cfg.objetivo : monto }];
      },
    };
  }

  window.crearWidgetPagoCobro = crearWidget;

  // ===== Wiring de la pantalla Cobrar (pedido completo) =====
  let widgetPedido = null;

  function cbmToggleDetalle() {
    const btn = document.getElementById('cbmDetalleBtn');
    const lista = document.getElementById('cbmDetalleLista');
    const abierto = lista.classList.toggle('cbm-visible');
    btn.classList.toggle('cbm-detalle-abierto', abierto);
  }

  function cbmSeleccionarMetodo() { /* manejado dentro del widget */ }

  function cbmInit(config) {
    document.getElementById('cbmDetalleLista').innerHTML = config.items.map((item) => `
      <div class="cbm-detalle-item">
        <span class="cbm-detalle-item-badge">${item.cantidad}</span>
        <span class="cbm-detalle-item-nombre">${item.descripcion}</span>
        <span class="cbm-detalle-item-precio">$${fmt(item.precio_unitario * item.cantidad)}</span>
      </div>`).join('');

    widgetPedido = crearWidget({
      objetivo: config.objetivo,
      textoConfirmar: 'Confirmar cobro',
      idSubLinea: 'cbmSubLinea',
      subLineaBase: document.getElementById('cbmSubLinea') ? document.getElementById('cbmSubLinea').textContent.trim() : '',
    });

    window.cbmConfirmarCobro = function () {
      const r = widgetPedido.puedeConfirmar();
      if (!r.ok) return;
      const btn = document.getElementById('cbmBtnConfirmar');
      btn.disabled = true;
      fetch(config.urlProcesar, {
        method: 'POST',
        headers: { 'X-CSRFToken': window.CSRF_TOKEN, 'Content-Type': 'application/json' },
        body: JSON.stringify({ dividir: false, pagos: widgetPedido.obtenerPagos() }),
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.status !== 'ok') { alert('Error: ' + data.message); btn.disabled = false; widgetPedido.puedeConfirmar(); return; }
          window.location.href = config.urlOrdenes;
        })
        .catch(() => { alert('Error inesperado al confirmar el cobro'); btn.disabled = false; widgetPedido.puedeConfirmar(); });
    };
  }

  window.cbmInit = cbmInit;
  window.cbmToggleDetalle = cbmToggleDetalle;
  window.cbmSeleccionarMetodo = cbmSeleccionarMetodo;
})();
