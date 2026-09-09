/* Configurador de combos · handoff_combo/README.md
 *
 * Un combo se recorre como una secuencia de pasos: solo uno activo a la vez,
 * los resueltos colapsan mostrando la respuesta y los pendientes se pueden
 * tocar para saltar adelante. Los pasos salen de los componentes reales del
 * combo, así que un combo con dos grupos y otro con seis usan el mismo código.
 *
 * `puedeAgregar()` es la única fuente de verdad: de ahí salen el estado del
 * botón, la línea roja del pie y el resaltado de la cabecera.
 */
(function () {
  'use strict';

  const TEMPERATURAS = [
    { valor: 'helada', label: 'Helada', icono: 'fa-snowflake' },
    { valor: 'ambiente', label: 'Al ambiente', icono: 'fa-sun' },
  ];

  // Paleta cíclica para los segmentos de la barra de reparto: cada sabor de
  // alitas necesita un color estable para que barra y punto coincidan.
  const COLORES_REPARTO = [
    '#d99000', '#8a5800', '#1d5a9e', '#23a05f',
    '#c8102e', '#7c3aed', '#0f766e', '#b45309',
  ];

  function escapeHtml(str) {
    return String(str == null ? '' : str).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function dinero(n) {
    return '$' + Number(n || 0).toFixed(2);
  }

  window.pzCrearConfiguradorCombo = function (deps) {
    const catalogo = deps.catalogo;
    const hoja = document.getElementById('cmbHoja');
    const overlay = document.getElementById('cmbOverlay');
    if (!hoja || !overlay) return null;

    // La hoja es position:fixed dentro de .main-content{overflow:hidden}:
    // sin mudarla al body queda recortada en mobile.
    if (window.pzMoverAlBodyEnMobile) {
      window.pzMoverAlBodyEnMobile(hoja);
      window.pzMoverAlBodyEnMobile(overlay);
    }

    const elNombre = document.getElementById('cmbNombre');
    const elEstado = document.getElementById('cmbEstado');
    const elPrecio = document.getElementById('cmbPrecio');
    const elProgreso = document.getElementById('cmbProgreso');
    const elPasos = document.getElementById('cmbPasos');
    const elCantidad = document.getElementById('cmbCantidad');
    const elAgregar = document.getElementById('cmbAgregar');
    const elMotivo = document.getElementById('cmbMotivo');
    const btnMenos = document.getElementById('cmbCantMenos');
    const btnMas = document.getElementById('cmbCantMas');

    let estado = null;
    let pasos = [];
    // Cada respuesta del servidor invalida a las anteriores: sin esto, una
    // petición lenta puede pisar el precio de una selección más nueva.
    let peticionPrecio = 0;

    // ===== DEFINICIÓN DE PASOS =====
    function construirPasos(combo) {
      const lista = [];
      if (combo.tamanos && combo.tamanos.length) {
        lista.push({ id: 'tamano', tipo: 'tamano', titulo: 'Tamaño', etiqueta: 'TAMAÑO', pista: 'Define el precio' });
      }
      const tienePizza = (combo.tamanos && combo.tamanos.length) || combo.pizza_tamano_fijo_id;
      if (tienePizza) {
        lista.push({ id: 'pizza', tipo: 'mitades', titulo: 'Sabor de la pizza', etiqueta: 'PIZZA', pista: 'Uno o mitad y mitad' });
      }
      if (combo.porcion_pizza_cantidad) {
        lista.push({
          id: 'porciones', tipo: 'multi', titulo: 'Porciones de pizza', etiqueta: 'PORCIÓN',
          pista: `${combo.porcion_pizza_cantidad} sabor${combo.porcion_pizza_cantidad > 1 ? 'es' : ''}`,
          cantidad: combo.porcion_pizza_cantidad, pool: catalogo.sabores, prefijo: 'Porción',
        });
      }
      if (combo.alitas_cantidad) {
        lista.push({
          id: 'alitas', tipo: 'reparto', titulo: `${combo.alitas_cantidad} alitas`, etiqueta: 'ALITAS',
          pista: 'Hasta 3 sabores', total: combo.alitas_cantidad, maxOpciones: 3,
          pool: catalogo.sabores_alitas || [],
        });
      }
      if (combo.bebida_cantidad) {
        lista.push({
          id: 'bebida', tipo: 'bebida', titulo: combo.bebida_cantidad > 1 ? 'Bebidas' : 'Bebida',
          etiqueta: 'BEBIDA', pista: 'Sabor y temperatura',
          cantidad: combo.bebida_cantidad, pool: catalogo.sabores_bebida || [], prefijo: 'Bebida',
        });
      }
      if (combo.michelada_cantidad) {
        lista.push({
          id: 'michelada', tipo: 'multi', titulo: combo.michelada_cantidad > 1 ? 'Micheladas' : 'Michelada',
          etiqueta: 'MICHELADA', pista: 'Elige el sabor',
          cantidad: combo.michelada_cantidad, pool: catalogo.sabores_michelada || [], prefijo: 'Michelada',
        });
      }
      return lista;
    }

    // ===== ESTADO RESUELTO / RESUMEN POR PASO =====
    function pasoResuelto(paso) {
      if (paso.tipo === 'tamano') return !!estado.tamanoId;
      if (paso.tipo === 'mitades') {
        return estado.modo === 'unico' ? !!estado.sabor1 : !!(estado.sabor1 && estado.sabor2);
      }
      if (paso.tipo === 'reparto') return asignadoReparto() === paso.total;
      if (paso.tipo === 'multi') {
        return estado[paso.id].filter(Boolean).length === paso.cantidad;
      }
      if (paso.tipo === 'bebida') {
        return estado.bebidas.length === paso.cantidad
          && estado.bebidas.every(b => b && b.saborId && b.temperatura);
      }
      return false;
    }

    function nombreSabor(pool, id) {
      const s = (pool || []).find(x => x.id === id);
      return s ? s.nombre : '';
    }

    function resumenPaso(paso) {
      if (paso.tipo === 'tamano') {
        const t = estado.combo.tamanos.find(x => x.tamano_id === estado.tamanoId);
        return t ? `${t.tamano_nombre} · ${dinero(t.precio)}` : '';
      }
      if (paso.tipo === 'mitades') {
        const n1 = nombreSabor(catalogo.sabores, estado.sabor1);
        if (estado.modo === 'unico') return n1;
        return `½ ${n1} · ½ ${nombreSabor(catalogo.sabores, estado.sabor2)}`;
      }
      if (paso.tipo === 'reparto') {
        return estado.alitas.map(a => `${a.cantidad} ${nombreSabor(paso.pool, a.saborId)}`).join(' · ');
      }
      if (paso.tipo === 'multi') {
        return estado[paso.id].filter(Boolean).map(id => nombreSabor(paso.pool, id)).join(' · ');
      }
      if (paso.tipo === 'bebida') {
        return estado.bebidas.map(function (b) {
          const temp = TEMPERATURAS.find(t => t.valor === b.temperatura);
          return nombreSabor(paso.pool, b.saborId) + (temp ? ` · ${temp.label.toLowerCase()}` : '');
        }).join(' · ');
      }
      return '';
    }

    // Lo que falta en el paso activo, resaltado en rojo bajo su título.
    function faltaEnPaso(paso) {
      if (paso.tipo === 'tamano') return estado.tamanoId ? '' : 'elige uno';
      if (paso.tipo === 'mitades') {
        if (estado.modo === 'unico') return estado.sabor1 ? '' : 'elige el sabor';
        if (!estado.sabor1) return 'falta la mitad 1';
        if (!estado.sabor2) return 'falta la mitad 2';
        return '';
      }
      if (paso.tipo === 'reparto') {
        const restan = paso.total - asignadoReparto();
        return restan > 0 ? `Faltan ${restan}` : (restan < 0 ? `Sobran ${-restan}` : '');
      }
      if (paso.tipo === 'multi') {
        const faltan = paso.cantidad - estado[paso.id].filter(Boolean).length;
        return faltan > 0 ? `falta${faltan > 1 ? 'n' : ''} ${faltan}` : '';
      }
      if (paso.tipo === 'bebida') {
        for (let i = 0; i < paso.cantidad; i++) {
          const b = estado.bebidas[i];
          if (!b || !b.saborId) return paso.cantidad > 1 ? `falta el sabor ${i + 1}` : 'falta el sabor';
          if (!b.temperatura) return paso.cantidad > 1 ? `falta la temperatura ${i + 1}` : 'falta la temperatura';
        }
        return '';
      }
      return '';
    }

    function asignadoReparto() {
      return estado.alitas.reduce((s, a) => s + a.cantidad, 0);
    }

    // El recargo premium no vive en el sabor sino en el tamaño elegido, y
    // cambia según se cobre la pizza completa o media.
    function recargoSabor(s) {
      if (!s.es_premium || !estado.tamanoId) return 0;
      const t = (catalogo.tamanos || []).find(x => x.id === estado.tamanoId);
      if (!t) return 0;
      return parseFloat(
        estado.modo === 'mitades' ? t.recargo_premium_mitad : t.recargo_premium_completo,
      ) || 0;
    }

    function colorSabor(paso, saborId) {
      const idx = (paso.pool || []).findIndex(s => s.id === saborId);
      return COLORES_REPARTO[(idx < 0 ? 0 : idx) % COLORES_REPARTO.length];
    }

    // ===== ÚNICA FUENTE DE VERDAD =====
    function puedeAgregar() {
      for (let i = 0; i < pasos.length; i++) {
        const paso = pasos[i];
        if (pasoResuelto(paso)) continue;
        if (paso.tipo === 'reparto') {
          const restan = paso.total - asignadoReparto();
          return {
            ok: false,
            motivo: restan > 0
              ? `Reparte las ${restan} alitas restantes`
              : `Quita ${-restan} alitas: el combo trae ${paso.total}`,
          };
        }
        if (paso.tipo === 'mitades' && estado.modo === 'mitades' && estado.sabor1 && !estado.sabor2) {
          return { ok: false, motivo: 'Elige la mitad 2 para continuar' };
        }
        if (paso.tipo === 'bebida') {
          return { ok: false, motivo: `Bebida: ${faltaEnPaso(paso)}` };
        }
        return { ok: false, motivo: `Falta elegir: ${paso.titulo.toLowerCase()}` };
      }
      return { ok: true, motivo: '' };
    }

    // ===== PRECIO =====
    function precioBase() {
      const c = estado.combo;
      if (c.tamanos && c.tamanos.length) {
        const t = c.tamanos.find(x => x.tamano_id === estado.tamanoId);
        return t ? parseFloat(t.precio) : 0;
      }
      return parseFloat(c.precio_fijo || 0);
    }

    // El precio nunca muestra $0.00 cuando ya hay tamaño: parte del base y el
    // servidor sólo lo refina con los recargos de sabor premium.
    function actualizarPrecio() {
      estado.precioUnitario = precioBase();
      pintarPrecio();

      const necesitaServidor = estado.combo.tamanos && estado.combo.tamanos.length
        && estado.tamanoId && estado.sabor1
        && (estado.modo === 'unico' || estado.sabor2);
      if (!necesitaServidor) return;

      const token = ++peticionPrecio;
      const body = new FormData();
      body.append('tamano_id', estado.tamanoId);
      body.append('sabor_1_id', estado.sabor1);
      body.append('sabor_2_id', estado.modo === 'mitades' ? estado.sabor2 : '');
      body.append('combo_id', estado.combo.id);

      fetch(deps.calcularPrecioUrl, {
        method: 'POST', body, headers: { 'X-CSRFToken': deps.csrfToken },
      })
        .then(r => r.json())
        .then(function (data) {
          if (token !== peticionPrecio || !estado) return;
          if (data.status === 'ok') {
            estado.precioUnitario = parseFloat(data.precio);
            pintarPrecio();
          }
        })
        .catch(function () { /* se queda con el precio base */ });
    }

    function pintarPrecio() {
      elPrecio.textContent = dinero(estado.precioUnitario * estado.cantidad);
    }

    // ===== RENDER =====
    function render() {
      pintarCabecera();
      pintarPasos();
      pintarPie();
    }

    function pintarCabecera() {
      const resueltos = pasos.filter(pasoResuelto).length;
      const tamanoNombre = estado.tamanoId
        ? (estado.combo.tamanos.find(t => t.tamano_id === estado.tamanoId) || {}).tamano_nombre
        : '';
      const completo = resueltos === pasos.length;
      const prefijo = tamanoNombre ? `${escapeHtml(tamanoNombre)} · ` : '';
      elEstado.innerHTML = completo
        ? prefijo + '<strong class="cmb-completo">completo</strong>'
        : prefijo + `<strong>${resueltos} de ${pasos.length} pasos</strong>`;

      elProgreso.innerHTML = pasos.map(function (paso) {
        let cls = 'cmb-progreso-seg';
        if (pasoResuelto(paso)) cls += ' cmb-progreso-seg-resuelto';
        else if (paso.id === estado.pasoActivo) cls += ' cmb-progreso-seg-activo';
        return `<span class="${cls}"></span>`;
      }).join('');

      pintarPrecio();
    }

    function pintarPasos() {
      elPasos.innerHTML = '';
      pasos.forEach(function (paso, idx) {
        const nodo = document.createElement('div');
        nodo.className = 'cmb-paso';
        if (paso.id === estado.pasoActivo) nodo.appendChild(vistaActivo(paso, idx));
        else if (pasoResuelto(paso)) nodo.appendChild(vistaResuelto(paso));
        else nodo.appendChild(vistaPendiente(paso, idx));
        elPasos.appendChild(nodo);
      });

      if (pasos.every(pasoResuelto)) elPasos.appendChild(vistaResumen());
    }

    function vistaResuelto(paso) {
      const fila = document.createElement('div');
      fila.className = 'cmb-paso-resuelto';
      fila.innerHTML = `
        <span class="cmb-check"><i class="fas fa-check"></i></span>
        <span class="cmb-resuelto-texto">
          <span class="cmb-resuelto-label">${escapeHtml(paso.etiqueta)}</span>
          <span class="cmb-resuelto-valor">${escapeHtml(resumenPaso(paso))}</span>
        </span>
        <button type="button" class="cmb-cambiar">Cambiar</button>`;
      fila.querySelector('.cmb-cambiar').addEventListener('click', function () {
        estado.pasoActivo = paso.id;
        render();
      });
      return fila;
    }

    function vistaPendiente(paso, idx) {
      const fila = document.createElement('button');
      fila.type = 'button';
      fila.className = 'cmb-paso-pendiente';
      fila.innerHTML = `
        <span class="cmb-num">${idx + 1}</span>
        <span class="cmb-pendiente-texto">
          <span class="cmb-pendiente-titulo">${escapeHtml(paso.titulo)}</span>
          <span class="cmb-pendiente-sub">${escapeHtml(paso.pista)}</span>
        </span>
        <i class="fas fa-chevron-right cmb-chevron"></i>`;
      fila.addEventListener('click', function () {
        estado.pasoActivo = paso.id;
        render();
      });
      return fila;
    }

    function vistaActivo(paso, idx) {
      const tarjeta = document.createElement('div');
      tarjeta.className = 'cmb-paso-activo';
      const falta = faltaEnPaso(paso);
      const sub = falta
        ? `${escapeHtml(paso.pista)} · <strong>${escapeHtml(falta)}</strong>`
        : escapeHtml(paso.pista);
      tarjeta.innerHTML = `
        <div class="cmb-activo-cabecera">
          <span class="cmb-num">${idx + 1}</span>
          <span class="cmb-activo-texto">
            <span class="cmb-activo-titulo">${escapeHtml(paso.titulo)}</span>
            <span class="cmb-activo-sub">${sub}</span>
          </span>
        </div>`;
      const cuerpo = document.createElement('div');
      cuerpo.className = 'cmb-activo-cuerpo';
      cuerpo.appendChild(cuerpoDePaso(paso));
      tarjeta.appendChild(cuerpo);
      return tarjeta;
    }

    function cuerpoDePaso(paso) {
      if (paso.tipo === 'tamano') return cuerpoTamano(paso);
      if (paso.tipo === 'mitades') return cuerpoMitades(paso);
      if (paso.tipo === 'reparto') return cuerpoReparto(paso);
      if (paso.tipo === 'bebida') return cuerpoBebida(paso);
      return cuerpoMulti(paso);
    }

    // Al resolver un paso se abre solo el siguiente pendiente.
    function avanzar(paso) {
      if (!pasoResuelto(paso)) { render(); return; }
      const siguiente = pasos.find(p => !pasoResuelto(p));
      estado.pasoActivo = siguiente ? siguiente.id : null;
      render();
    }

    function botonOpcion(nombre, seleccionado, extraHtml) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'cmb-opcion'
        + (nombre.length > 16 ? ' cmb-opcion-larga' : '')
        + (seleccionado ? ' cmb-opcion-activa' : '');
      btn.innerHTML = `<span>${escapeHtml(nombre)}${seleccionado ? ' <i class="fas fa-check"></i>' : ''}</span>`
        + (extraHtml || '');
      return btn;
    }

    function cuerpoTamano(paso) {
      const grid = document.createElement('div');
      grid.className = 'cmb-grid';
      estado.combo.tamanos.forEach(function (t) {
        const btn = botonOpcion(
          t.tamano_nombre, estado.tamanoId === t.tamano_id,
          `<span class="cmb-opcion-precio">${dinero(t.precio)}</span>`,
        );
        btn.addEventListener('click', function () {
          estado.tamanoId = t.tamano_id;
          actualizarPrecio();
          avanzar(paso);
        });
        grid.appendChild(btn);
      });
      return grid;
    }

    function cuerpoMitades(paso) {
      const wrap = document.createElement('div');
      wrap.style.display = 'flex';
      wrap.style.flexDirection = 'column';
      wrap.style.gap = '11px';

      const modos = document.createElement('div');
      modos.className = 'cmb-modo';
      [['unico', 'Un solo sabor'], ['mitades', 'Mitad y mitad']].forEach(function (m) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cmb-modo-btn' + (estado.modo === m[0] ? ' cmb-modo-btn-activo' : '');
        btn.textContent = m[1];
        btn.addEventListener('click', function () {
          if (estado.modo === m[0]) return;
          estado.modo = m[0];
          // Pasar a un solo sabor conserva la mitad 1 y descarta la 2.
          if (estado.modo === 'unico') estado.sabor2 = null;
          estado.ranuraEditando = estado.sabor1 ? 2 : 1;
          actualizarPrecio();
          render();
        });
        modos.appendChild(btn);
      });
      wrap.appendChild(modos);

      if (estado.modo === 'mitades') wrap.appendChild(vistaRanuras());

      const grid = document.createElement('div');
      grid.className = 'cmb-grid';
      (catalogo.sabores || []).forEach(function (s) {
        const sel = estado.sabor1 === s.id || (estado.modo === 'mitades' && estado.sabor2 === s.id);
        const recargo = recargoSabor(s);
        const btn = botonOpcion(
          s.nombre, sel,
          recargo > 0 ? `<span class="cmb-recargo">+${dinero(recargo)}</span>` : '',
        );
        btn.addEventListener('click', function () { elegirSaborPizza(paso, s.id); });
        grid.appendChild(btn);
      });
      wrap.appendChild(grid);
      return wrap;
    }

    function vistaRanuras() {
      const fila = document.createElement('div');
      fila.className = 'cmb-ranuras';
      [1, 2].forEach(function (n) {
        const saborId = n === 1 ? estado.sabor1 : estado.sabor2;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cmb-ranura'
          + (saborId ? ' cmb-ranura-llena' : ' cmb-ranura-pendiente')
          + (estado.ranuraEditando === n ? ' cmb-ranura-editando' : '');
        btn.innerHTML = `
          <span class="cmb-ranura-label">MITAD ${n}</span>
          <span class="cmb-ranura-valor">${saborId ? escapeHtml(nombreSabor(catalogo.sabores, saborId)) : 'Elige abajo'}</span>`;
        btn.addEventListener('click', function () {
          estado.ranuraEditando = n;
          render();
        });
        fila.appendChild(btn);
      });
      return fila;
    }

    // El sabor que se toca cae en la ranura pendiente (o en la que se fijó).
    function elegirSaborPizza(paso, saborId) {
      if (estado.modo === 'unico') {
        estado.sabor1 = saborId;
        estado.sabor2 = null;
      } else {
        const destino = !estado.sabor1 ? 1 : (!estado.sabor2 ? 2 : estado.ranuraEditando);
        if (destino === 1) estado.sabor1 = saborId;
        else estado.sabor2 = saborId;
        estado.ranuraEditando = destino === 1 ? 2 : 1;
      }
      actualizarPrecio();
      avanzar(paso);
    }

    function cuerpoReparto(paso) {
      const wrap = document.createElement('div');
      wrap.style.display = 'flex';
      wrap.style.flexDirection = 'column';
      wrap.style.gap = '11px';

      const asignado = asignadoReparto();

      const barraFila = document.createElement('div');
      barraFila.className = 'cmb-reparto-barra';
      const segmentos = estado.alitas.map(function (a) {
        const ancho = (a.cantidad / paso.total) * 100;
        return `<span class="cmb-barra-seg" style="width:${ancho}%;background:${colorSabor(paso, a.saborId)}"></span>`;
      }).join('');
      barraFila.innerHTML = `
        <span class="cmb-barra">${segmentos}</span>
        <span class="cmb-reparto-contador"><strong>${asignado}</strong>/${paso.total}</span>`;
      wrap.appendChild(barraFila);

      const atajos = document.createElement('div');
      atajos.className = 'cmb-atajos';
      [
        ['Todas iguales', function () {
          const primero = estado.alitas[0] || { saborId: (paso.pool[0] || {}).id };
          if (!primero.saborId) return;
          estado.alitas = [{ saborId: primero.saborId, cantidad: paso.total }];
        }],
        ['Mitad y mitad', function () {
          const dos = estado.alitas.slice(0, 2);
          if (dos.length < 2) { deps.mostrarToast('Elige dos sabores primero'); return; }
          const mitad = Math.ceil(paso.total / 2);
          estado.alitas = [
            { saborId: dos[0].saborId, cantidad: mitad },
            { saborId: dos[1].saborId, cantidad: paso.total - mitad },
          ];
        }],
        ['Limpiar', function () { estado.alitas = []; }],
      ].forEach(function (a) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cmb-atajo';
        btn.textContent = a[0];
        btn.addEventListener('click', function () { a[1](); avanzar(paso); });
        atajos.appendChild(btn);
      });
      wrap.appendChild(atajos);

      if (estado.alitas.length) {
        const elegidos = document.createElement('div');
        elegidos.className = 'cmb-elegidos';
        estado.alitas.forEach(function (a) {
          const fila = document.createElement('div');
          fila.className = 'cmb-elegido';
          fila.innerHTML = `
            <span class="cmb-punto" style="background:${colorSabor(paso, a.saborId)}"></span>
            <span class="cmb-elegido-nombre">${escapeHtml(nombreSabor(paso.pool, a.saborId))}</span>
            <span class="cmb-mini-stepper">
              <button type="button" class="cmb-mini-btn" data-d="-1"><i class="fas fa-minus"></i></button>
              <span class="cmb-mini-num">${a.cantidad}</span>
              <button type="button" class="cmb-mini-btn" data-d="1"${asignado >= paso.total ? ' disabled' : ''}><i class="fas fa-plus"></i></button>
            </span>`;
          fila.querySelectorAll('.cmb-mini-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
              cambiarReparto(paso, a.saborId, parseInt(btn.dataset.d, 10));
            });
          });
          elegidos.appendChild(fila);
        });
        wrap.appendChild(elegidos);

        const div = document.createElement('div');
        div.className = 'cmb-divisor';
        wrap.appendChild(div);
      }

      const chips = document.createElement('div');
      chips.className = 'cmb-chips';
      const alMaximo = estado.alitas.length >= paso.maxOpciones;
      (paso.pool || []).forEach(function (s) {
        if (estado.alitas.some(a => a.saborId === s.id)) return;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cmb-chip' + (alMaximo ? ' cmb-chip-atenuado' : '');
        btn.innerHTML = `${escapeHtml(s.nombre)} <i class="fas fa-plus"></i>`;
        btn.disabled = alMaximo;
        btn.addEventListener('click', function () {
          // Entra con el resto pendiente: en la mayoría de los pedidos es
          // un solo sabor y así el paso queda resuelto de un toque.
          const restan = paso.total - asignadoReparto();
          if (restan <= 0) { deps.mostrarToast(`Ya repartiste las ${paso.total} alitas`); return; }
          estado.alitas.push({ saborId: s.id, cantidad: restan });
          avanzar(paso);
        });
        chips.appendChild(btn);
      });
      wrap.appendChild(chips);

      const ayuda = document.createElement('span');
      ayuda.className = 'cmb-ayuda';
      ayuda.textContent = `Toca un sabor para sumarlo. Con ${paso.maxOpciones} elegidos el resto se atenúa.`;
      wrap.appendChild(ayuda);

      return wrap;
    }

    function cambiarReparto(paso, saborId, delta) {
      const entry = estado.alitas.find(a => a.saborId === saborId);
      if (!entry) return;
      if (delta > 0 && asignadoReparto() >= paso.total) return;
      entry.cantidad += delta;
      // Bajar a 0 devuelve el sabor a los chips disponibles.
      if (entry.cantidad <= 0) estado.alitas = estado.alitas.filter(a => a.saborId !== saborId);
      avanzar(paso);
    }

    function cuerpoMulti(paso) {
      const wrap = document.createElement('div');
      wrap.style.display = 'flex';
      wrap.style.flexDirection = 'column';
      wrap.style.gap = '12px';

      for (let i = 0; i < paso.cantidad; i++) {
        const bloque = document.createElement('div');
        if (paso.cantidad > 1) {
          const label = document.createElement('span');
          label.className = 'cmb-sublabel';
          label.textContent = `${paso.prefijo} ${i + 1}`.toUpperCase();
          bloque.appendChild(label);
        }
        const grid = document.createElement('div');
        grid.className = 'cmb-grid';
        (paso.pool || []).forEach(function (s) {
          const btn = botonOpcion(s.nombre, estado[paso.id][i] === s.id, '');
          btn.addEventListener('click', function () {
            estado[paso.id][i] = s.id;
            if (paso.id === 'porciones') actualizarPrecio();
            avanzar(paso);
          });
          grid.appendChild(btn);
        });
        bloque.appendChild(grid);
        wrap.appendChild(bloque);
      }
      return wrap;
    }

    // La temperatura viaja en la comanda: hasta ahora se preguntaba de viva voz.
    function cuerpoBebida(paso) {
      const wrap = document.createElement('div');
      wrap.style.display = 'flex';
      wrap.style.flexDirection = 'column';
      wrap.style.gap = '12px';

      for (let i = 0; i < paso.cantidad; i++) {
        const actual = estado.bebidas[i];

        const bloque = document.createElement('div');
        if (paso.cantidad > 1) {
          const titulo = document.createElement('span');
          titulo.className = 'cmb-sublabel';
          titulo.textContent = `BEBIDA ${i + 1}`;
          bloque.appendChild(titulo);
        }

        const labelSabor = document.createElement('span');
        labelSabor.className = 'cmb-sublabel';
        labelSabor.textContent = 'SABOR';
        bloque.appendChild(labelSabor);

        const grid = document.createElement('div');
        grid.className = 'cmb-grid';
        (paso.pool || []).forEach(function (s) {
          const btn = botonOpcion(s.nombre, actual.saborId === s.id, '');
          btn.addEventListener('click', function () {
            actual.saborId = s.id;
            avanzar(paso);
          });
          grid.appendChild(btn);
        });
        bloque.appendChild(grid);

        const labelTemp = document.createElement('span');
        labelTemp.className = 'cmb-sublabel';
        labelTemp.style.marginTop = '11px';
        labelTemp.textContent = 'TEMPERATURA';
        bloque.appendChild(labelTemp);

        const temps = document.createElement('div');
        temps.className = 'cmb-temp';
        TEMPERATURAS.forEach(function (t) {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'cmb-temp-btn'
            + (actual.temperatura === t.valor ? ` cmb-temp-btn-activo-${t.valor}` : '');
          btn.innerHTML = `<i class="fas ${t.icono}"></i> ${t.label}`;
          btn.addEventListener('click', function () {
            actual.temperatura = t.valor;
            avanzar(paso);
          });
          temps.appendChild(btn);
        });
        bloque.appendChild(temps);

        wrap.appendChild(bloque);
      }
      return wrap;
    }

    function vistaResumen() {
      const caja = document.createElement('div');
      caja.className = 'cmb-resumen';
      const filas = pasos.map(function (paso) {
        return `
          <div class="cmb-resumen-fila">
            <span class="cmb-resumen-grupo">${escapeHtml(paso.etiqueta)}</span>
            <span class="cmb-resumen-valor">${escapeHtml(resumenPaso(paso))}</span>
          </div>`;
      }).join('');
      caja.innerHTML = `
        <span class="cmb-resumen-label">RESUMEN DEL COMBO</span>
        ${filas}
        <div class="cmb-resumen-pie">
          <span class="cmb-nota-label">Nota para cocina (opcional)</span>
          <button type="button" class="cmb-nota-btn">${estado.nota ? 'Editar' : 'Agregar'}</button>
        </div>`;

      const pie = caja.querySelector('.cmb-resumen-pie');
      const btnNota = caja.querySelector('.cmb-nota-btn');
      // Al repintar se reconstruye el campo pero no se roba el foco: solo lo
      // toma cuando el cajero acaba de pulsar "Agregar".
      if (estado.notaAbierta) mostrarCampoNota(pie, false);
      btnNota.addEventListener('click', function () {
        estado.notaAbierta = true;
        mostrarCampoNota(pie, true);
      });
      return caja;
    }

    function mostrarCampoNota(pie, enfocar) {
      pie.innerHTML = '';
      const input = document.createElement('input');
      input.type = 'text';
      input.className = 'cmb-nota-input';
      input.placeholder = 'Ej. sin cebolla, cortar en 8';
      input.maxLength = 200;
      input.value = estado.nota;
      input.addEventListener('input', function () { estado.nota = input.value; });
      pie.appendChild(input);
      if (enfocar) input.focus();
    }

    function pintarPie() {
      const veredicto = puedeAgregar();
      elAgregar.classList.toggle('cmb-agregar-bloqueado', !veredicto.ok);
      elAgregar.disabled = !veredicto.ok;
      elAgregar.innerHTML = veredicto.ok
        ? `<i class="fas fa-check"></i> Agregar · ${dinero(estado.precioUnitario * estado.cantidad)}`
        : 'Agregar';
      elMotivo.textContent = veredicto.motivo;
      elCantidad.textContent = estado.cantidad;
      btnMenos.disabled = estado.cantidad <= 1;
    }

    // ===== APERTURA / CIERRE =====
    function abrir(combo) {
      estado = {
        combo: combo,
        cantidad: 1,
        nota: '',
        notaAbierta: false,
        tamanoId: null,
        modo: 'unico',
        sabor1: null,
        sabor2: null,
        ranuraEditando: 1,
        porciones: [],
        alitas: [],
        bebidas: [],
        michelada: [],
        precioUnitario: 0,
      };
      pasos = construirPasos(combo);
      pasos.forEach(function (paso) {
        if (paso.tipo === 'bebida') {
          estado.bebidas = Array.from({ length: paso.cantidad }, () => ({ saborId: null, temperatura: null }));
        }
      });
      estado.pasoActivo = pasos.length ? pasos[0].id : null;
      elNombre.textContent = combo.nombre;
      actualizarPrecio();
      render();
      elPasos.scrollTop = 0;
      hoja.classList.add('cmb-hoja-abierta');
      overlay.classList.add('cmb-overlay-activo');
      document.body.style.overflow = 'hidden';
    }

    function cerrar() {
      hoja.classList.remove('cmb-hoja-abierta');
      overlay.classList.remove('cmb-overlay-activo');
      document.body.style.overflow = '';
    }

    // ===== EVENTOS DEL PIE =====
    btnMenos.addEventListener('click', function () {
      if (estado.cantidad <= 1) return;
      estado.cantidad--;
      pintarPrecio();
      pintarPie();
    });

    btnMas.addEventListener('click', function () {
      estado.cantidad++;
      pintarPrecio();
      pintarPie();
    });

    elAgregar.addEventListener('click', function () {
      const veredicto = puedeAgregar();
      if (!veredicto.ok) return;
      deps.onAgregar(construirItemCarrito());
      cerrar();
    });

    overlay.addEventListener('click', cerrar);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && hoja.classList.contains('cmb-hoja-abierta')) cerrar();
    });

    function construirItemCarrito() {
      const c = estado.combo;
      const partes = [];
      pasos.forEach(function (paso) {
        if (paso.id === 'tamano' || paso.id === 'pizza') return;
        const txt = resumenPaso(paso);
        if (txt) partes.push(`${paso.etiqueta.charAt(0) + paso.etiqueta.slice(1).toLowerCase()}: ${txt}`);
      });

      let label = c.nombre;
      const tamano = estado.tamanoId
        ? (c.tamanos.find(t => t.tamano_id === estado.tamanoId) || {}).tamano_nombre
        : null;
      if (tamano) label += ` (${tamano})`;
      const pizza = pasos.find(p => p.id === 'pizza');
      if (pizza) label += ' - ' + resumenPaso(pizza);
      if (partes.length) label += ' | ' + partes.join(' | ');

      return {
        kind: 'combo',
        cantidad: estado.cantidad,
        observacion: estado.nota,
        combo_id: c.id,
        tamano_id: estado.tamanoId,
        sabor_1_id: estado.sabor1,
        sabor_2_id: estado.modo === 'mitades' ? estado.sabor2 : null,
        alitas_sabores: estado.alitas.map(a => ({ sabor_id: a.saborId, cantidad: a.cantidad })),
        bebidas: estado.bebidas.map(b => ({ sabor_id: b.saborId, temperatura: b.temperatura })),
        sabores_michelada_ids: estado.michelada.filter(Boolean),
        sabores_porcion_ids: estado.porciones.filter(Boolean),
        _label: label,
        _precio_unitario: estado.precioUnitario,
      };
    }

    return { abrir: abrir, cerrar: cerrar };
  };
}());
