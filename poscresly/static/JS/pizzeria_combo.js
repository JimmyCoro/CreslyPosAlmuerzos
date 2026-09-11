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
    // Cada producto se describe como una lista de pasos; de ahí en adelante la
    // hoja es la misma para una pizza, unas alitas o un combo de seis grupos.
    function construirPasos(spec) {
      if (spec.kind === 'combo') return construirPasosCombo(spec.combo);

      if (spec.kind === 'pizza') {
        return [{
          id: 'pizza', tipo: 'mitades', titulo: 'Sabor de la pizza', etiqueta: 'PIZZA',
          pista: spec.permiteMitad ? 'Uno o mitad y mitad' : 'Elige el sabor',
          permiteMitad: spec.permiteMitad,
        }];
      }
      if (spec.kind === 'porcion') {
        return [{
          id: 'porciones', tipo: 'multi', titulo: 'Sabor de la porción', etiqueta: 'SABOR',
          pista: 'Elige el sabor', unidades: 1, pool: catalogo.sabores, prefijo: 'Porción',
        }];
      }
      if (spec.kind === 'producto_alitas') {
        const total = spec.producto.alitas_cantidad;
        return [{
          id: 'alitas', tipo: 'reparto', titulo: `${total} alitas`, etiqueta: `${total} ALITAS`,
          pista: 'Iguales o repartidas',
          total: total, unidades: total, maxOpciones: maxSaboresReparto(total),
          pool: catalogo.sabores_alitas || [], prefijo: 'Alitas',
        }];
      }
      if (spec.kind === 'producto_bebida') {
        return [{
          id: 'bebida', tipo: 'bebida', titulo: 'Bebida', etiqueta: 'BEBIDA',
          pista: 'Sabor y temperatura', unidades: 1,
          pool: catalogo.sabores_bebida || [], prefijo: 'Bebida',
        }];
      }
      if (spec.kind === 'producto_michelada') {
        return [{
          id: 'michelada', tipo: 'multi', titulo: 'Michelada', etiqueta: 'MICHELADA',
          pista: 'Elige el sabor', unidades: 1,
          pool: catalogo.sabores_michelada || [], prefijo: 'Michelada',
        }];
      }
      return [];
    }

    function conUnidades(n, singular, plural) {
      return n > 1 ? `${n} ${plural}` : singular.charAt(0).toUpperCase() + singular.slice(1);
    }

    // El máximo de sabores sale del grupo, no de una constante: repartir 4
    // alitas entre 3 sabores no tiene sentido en la práctica (14 → 3, 4 → 2).
    function maxSaboresReparto(total) {
      return Math.min(3, Math.max(1, Math.floor(total / 2)));
    }

    function unidadesDe(paso) {
      return paso.unidades || 1;
    }

    function modoDe(paso) {
      return estado.modos[paso.id] || 'iguales';
    }

    function construirPasosCombo(combo) {
      const lista = [];
      if (combo.tamanos && combo.tamanos.length) {
        lista.push({ id: 'tamano', tipo: 'tamano', titulo: 'Tamaño', etiqueta: 'TAMAÑO', pista: 'Define el precio' });
      }
      const tienePizza = (combo.tamanos && combo.tamanos.length) || combo.pizza_tamano_fijo_id;
      if (tienePizza) {
        lista.push({ id: 'pizza', tipo: 'mitades', titulo: 'Sabor de la pizza', etiqueta: 'PIZZA', pista: 'Uno o mitad y mitad' });
      }
      if (combo.porcion_pizza_cantidad) {
        const n = combo.porcion_pizza_cantidad;
        lista.push({
          id: 'porciones', tipo: 'multi',
          titulo: conUnidades(n, 'porción de pizza', 'porciones de pizza'),
          etiqueta: conUnidades(n, 'PORCIÓN DE PIZZA', 'PORCIONES DE PIZZA'),
          pista: n > 1 ? 'Iguales o distintas' : 'Elige el sabor',
          corto: `${n} porciones`,
          unidades: n, pool: catalogo.sabores, prefijo: 'Porción',
        });
      }
      if (combo.alitas_cantidad) {
        const n = combo.alitas_cantidad;
        lista.push({
          id: 'alitas', tipo: 'reparto',
          titulo: `${n} alitas`, etiqueta: `${n} ALITAS`,
          pista: 'Iguales o repartidas',
          corto: `${n} alitas`,
          total: n, unidades: n, maxOpciones: maxSaboresReparto(n),
          pool: catalogo.sabores_alitas || [], prefijo: 'Alitas',
        });
      }
      if (combo.bebida_cantidad) {
        const n = combo.bebida_cantidad;
        lista.push({
          id: 'bebida', tipo: 'bebida',
          titulo: conUnidades(n, 'bebida', 'bebidas'),
          etiqueta: conUnidades(n, 'BEBIDA', 'BEBIDAS'),
          pista: 'Sabor y temperatura',
          corto: `${n} bebidas`,
          unidades: n, pool: catalogo.sabores_bebida || [], prefijo: 'Bebida',
        });
      }
      if (combo.michelada_cantidad) {
        const n = combo.michelada_cantidad;
        lista.push({
          id: 'michelada', tipo: 'multi',
          titulo: conUnidades(n, 'michelada', 'micheladas'),
          etiqueta: conUnidades(n, 'MICHELADA', 'MICHELADAS'),
          pista: n > 1 ? 'Iguales o distintas' : 'Elige el sabor',
          corto: `${n} micheladas`,
          unidades: n, pool: catalogo.sabores_michelada || [], prefijo: 'Michelada',
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
        return estado[paso.id].filter(Boolean).length === unidadesDe(paso);
      }
      if (paso.tipo === 'bebida') {
        return estado.bebidas.length === unidadesDe(paso)
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
        const t = estado.spec.combo.tamanos.find(x => x.tamano_id === estado.tamanoId);
        return t ? `${t.tamano_nombre} · ${dinero(t.precio)}` : '';
      }
      if (paso.tipo === 'mitades') {
        const n1 = nombreSabor(catalogo.sabores, estado.sabor1);
        if (estado.modo === 'unico') return n1;
        return `½ ${n1} · ½ ${nombreSabor(catalogo.sabores, estado.sabor2)}`;
      }
      // El número por delante ("Las 2 de Peperoni") dice cuántas unidades cubre
      // la elección sin tener que repetir el grupo una vez por unidad.
      if (paso.tipo === 'reparto') {
        if (modoDe(paso) === 'iguales' && estado.alitas.length === 1) {
          return `Las ${paso.total} ${nombreSabor(paso.pool, estado.alitas[0].saborId)}`;
        }
        return estado.alitas.map(a => `${a.cantidad} ${nombreSabor(paso.pool, a.saborId)}`).join(' · ');
      }
      if (paso.tipo === 'multi') {
        const elegidos = estado[paso.id].filter(Boolean);
        if (modoDe(paso) === 'iguales' && unidadesDe(paso) > 1 && elegidos.length) {
          return `Las ${unidadesDe(paso)} de ${nombreSabor(paso.pool, elegidos[0])}`;
        }
        return elegidos.map(id => nombreSabor(paso.pool, id)).join(' · ');
      }
      if (paso.tipo === 'bebida') {
        const textos = estado.bebidas.map(b => textoBebida(paso, b));
        return modoDe(paso) === 'iguales' ? textos[0] || '' : textos.join(' · ');
      }
      return '';
    }

    // Sin sabor la ranura sigue pendiente aunque ya tenga temperatura: si
    // devolviera " · helada" se pintaría como llena.
    function textoBebida(paso, b) {
      if (!b || !b.saborId) return '';
      const temp = TEMPERATURAS.find(t => t.valor === b.temperatura);
      return nombreSabor(paso.pool, b.saborId) + (temp ? ` · ${temp.label.toLowerCase()}` : '');
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
        const idx = estado[paso.id].findIndex((v, i) => i < unidadesDe(paso) && !v);
        if (idx === -1) return '';
        if (modoDe(paso) === 'iguales' || unidadesDe(paso) === 1) return 'elige el sabor';
        return `falta ${etiquetaRanura(paso, idx).toLowerCase()}`;
      }
      if (paso.tipo === 'bebida') {
        const varias = unidadesDe(paso) > 1 && modoDe(paso) === 'distintas';
        for (let i = 0; i < unidadesDe(paso); i++) {
          const b = estado.bebidas[i];
          const suf = varias ? ` de la bebida ${i + 1}` : '';
          if (!b || !b.saborId) return `falta el sabor${suf}`;
          if (!b.temperatura) return `falta la temperatura${suf}`;
        }
        return '';
      }
      return '';
    }

    function etiquetaRanura(paso, idx) {
      return `${paso.prefijo || 'Unidad'} ${idx + 1}`;
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
          return { ok: false, motivo: `${paso.titulo}: ${faltaEnPaso(paso)}` };
        }
        if (paso.tipo === 'multi' && modoDe(paso) === 'distintas') {
          const idx = estado[paso.id].findIndex((v, i) => i < unidadesDe(paso) && !v);
          if (idx !== -1) {
            return { ok: false, motivo: `Elige la ${etiquetaRanura(paso, idx).toLowerCase()} para continuar` };
          }
        }
        return { ok: false, motivo: `Falta elegir: ${paso.titulo.toLowerCase()}` };
      }
      return { ok: true, motivo: '' };
    }

    // ===== PRECIO =====
    function comboConTamanos() {
      const c = estado.spec.combo;
      return !!(c && c.tamanos && c.tamanos.length);
    }

    function precioBase() {
      const spec = estado.spec;
      if (spec.kind === 'combo') {
        if (comboConTamanos()) {
          const t = spec.combo.tamanos.find(x => x.tamano_id === estado.tamanoId);
          return t ? parseFloat(t.precio) : 0;
        }
        return parseFloat(spec.combo.precio_fijo || 0);
      }
      if (spec.kind === 'pizza') return parseFloat(spec.tamano.precio_base || 0);
      return parseFloat(spec.producto.precio || 0);
    }

    // El precio nunca muestra $0.00 cuando ya hay tamaño: parte del base y el
    // servidor sólo lo refina con los recargos de sabor premium.
    function actualizarPrecio() {
      estado.precioUnitario = precioBase();
      pintarPrecio();

      // Solo pizza y combos con tamaño necesitan al servidor: ahí el recargo
      // por sabor premium depende del tamaño y no se puede calcular aquí.
      const spec = estado.spec;
      const necesitaServidor = (spec.kind === 'pizza' || (spec.kind === 'combo' && comboConTamanos()))
        && estado.tamanoId && estado.sabor1
        && (estado.modo === 'unico' || estado.sabor2);
      if (!necesitaServidor) return;

      const token = ++peticionPrecio;
      const body = new FormData();
      body.append('tamano_id', estado.tamanoId);
      body.append('sabor_1_id', estado.sabor1);
      body.append('sabor_2_id', estado.modo === 'mitades' ? estado.sabor2 : '');
      if (spec.kind === 'combo') body.append('combo_id', spec.combo.id);

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

    // "2 porciones · 4 alitas · 2 bebidas". Vacío si ningún grupo repite
    // unidades: ahí la cabecera sigue contando pasos, que es más informativo.
    function descripcionUnidades() {
      const partes = pasos
        .filter(p => unidadesDe(p) > 1)
        .map(p => p.corto || p.titulo.toLowerCase());
      return partes.length ? partes.join(' · ') : '';
    }

    function pintarCabecera() {
      const resueltos = pasos.filter(pasoResuelto).length;
      const tamanoNombre = (estado.tamanoId && comboConTamanos())
        ? (estado.spec.combo.tamanos.find(t => t.tamano_id === estado.tamanoId) || {}).tamano_nombre
        : '';
      const completo = resueltos === pasos.length;
      const prefijo = tamanoNombre ? `${escapeHtml(tamanoNombre)} · ` : '';

      // Cuando el combo trae unidades repetidas, la sub-línea lo describe
      // ("2 porciones · 4 alitas · 2 bebidas") en vez de contar pasos.
      const composicion = descripcionUnidades();
      if (composicion) {
        const activo = pasos.find(p => p.id === estado.pasoActivo);
        const falta = (!completo && activo) ? faltaEnPaso(activo) : '';
        elEstado.innerHTML = prefijo + escapeHtml(composicion)
          + (falta ? ` · <strong>${escapeHtml(falta)}</strong>` : '')
          + (completo ? ' · <strong class="cmb-completo">completo</strong>' : '');
      } else {
        elEstado.innerHTML = completo
          ? prefijo + '<strong class="cmb-completo">completo</strong>'
          : prefijo + `<strong>${resueltos} de ${pasos.length} pasos</strong>`;
      }

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
      const pista = pistaActiva(paso);
      const sub = falta
        ? `${escapeHtml(pista)} · <strong>${escapeHtml(falta)}</strong>`
        : escapeHtml(pista);
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

    // ===== UNIDADES REPETIDAS · handoff_combo_duo =====
    // Un grupo con varias unidades pide UNA respuesta que cubre todas. Solo si
    // el cliente pide algo distinto se abren las ranuras, y aun así el catálogo
    // se muestra una sola vez debajo.
    function tieneInterruptor(paso) {
      return unidadesDe(paso) > 1;
    }

    function pistaActiva(paso) {
      if (!tieneInterruptor(paso)) return paso.pista;
      return modoDe(paso) === 'iguales' ? `Las ${unidadesDe(paso)} iguales` : 'Distintas';
    }

    function vistaInterruptor(paso) {
      const fila = document.createElement('div');
      fila.className = 'cmb-modo';
      [
        ['iguales', `Las ${unidadesDe(paso)} iguales`],
        ['distintas', 'Distintas'],
      ].forEach(function (m) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cmb-modo-btn' + (modoDe(paso) === m[0] ? ' cmb-modo-btn-activo' : '');
        btn.textContent = m[1];
        btn.addEventListener('click', function () {
          if (modoDe(paso) === m[0]) return;
          cambiarModoGrupo(paso, m[0]);
        });
        fila.appendChild(btn);
      });
      return fila;
    }

    // Pasar a "distintas" copia lo elegido a la ranura 1 y deja el resto
    // pendiente; volver a "iguales" conserva la ranura 1 y descarta las demás.
    function cambiarModoGrupo(paso, modo) {
      estado.modos[paso.id] = modo;
      const n = unidadesDe(paso);

      if (paso.tipo === 'multi') {
        const primero = estado[paso.id].filter(Boolean)[0] || null;
        estado[paso.id] = modo === 'iguales'
          ? Array.from({ length: n }, () => primero)
          : [primero].concat(Array.from({ length: n - 1 }, () => null));
      } else if (paso.tipo === 'bebida') {
        const primera = estado.bebidas[0] || { saborId: null, temperatura: null };
        estado.bebidas = modo === 'iguales'
          ? Array.from({ length: n }, () => ({ saborId: primera.saborId, temperatura: primera.temperatura }))
          : [primera].concat(Array.from({ length: n - 1 }, () => ({ saborId: null, temperatura: null })));
      } else if (paso.tipo === 'reparto' && modo === 'iguales') {
        const primero = estado.alitas[0];
        estado.alitas = primero ? [{ saborId: primero.saborId, cantidad: paso.total }] : [];
      }

      estado.ranuraActiva[paso.id] = 0;
      render();
    }

    function vistaRanurasUnidades(paso, valores, textoDe) {
      const fila = document.createElement('div');
      fila.className = 'cmb-ranuras' + (unidadesDe(paso) > 2 ? ' cmb-ranuras-wrap' : '');
      for (let i = 0; i < unidadesDe(paso); i++) {
        const texto = textoDe(valores[i]);
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cmb-ranura'
          + (texto ? ' cmb-ranura-llena' : ' cmb-ranura-pendiente')
          + (ranuraEnEdicion(paso) === i ? ' cmb-ranura-editando' : '');
        btn.innerHTML = `
          <span class="cmb-ranura-label">${escapeHtml(etiquetaRanura(paso, i).toUpperCase())}</span>
          <span class="cmb-ranura-valor">${texto ? escapeHtml(texto) : 'Elige abajo'}</span>`;
        btn.addEventListener('click', function () {
          estado.ranuraActiva[paso.id] = i;
          render();
        });
        fila.appendChild(btn);
      }
      return fila;
    }

    // El toque cae en la primera ranura vacía; si están todas llenas, en la que
    // el cajero haya fijado tocándola.
    function ranuraEnEdicion(paso) {
      const valores = paso.tipo === 'bebida'
        ? estado.bebidas.map(b => (b && b.saborId ? b.saborId : null))
        : estado[paso.id];
      const vacia = valores.findIndex((v, i) => i < unidadesDe(paso) && !v);
      if (vacia !== -1) return vacia;
      return estado.ranuraActiva[paso.id] || 0;
    }

    function notaUnCatalogo() {
      const nota = document.createElement('div');
      nota.className = 'cmb-nota-ayuda';
      nota.innerHTML = '<i class="fas fa-clone"></i><span>Un catálogo, no uno por unidad:'
        + ' el sabor que tocas cae en la ranura pendiente.</span>';
      return nota;
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
      estado.spec.combo.tamanos.forEach(function (t) {
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

      // Una porción individual no se parte en dos sabores: ahí el selector de
      // modo sobra y la rejilla de sabores va directa.
      if (paso.permiteMitad === false) {
        wrap.appendChild(rejillaSaboresPizza(paso));
        return wrap;
      }

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
      wrap.appendChild(rejillaSaboresPizza(paso));
      return wrap;
    }

    function rejillaSaboresPizza(paso) {
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
      return grid;
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
      wrap.className = 'cmb-cuerpo-col';

      if (tieneInterruptor(paso)) wrap.appendChild(vistaInterruptor(paso));

      // "Las 4 iguales": el catálogo directo y un toque pone las N. El reparto
      // con barra y steppers solo aparece cuando el cliente pide sabores mezclados.
      if (tieneInterruptor(paso) && modoDe(paso) === 'iguales') {
        const grid = document.createElement('div');
        grid.className = 'cmb-grid';
        (paso.pool || []).forEach(function (s) {
          const sel = estado.alitas.length === 1 && estado.alitas[0].saborId === s.id;
          const btn = botonOpcion(s.nombre, sel, '');
          btn.addEventListener('click', function () {
            estado.alitas = [{ saborId: s.id, cantidad: paso.total }];
            avanzar(paso);
          });
          grid.appendChild(btn);
        });
        wrap.appendChild(grid);
        return wrap;
      }

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
          const nombre = nombreSabor(paso.pool, a.saborId);
          fila.innerHTML = `
            <span class="cmb-punto" style="background:${colorSabor(paso, a.saborId)}"></span>
            <span class="cmb-elegido-nombre">${escapeHtml(nombre)}</span>
            <span class="cmb-mini-stepper">
              <button type="button" class="cmb-mini-btn" data-d="-1" aria-label="Quitar una de ${escapeHtml(nombre)}"><i class="fas fa-minus"></i></button>
              <input type="text" inputmode="numeric" class="cmb-mini-input" value="${a.cantidad}" maxlength="3" aria-label="Cantidad de ${escapeHtml(nombre)}">
              <button type="button" class="cmb-mini-btn" data-d="1"${asignado >= paso.total ? ' disabled' : ''} aria-label="Agregar una de ${escapeHtml(nombre)}"><i class="fas fa-plus"></i></button>
            </span>`;
          fila.querySelectorAll('.cmb-mini-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
              cambiarReparto(paso, a.saborId, parseInt(btn.dataset.d, 10));
            });
          });

          // Escribir la cantidad no puede repintar la hoja: eso destruiría el
          // input que se está usando y se perdería el foco a media cifra.
          const input = fila.querySelector('.cmb-mini-input');
          input.addEventListener('focus', function () { input.select(); });
          input.addEventListener('input', function () {
            const limpio = input.value.replace(/\D/g, '');
            if (limpio !== input.value) input.value = limpio;
            const tope = paso.total - asignadoEnOtros(a.saborId);
            const valor = Math.min(parseInt(limpio, 10) || 0, tope);
            if (limpio !== '' && String(valor) !== limpio) input.value = String(valor);
            a.cantidad = valor;
            refrescarRepartoEnVivo(paso);
          });
          input.addEventListener('blur', function () {
            // Solo repinta si el sabor debe volver a los chips: un repintado
            // en cada blur cancelaría el clic que se está haciendo en +/−.
            if (a.cantidad > 0) return;
            estado.alitas = estado.alitas.filter(x => x.saborId !== a.saborId);
            render();
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
          // Entra con 1 y no con el resto pendiente: el sabor se agrega para
          // luego repartir, no para llevarse todas las alitas de un toque.
          if (paso.total - asignadoReparto() <= 0) {
            deps.mostrarToast(`Ya repartiste las ${paso.total}: baja otro sabor primero`);
            return;
          }
          estado.alitas.push({ saborId: s.id, cantidad: 1 });
          avanzar(paso);
        });
        chips.appendChild(btn);
      });
      wrap.appendChild(chips);

      const ayuda = document.createElement('span');
      ayuda.className = 'cmb-ayuda';
      ayuda.textContent = `Toca un sabor para agregarlo y escribe cuántas van de cada uno. Hasta ${paso.maxOpciones} sabores.`;
      wrap.appendChild(ayuda);

      return wrap;
    }

    function asignadoEnOtros(saborId) {
      return estado.alitas.reduce((s, a) => s + (a.saborId === saborId ? 0 : a.cantidad), 0);
    }

    // Repinta solo lo que depende del reparto (barra, contador, sub-línea del
    // paso y pie), dejando intacto el input que el cajero está escribiendo.
    function refrescarRepartoEnVivo(paso) {
      const asignado = asignadoReparto();

      const barra = elPasos.querySelector('.cmb-barra');
      if (barra) {
        barra.innerHTML = estado.alitas.map(function (a) {
          const ancho = (a.cantidad / paso.total) * 100;
          return `<span class="cmb-barra-seg" style="width:${ancho}%;background:${colorSabor(paso, a.saborId)}"></span>`;
        }).join('');
      }

      const contador = elPasos.querySelector('.cmb-reparto-contador');
      if (contador) contador.innerHTML = `<strong>${asignado}</strong>/${paso.total}`;

      const sub = elPasos.querySelector('.cmb-activo-sub');
      if (sub) {
        const falta = faltaEnPaso(paso);
        sub.innerHTML = falta
          ? `${escapeHtml(paso.pista)} · <strong>${escapeHtml(falta)}</strong>`
          : escapeHtml(paso.pista);
      }

      elPasos.querySelectorAll('.cmb-mini-btn[data-d="1"]').forEach(function (btn) {
        btn.disabled = asignado >= paso.total;
      });

      pintarCabecera();
      pintarPie();
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
      wrap.className = 'cmb-cuerpo-col';
      const distintas = tieneInterruptor(paso) && modoDe(paso) === 'distintas';

      if (tieneInterruptor(paso)) wrap.appendChild(vistaInterruptor(paso));
      if (distintas) {
        wrap.appendChild(vistaRanurasUnidades(
          paso, estado[paso.id], id => nombreSabor(paso.pool, id),
        ));
      }

      const grid = document.createElement('div');
      grid.className = 'cmb-grid';
      (paso.pool || []).forEach(function (s) {
        const sel = distintas
          ? estado[paso.id][ranuraEnEdicion(paso)] === s.id
          : estado[paso.id].filter(Boolean)[0] === s.id;
        const btn = botonOpcion(s.nombre, sel, '');
        btn.addEventListener('click', function () {
          if (distintas) {
            const destino = ranuraEnEdicion(paso);
            estado[paso.id][destino] = s.id;
            // Deja fijada la siguiente ranura para que el toque siguiente
            // tenga destino claro cuando ya no queden vacías.
            estado.ranuraActiva[paso.id] = (destino + 1) % unidadesDe(paso);
          } else {
            // Una sola elección cubre todas las unidades del grupo.
            estado[paso.id] = Array.from({ length: unidadesDe(paso) }, () => s.id);
          }
          if (paso.id === 'porciones') actualizarPrecio();
          avanzar(paso);
        });
        grid.appendChild(btn);
      });
      wrap.appendChild(grid);

      if (distintas) wrap.appendChild(notaUnCatalogo());
      return wrap;
    }

    // La temperatura viaja en la comanda: hasta ahora se preguntaba de viva voz.
    function cuerpoBebida(paso) {
      const wrap = document.createElement('div');
      wrap.className = 'cmb-cuerpo-col';
      const distintas = tieneInterruptor(paso) && modoDe(paso) === 'distintas';

      if (tieneInterruptor(paso)) wrap.appendChild(vistaInterruptor(paso));
      if (distintas) {
        wrap.appendChild(vistaRanurasUnidades(paso, estado.bebidas, b => textoBebida(paso, b)));
      }

      // En "iguales" se edita la unidad 0 y el cambio se copia a todas; en
      // "distintas" se edita solo la ranura fijada.
      const idx = distintas ? ranuraEnEdicion(paso) : 0;
      const actual = estado.bebidas[idx];

      const aplicar = function (cambio) {
        if (distintas) {
          Object.assign(estado.bebidas[idx], cambio);
        } else {
          estado.bebidas.forEach(b => Object.assign(b, cambio));
        }
        avanzar(paso);
      };

      const labelSabor = document.createElement('span');
      labelSabor.className = 'cmb-sublabel';
      labelSabor.textContent = 'SABOR';
      wrap.appendChild(labelSabor);

      const grid = document.createElement('div');
      grid.className = 'cmb-grid';
      (paso.pool || []).forEach(function (s) {
        const btn = botonOpcion(s.nombre, actual.saborId === s.id, '');
        btn.addEventListener('click', function () { aplicar({ saborId: s.id }); });
        grid.appendChild(btn);
      });
      wrap.appendChild(grid);

      const labelTemp = document.createElement('span');
      labelTemp.className = 'cmb-sublabel';
      labelTemp.textContent = 'TEMPERATURA';
      wrap.appendChild(labelTemp);

      const temps = document.createElement('div');
      temps.className = 'cmb-temp';
      TEMPERATURAS.forEach(function (t) {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'cmb-temp-btn'
          + (actual.temperatura === t.valor ? ` cmb-temp-btn-activo-${t.valor}` : '');
        btn.innerHTML = `<i class="fas ${t.icono}"></i> ${t.label}`;
        btn.addEventListener('click', function () { aplicar({ temperatura: t.valor }); });
        temps.appendChild(btn);
      });
      wrap.appendChild(temps);

      if (distintas) wrap.appendChild(notaUnCatalogo());
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
    function abrir(spec) {
      estado = {
        spec: spec,
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
        // Todo grupo con varias unidades arranca en "iguales": casi nadie pide
        // dos porciones distintas, y quien lo hace paga un toque más.
        modos: {},
        ranuraActiva: {},
        precioUnitario: 0,
      };
      // Una pizza suelta ya trae su tamaño elegido desde la tarjeta que se tocó.
      if (spec.kind === 'pizza') estado.tamanoId = spec.tamano.id;

      pasos = construirPasos(spec);
      pasos.forEach(function (paso) {
        const n = unidadesDe(paso);
        if (paso.tipo === 'bebida') {
          estado.bebidas = Array.from({ length: n }, () => ({ saborId: null, temperatura: null }));
        } else if (paso.tipo === 'multi') {
          estado[paso.id] = Array.from({ length: n }, () => null);
        }
        estado.modos[paso.id] = 'iguales';
        estado.ranuraActiva[paso.id] = 0;
      });
      estado.pasoActivo = pasos.length ? pasos[0].id : null;
      elNombre.textContent = spec.nombre;
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
      const spec = estado.spec;
      if (spec.kind !== 'combo') return itemProductoSuelto(spec);

      const c = spec.combo;
      const partes = [];
      pasos.forEach(function (paso) {
        if (paso.id === 'tamano' || paso.id === 'pizza') return;
        const txt = resumenPaso(paso);
        // El resumen ya trae el número ("Las 2 de Peperoni"), así que la
        // etiqueta va sin él para no repetirlo en la línea del carrito.
        const base = paso.etiqueta.replace(/^\d+\s+/, '').toLowerCase();
        if (txt) partes.push(`${base.charAt(0).toUpperCase() + base.slice(1)}: ${txt}`);
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

    // Pizza suelta, porción, alitas, bebida y michelada: cada una arma el ítem
    // que ya espera el backend, pero todas se configuran en la misma hoja.
    function itemProductoSuelto(spec) {
      const base = {
        cantidad: estado.cantidad,
        observacion: estado.nota,
        _precio_unitario: estado.precioUnitario,
      };

      if (spec.kind === 'pizza') {
        const sabores = resumenPaso(pasos[0]);
        return Object.assign(base, {
          kind: 'pizza',
          tamano_id: estado.tamanoId,
          sabor_1_id: estado.sabor1,
          sabor_2_id: estado.modo === 'mitades' ? estado.sabor2 : null,
          _label: `Pizza ${spec.tamano.nombre} - ${sabores}`,
        });
      }

      const producto = spec.producto;

      if (spec.kind === 'porcion') {
        const sabor = nombreSabor(catalogo.sabores, estado.porciones[0]);
        return Object.assign(base, {
          kind: 'producto',
          producto_id: producto.id,
          // El sabor de la porción no tiene columna propia: viaja en la nota.
          observacion: [`Sabor: ${sabor}`, estado.nota].filter(Boolean).join(' · '),
          _label: `${producto.nombre} - ${sabor}`,
        });
      }

      if (spec.kind === 'producto_alitas') {
        return Object.assign(base, {
          kind: 'producto',
          producto_id: producto.id,
          alitas_sabores: estado.alitas.map(a => ({ sabor_id: a.saborId, cantidad: a.cantidad })),
          _label: `${producto.nombre} - ${resumenPaso(pasos[0])}`,
        });
      }

      if (spec.kind === 'producto_bebida') {
        const bebida = estado.bebidas[0];
        return Object.assign(base, {
          kind: 'producto',
          producto_id: producto.id,
          sabor_bebida_id: bebida.saborId,
          temperatura: bebida.temperatura,
          _label: `${producto.nombre} - ${resumenPaso(pasos[0])}`,
        });
      }

      return Object.assign(base, {
        kind: 'producto',
        producto_id: producto.id,
        sabor_bebida_id: estado.michelada[0],
        _label: `${producto.nombre} - ${resumenPaso(pasos[0])}`,
      });
    }

    return { abrir: abrir, cerrar: cerrar };
  };
}());
