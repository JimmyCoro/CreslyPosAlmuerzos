// Configurar menú (1C) y Elegir plato (1D) · handoff_menu_del_dia.
// El estado inicial llega como JSON (menu/servicio.py::estado_configurar).
// Nada se guarda hasta "Publicar menú": así un menú a medias nunca llega a
// Pedidos. El POST vuelve a validar todo; el botón bloqueado es solo ayuda.
(function () {
  var nodoEstado = document.getElementById('almEstado');
  var main = document.getElementById('almConf');
  if (!nodoEstado || !main) return;

  var E = JSON.parse(nodoEstado.textContent);
  var cats = E.categorias;
  var recetario = E.recetario;

  var btnPublicar = document.getElementById('almPublicar');
  var lineaFalta = document.getElementById('almPublicarFalta');
  var sub = document.getElementById('almConfSub');
  var btnCopiar = document.getElementById('almCopiarAnterior');
  var aviso = document.getElementById('almAviso');

  var hoja = document.getElementById('almHoja');
  var fondo = document.getElementById('almHojaFondo');
  var hojaTitulo = document.getElementById('almHojaTitulo');
  var hojaPista = document.getElementById('almHojaPista');
  var buscar = document.getElementById('almHojaBuscar');
  var etiqueta = document.getElementById('almHojaEtiqueta');
  var listaPlatos = document.getElementById('almHojaPlatos');
  var crearAbrir = document.getElementById('almCrearAbrir');
  var crearTexto = document.getElementById('almCrearTexto');
  var crearForm = document.getElementById('almCrearForm');
  var crearNombre = document.getElementById('almCrearNombre');
  var crearError = document.getElementById('almCrearError');
  var porciones = document.getElementById('almHojaPorciones');
  var cupoInput = document.getElementById('almHojaCupo');
  var btnPoner = document.getElementById('almHojaPoner');
  var btnQuitar = document.getElementById('almHojaQuitar');

  var sucio = false;
  var enviando = false;

  // Lo ya vendido hoy de cada plato: se conserva si el plato sigue en el menú.
  var vendidosHoy = {};
  cats.forEach(function (c) {
    vendidosHoy[c.clave] = {};
    c.ranuras.forEach(function (r) { vendidosHoy[c.clave][r.plato_id] = r.vendidos; });
    c.slots = c.ranuras.slice();
    var base = Math.max(c.min, c.obligatoria ? 0 : 1);
    while (c.slots.length < base) c.slots.push(null);
  });

  // ------------------------------------------------------------ utilidades
  function el(tag, clase, texto) {
    var n = document.createElement(tag);
    if (clase) n.className = clase;
    if (texto != null) n.textContent = texto;
    return n;
  }
  function icono(nombre) {
    var i = el('i', 'bi ' + nombre);
    i.setAttribute('aria-hidden', 'true');
    return i;
  }
  function minuscula(s) { return s ? s.charAt(0).toLowerCase() + s.slice(1) : s; }
  function mayuscula(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }
  function plural(n, s, p) { return n === 1 ? s : p; }
  function normalizar(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim();
  }
  function llenas(c) { return c.slots.filter(Boolean).length; }
  function clampCupo(v) {
    var n = parseInt(String(v).replace(/\D/g, ''), 10);
    if (isNaN(n) || n < 1) n = 1;
    return Math.min(n, E.cupo_maximo);
  }
  function mostrarAviso(texto) {
    aviso.textContent = texto;
    aviso.classList.add('alm-aviso-visible');
    clearTimeout(mostrarAviso.t);
    mostrarAviso.t = setTimeout(function () { aviso.classList.remove('alm-aviso-visible'); }, 2800);
  }

  // Espejo de servicio.campos_faltantes / frase_faltantes (contar=True).
  function faltantes() {
    return cats.filter(function (c) { return c.obligatoria && llenas(c) < c.min; })
      .map(function (c) { return { cat: c, n: c.min - llenas(c) }; });
  }
  function fraseFaltantes(f) {
    if (!f.length) return '';
    var partes = f.map(function (x) { return x.n + ' ' + plural(x.n, x.cat.singular, x.cat.plural); });
    var lista = partes.length === 1 ? partes[0] : partes.slice(0, -1).join(', ') + ' y ' + partes[partes.length - 1];
    var total = f.reduce(function (a, x) { return a + x.n; }, 0);
    return (total === 1 ? 'falta ' : 'faltan ') + lista;
  }

  // --------------------------------------------------------------- render
  function render() {
    main.textContent = '';
    cats.forEach(function (c, ci) { main.appendChild(renderCategoria(c, ci)); });
    actualizarEstado();
  }

  function renderCategoria(c, ci) {
    var sec = el('section', 'alm-seccion');
    sec.setAttribute('aria-labelledby', 'almConfSec-' + c.clave);

    var head = el('div', 'alm-sec-head');
    var h = el('h2', 'alm-sec-nombre', c.nombre.toUpperCase());
    h.id = 'almConfSec-' + c.clave;
    head.appendChild(h);
    var n = llenas(c);
    var regla;
    if (!c.obligatoria) regla = el('span', 'alm-sec-meta alm-sec-meta-opcional', 'opcional');
    else if (n < c.min) regla = el('span', 'alm-sec-meta alm-sec-meta-rojo', 'obligatorio · elige ' + c.min);
    else regla = el('span', 'alm-sec-meta alm-sec-meta-listo', 'completo');
    head.appendChild(regla);
    head.appendChild(el('span', 'alm-sec-avance', c.obligatoria ? n + ' de ' + c.min : (n ? String(n) : '')));
    sec.appendChild(head);

    if (c.clave === 'jugo') {
      // El agua es una bebida más en la tarjeta, pero fija: no se elige ni se agota.
      var agua = el('div', 'alm-ranura-llena alm-ranura-fija');
      var aguaTexto = el('div', 'alm-ranura-fija-texto');
      aguaTexto.appendChild(el('span', 'alm-ranura-nombre', 'Agua'));
      aguaTexto.appendChild(el('span', 'alm-ranura-sub', 'Siempre disponible · no se configura ni se agota'));
      agua.appendChild(aguaTexto);
      agua.appendChild(el('span', 'alm-linea-etiqueta', 'SIEMPRE'));
      sec.appendChild(agua);
    }

    var primeraVacia = c.slots.indexOf(null);
    c.slots.forEach(function (r, si) {
      sec.appendChild(r ? renderLlena(c, ci, si, r) : renderVacia(c, ci, si, si === primeraVacia));
    });

    if (c.slots.length < c.max) {
      var textoAnadir = c.clave === 'segundo' ? 'Añadir un tercer segundo'
        : c.clave === 'sopa' ? 'Añadir otra sopa' : 'Añadir otro jugo';
      var anadir = el('button', 'alm-anadir');
      anadir.type = 'button';
      anadir.appendChild(icono('bi-plus-lg'));
      anadir.appendChild(el('span', null, textoAnadir));
      anadir.addEventListener('click', function () {
        c.slots.push(null);
        render();
        abrirHoja(ci, c.slots.length - 1);
      });
      sec.appendChild(anadir);
    }

    return sec;
  }

  function renderVacia(c, ci, si, siguiente) {
    var b = el('button', 'alm-ranura-vacia' + (siguiente ? ' alm-ranura-siguiente' : ''));
    b.type = 'button';
    b.dataset.slot = ci + '-' + si;
    b.appendChild(icono('bi-plus-lg'));
    b.appendChild(el('span', null, 'Elegir ' + minuscula(c.titulos[si] || c.singular)));
    b.addEventListener('click', function () { abrirHoja(ci, si); });
    return b;
  }

  function renderLlena(c, ci, si, r) {
    var card = el('div', 'alm-ranura-llena');
    var abrir = el('button', 'alm-ranura-abrir');
    abrir.type = 'button';
    abrir.dataset.slot = ci + '-' + si;
    abrir.setAttribute('aria-label', (c.titulos[si] || c.singular) + ': ' + r.nombre + '. Toca para cambiar');
    abrir.appendChild(el('span', 'alm-ranura-nombre', r.nombre));
    var subTxt = 'Toca para cambiar';
    if (c.con_cupo && r.vendidos) subTxt += ' · ' + r.vendidos + ' ' + plural(r.vendidos, 'vendida', 'vendidas');
    abrir.appendChild(el('span', 'alm-ranura-sub', subTxt));
    abrir.addEventListener('click', function () { abrirHoja(ci, si); });
    card.appendChild(abrir);

    if (c.con_cupo) card.appendChild(stepper(r, r.nombre));
    return card;
  }

  function stepper(r, nombre) {
    var wrap = el('div', 'alm-stepper');
    var menos = el('button', 'alm-step', '−');
    var mas = el('button', 'alm-step', '+');
    var cant = el('input', 'alm-step-cant');
    menos.type = mas.type = 'button';
    menos.setAttribute('aria-label', 'Una porción menos de ' + nombre);
    mas.setAttribute('aria-label', 'Una porción más de ' + nombre);
    cant.type = 'text';
    cant.inputMode = 'numeric';
    cant.maxLength = 3;
    cant.value = r.cupo;
    cant.setAttribute('aria-label', 'Porciones de ' + nombre);

    function fijar(v) {
      r.cupo = clampCupo(v);
      cant.value = r.cupo;
      menos.disabled = r.cupo <= 1;
      mas.disabled = r.cupo >= E.cupo_maximo;
      sucio = true;
    }
    menos.disabled = r.cupo <= 1;
    menos.addEventListener('click', function () { fijar(r.cupo - 1); });
    mas.addEventListener('click', function () { fijar(r.cupo + 1); });
    cant.addEventListener('input', function () { cant.value = cant.value.replace(/\D/g, ''); });
    cant.addEventListener('change', function () { fijar(cant.value); });
    cant.addEventListener('focus', function () { cant.select(); });

    wrap.appendChild(menos);
    wrap.appendChild(cant);
    wrap.appendChild(mas);
    return wrap;
  }

  function actualizarEstado() {
    var f = faltantes();
    var frase = fraseFaltantes(f);
    btnPublicar.setAttribute('aria-disabled', f.length ? 'true' : 'false');
    lineaFalta.textContent = frase ? mayuscula(frase) : 'Listo. Al publicar se puede vender el almuerzo.';
    lineaFalta.classList.toggle('alm-linea-ok', !frase);
    if (sub) {
      sub.textContent = '';
      sub.appendChild(document.createTextNode(E.fecha_texto + ' · '));
      sub.appendChild(el('strong', frase ? 'pzsh-hl-rojo' : 'pzsh-hl-verde', frase || 'listo para publicar'));
    }
  }

  // ---------------------------------------------------------------- hoja
  var H = null; // { ci, si, sel, cupo, query, origen }

  function abrirHoja(ci, si) {
    var c = cats[ci];
    var actual = c.slots[si];
    H = {
      ci: ci, si: si,
      sel: actual ? actual.plato_id : null,
      cupo: actual ? actual.cupo : E.cupo_defecto,
      query: '',
      origen: document.activeElement
    };

    hojaTitulo.textContent = c.titulos[si] || mayuscula(c.singular);
    hojaPista.textContent = '';
    hojaPista.appendChild(document.createTextNode('Del recetario.'));
    if (c.pista) {
      hojaPista.appendChild(document.createTextNode(' '));
      hojaPista.appendChild(el('strong', null, c.pista.nombre));
      hojaPista.appendChild(document.createTextNode(' se sirvió ' + c.pista.cuando + '.'));
    }
    buscar.value = '';
    buscar.placeholder = c.buscar;
    porciones.hidden = !c.con_cupo;
    cupoInput.value = H.cupo;
    cerrarCrear();

    var extra = si >= Math.max(c.min, c.obligatoria ? 0 : 1);
    btnQuitar.hidden = !(actual || extra);
    btnQuitar.textContent = actual ? 'Quitar de la ranura' : 'Quitar esta ranura';

    renderPlatos();
    actualizarPoner();

    hoja.hidden = false;
    fondo.hidden = false;
    document.body.style.overflow = 'hidden';
    requestAnimationFrame(function () {
      hoja.classList.add('alm-abierta');
      fondo.classList.add('alm-abierta');
    });
    hojaTitulo.focus();
  }

  function cerrarHoja(focoDestino) {
    if (!H) return;
    var origen = H.origen;
    H = null;
    hoja.classList.remove('alm-abierta');
    fondo.classList.remove('alm-abierta');
    document.body.style.overflow = '';
    setTimeout(function () {
      if (!H) { hoja.hidden = true; fondo.hidden = true; }
    }, 240);
    var destino = focoDestino || (origen && document.body.contains(origen) ? origen : null);
    if (destino) destino.focus();
  }

  function subPlato(c, p, ocupado) {
    if (ocupado) return 'Ya está en el menú';
    var genero = c.clave === 'sopa' ? 'Servida' : 'Servido';
    if (p.veces_mes > 0) return genero + ' ' + p.veces_mes + ' ' + plural(p.veces_mes, 'vez', 'veces') + ' este mes';
    if (p.hace_dias === 1) return genero + ' ayer';
    if (p.hace_dias != null && p.hace_dias <= 30) return 'Última vez hace ' + p.hace_dias + ' días';
    if (p.hace_dias != null) return 'Hace más de un mes';
    return 'Sin servir todavía';
  }

  function renderPlatos() {
    var c = cats[H.ci];
    var q = normalizar(H.query);
    var ocupados = {};
    c.slots.forEach(function (r, i) { if (r && i !== H.si) ocupados[r.plato_id] = true; });

    var lista = (recetario[c.clave] || []).filter(function (p) {
      return !q || normalizar(p.nombre).indexOf(q) !== -1;
    });

    etiqueta.textContent = q ? 'RESULTADOS' : 'LAS MÁS SERVIDAS';
    listaPlatos.textContent = '';
    if (!lista.length) {
      listaPlatos.appendChild(el('p', 'alm-platos-vacio',
        q ? 'No hay ' + c.plural + ' con «' + H.query.trim() + '» en el recetario.'
          : 'Todavía no hay ' + c.plural + ' en el recetario.'));
    }
    lista.forEach(function (p) {
      var ocupado = !!ocupados[p.id];
      var b = el('button', 'alm-plato');
      b.type = 'button';
      b.setAttribute('role', 'radio');
      b.setAttribute('aria-checked', H.sel === p.id ? 'true' : 'false');
      b.disabled = ocupado;
      var t = el('span', 'alm-plato-texto');
      t.appendChild(el('span', 'alm-plato-nombre', p.nombre));
      t.appendChild(el('span', 'alm-plato-sub', subPlato(c, p, ocupado)));
      b.appendChild(t);
      var radio = el('span', 'alm-plato-radio');
      radio.setAttribute('aria-hidden', 'true');
      if (H.sel === p.id) radio.appendChild(icono('bi-check-lg'));
      b.appendChild(radio);
      b.addEventListener('click', function () {
        H.sel = p.id;
        renderPlatos();
        actualizarPoner();
        var marcado = listaPlatos.querySelector('[aria-checked="true"]');
        if (marcado) marcado.focus();
      });
      listaPlatos.appendChild(b);
    });

    crearTexto.textContent = q ? 'Crear «' + H.query.trim() + '»' : c.nueva;
  }

  function platoSeleccionado() {
    if (!H || H.sel == null) return null;
    var lista = recetario[cats[H.ci].clave] || [];
    for (var i = 0; i < lista.length; i++) if (lista[i].id === H.sel) return lista[i];
    return null;
  }

  function actualizarPoner() {
    var c = cats[H.ci];
    var p = platoSeleccionado();
    btnPoner.textContent = '';
    var span = el('span');
    if (!p) {
      span.textContent = c.clave === 'sopa' ? 'Elige una sopa' : 'Elige un ' + c.singular;
    } else if (c.con_cupo) {
      span.textContent = 'Poner ' + minuscula(p.nombre) + ', ' + H.cupo + ' ' + plural(H.cupo, 'porción', 'porciones');
    } else {
      span.textContent = 'Poner ' + minuscula(p.nombre);
    }
    btnPoner.appendChild(span);
    btnPoner.disabled = !p;
  }

  buscar.addEventListener('input', function () {
    if (!H) return;
    H.query = buscar.value;
    renderPlatos();
  });

  cupoInput.addEventListener('input', function () { cupoInput.value = cupoInput.value.replace(/\D/g, ''); });
  cupoInput.addEventListener('change', function () {
    if (!H) return;
    H.cupo = clampCupo(cupoInput.value);
    cupoInput.value = H.cupo;
    actualizarPoner();
  });
  cupoInput.addEventListener('focus', function () { cupoInput.select(); });
  porciones.querySelectorAll('.alm-step').forEach(function (b) {
    b.addEventListener('click', function () {
      if (!H) return;
      H.cupo = clampCupo((parseInt(cupoInput.value, 10) || H.cupo) + parseInt(b.dataset.step, 10));
      cupoInput.value = H.cupo;
      actualizarPoner();
    });
  });

  btnPoner.addEventListener('click', function () {
    var p = platoSeleccionado();
    if (!H || !p) return;
    var c = cats[H.ci];
    var si = H.si, ci = H.ci;
    H.cupo = clampCupo(cupoInput.value);
    c.slots[si] = {
      plato_id: p.id,
      nombre: p.nombre,
      cupo: c.con_cupo ? H.cupo : 0,
      vendidos: vendidosHoy[c.clave][p.id] || 0
    };
    sucio = true;
    H.origen = null;
    cerrarHoja();
    render();
    var nuevo = main.querySelector('[data-slot="' + ci + '-' + si + '"]');
    if (nuevo) nuevo.focus();
  });

  btnQuitar.addEventListener('click', function () {
    if (!H) return;
    var c = cats[H.ci];
    var ci = H.ci;
    var base = Math.max(c.min, c.obligatoria ? 0 : 1);
    if (H.si >= base) c.slots.splice(H.si, 1);
    else c.slots[H.si] = null;
    // Si se quitó una ranura base, las extras vacías sobran.
    while (c.slots.length > base && c.slots[c.slots.length - 1] === null) c.slots.pop();
    sucio = true;
    H.origen = null;
    cerrarHoja();
    render();
    var destino = main.querySelectorAll('.alm-seccion')[ci];
    var foco = destino && destino.querySelector('button');
    if (foco) foco.focus();
  });

  // Crear plato nuevo sin salir de la hoja
  function cerrarCrear() {
    crearForm.hidden = true;
    crearAbrir.hidden = false;
    crearError.textContent = '';
  }
  crearAbrir.addEventListener('click', function () {
    crearAbrir.hidden = true;
    crearForm.hidden = false;
    crearNombre.value = H ? H.query.trim() : '';
    crearNombre.placeholder = 'Nombre del plato';
    crearNombre.focus();
  });
  crearForm.addEventListener('submit', function (ev) {
    ev.preventDefault();
    if (!H) return;
    var c = cats[H.ci];
    var nombre = crearNombre.value.trim();
    if (!nombre) { crearError.textContent = 'Escribe el nombre del plato.'; crearNombre.focus(); return; }
    var ok = crearForm.querySelector('.alm-crear-ok');
    ok.disabled = true;
    crearError.textContent = '';
    fetch(E.urls.crear_plato, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
      body: JSON.stringify({ categoria: c.clave, nombre: nombre })
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        ok.disabled = false;
        if (!data.ok) { crearError.textContent = data.error || 'No se pudo crear el plato.'; return; }
        if (!H) return;
        var lista = recetario[c.clave] = recetario[c.clave] || [];
        var existe = lista.some(function (p) { return p.id === data.plato.id; });
        if (!existe) lista.unshift(data.plato);
        H.sel = data.plato.id;
        H.query = '';
        buscar.value = '';
        cerrarCrear();
        renderPlatos();
        actualizarPoner();
        mostrarAviso(data.plato.existia ? data.plato.nombre + ' ya estaba en el recetario' : data.plato.nombre + ' se añadió al recetario');
        btnPoner.focus();
      })
      .catch(function () {
        ok.disabled = false;
        crearError.textContent = 'Sin conexión. Inténtalo de nuevo.';
      });
  });

  fondo.addEventListener('click', function () { cerrarHoja(); });
  hoja.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') {
      if (!crearForm.hidden) { cerrarCrear(); crearAbrir.focus(); }
      else cerrarHoja();
      return;
    }
    if (ev.key !== 'Tab') return;
    var focos = Array.prototype.filter.call(
      hoja.querySelectorAll('button, input, [tabindex]'),
      function (n) { return !n.disabled && n.offsetParent !== null && n.tabIndex >= 0; }
    );
    if (!focos.length) return;
    var primero = focos[0], ultimo = focos[focos.length - 1];
    if (ev.shiftKey && document.activeElement === primero) { ev.preventDefault(); ultimo.focus(); }
    else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primero.focus(); }
  });

  // ------------------------------------------------------ copiar anterior
  function copiarAnterior(silencioso) {
    var ant = E.anterior;
    if (!ant) return;
    var hayAlgo = cats.some(function (c) { return llenas(c) > 0; });
    if (!silencioso && hayAlgo && !window.confirm('¿Reemplazar lo elegido por el menú ' + ant.titulo.replace('Repetir el menú ', '') + '?')) return;
    cats.forEach(function (c) {
      var disponibles = {};
      (recetario[c.clave] || []).forEach(function (p) { disponibles[p.id] = true; });
      var filas = (ant.ranuras[c.clave] || []).filter(function (r) { return disponibles[r.plato_id]; })
        .slice(0, c.max)
        .map(function (r) {
          return {
            plato_id: r.plato_id, nombre: r.nombre,
            cupo: c.con_cupo ? clampCupo(r.cupo) : 0,
            vendidos: vendidosHoy[c.clave][r.plato_id] || 0
          };
        });
      var base = Math.max(c.min, c.obligatoria ? 0 : 1);
      while (filas.length < base) filas.push(null);
      c.slots = filas;
    });
    sucio = true;
    render();
    mostrarAviso('Menú copiado. Revisa las porciones antes de publicar.');
  }
  if (btnCopiar) btnCopiar.addEventListener('click', function () { copiarAnterior(false); });

  // ------------------------------------------------------------- publicar
  btnPublicar.addEventListener('click', function () {
    if (enviando) return;
    var f = faltantes();
    if (f.length) {
      var ci = cats.indexOf(f[0].cat);
      var vacia = main.querySelectorAll('.alm-seccion')[ci].querySelector('.alm-ranura-vacia');
      if (vacia) vacia.focus();
      return;
    }
    var datos = {};
    cats.forEach(function (c) {
      datos[c.clave] = c.slots.filter(Boolean).map(function (r) {
        return { plato_id: r.plato_id, cupo: r.cupo };
      });
    });
    enviando = true;
    btnPublicar.setAttribute('aria-busy', 'true');
    btnPublicar.textContent = 'Publicando…';
    fetch(E.urls.publicar, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
      body: JSON.stringify(datos)
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        if (data.ok) {
          sucio = false;
          window.location.href = data.url;
          return;
        }
        throw new Error(data.error || 'No se pudo publicar el menú.');
      })
      .catch(function (err) {
        enviando = false;
        btnPublicar.removeAttribute('aria-busy');
        btnPublicar.textContent = 'Publicar menú';
        lineaFalta.classList.remove('alm-linea-ok');
        lineaFalta.textContent = err && err.message && err.message !== 'Failed to fetch'
          ? err.message : 'Sin conexión. Inténtalo de nuevo.';
      });
  });

  window.addEventListener('beforeunload', function (ev) {
    if (!sucio) return;
    ev.preventDefault();
    ev.returnValue = '';
  });

  render();
  if (E.copiar_al_abrir) copiarAnterior(true);
})();
