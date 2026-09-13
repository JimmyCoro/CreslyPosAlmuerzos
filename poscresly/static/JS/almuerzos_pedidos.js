/* =====================================================================
   Almuerzos · Pedidos del día (pizzeria/handoff_nuevo_pedido_almuerzos)
   Lista 2A, hoja única de pedido 3A/3B/3D, agregar producto 2D y acciones
   3E. Habla con los mismos endpoints de pedidos/views.py que la pantalla
   anterior y envía el mismo payload a guardar-pedido; lo único nuevo es
   el pago Mixto (monto_efectivo).
   ===================================================================== */
(function () {
  'use strict';

  var CFG = JSON.parse(document.getElementById('alm-config').textContent);
  var PRECIOS = JSON.parse(document.getElementById('alm-precios').textContent);
  var MENU = JSON.parse(document.getElementById('alm-menu').textContent);
  window.PRECIOS = PRECIOS;
  window.carrito = [];

  var CENTAVO = 0.004;
  var MS_HOJA = 240;

  // ------------------------------------------------------------ utilidades
  function $(sel, raiz) { return (raiz || document).querySelector(sel); }
  function $$(sel, raiz) { return Array.prototype.slice.call((raiz || document).querySelectorAll(sel)); }
  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function r2(n) { return Math.round((Number(n) || 0) * 100) / 100; }
  function dinero(n) { return '$' + r2(n).toFixed(2); }
  function numero(v) {
    var n = parseFloat(String(v == null ? '' : v).replace(',', '.'));
    return isFinite(n) ? n : NaN;
  }
  function plural(n, uno, varios) { return n + ' ' + (n === 1 ? uno : varios); }

  function post(url, datos) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': CFG.csrf },
      body: new URLSearchParams(datos)
    }).then(leerJson);
  }
  function leerJson(resp) {
    return resp.json().catch(function () { return {}; }).then(function (data) {
      if (!resp.ok && data.status !== 'error') data = { status: 'error', message: 'Error ' + resp.status };
      return data;
    });
  }

  var avisoTimer = null;
  function avisar(texto, tono) {
    var el = $('#almpAviso');
    el.textContent = texto;
    el.classList.toggle('almp-aviso-error', tono === 'error');
    el.classList.add('alm-aviso-visible');
    clearTimeout(avisoTimer);
    avisoTimer = setTimeout(function () { el.classList.remove('alm-aviso-visible'); }, tono === 'error' ? 4200 : 2600);
  }

  // ------------------------------------------------------ hojas inferiores
  // Se cierran tocando el fondo, deslizando la cabecera hacia abajo o con Esc.
  var pila = [];
  var ganchosCierre = {};

  function abrirHoja(id) {
    var hoja = document.getElementById(id);
    var fondo = $('[data-fondo-de="' + id + '"]');
    if (pila.indexOf(id) !== -1) return;
    hoja._origen = document.activeElement;
    fondo.hidden = false;
    hoja.hidden = false;
    hoja.style.transform = '';
    // reflow para que la transición arranque desde abajo
    void hoja.offsetHeight;
    fondo.classList.add('alm-abierta');
    hoja.classList.add('alm-abierta');
    pila.push(id);
    document.body.classList.add('almp-hoja-abierta');
    var titulo = hoja.querySelector('.almp-hoja-titulo');
    setTimeout(function () { if (titulo) titulo.focus({ preventScroll: true }); }, 60);
  }

  function cerrarHoja(id, forzar) {
    if (pila.indexOf(id) === -1) return;
    if (!forzar && ganchosCierre[id] && ganchosCierre[id]() === false) return;
    var hoja = document.getElementById(id);
    var fondo = $('[data-fondo-de="' + id + '"]');
    hoja.classList.remove('alm-abierta');
    fondo.classList.remove('alm-abierta');
    hoja.style.transform = '';
    pila.splice(pila.indexOf(id), 1);
    if (!pila.length) document.body.classList.remove('almp-hoja-abierta');
    setTimeout(function () {
      if (pila.indexOf(id) !== -1) return;
      hoja.hidden = true;
      fondo.hidden = true;
    }, MS_HOJA);
    if (hoja._origen && document.contains(hoja._origen)) {
      try { hoja._origen.focus({ preventScroll: true }); } catch (e) { /* noop */ }
    }
  }

  $$('.alm-hoja-fondo[data-fondo-de]').forEach(function (fondo) {
    fondo.addEventListener('click', function () { cerrarHoja(fondo.getAttribute('data-fondo-de')); });
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && pila.length) { e.preventDefault(); cerrarHoja(pila[pila.length - 1]); }
  });
  $$('[data-arrastre]').forEach(function (cabeza) {
    var hoja = cabeza.closest('.alm-hoja');
    var y0 = null, dy = 0;
    cabeza.addEventListener('touchstart', function (e) {
      y0 = e.touches[0].clientY; dy = 0; hoja.style.transition = 'none';
    }, { passive: true });
    cabeza.addEventListener('touchmove', function (e) {
      if (y0 == null) return;
      dy = Math.max(0, e.touches[0].clientY - y0);
      hoja.style.transform = 'translateY(' + dy + 'px)';
    }, { passive: true });
    cabeza.addEventListener('touchend', function () {
      hoja.style.transition = '';
      if (dy > 90) {
        hoja.style.transform = '';
        cerrarHoja(hoja.id);
      } else {
        hoja.style.transform = '';
      }
      y0 = null;
    });
  });

  // =====================================================================
  // 2A · Lista de pedidos
  // =====================================================================
  var PEDIDOS = [];
  var filtro = 'todos';
  var busqueda = '';
  var modoListos = false;
  var seleccionados = new Set();
  var TIPO_POR_FILTRO = { servirse: 'Servirse', llevar: 'Llevar', reservados: 'Reservado' };
  var NOMBRE_ITEM = { Almuerzo: 'Almuerzo', Sopa: 'Sopa sola', Segundo: 'Segundo solo', Extra: 'Extra' };
  var PAGO_CORTO = { Efectivo: 'Efectivo', Transferencia: 'Transf.', Mixto: 'Mixto' };

  var lista = $('#contenedor-cards-pedidos');

  function cargarPedidos() {
    return fetch(CFG.urls.pedidos + '?tipo=todos')
      .then(leerJson)
      .then(function (data) {
        if (data.status !== 'ok') throw new Error(data.message || 'No se pudieron cargar los pedidos');
        PEDIDOS = data.pedidos || [];
        var ids = new Set(PEDIDOS.map(function (p) { return String(p.id); }));
        seleccionados.forEach(function (id) { if (!ids.has(id)) seleccionados.delete(id); });
        renderLista();
      })
      .catch(function (err) {
        lista.setAttribute('aria-busy', 'false');
        lista.innerHTML = '';
        avisar(err.message || 'No se pudieron cargar los pedidos', 'error');
      });
  }
  window.cargarPedidosExistentes = cargarPedidos;

  function pedidoPorId(id) {
    for (var i = 0; i < PEDIDOS.length; i++) if (String(PEDIDOS[i].id) === String(id)) return PEDIDOS[i];
    return null;
  }

  function chipModo(p) {
    if (p.tipo === 'Llevar') return { texto: 'LLEVAR', tono: 'azul' };
    if (p.tipo === 'Reservado') return { texto: 'RESERVA', tono: 'ambar' };
    return { texto: p.mesa ? 'MESA ' + p.mesa : 'SERVIRSE', tono: 'verde' };
  }

  function horaCorta(iso) {
    var d = new Date(iso);
    return isNaN(d) ? '' : d.toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit', hour12: false });
  }

  function textoBusqueda(p) {
    return [
      p.numero_pedido_completo, p.mesa ? 'mesa ' + p.mesa : '', p.contacto, p.observaciones_generales, p.tipo,
      (p.productos || []).map(function (x) { return x.tipo + ' ' + (x.componentes || []).join(' ') + ' ' + (x.observacion || ''); }).join(' ')
    ].join(' ').toLowerCase();
  }

  function visibles() {
    return PEDIDOS.filter(function (p) {
      if (filtro !== 'todos' && p.tipo !== TIPO_POR_FILTRO[filtro]) return false;
      return !busqueda || textoBusqueda(p).indexOf(busqueda) !== -1;
    });
  }

  function htmlCard(p) {
    var chip = chipModo(p);
    var id = String(p.id);
    var sel = seleccionados.has(id);
    var nombre = (p.contacto || '').trim();
    var segunda = '';
    if (p.tipo === 'Reservado' && p.subtipo_reservado) {
      var sub = String(p.subtipo_reservado).toLowerCase();
      segunda = '<span class="almp-modo almp-modo-' + (sub === 'llevar' ? 'azul' : 'verde') + '">' +
        (sub === 'llevar' ? 'Para llevar' : 'Servirse') + '</span>';
    }
    var filaNombre = '';
    if (nombre || segunda) {
      filaNombre = '<div class="almp-card-nombre">' +
        '<span class="almp-nombre' + (nombre ? '' : ' almp-nombre-vacio') + '">' + esc(nombre || 'Sin nombre') + '</span>' +
        segunda + '</div>';
    }
    var obs = p.observaciones_generales
      ? '<p class="almp-card-obs"><i class="bi bi-chat-left-text" aria-hidden="true"></i><span>' + esc(p.observaciones_generales) + '</span></p>'
      : '';
    var items = (p.productos || []).map(function (it) {
      var detalle = (it.componentes || []).filter(Boolean).join(' · ');
      if (it.observacion) detalle += (detalle ? ' · ' : '') + it.observacion;
      return '<li class="almp-item">' +
        '<span class="almp-item-cant">' + esc(it.cantidad) + '</span>' +
        '<span class="almp-item-textos"><span class="almp-item-nombre">' + esc(NOMBRE_ITEM[it.tipo] || it.tipo) + '</span>' +
        (detalle ? '<span class="almp-item-detalle">' + esc(detalle) + '</span>' : '') + '</span>' +
        '<span class="almp-item-precio">' + dinero(it.cantidad * it.precio_unitario) + '</span></li>';
    }).join('');
    var pagoTitulo = p.forma_pago === 'Mixto' && p.monto_efectivo != null
      ? ' title="Efectivo ' + dinero(p.monto_efectivo) + ' · Transferencia ' + dinero(p.monto_transferencia) + '"'
      : '';
    var check = modoListos
      ? '<span class="almp-check" aria-hidden="true"><i class="bi bi-check-lg"></i></span>'
      : '';

    return '<article class="almp-card pedido-card' + (sel ? ' almp-card-sel' : '') + '" data-pedido-id="' + esc(id) + '"' +
      (modoListos ? ' role="checkbox" tabindex="0" aria-checked="' + sel + '" aria-label="Pedido #' + esc(p.numero_pedido_completo) + '"' : '') + '>' +
      '<div class="almp-card-top">' + check +
        '<span class="almp-num">#' + esc(p.numero_pedido_completo) + '</span>' +
        '<span class="almp-chip almp-chip-' + chip.tono + '">' + chip.texto + '</span>' +
        '<span class="almp-spacer"></span>' +
        '<time class="almp-hora" datetime="' + esc(p.fecha_creacion) + '">' + horaCorta(p.fecha_creacion) + '</time>' +
      '</div>' + filaNombre + obs +
      '<ul class="almp-items">' + items + '</ul>' +
      '<div class="almp-pie">' +
        '<div class="almp-pie-total">' +
          '<span class="almp-total-lbl">TOTAL</span>' +
          '<span class="almp-total">' + dinero(p.total) + '</span>' +
          '<span class="almp-spacer"></span>' +
          '<span class="almp-cobrado"' + pagoTitulo + '><i class="bi bi-check2" aria-hidden="true"></i>Cobrado · ' + esc(PAGO_CORTO[p.forma_pago] || p.forma_pago) + '</span>' +
        '</div>' +
        (modoListos ? '' :
        '<div class="almp-card-acciones">' +
          '<button type="button" class="almp-card-btn btn-editar" data-accion="editar"><i class="bi bi-pencil" aria-hidden="true"></i>Editar</button>' +
          '<button type="button" class="almp-card-btn almp-card-btn-verde btn-guardar" data-accion="completar"><i class="bi bi-check2" aria-hidden="true"></i>Completar</button>' +
          '<button type="button" class="almp-card-mas" data-accion="mas" aria-label="Más acciones del pedido #' + esc(p.numero_pedido_completo) + '"><i class="bi bi-three-dots" aria-hidden="true"></i></button>' +
        '</div>') +
      '</div>' +
    '</article>';
  }

  function renderLista() {
    var vs = visibles();
    lista.setAttribute('aria-busy', 'false');
    lista.classList.toggle('almp-lista-listos', modoListos);
    lista.innerHTML = vs.map(htmlCard).join('');

    var vacio = $('#almpVacio');
    vacio.hidden = vs.length > 0;
    if (!vs.length) {
      if (busqueda) {
        $('#almpVacioTitulo').textContent = 'Sin resultados';
        $('#almpVacioTexto').textContent = 'Ningún pedido coincide con “' + busqueda + '”.';
      } else if (filtro !== 'todos') {
        $('#almpVacioTitulo').textContent = 'Nada en este filtro';
        $('#almpVacioTexto').textContent = 'Los pedidos de este tipo aparecen aquí apenas se toman.';
      } else {
        $('#almpVacioTitulo').textContent = 'Nada por entregar';
        $('#almpVacioTexto').textContent = 'Toca ＋ para tomar el primer pedido.';
      }
    }
    renderContadores();
    renderLote();
  }

  function renderContadores() {
    var c = { todos: PEDIDOS.length, servirse: 0, llevar: 0, reservados: 0 };
    var monto = 0;
    PEDIDOS.forEach(function (p) {
      monto += Number(p.total) || 0;
      if (p.tipo === 'Servirse') c.servirse++;
      else if (p.tipo === 'Llevar') c.llevar++;
      else if (p.tipo === 'Reservado') c.reservados++;
    });
    Object.keys(c).forEach(function (k) {
      var el = document.getElementById('contador-' + k);
      if (el) el.textContent = c[k];
    });
    var sub = document.getElementById('almPedSub');
    if (sub) {
      var hi = c.todos ? plural(c.todos, 'por entregar', 'por entregar') : 'nada por entregar';
      sub.innerHTML = esc(CFG.fecha) + '<strong class="pzsh-hl-' + (c.todos ? 'ambar' : 'neutro') + '">' + esc(hi) + '</strong> · ' + dinero(monto);
    }
  }
  window.actualizarContadoresTabs = renderContadores;

  // Filtros (chips del subheader)
  $$('#almPedFiltros [data-filtro]').forEach(function (chip) {
    chip.setAttribute('aria-pressed', chip.classList.contains('pzsh-chip-active') ? 'true' : 'false');
    chip.addEventListener('click', function () {
      filtro = chip.getAttribute('data-filtro');
      $$('#almPedFiltros [data-filtro]').forEach(function (c) {
        var activo = c === chip;
        c.classList.toggle('pzsh-chip-active', activo);
        c.setAttribute('aria-pressed', activo ? 'true' : 'false');
      });
      renderLista();
    });
  });

  // Búsqueda
  var cajaBuscar = $('#almpBuscar');
  var inputBuscar = $('#buscadorPedidos');
  function abrirBusqueda() {
    cajaBuscar.hidden = false;
    inputBuscar.focus();
  }
  function cerrarBusqueda() {
    cajaBuscar.hidden = true;
    inputBuscar.value = '';
    if (busqueda) { busqueda = ''; renderLista(); }
  }
  var btnBuscar = document.getElementById('almPedBuscarBtn');
  if (btnBuscar) btnBuscar.addEventListener('click', function () {
    if (cajaBuscar.hidden) abrirBusqueda(); else cerrarBusqueda();
  });
  $('#almpBuscarCerrar').addEventListener('click', cerrarBusqueda);
  inputBuscar.addEventListener('input', function () {
    busqueda = inputBuscar.value.trim().toLowerCase();
    renderLista();
  });
  inputBuscar.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !pila.length) { e.stopPropagation(); cerrarBusqueda(); }
  });

  // Clicks dentro de las cards
  lista.addEventListener('click', function (e) {
    var card = e.target.closest('.almp-card[data-pedido-id]');
    if (!card) return;
    var id = card.getAttribute('data-pedido-id');
    if (modoListos) { alternarSeleccion(id); return; }
    var btn = e.target.closest('[data-accion]');
    if (!btn) return;
    var accion = btn.getAttribute('data-accion');
    if (accion === 'editar') editarPedido(id, false, btn);
    else if (accion === 'completar') completarPedido(id, btn);
    else if (accion === 'mas') abrirAcciones(id, btn);
  });
  lista.addEventListener('keydown', function (e) {
    if (!modoListos || (e.key !== ' ' && e.key !== 'Enter')) return;
    var card = e.target.closest('.almp-card[data-pedido-id]');
    if (!card) return;
    e.preventDefault();
    alternarSeleccion(card.getAttribute('data-pedido-id'));
  });

  function quitarCard(id) {
    PEDIDOS = PEDIDOS.filter(function (p) { return String(p.id) !== String(id); });
    seleccionados.delete(String(id));
    var card = $('.almp-card[data-pedido-id="' + id + '"]', lista);
    if (card && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      card.classList.add('almp-card-saliendo');
      setTimeout(renderLista, 200);
    } else {
      renderLista();
    }
  }

  function completarPedido(id, btn) {
    var p = pedidoPorId(id);
    if (btn) { btn.disabled = true; btn.setAttribute('aria-busy', 'true'); }
    return post(CFG.urls.completar, { pedido_id: id })
      .then(function (data) {
        if (data.status !== 'ok') throw new Error(data.message || 'No se pudo completar');
        marcarPropio();
        avisar('Pedido #' + (p ? p.numero_pedido_completo : id) + ' entregado');
        quitarCard(id);
      })
      .catch(function (err) {
        if (btn) { btn.disabled = false; btn.removeAttribute('aria-busy'); }
        avisar('Error al completar: ' + err.message, 'error');
      });
  }

  // ------------------------------------------------ Modo Listos (varios)
  var tabListos = document.getElementById('almTabListos');
  var lote = $('#almpLote');
  var btnLoteOk = $('#btn-marcar-listos');

  function entrarListos() {
    modoListos = true;
    seleccionados.clear();
    if (tabListos) tabListos.setAttribute('aria-pressed', 'true');
    lote.hidden = false;
    document.body.classList.add('almp-modo-listos');
    renderLista();
  }
  function salirListos() {
    modoListos = false;
    seleccionados.clear();
    if (tabListos) tabListos.setAttribute('aria-pressed', 'false');
    lote.hidden = true;
    document.body.classList.remove('almp-modo-listos');
    renderLista();
  }
  function alternarSeleccion(id) {
    id = String(id);
    if (seleccionados.has(id)) seleccionados.delete(id); else seleccionados.add(id);
    var card = $('.almp-card[data-pedido-id="' + id + '"]', lista);
    if (card) {
      card.classList.toggle('almp-card-sel', seleccionados.has(id));
      card.setAttribute('aria-checked', seleccionados.has(id) ? 'true' : 'false');
    }
    renderLote();
  }
  function renderLote() {
    if (!modoListos) return;
    var n = seleccionados.size;
    $('#almpLoteTexto').innerHTML = n
      ? '<strong>' + plural(n, 'pedido elegido', 'pedidos elegidos') + '</strong>'
      : 'Toca los pedidos que ya se entregaron';
    btnLoteOk.disabled = n === 0;
    btnLoteOk.textContent = n ? 'Marcar ' + n + ' listo' + (n === 1 ? '' : 's') : 'Marcar listos';
    var vs = visibles();
    var todos = vs.length > 0 && vs.every(function (p) { return seleccionados.has(String(p.id)); });
    $('#btn-seleccionar-todos').textContent = todos ? 'Ninguno' : 'Todos';
    if (tabListos) {
      var badge = tabListos.querySelector('.almtb-badge');
      if (n && !badge) { badge = document.createElement('span'); badge.className = 'almtb-badge'; tabListos.appendChild(badge); }
      if (badge) { if (n) badge.textContent = n; else badge.remove(); }
    }
  }
  if (tabListos) tabListos.addEventListener('click', function () { if (modoListos) salirListos(); else entrarListos(); });
  $('#almpLoteSalir').addEventListener('click', salirListos);
  $('#btn-seleccionar-todos').addEventListener('click', function () {
    var vs = visibles();
    var todos = vs.length > 0 && vs.every(function (p) { return seleccionados.has(String(p.id)); });
    vs.forEach(function (p) { if (todos) seleccionados.delete(String(p.id)); else seleccionados.add(String(p.id)); });
    renderLista();
  });
  btnLoteOk.addEventListener('click', function () {
    var ids = Array.from(seleccionados);
    if (!ids.length) return;
    btnLoteOk.disabled = true;
    btnLoteOk.setAttribute('aria-busy', 'true');
    fetch(CFG.urls.completarVarios, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CFG.csrf },
      body: JSON.stringify({ pedido_ids: ids })
    }).then(leerJson).then(function (data) {
      if (data.status !== 'ok') throw new Error(data.message || 'No se pudieron marcar');
      marcarPropio();
      avisar(plural(ids.length, 'pedido entregado', 'pedidos entregados'));
      salirListos();
      return cargarPedidos();
    }).catch(function (err) {
      avisar('Error: ' + err.message, 'error');
    }).then(function () {
      btnLoteOk.removeAttribute('aria-busy');
      renderLote();
    });
  });

  // =====================================================================
  // 3A · Hoja única de pedido
  // =====================================================================
  var P = null;

  function estadoInicial() {
    return {
      modo: 'nuevo',           // nuevo | editar | agregar
      pedidoId: null,
      numero: '',
      tipo: 'Servirse',
      subtipo: 'servirse',
      mesa: '',
      nombre: '',
      obs: '',
      forma: '',
      recibe: '',
      efectivo: '',
      transferencia: '',
      tocado: { efectivo: false, transferencia: false },
      totalPrevio: 0,
      guardando: false
    };
  }

  function totalCarrito() {
    return r2(window.carrito.reduce(function (s, it) { return s + it.cantidad * it.precio_unitario; }, 0));
  }
  // Monto que reparte el pago mixto: el pedido completo (al agregar
  // productos, lo ya cobrado + lo nuevo).
  function totalReparto() {
    return r2(totalCarrito() + (P.modo === 'agregar' ? P.totalPrevio : 0));
  }
  function porAsignar() {
    var ef = numero(P.efectivo), tr = numero(P.transferencia);
    return r2(totalReparto() - (isNaN(ef) ? 0 : ef) - (isNaN(tr) ? 0 : tr));
  }

  // Puerta única: alimenta el botón, la línea bajo él y la sub-línea.
  function faltantes() {
    var f = [];
    var cliente = P.modo !== 'agregar'; // al agregar, el cliente no se toca
    if (cliente && P.tipo === 'Servirse' && !P.mesa) f.push({ clave: 'mesa', bloque: 'almpBloqueCliente', linea: 'Elige la mesa', sub: 'falta la mesa' });
    if (cliente && P.tipo !== 'Servirse' && !P.nombre.trim()) f.push({ clave: 'nombre', bloque: 'almpBloqueCliente', linea: 'Escribe el nombre o teléfono', sub: 'falta el nombre' });
    if (!window.carrito.length) f.push({ clave: 'productos', bloque: 'almpBloqueProductos', linea: 'Agrega al menos un plato', sub: P.modo === 'agregar' ? 'falta agregar platos' : 'faltan los platos' });
    if (!P.forma) f.push({ clave: 'pago', bloque: 'almpBloquePago', linea: 'Elige efectivo, transferencia o mixto', sub: 'falta la forma de pago' });
    if (P.forma === 'Mixto') {
      var ef = numero(P.efectivo), tr = numero(P.transferencia), pa = porAsignar();
      if ((!isNaN(ef) && ef < 0) || (!isNaN(tr) && tr < 0)) {
        f.push({ clave: 'reparto', bloque: 'almpBloquePago', linea: 'Los montos no pueden ser negativos', sub: 'reparto inválido' });
      } else if (pa > CENTAVO) {
        f.push({ clave: 'reparto', bloque: 'almpBloquePago', linea: 'Asigna los ' + dinero(pa) + ' que faltan entre efectivo y transferencia', sub: 'faltan ' + dinero(pa) + ' por asignar' });
      } else if (pa < -CENTAVO) {
        f.push({ clave: 'reparto', bloque: 'almpBloquePago', linea: 'Sobran ' + dinero(-pa) + ': el reparto supera el total', sub: 'sobran ' + dinero(-pa) + ' en el reparto' });
      }
    }
    return f;
  }

  var hoja = $('#almpHojaPedido');
  var selMesa = $('#mesa');
  var inNombre = $('#almpNombre');
  var inObs = $('#observaciones_generales');
  var inRecibe = $('#almpRecibe');
  var inMixEf = $('#almpMixtoEfectivo');
  var inMixTr = $('#almpMixtoTransf');

  function render() {
    renderCliente();
    renderCarrito();
    renderPago();
    renderEstado();
  }

  function renderCliente() {
    $$('#tipoPedidoTabs [data-tipo]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-tipo') === P.tipo ? 'true' : 'false');
    });
    var esServirse = P.tipo === 'Servirse';
    $('#almpSubtipo').hidden = P.tipo !== 'Reservado';
    $$('#almpSubtipo [data-subtipo]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-subtipo') === P.subtipo ? 'true' : 'false');
    });
    selMesa.disabled = !esServirse;
    $('#almpCampoMesa').classList.toggle('almp-campo-off', !esServirse);
    if (selMesa.value !== String(P.mesa || '')) selMesa.value = esServirse ? (P.mesa || '') : '';
    inNombre.placeholder = esServirse ? 'Nombre (opcional)' : 'Nombre o teléfono';
    if (inNombre.value !== P.nombre) inNombre.value = P.nombre;
    if (inObs.value !== P.obs) inObs.value = P.obs;

    var meta = $('#almpClienteMeta');
    var texto, tono = 'neutro';
    if (esServirse) texto = P.mesa ? 'Mesa ' + P.mesa + ' · servirse' : 'Servirse';
    else if (P.tipo === 'Llevar') { texto = 'Para llevar'; tono = 'azul'; }
    else { texto = 'Reserva · ' + (P.subtipo === 'llevar' ? 'para llevar' : 'servirse aquí'); tono = 'ambar'; }
    if (P.nombre.trim()) texto += ' · ' + P.nombre.trim();
    meta.textContent = texto;
    meta.className = 'almp-bloque-meta almp-meta-' + tono;

    var bloqueado = P.modo === 'agregar';
    $$('#almpBloqueCliente button, #almpBloqueCliente input, #almpBloqueCliente select').forEach(function (el) {
      if (el === selMesa) { el.disabled = bloqueado || !esServirse; return; }
      el.disabled = bloqueado;
    });
    $('#almpBloqueCliente').classList.toggle('almp-bloque-bloqueado', bloqueado);
  }

  function renderCarrito() {
    var ul = $('#resumenCarrito');
    var platos = window.carrito.reduce(function (s, it) { return s + it.cantidad; }, 0);
    $('#almpProductosMeta').textContent = platos ? plural(platos, 'plato', 'platos') : '';
    if (!window.carrito.length) {
      ul.innerHTML = '<li class="almp-carrito-vacio">' +
        (P.modo === 'agregar' ? 'Elige lo que se suma al pedido.' : 'Aún no hay platos. Agrégalos con los botones de abajo.') + '</li>';
      return;
    }
    ul.innerHTML = window.carrito.map(function (it, i) {
      var detalle = (it.componentes || []).filter(Boolean).join(' · ');
      return '<li class="almp-linea resumen-item" data-tipo="' + esc(it.tipo) + '" data-componentes="' + esc((it.componentes || []).join('|')) + '">' +
        '<div class="almp-linea-textos">' +
          '<span class="almp-linea-nombre">' + esc(NOMBRE_ITEM[it.tipo] || it.tipo) + '</span>' +
          (detalle ? '<span class="almp-linea-detalle">' + esc(detalle) + '</span>' : '') +
          (it.observacion ? '<span class="almp-linea-obs"><i class="bi bi-chat-left-text" aria-hidden="true"></i>' + esc(it.observacion) + '</span>' : '') +
        '</div>' +
        '<div class="almp-stepper" role="group" aria-label="Cantidad de ' + esc(NOMBRE_ITEM[it.tipo] || it.tipo) + '">' +
          '<button type="button" class="almp-step btn-restar" data-linea="' + i + '" data-delta="-1" aria-label="' + (it.cantidad === 1 ? 'Quitar' : 'Uno menos') + '">' +
            '<i class="bi ' + (it.cantidad === 1 ? 'bi-trash3' : 'bi-dash-lg') + '" aria-hidden="true"></i></button>' +
          '<span class="almp-step-n cantidad-producto">' + it.cantidad + '</span>' +
          '<button type="button" class="almp-step btn-sumar" data-linea="' + i + '" data-delta="1" aria-label="Uno más"><i class="bi bi-plus-lg" aria-hidden="true"></i></button>' +
        '</div>' +
        '<span class="almp-linea-precio resumen-precio">' + dinero(it.cantidad * it.precio_unitario) + '</span>' +
      '</li>';
    }).join('');
  }

  function renderPago() {
    var total = totalCarrito();
    var agregar = P.modo === 'agregar';
    $$('#almpBloquePago [data-forma-pago]').forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-forma-pago') === P.forma ? 'true' : 'false');
      b.disabled = agregar;
    });

    // Efectivo
    var ef = $('#almpEfectivo');
    ef.hidden = P.forma !== 'Efectivo' || total <= 0;
    if (!ef.hidden) {
      if (document.activeElement !== inRecibe) inRecibe.value = P.recibe;
      var recibe = numero(P.recibe);
      var caja = $('#almpVueltoCaja');
      var lbl = $('#almpVueltoLbl');
      var val = $('#almpVuelto');
      caja.classList.remove('almp-monto-falta', 'almp-monto-ok');
      if (isNaN(recibe)) { lbl.textContent = 'VUELTO'; val.textContent = '—'; }
      else if (recibe + CENTAVO < total) { lbl.textContent = 'FALTA'; val.textContent = dinero(total - recibe); caja.classList.add('almp-monto-falta'); }
      else { lbl.textContent = 'VUELTO'; val.textContent = dinero(recibe - total); caja.classList.add('almp-monto-ok'); }

      var billetes = [total];
      [5, 10, 20].forEach(function (b) { if (b > total + CENTAVO && billetes.length < 3) billetes.push(b); });
      if (billetes.length < 3) billetes.push(Math.ceil((total + 0.01) / 10) * 10 + 10);
      var atajos = $('#almpAtajosBillete');
      var firma = billetes.join('|');
      if (atajos.getAttribute('data-firma') !== firma) {
        atajos.setAttribute('data-firma', firma);
        atajos.innerHTML = billetes.map(function (b, i) {
          return '<button type="button" class="almp-atajo" data-billete="' + b + '" aria-pressed="false"' +
            (i === 0 ? ' aria-label="Pago exacto ' + dinero(b) + '"' : '') + '>' + (i === 0 ? dinero(b) : '$' + b) + '</button>';
        }).join('') + '<button type="button" class="almp-atajo" data-billete="otro">Otro</button>';
      }
      $$('[data-billete]', atajos).forEach(function (b) {
        var v = b.getAttribute('data-billete');
        if (v !== 'otro') b.setAttribute('aria-pressed', !isNaN(recibe) && Math.abs(Number(v) - recibe) <= CENTAVO ? 'true' : 'false');
      });
    }

    // Mixto
    var mx = $('#almpMixto');
    mx.hidden = P.forma !== 'Mixto';
    if (!mx.hidden) {
      if (document.activeElement !== inMixEf) inMixEf.value = P.efectivo;
      if (document.activeElement !== inMixTr) inMixTr.value = P.transferencia;
      var pa = porAsignar();
      var resto = $('#almpPorAsignar');
      resto.classList.toggle('almp-reparto-ok', Math.abs(pa) <= CENTAVO);
      $('#almpPorAsignarLbl').textContent = Math.abs(pa) <= CENTAVO ? 'REPARTO COMPLETO' : (pa > 0 ? 'POR ASIGNAR' : 'SOBRA');
      $('#almpPorAsignarValor').textContent = Math.abs(pa) <= CENTAVO ? dinero(totalReparto()) : dinero(Math.abs(pa));
    }

    // Meta del bloque
    var meta = $('#almpPagoMeta');
    var tono = 'verde', texto;
    if (!P.forma) {
      tono = 'rojo';
      texto = 'obligatoria · se cobra al tomar el pedido';
    } else if (P.forma === 'Mixto') {
      var completo = Math.abs(porAsignar()) <= CENTAVO;
      tono = completo ? 'verde' : 'rojo';
      texto = completo ? 'mixto · reparto completo'
        : 'asignado ' + dinero(totalReparto() - porAsignar()) + ' de ' + dinero(totalReparto());
    } else {
      var rc = numero(P.recibe);
      texto = P.forma.toLowerCase();
      if (P.forma === 'Efectivo' && !isNaN(rc) && rc + CENTAVO >= total) texto += ' · vuelto ' + dinero(rc - total);
      if (agregar) { texto = 'se mantiene ' + texto; tono = 'suave'; }
    }
    meta.textContent = texto;
    meta.className = 'almp-bloque-meta almp-meta-' + tono;
  }

  function renderEstado() {
    var total = totalCarrito();
    var f = faltantes();
    var listo = f.length === 0;

    $('#almpPedTotal').textContent = dinero(total);
    var titulo = P.modo === 'nuevo' ? 'Nuevo pedido' : (P.modo === 'agregar' ? 'Agregar a #' : 'Pedido #') + P.numero;
    $('#almpPedTitulo').textContent = titulo;

    var pre = P.modo === 'agregar' ? 'Ya cobrado ' + dinero(P.totalPrevio) + ' · ' : (P.modo === 'editar' ? 'Editando · ' : '');
    $('#almpPedSub').innerHTML = esc(pre) + '<strong class="almp-hl-' + (listo ? 'verde' : 'rojo') + '">' +
      esc(listo ? (P.modo === 'nuevo' ? 'listo para cobrar' : 'listo para guardar') : f[0].sub) + '</strong>';

    var btn = $('#almpGuardar');
    var textos = { nuevo: 'Cobrar e imprimir', editar: 'Guardar e imprimir', agregar: 'Agregar e imprimir' };
    $('#almpGuardarTexto').textContent = textos[P.modo];
    $('#almpGuardarMonto').textContent = dinero(total);
    btn.setAttribute('aria-disabled', listo ? 'false' : 'true');
    $('#almpGuardarSinTicket').setAttribute('aria-disabled', listo ? 'false' : 'true');

    var linea = $('#almpPedLinea');
    linea.classList.toggle('almp-pie-linea-falta', !listo);
    if (!listo) linea.textContent = f[0].linea;
    else if (P.modo === 'agregar') linea.textContent = 'La cocina recibe solo lo agregado';
    else if (P.modo === 'editar') linea.textContent = 'Reimprime la comanda con los cambios';
    else linea.textContent = 'Imprime la comanda · el pedido entra como cobrado';
  }

  // ---- eventos de la hoja
  $$('#tipoPedidoTabs [data-tipo]').forEach(function (b) {
    b.addEventListener('click', function () {
      P.tipo = b.getAttribute('data-tipo');
      if (P.tipo !== 'Servirse') P.mesa = '';
      render();
    });
  });
  $$('#almpSubtipo [data-subtipo]').forEach(function (b) {
    b.addEventListener('click', function () { P.subtipo = b.getAttribute('data-subtipo'); render(); });
  });
  selMesa.addEventListener('change', function () { P.mesa = selMesa.value; render(); });
  inNombre.addEventListener('input', function () { P.nombre = inNombre.value; renderCliente(); renderEstado(); });
  inObs.addEventListener('input', function () { P.obs = inObs.value; });

  $('#resumenCarrito').addEventListener('click', function (e) {
    var b = e.target.closest('[data-linea]');
    if (!b) return;
    var i = Number(b.getAttribute('data-linea'));
    var it = window.carrito[i];
    if (!it) return;
    it.cantidad += Number(b.getAttribute('data-delta'));
    if (it.cantidad <= 0) window.carrito.splice(i, 1);
    alCambiarTotal();
  });

  $$('#almpBloquePago [data-forma-pago]').forEach(function (b) {
    b.addEventListener('click', function () {
      P.forma = b.getAttribute('data-forma-pago');
      if (P.forma === 'Mixto' && !P.tocado.efectivo && !P.tocado.transferencia) {
        P.efectivo = ''; P.transferencia = '';
      }
      render();
    });
  });

  inRecibe.addEventListener('input', function () { P.recibe = inRecibe.value; renderPago(); renderEstado(); });
  $('#almpAtajosBillete').addEventListener('click', function (e) {
    var b = e.target.closest('[data-billete]');
    if (!b) return;
    if (b.getAttribute('data-billete') === 'otro') { P.recibe = ''; renderPago(); inRecibe.focus(); return; }
    P.recibe = r2(b.getAttribute('data-billete')).toFixed(2);
    renderPago(); renderEstado();
  });

  // Mixto: se escribe una parte y la otra se completa sola mientras no la
  // haya tocado el cajero; si tocó las dos, "por asignar" dice la diferencia.
  function alEscribirMixto(campo, input) {
    var otro = campo === 'efectivo' ? 'transferencia' : 'efectivo';
    P[campo] = input.value;
    P.tocado[campo] = input.value.trim() !== '';
    var v = numero(input.value);
    if (!P.tocado[otro]) P[otro] = isNaN(v) ? '' : Math.max(r2(totalReparto() - v), 0).toFixed(2);
    renderPago(); renderEstado();
  }
  inMixEf.addEventListener('input', function () { alEscribirMixto('efectivo', inMixEf); });
  inMixTr.addEventListener('input', function () { alEscribirMixto('transferencia', inMixTr); });
  // Al salir del campo, el monto queda con dos decimales.
  [[inMixEf, 'efectivo'], [inMixTr, 'transferencia'], [inRecibe, 'recibe']].forEach(function (par) {
    par[0].addEventListener('blur', function () {
      var v = numero(P[par[1]]);
      if (!isNaN(v)) P[par[1]] = r2(v).toFixed(2);
      renderPago();
    });
  });
  $('#almpRestoEfectivo').addEventListener('click', function () {
    var tr = numero(P.transferencia);
    P.efectivo = Math.max(r2(totalReparto() - (isNaN(tr) ? 0 : tr)), 0).toFixed(2);
    if (isNaN(tr)) P.transferencia = '0.00';
    P.tocado.efectivo = P.tocado.transferencia = true;
    renderPago(); renderEstado();
  });
  $('#almpRestoTransf').addEventListener('click', function () {
    var ef = numero(P.efectivo);
    P.transferencia = Math.max(r2(totalReparto() - (isNaN(ef) ? 0 : ef)), 0).toFixed(2);
    if (isNaN(ef)) P.efectivo = '0.00';
    P.tocado.efectivo = P.tocado.transferencia = true;
    renderPago(); renderEstado();
  });

  function alCambiarTotal() {
    if (P.forma === 'Mixto') {
      var total = totalReparto();
      if (P.tocado.efectivo && !P.tocado.transferencia) {
        var e = numero(P.efectivo); P.transferencia = isNaN(e) ? '' : Math.max(r2(total - e), 0).toFixed(2);
      } else if (P.tocado.transferencia && !P.tocado.efectivo) {
        var t = numero(P.transferencia); P.efectivo = isNaN(t) ? '' : Math.max(r2(total - t), 0).toFixed(2);
      }
    }
    render();
  }

  // ---- abrir en sus tres modos
  function limpiarFormularioPedido() {
    P = estadoInicial();
    window.carrito = [];
    window.pedidoEditando = null;
    window.pedidoAgregandoProductos = null;
    render();
  }
  window.limpiarFormularioPedido = limpiarFormularioPedido;

  function nuevoPedido() {
    if (modoListos) salirListos();
    limpiarFormularioPedido();
    $('#almpPedCuerpo').scrollTop = 0;
    abrirHoja('almpHojaPedido');
  }

  function itemDesdeServidor(prod) {
    return {
      tipo: prod.tipo,
      componentes: (prod.componentes || []).filter(Boolean),
      cantidad: Number(prod.cantidad) || 1,
      precio_unitario: Number(prod.precio_unitario) || 0,
      observacion: prod.observacion || '',
      sopa_id: prod.sopa_id || null,
      segundo_id: prod.segundo_id || null,
      jugo_id: prod.jugo_id || null,
      // El servidor identifica los extras por extras_ids al editar
      extras_ids: prod.tipo === 'Extra' ? String(prod.extras_ids || prod.extra_id || '') : null
    };
  }

  function editarPedido(id, soloAgregar, origen, enfocarPago) {
    if (origen) { origen.disabled = true; origen.setAttribute('aria-busy', 'true'); }
    return fetch(CFG.urls.pedido.replace(/0\/?$/, id + '/'))
      .then(leerJson)
      .then(function (data) {
        if (data.status !== 'ok') throw new Error(data.message || 'No se pudo cargar el pedido');
        var ped = data.pedido;
        var enLista = pedidoPorId(id);
        P = estadoInicial();
        P.modo = soloAgregar ? 'agregar' : 'editar';
        P.pedidoId = String(ped.id);
        P.numero = ped.numero_pedido_completo;
        P.tipo = ped.tipo;
        P.subtipo = (ped.subtipo_reservado || 'servirse').toLowerCase();
        P.mesa = ped.mesa ? String(ped.mesa) : '';
        P.nombre = ped.contacto || '';
        P.obs = ped.observaciones_generales || '';
        P.forma = ped.forma_pago || '';
        P.totalPrevio = Number(enLista ? enLista.total : ped.total) || 0;
        if (P.forma === 'Mixto' && ped.monto_efectivo != null) {
          P.efectivo = r2(ped.monto_efectivo).toFixed(2);
          P.transferencia = r2(ped.monto_transferencia).toFixed(2);
          P.tocado = { efectivo: true, transferencia: soloAgregar };
        }
        if (soloAgregar) {
          window.carrito = [];
          window.pedidoEditando = null;
          window.pedidoAgregandoProductos = P.pedidoId;
        } else {
          window.carrito = (ped.productos || []).map(itemDesdeServidor);
          window.pedidoEditando = P.pedidoId;
          window.pedidoAgregandoProductos = null;
        }
        render();
        var cuerpo = $('#almpPedCuerpo');
        cuerpo.scrollTop = 0;
        abrirHoja('almpHojaPedido');
        if (enfocarPago) setTimeout(function () { $('#almpBloquePago').scrollIntoView({ block: 'start', behavior: 'smooth' }); }, MS_HOJA);
      })
      .catch(function (err) { avisar('Error al cargar el pedido: ' + err.message, 'error'); })
      .then(function () { if (origen) { origen.disabled = false; origen.removeAttribute('aria-busy'); } });
  }

  // Cerrar con productos sin guardar: se pregunta, como antes.
  ganchosCierre.almpHojaPedido = function () {
    if (P.guardando) return false;
    if (!window.carrito.length) { limpiarFormularioPedido(); return true; }
    if (window.confirm('¿Deseas guardar los cambios del pedido?')) {
      guardarPedidoFrontend(true);
      return false;
    }
    limpiarFormularioPedido();
    return true;
  };

  function mostrarFaltante(f) {
    var bloque = document.getElementById(f.bloque);
    bloque.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    bloque.classList.remove('almp-bloque-flash');
    void bloque.offsetWidth;
    bloque.classList.add('almp-bloque-flash');
    var foco = { mesa: selMesa, nombre: inNombre, reparto: inMixEf }[f.clave];
    if (foco && !foco.disabled) setTimeout(function () { foco.focus({ preventScroll: true }); }, 250);
  }

  function guardarPedidoFrontend(conImpresion) {
    if (window._guardandoPedido) return;
    var f = faltantes();
    if (f.length) { mostrarFaltante(f[0]); return; }

    var esAgregar = P.modo === 'agregar';
    var datos = {
      tipo_pedido: P.tipo,
      forma_pago: P.forma,
      mesa: P.tipo === 'Servirse' ? P.mesa : '',
      cliente: P.nombre.trim(),
      subtipo_reservado: P.subtipo,
      observaciones_generales: P.obs,
      productos_carrito: JSON.stringify(window.carrito),
      pedido_id: P.pedidoId || '',
      es_agregar_productos: esAgregar ? 'true' : 'false',
      imprimir: conImpresion ? 'true' : 'false'
    };
    if (P.forma === 'Mixto') datos.monto_efectivo = r2(numero(P.efectivo) || 0).toFixed(2);

    window._guardandoPedido = true;
    P.guardando = true;
    var btns = [$('#almpGuardar'), $('#almpGuardarSinTicket')];
    btns.forEach(function (b) { b.disabled = true; });
    (conImpresion ? btns[0] : btns[1]).setAttribute('aria-busy', 'true');

    post(CFG.urls.guardar, datos)
      .then(function (data) {
        if (data.status !== 'ok') throw new Error(data.message || 'Error desconocido');
        marcarPropio();
        window.ultimoPedidoId = data.pedido_data && data.pedido_data.id;
        P.guardando = false;
        window.carrito = [];
        cerrarHoja('almpHojaPedido', true);
        limpiarFormularioPedido();
        avisar(data.message || 'Pedido guardado');
        actualizarCantidades();
        return cargarPedidos();
      })
      .catch(function (err) {
        avisar('Error al guardar el pedido: ' + err.message, 'error');
        if (pila.indexOf('almpHojaPedido') === -1) abrirHoja('almpHojaPedido');
      })
      .then(function () {
        window._guardandoPedido = false;
        if (P) P.guardando = false;
        btns.forEach(function (b) { b.disabled = false; b.removeAttribute('aria-busy'); });
      });
  }
  window.guardarPedidoFrontend = guardarPedidoFrontend;

  $('#almpGuardar').addEventListener('click', function () { guardarPedidoFrontend(true); });
  $('#almpGuardarSinTicket').addEventListener('click', function () { guardarPedidoFrontend(false); });

  // =====================================================================
  // 2D · Agregar producto
  // =====================================================================
  var PROD = null;
  var TITULOS = { almuerzo: 'Agregar almuerzo', sopa: 'Agregar sopa', segundo: 'Agregar segundo', extra: 'Agregar extra' };
  var SECCIONES = { almuerzo: ['sopa', 'segundo', 'jugo'], sopa: ['sopa', 'jugo'], segundo: ['segundo', 'jugo'], extra: ['extra'] };
  var ETQ = { sopa: 'SOPA', segundo: 'SEGUNDO', jugo: 'JUGO', extra: 'EXTRAS' };

  function estadoPorRestantes(n) {
    if (n <= 0) return 'agotado';
    if (n <= MENU.umbral) return 'por_agotarse';
    return 'disponible';
  }

  function actualizarCantidades() {
    return fetch(CFG.urls.cantidades).then(leerJson).then(function (data) {
      if (data.status !== 'ok') return;
      [['sopas', data.sopas], ['segundos', data.segundos]].forEach(function (par) {
        (par[1] || []).forEach(function (srv) {
          MENU[par[0]].forEach(function (pl) {
            if (pl.dia_id === srv.id) { pl.restantes = srv.cantidad_actual; pl.estado = estadoPorRestantes(srv.cantidad_actual); }
          });
        });
      });
      if (PROD && pila.indexOf('almpHojaProducto') !== -1) renderProducto();
    }).catch(function () { /* se queda con las cifras que ya tenía */ });
  }

  function precioBase() {
    if (PROD.tipo === 'extra') {
      return r2(MENU.extras.reduce(function (s, e) {
        return PROD.extras.has(e.id) ? s + (Number((PRECIOS.extra || {})[e.nombre]) || Number(e.precio) || 0) : s;
      }, 0));
    }
    var clave = P.tipo === 'Reservado' ? (P.subtipo === 'llevar' ? 'Llevar' : 'Servirse') : P.tipo;
    return Number((PRECIOS[PROD.tipo] || {})[clave]) || 0;
  }

  function faltaProducto() {
    var secs = SECCIONES[PROD.tipo];
    if (secs.indexOf('sopa') !== -1 && !PROD.sopa) return { sub: 'falta elegir la sopa', linea: 'Elige una sopa para poder agregarlo' };
    if (secs.indexOf('segundo') !== -1 && !PROD.segundo) return { sub: 'falta elegir el segundo', linea: 'Elige un segundo para poder agregarlo' };
    if (secs.indexOf('jugo') !== -1 && !PROD.jugo) return { sub: 'falta elegir el jugo', linea: 'Elige el jugo para poder agregarlo' };
    if (PROD.tipo === 'extra' && !PROD.extras.size) return { sub: 'elige al menos uno', linea: 'Elige al menos un extra' };
    return null;
  }

  function htmlFilaPlato(cat, pl) {
    var elegido = PROD[cat] === pl.id;
    var agotado = pl.estado === 'agotado' && !elegido;
    var cifra = agotado
      ? '<span class="almp-tag-agotado">AGOTADA</span>'
      : '<span class="almp-porciones almp-porciones-' + pl.estado + '">' + plural(pl.restantes, 'porción', 'porciones') + '</span>';
    return '<button type="button" class="almp-opcion" role="radio" aria-checked="' + elegido + '" data-cat="' + cat + '" data-id="' + pl.id + '"' + (agotado ? ' disabled' : '') + '>' +
      '<span class="almp-radio" aria-hidden="true"><i class="bi bi-check"></i></span>' +
      '<span class="almp-opcion-nombre">' + esc(pl.nombre) + '</span>' + cifra + '</button>';
  }

  function renderProducto() {
    var secs = SECCIONES[PROD.tipo];
    var html = secs.map(function (cat) {
      var elegido;
      var cuerpo;
      if (cat === 'jugo') {
        elegido = !!PROD.jugo;
        cuerpo = MENU.jugos.length
          ? '<div class="almp-jugos" role="radiogroup" aria-label="Jugo">' + MENU.jugos.map(function (j) {
              return '<button type="button" class="almp-jugo" role="radio" aria-checked="' + (PROD.jugo === j.id) + '" data-cat="jugo" data-id="' + j.id + '">' + esc(j.nombre) + '</button>';
            }).join('') + '</div>'
          : '<p class="almp-sin-opciones">No hay jugos en el menú de hoy.</p>';
      } else if (cat === 'extra') {
        elegido = PROD.extras.size > 0;
        cuerpo = MENU.extras.length
          ? '<div class="almp-opciones" role="group" aria-label="Extras">' + MENU.extras.map(function (e) {
              var on = PROD.extras.has(e.id);
              return '<button type="button" class="almp-opcion almp-opcion-multi" role="checkbox" aria-checked="' + on + '" data-cat="extra" data-id="' + e.id + '">' +
                '<span class="almp-radio almp-radio-cuadro" aria-hidden="true"><i class="bi bi-check"></i></span>' +
                '<span class="almp-opcion-nombre">' + esc(e.nombre) + '</span>' +
                '<span class="almp-opcion-precio">' + dinero((PRECIOS.extra || {})[e.nombre] != null ? PRECIOS.extra[e.nombre] : e.precio) + '</span></button>';
            }).join('') + '</div>'
          : '<p class="almp-sin-opciones">No hay extras en el catálogo.</p>';
      } else {
        var platos = MENU[cat === 'sopa' ? 'sopas' : 'segundos'];
        elegido = !!PROD[cat];
        cuerpo = platos.length
          ? '<div class="almp-opciones" role="radiogroup" aria-label="' + (cat === 'sopa' ? 'Sopa' : 'Segundo') + '">' + platos.map(function (pl) { return htmlFilaPlato(cat, pl); }).join('') + '</div>'
          : '<p class="almp-sin-opciones">No hay ' + (cat === 'sopa' ? 'sopas' : 'segundos') + ' en el menú de hoy. <a href="' + esc(CFG.urls.menu) + '">Ir al menú</a></p>';
      }
      var meta = elegido
        ? '<span class="almp-bloque-meta almp-meta-verde">' + (cat === 'extra' ? plural(PROD.extras.size, 'elegido', 'elegidos') : (cat === 'sopa' ? 'elegida' : 'elegido')) + '</span>'
        : '<span class="almp-bloque-meta almp-meta-' + (cat === 'extra' ? 'suave' : 'rojo') + '">' + (cat === 'extra' ? 'puedes elegir varios' : 'falta elegir') + '</span>';
      return '<section class="almp-bloque almp-bloque-compacto"><div class="almp-bloque-head"><h3 class="almp-etq">' + ETQ[cat] + '</h3>' + meta + '</div>' + cuerpo + '</section>';
    }).join('');

    var cuerpoEl = $('#almpProdCuerpo');
    var obsPrevio = $('#observacion-producto');
    var obsValor = obsPrevio ? obsPrevio.value : PROD.obs;
    var scroll = cuerpoEl.scrollTop;
    cuerpoEl.innerHTML = html +
      '<section class="almp-bloque almp-bloque-compacto"><div class="almp-bloque-head"><label class="almp-etq" for="observacion-producto">OBSERVACIÓN</label><span class="almp-bloque-meta almp-meta-suave">opcional</span></div>' +
      '<input type="text" class="almp-input" id="observacion-producto" placeholder="Ej: sin arroz, presa pechuga" autocomplete="off" maxlength="200" value="' + esc(obsValor) + '"></section>';
    cuerpoEl.scrollTop = scroll;

    var falta = faltaProducto();
    var partes = { almuerzo: 'Sopa, segundo y jugo', sopa: 'Sopa y jugo', segundo: 'Segundo y jugo', extra: 'Uno o varios' }[PROD.tipo];
    $('#almpProdSub').innerHTML = esc(partes) + ' · <strong class="almp-hl-' + (falta ? 'rojo' : 'verde') + '">' + esc(falta ? falta.sub : 'listo para agregar') + '</strong>';
    $('#almpProdCantidad').textContent = PROD.cantidad;
    $('#almpProdMenos').disabled = PROD.cantidad <= 1;
    $('#almpProdPrecio').textContent = dinero(precioBase() * PROD.cantidad);
    var btn = $('#btnAgregarProducto');
    btn.setAttribute('aria-disabled', falta ? 'true' : 'false');
    var linea = $('#almpProdLinea');
    linea.textContent = falta ? falta.linea : (PROD.cantidad > 1 ? 'Se agregan ' + PROD.cantidad + ' iguales' : '');
    linea.classList.toggle('almp-pie-linea-falta', !!falta);
  }

  function abrirModalProducto(tipo) {
    PROD = { tipo: tipo, sopa: null, segundo: null, jugo: null, extras: new Set(), cantidad: 1, obs: '', enviando: false };
    // Con un solo jugo (o solo Agua) no hay nada que decidir.
    if (SECCIONES[tipo].indexOf('jugo') !== -1 && MENU.jugos.length === 1) PROD.jugo = MENU.jugos[0].id;
    $('#almpProdTitulo').textContent = TITULOS[tipo];
    var obs = $('#observacion-producto'); if (obs) obs.value = '';
    $('#almpProdCuerpo').scrollTop = 0;
    renderProducto();
    abrirHoja('almpHojaProducto');
    actualizarCantidades();
  }
  window.abrirModalProducto = abrirModalProducto;

  $$('.almp-agregar [data-producto]').forEach(function (b) {
    b.addEventListener('click', function () { abrirModalProducto(b.getAttribute('data-producto')); });
  });

  $('#almpProdCuerpo').addEventListener('click', function (e) {
    var b = e.target.closest('[data-cat]');
    if (!b || b.disabled) return;
    var cat = b.getAttribute('data-cat');
    var id = Number(b.getAttribute('data-id'));
    PROD.obs = ($('#observacion-producto') || {}).value || '';
    if (cat === 'extra') { if (PROD.extras.has(id)) PROD.extras.delete(id); else PROD.extras.add(id); }
    else PROD[cat] = id;
    renderProducto();
    var mismo = $('[data-cat="' + cat + '"][data-id="' + id + '"]', $('#almpProdCuerpo'));
    if (mismo) mismo.focus({ preventScroll: true });
  });
  $('#almpProdMenos').addEventListener('click', function () { if (PROD.cantidad > 1) { PROD.cantidad--; PROD.obs = $('#observacion-producto').value; renderProducto(); } });
  $('#almpProdMas').addEventListener('click', function () { PROD.cantidad++; PROD.obs = $('#observacion-producto').value; renderProducto(); });

  function nombrePorId(lista, id) {
    for (var i = 0; i < lista.length; i++) if (lista[i].id === id) return lista[i].nombre;
    return '';
  }

  $('#btnAgregarProducto').addEventListener('click', function () {
    var btn = this;
    if (PROD.enviando) return;
    var falta = faltaProducto();
    if (falta) {
      var primera = $('#almpProdCuerpo .almp-meta-rojo');
      if (primera) primera.closest('.almp-bloque').scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      return;
    }
    var tipo = PROD.tipo;
    var observacion = ($('#observacion-producto').value || '').trim();
    var extrasIds = Array.from(PROD.extras).join(',');
    var componentes;
    var tipoProducto = { almuerzo: 'Almuerzo', sopa: 'Sopa', segundo: 'Segundo', extra: 'Extra' }[tipo];
    if (tipo === 'extra') {
      componentes = MENU.extras.filter(function (e) { return PROD.extras.has(e.id); }).map(function (e) { return e.nombre; });
    } else {
      componentes = [];
      if (PROD.sopa) componentes.push(nombrePorId(MENU.sopas, PROD.sopa));
      if (PROD.segundo) componentes.push(nombrePorId(MENU.segundos, PROD.segundo));
      if (PROD.jugo) componentes.push(nombrePorId(MENU.jugos, PROD.jugo));
    }
    var precio = precioBase();
    var cantidad = PROD.cantidad;

    PROD.enviando = true;
    btn.setAttribute('aria-busy', 'true');
    post(CFG.urls.carrito, {
      tipo: tipo,
      sopa_id: PROD.sopa || '',
      segundo_id: PROD.segundo || '',
      jugo_id: PROD.jugo || '',
      extras_ids: extrasIds,
      cantidad: cantidad,
      observacion: observacion
    }).then(function (data) {
      if (data.status !== 'ok') throw new Error(data.message || 'Error desconocido');
      var clave = componentes.join('|');
      var existente = null;
      window.carrito.forEach(function (it) { if (it.tipo === tipoProducto && (it.componentes || []).join('|') === clave) existente = it; });
      if (existente) {
        existente.cantidad += cantidad;
      } else {
        window.carrito.push({
          tipo: tipoProducto,
          componentes: componentes,
          cantidad: cantidad,
          precio_unitario: precio,
          observacion: observacion,
          sopa_id: PROD.sopa ? String(PROD.sopa) : null,
          segundo_id: PROD.segundo ? String(PROD.segundo) : null,
          jugo_id: PROD.jugo ? String(PROD.jugo) : null,
          extras_ids: tipoProducto === 'Extra' ? extrasIds : null
        });
      }
      cerrarHoja('almpHojaProducto', true);
      alCambiarTotal();
    }).catch(function (err) {
      avisar('Error al agregar: ' + err.message, 'error');
    }).then(function () {
      PROD.enviando = false;
      btn.removeAttribute('aria-busy');
    });
  });

  // =====================================================================
  // 3E · Acciones del pedido
  // =====================================================================
  var accionesId = null;
  var confirmarTimer = null;
  var btnEliminar = $('#almpEliminar');

  function textoPago(p) {
    if (p.forma_pago === 'Mixto' && p.monto_efectivo != null) {
      return 'Ahora: mixto · ' + dinero(p.monto_efectivo) + ' efectivo + ' + dinero(p.monto_transferencia) + ' transf.';
    }
    return 'Ahora: ' + String(p.forma_pago || '—').toLowerCase();
  }

  function resetEliminar() {
    clearTimeout(confirmarTimer);
    btnEliminar.classList.remove('almp-btn-riesgo-confirmar');
    btnEliminar.textContent = 'Eliminar pedido';
    btnEliminar.disabled = false;
  }

  function abrirAcciones(id, origen) {
    var p = pedidoPorId(id);
    if (!p) return;
    accionesId = String(id);
    resetEliminar();
    $('#almpAccTitulo').textContent = 'Pedido #' + p.numero_pedido_completo;
    var quien = (p.contacto || '').trim() || (p.mesa ? 'Mesa ' + p.mesa : 'Sin nombre');
    var modo = { Servirse: 'servirse', Llevar: 'llevar', Reservado: 'reserva' }[p.tipo] || p.tipo;
    $('#almpAccSub').innerHTML = esc(quien + ' · ' + modo + ' · ') + '<strong class="almp-hl-verde">cobrado ' + dinero(p.total) + '</strong>';
    $('#almpAccPagoSub').textContent = textoPago(p);
    $('#almpRiesgoTexto').textContent = 'Se borra el pedido de ' + dinero(p.total) + ' y sus porciones vuelven al menú del día. No se puede deshacer.';
    abrirHoja('almpHojaAcciones');
    if (origen) document.getElementById('almpHojaAcciones')._origen = origen;
  }

  $$('#almpHojaAcciones [data-accion]').forEach(function (b) {
    b.addEventListener('click', function () {
      var id = accionesId;
      var accion = b.getAttribute('data-accion');
      cerrarHoja('almpHojaAcciones', true);
      if (accion === 'editar') editarPedido(id, false);
      else if (accion === 'agregar') editarPedido(id, true);
      else if (accion === 'pago') editarPedido(id, false, null, true);
      else if (accion === 'completar') completarPedido(id);
    });
  });

  // Doble toque para eliminar: el primero arma, el segundo borra.
  btnEliminar.addEventListener('click', function () {
    if (!btnEliminar.classList.contains('almp-btn-riesgo-confirmar')) {
      btnEliminar.classList.add('almp-btn-riesgo-confirmar');
      btnEliminar.textContent = 'Toca otra vez para eliminar';
      confirmarTimer = setTimeout(resetEliminar, 4000);
      return;
    }
    clearTimeout(confirmarTimer);
    var id = accionesId;
    var p = pedidoPorId(id);
    btnEliminar.disabled = true;
    btnEliminar.setAttribute('aria-busy', 'true');
    post(CFG.urls.eliminar, { pedido_id: id })
      .then(function (data) {
        if (data.status !== 'ok') throw new Error(data.message || 'Error desconocido');
        marcarPropio();
        cerrarHoja('almpHojaAcciones', true);
        avisar('Pedido #' + (p ? p.numero_pedido_completo : id) + ' eliminado');
        quitarCard(id);
        actualizarCantidades();
      })
      .catch(function (err) {
        avisar('Error al eliminar el pedido: ' + err.message, 'error');
        resetEliminar();
      })
      .then(function () { btnEliminar.removeAttribute('aria-busy'); });
  });

  // =====================================================================
  // Tiempo real (ws/pedidos/): refresca la lista sin recargar la página,
  // así nunca se pierde un pedido a medio tomar.
  // =====================================================================
  var ultimoPropio = 0;
  function marcarPropio() { ultimoPropio = Date.now(); }

  var refrescoTimer = null;
  function refrescarPronto() {
    clearTimeout(refrescoTimer);
    refrescoTimer = setTimeout(function () { cargarPedidos(); actualizarCantidades(); }, 350);
  }

  function conectarSocket(intento) {
    if (!('WebSocket' in window)) return;
    var proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    var ws;
    try { ws = new WebSocket(proto + '//' + location.host + '/ws/pedidos/'); } catch (e) { return; }
    ws.onopen = function () { intento = 0; };
    ws.onmessage = function (ev) {
      var data;
      try { data = JSON.parse(ev.data); } catch (e) { return; }
      var tipos = ['pedido_creado', 'pedido_actualizado', 'pedido_eliminado', 'pedidos_marcados_completados'];
      if (tipos.indexOf(data.type) === -1) return;
      var ajeno = Date.now() - ultimoPropio > 2500;
      if (ajeno && data.type === 'pedido_creado' && data.pedido) avisar('Nuevo pedido #' + data.pedido.numero_pedido_completo);
      refrescarPronto();
    };
    ws.onclose = function () {
      var n = (intento || 0) + 1;
      if (n <= 8) setTimeout(function () { conectarSocket(n); }, Math.min(1000 * n, 8000));
    };
  }

  // ------------------------------------------------------------- arranque
  var tabNuevo = document.getElementById('almTabNuevo');
  if (tabNuevo) tabNuevo.addEventListener('click', nuevoPedido);

  limpiarFormularioPedido();
  cargarPedidos().then(function () {
    var qs = new URLSearchParams(location.search);
    if (qs.get('nuevo')) nuevoPedido();
    else if (qs.get('listos')) entrarListos();
    if (qs.get('nuevo') || qs.get('listos')) history.replaceState(null, '', location.pathname);
  });
  conectarSocket(0);
})();
