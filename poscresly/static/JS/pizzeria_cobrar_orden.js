(function () {
  const ITEMS = window.PZ_ITEMS_COBRO || [];
  const TOTAL_PEDIDO = window.PZ_TOTAL_PEDIDO || 0;
  const METODOS = ['Efectivo', 'Tarjeta', 'Transferencia'];
  const ICONOS_METODO = { Efectivo: 'fa-money-bill-wave', Tarjeta: 'fa-credit-card', Transferencia: 'fa-right-left' };
  const BILLETES_USD = [5, 10, 20, 50, 100];
  const TOLERANCIA = 0.01;

  let modo = 'completo';
  let pagosCompletos = [{ metodo: 'Efectivo', monto: TOTAL_PEDIDO }];
  let montoRecibidoCompleto = '';
  let mixtoCompleto = false;
  let personas = [];
  let personaActiva = 0;

  function claveItem(item) { return `${item.tipo}:${item.id}`; }
  function fmt(n) { return (Math.round((n || 0) * 100) / 100).toFixed(2); }
  function sumaPagos(pagos) { return pagos.reduce((acc, p) => acc + (parseFloat(p.monto) || 0), 0); }

  function asignadoTotalItem(clave) {
    let total = 0;
    personas.forEach(p => { total += p.asignaciones[clave] || 0; });
    return total;
  }

  function restanteItem(clave, cantidadTotal, excluirPersonaIdx) {
    let asignado = 0;
    personas.forEach((p, idx) => {
      if (idx === excluirPersonaIdx) return;
      asignado += p.asignaciones[clave] || 0;
    });
    return cantidadTotal - asignado;
  }

  function subtotalPersona(idx) {
    const persona = personas[idx];
    let total = 0;
    ITEMS.forEach(item => {
      const cant = persona.asignaciones[claveItem(item)] || 0;
      total += cant * item.precio_unitario;
    });
    return total;
  }

  // ---------- Contexto de pago activo (pedido completo o persona activa) ----------
  function contextoActivo() {
    if (modo === 'completo') {
      return {
        pagos: pagosCompletos,
        objetivo: TOTAL_PEDIDO,
        montoRecibido: montoRecibidoCompleto,
        setMontoRecibido: (v) => { montoRecibidoCompleto = v; },
        mixto: mixtoCompleto,
        setMixto: (v) => { mixtoCompleto = v; },
        marcarSinConfirmar: () => {},
      };
    }
    const persona = personas[personaActiva];
    return {
      pagos: persona.pagos,
      objetivo: subtotalPersona(personaActiva),
      montoRecibido: persona.montoRecibido,
      setMontoRecibido: (v) => { persona.montoRecibido = v; },
      mixto: persona.mixto,
      setMixto: (v) => { persona.mixto = v; },
      // Si se toca el pago después de haber "cobrado" a esta persona, hay que
      // volver a confirmarla — ya no vale lo que se había marcado antes.
      marcarSinConfirmar: () => { persona.confirmada = false; },
    };
  }

  // ---------- Modo ----------
  function cbCambiarModo(nuevoModo) {
    modo = nuevoModo;
    document.getElementById('cbModoDividirBtn').classList.toggle('cb-header-btn-activo', modo === 'dividir');

    if (modo === 'dividir' && personas.length < 2) {
      while (personas.length < 2) cbAgregarPersonaSilencioso();
      personaActiva = 0;
    }

    renderIzquierda();
    renderDerecha();
  }

  function cbToggleDividir() {
    cbCambiarModo(modo === 'dividir' ? 'completo' : 'dividir');
  }

  // ---------- Columna izquierda ----------
  function renderIzquierda() {
    document.getElementById('cbSeccionCompleto').style.display = modo === 'completo' ? '' : 'none';
    document.getElementById('cbSeccionDividir').style.display = modo === 'dividir' ? '' : 'none';
    if (modo === 'completo') {
      renderItemsListaCompleto();
    } else {
      renderPersonasCards();
      renderItemsListaDividir();
      renderResumenGlobal();
    }
  }

  function renderItemsListaCompleto() {
    document.getElementById('cbItemsListaCompleto').innerHTML = ITEMS.map(item => `
      <div class="cb-item-row cb-item-row-solo">
        <span class="cb-item-desc">${item.cantidad}x ${item.descripcion}</span>
        <span class="cb-item-precio">$${fmt(item.precio_unitario * item.cantidad)}</span>
      </div>
    `).join('');
  }

  function cbAgregarPersonaSilencioso() {
    personas.push({
      nombre: `Persona ${personas.length + 1}`,
      asignaciones: {},
      pagos: [{ metodo: 'Efectivo', monto: 0 }],
      montoRecibido: '',
      mixto: false,
      confirmada: false,
    });
  }

  function cbAgregarPersona() {
    cbAgregarPersonaSilencioso();
    personaActiva = personas.length - 1;
    renderIzquierda();
    renderDerecha();
    const input = document.querySelector(`.cb-persona-nombre-input[data-idx="${personaActiva}"]`);
    if (input) { input.focus(); input.select(); }
  }

  function cbQuitarPersona(idx) {
    if (personas.length <= 2) {
      alert('Se necesitan al menos 2 personas para dividir la cuenta');
      return;
    }
    personas.splice(idx, 1);
    if (personaActiva >= personas.length) personaActiva = personas.length - 1;
    renderIzquierda();
    renderDerecha();
  }

  function cbSeleccionarPersona(idx) {
    personaActiva = idx;
    renderIzquierda();
    renderDerecha();
  }

  function cbRenombrarPersona(idx, nombre) {
    personas[idx].nombre = nombre || `Persona ${idx + 1}`;
  }

  function platillosPersona(idx) {
    return Object.values(personas[idx].asignaciones).reduce((acc, c) => acc + c, 0);
  }

  function renderPersonasCards() {
    const cards = personas.map((p, idx) => {
      const nPlatillos = platillosPersona(idx);
      return `
      <div class="cb-persona-card ${idx === personaActiva ? 'cb-persona-activa' : ''} ${p.confirmada ? 'cb-persona-confirmada' : ''}" onclick="cbSeleccionarPersona(${idx})">
        ${personas.length > 2 ? `<button type="button" class="cb-persona-card-quitar" onclick="event.stopPropagation(); cbQuitarPersona(${idx})"><i class="fas fa-times"></i></button>` : ''}
        <input type="text" class="cb-persona-nombre-input" data-idx="${idx}" value="${p.nombre}"
          placeholder="Nombre" onclick="event.stopPropagation()" oninput="cbRenombrarPersona(${idx}, this.value)">
        <span class="cb-persona-card-precio">${p.confirmada ? '<i class="fas fa-check-circle cb-persona-card-check"></i>' : ''}$${fmt(subtotalPersona(idx))}</span>
        <span class="cb-persona-card-platillos">${nPlatillos} platillo${nPlatillos === 1 ? '' : 's'}</span>
      </div>
    `;
    }).join('');
    const cardAgregar = `
      <button type="button" class="cb-persona-card-agregar" onclick="cbAgregarPersona()">
        <i class="fas fa-user-plus"></i>
        <span>Agregar persona</span>
      </button>
    `;
    document.getElementById('cbPersonasCards').innerHTML = cards + cardAgregar;
  }

  function cbAsignarItem(idx, clave, cantidadTotal, valor) {
    let cant = parseInt(valor, 10);
    if (isNaN(cant) || cant < 0) cant = 0;
    const maxDisponible = restanteItem(clave, cantidadTotal, idx);
    if (cant > maxDisponible) cant = maxDisponible;
    if (cant === 0) delete personas[idx].asignaciones[clave];
    else personas[idx].asignaciones[clave] = cant;
    personas[idx].confirmada = false;
    renderIzquierda();
    renderDerecha();
  }

  function renderItemsListaDividir() {
    const persona = personas[personaActiva];
    const cont = document.getElementById('cbItemsListaDividir');
    const titulo = document.getElementById('cbDividirDetalleTitle');
    if (titulo) titulo.textContent = persona ? `Platillos de ${persona.nombre}` : 'Detalle';
    if (!persona) { cont.innerHTML = ''; return; }
    cont.innerHTML = ITEMS.map(item => {
      const clave = claveItem(item);
      const asignadoAqui = persona.asignaciones[clave] || 0;
      const disponible = restanteItem(clave, item.cantidad, personaActiva);
      const otras = personas
        .map((p, idx) => ({ nombre: p.nombre, cant: p.asignaciones[clave] || 0 }))
        .filter((o, idx) => idx !== personaActiva && o.cant > 0);
      return `
        <div class="cb-item-row cb-item-row-dividir">
          <div class="cb-item-info">
            <div class="cb-item-titulo-row">
              <span class="cb-item-desc">${item.descripcion}</span>
              <span class="cb-item-badge-cant">x${item.cantidad}</span>
            </div>
            <span class="cb-item-precio">$${fmt(item.precio_unitario)} c/u</span>
            ${otras.map(o => `<span class="cb-item-tag-persona">${o.nombre}: ${o.cant}</span>`).join('')}
          </div>
          <div class="cb-stepper-pill">
            <button type="button" class="cb-stepper-btn" onclick="cbCambiarCantidadItem('${clave}', ${item.cantidad}, -1)" ${asignadoAqui <= 0 ? 'disabled' : ''}><i class="fas fa-minus"></i></button>
            <span class="cb-stepper-value">${asignadoAqui}</span>
            <button type="button" class="cb-stepper-btn" onclick="cbCambiarCantidadItem('${clave}', ${item.cantidad}, 1)" ${asignadoAqui >= disponible ? 'disabled' : ''}><i class="fas fa-plus"></i></button>
          </div>
        </div>
      `;
    }).join('');
  }

  function cbCambiarCantidadItem(clave, cantidadTotal, delta) {
    const actual = personas[personaActiva].asignaciones[clave] || 0;
    cbAsignarItem(personaActiva, clave, cantidadTotal, actual + delta);
  }

  function renderResumenGlobal() {
    let totalUnidades = 0, asignados = 0;
    ITEMS.forEach(item => {
      totalUnidades += item.cantidad;
      asignados += asignadoTotalItem(claveItem(item));
    });
    const ok = asignados === totalUnidades;
    document.getElementById('cbResumenGlobal').innerHTML = ok
      ? '<span class="cb-restante-ok"><i class="fas fa-check-circle"></i> Todos los productos asignados</span>'
      : `<span class="cb-restante-pendiente">Productos asignados: ${asignados}/${totalUnidades}</span>`;
    actualizarBotonConfirmar();
  }

  // ---------- Columna derecha ----------
  function renderDerecha() {
    renderTotalBox();
    renderMixtoToggle();
    renderMetodoCards();
    renderPagosMixto();
    renderEfectivoBox();
    renderRestanteGeneral();
  }

  function renderTotalBox() {
    const ctx = contextoActivo();
    document.getElementById('cbSubtotalValor').textContent = '$' + fmt(ctx.objetivo);
    document.getElementById('cbTotalValor').textContent = '$' + fmt(ctx.objetivo);
  }

  // ---------- Método de pago (único vs. mixto) ----------
  function renderMixtoToggle() {
    const ctx = contextoActivo();
    document.getElementById('cbMixtoToggle').classList.toggle('cb-mixto-toggle-activo', ctx.mixto);
  }

  function cbToggleMixto() {
    const ctx = contextoActivo();
    if (ctx.mixto) {
      ctx.pagos.splice(1);
      ctx.pagos[0].metodo = 'Efectivo';
      ctx.pagos[0].monto = ctx.objetivo;
      ctx.setMontoRecibido('');
      ctx.setMixto(false);
    } else {
      // El pago mixto siempre es Efectivo (fila 1) + Transferencia (fila 2).
      ctx.pagos.splice(0, ctx.pagos.length, { metodo: 'Efectivo', monto: 0 }, { metodo: 'Transferencia', monto: 0 });
      ctx.setMontoRecibido('');
      ctx.setMixto(true);
    }
    ctx.marcarSinConfirmar();
    renderDerecha();
  }

  function renderMetodoCards() {
    const ctx = contextoActivo();
    const cont = document.getElementById('cbMetodoCards');
    if (ctx.mixto) { cont.innerHTML = ''; return; }
    const principal = ctx.pagos[0].metodo;
    cont.innerHTML = METODOS.map(m => `
      <button type="button" class="cb-metodo-card ${m === principal ? 'cb-metodo-activo' : ''}" onclick="cbSeleccionarMetodoPrincipal('${m}')">
        <i class="fas ${ICONOS_METODO[m]}"></i>
        <span>${m}</span>
      </button>
    `).join('');
  }

  function cbSeleccionarMetodoPrincipal(metodo) {
    const ctx = contextoActivo();
    ctx.pagos[0].metodo = metodo;
    ctx.pagos[0].monto = ctx.objetivo;
    ctx.setMontoRecibido('');
    ctx.marcarSinConfirmar();
    renderDerecha();
  }

  // ---------- Filas de pago mixto: siempre Efectivo (fila 1) + Transferencia (fila 2).
  // El método de cada fila es fijo; lo único editable es el monto.
  function renderPagosMixto() {
    const ctx = contextoActivo();
    const cont = document.getElementById('cbPagosMixto');
    if (!ctx.mixto) { cont.innerHTML = ''; return; }
    cont.innerHTML = ctx.pagos.map((p, idx) => `
      <div class="cb-pago-row">
        <div class="cb-metodo-mini-grupo">
          <span class="cb-metodo-mini cb-metodo-mini-fijo">
            <i class="fas ${ICONOS_METODO[p.metodo]}"></i><span>${p.metodo}</span>
          </span>
        </div>
        <div class="cb-input-monto-wrap">
          <span>$</span>
          <input type="number" step="0.01" min="0" class="cb-input-monto" value="${p.monto}" oninput="cbCambiarMontoMixto(${idx}, this.value)">
        </div>
        <button type="button" class="cb-btn-restante" onclick="cbLlenarRestanteMixto(${idx})" title="Completar con el restante">
          <i class="fas fa-equals"></i>
        </button>
      </div>
    `).join('');
  }

  function cbCambiarMontoMixto(idx, valor) {
    const ctx = contextoActivo();
    ctx.pagos[idx].monto = parseFloat(valor) || 0;
    ctx.marcarSinConfirmar();
    if (idx === 0) renderEfectivoBox();
    renderRestanteGeneral();
  }

  // Llena esta fila con lo que falta para completar el total, según lo que
  // ya tiene la otra fila (doble clic rápido en vez de calcular a mano).
  function cbLlenarRestanteMixto(idx) {
    const ctx = contextoActivo();
    const otros = ctx.pagos.reduce((acc, p, i) => (i === idx ? acc : acc + (parseFloat(p.monto) || 0)), 0);
    const restante = ctx.objetivo - otros;
    ctx.pagos[idx].monto = restante > 0 ? Math.round(restante * 100) / 100 : 0;
    ctx.marcarSinConfirmar();
    renderDerecha();
  }

  function renderEfectivoBox() {
    const ctx = contextoActivo();
    const box = document.getElementById('cbEfectivoBox');
    if (ctx.pagos[0].metodo !== 'Efectivo') {
      box.style.display = 'none';
      return;
    }
    box.style.display = '';
    document.getElementById('cbMontoRecibido').value = ctx.montoRecibido;
    renderQuickAmounts(ctx.pagos[0].monto);
    renderVuelto();
  }

  function montosRapidos(objetivo) {
    const base = Math.round((objetivo || 0) * 100) / 100;
    return [base, ...BILLETES_USD.filter(b => b > base)].slice(0, 4);
  }

  function renderQuickAmounts(requerido) {
    document.getElementById('cbQuickAmounts').innerHTML = montosRapidos(requerido).map(m => `
      <button type="button" class="cb-quick-btn" onclick="cbSetMontoRecibidoRapido(${m})">$${fmt(m)}</button>
    `).join('');
  }

  function cbSetMontoRecibidoRapido(valor) {
    contextoActivo().setMontoRecibido(valor);
    document.getElementById('cbMontoRecibido').value = valor;
    renderVuelto();
  }

  function cbCambiarMontoRecibido(valor) {
    contextoActivo().setMontoRecibido(valor);
    renderVuelto();
  }

  function renderVuelto() {
    const ctx = contextoActivo();
    const recibido = parseFloat(ctx.montoRecibido);
    const requerido = ctx.pagos[0].monto;
    const el = document.getElementById('cbVueltoRow');
    if (isNaN(recibido) || recibido <= 0) {
      el.innerHTML = '';
      return;
    }
    const vuelto = recibido - requerido;
    el.innerHTML = vuelto >= -TOLERANCIA
      ? `<span class="cb-vuelto-ok">Vuelto: $${fmt(Math.max(vuelto, 0))}</span>`
      : `<span class="cb-vuelto-falta">Falta: $${fmt(Math.abs(vuelto))}</span>`;
  }

  function renderRestanteGeneral() {
    const ctx = contextoActivo();
    const restante = ctx.objetivo - sumaPagos(ctx.pagos);
    const ok = Math.abs(restante) < TOLERANCIA;
    document.getElementById('cbRestanteGeneral').innerHTML = ok
      ? '<span class="cb-restante-ok"><i class="fas fa-check-circle"></i> Pagos completos</span>'
      : `<span class="cb-restante-pendiente">Restante: $${fmt(restante)}</span>`;
    actualizarBotonConfirmar();
  }

  // ---------- Imprimir (placeholder) ----------
  function cbImprimir() {
    alert('Función de impresión próximamente.');
  }

  // ---------- Cancelar pedido ----------
  function cbCancelarPedido() {
    if (!confirm('¿Cancelar este pedido? Esta acción no se puede deshacer.')) return;

    fetch(window.PZ_URLS.cancelarPedido, {
      method: 'POST',
      headers: { 'X-CSRFToken': window.CSRF_TOKEN },
    })
      .then(r => r.json().catch(() => {
        throw new Error(`Respuesta inválida del servidor (HTTP ${r.status})`);
      }))
      .then(data => {
        if (data.status === 'ok') {
          window.location.href = window.PZ_URLS.ordenes;
        } else {
          alert('Error: ' + data.message);
        }
      })
      .catch((err) => alert(err && err.message ? err.message : 'Error inesperado al cancelar el pedido'));
  }

  // ---------- Validación / confirmar ----------

  // ¿La persona tiene platillos asignados y su(s) pago(s) cuadran con su subtotal?
  function personaListaParaCobrar(idx) {
    const persona = personas[idx];
    if (!persona) return false;
    const tieneItems = Object.values(persona.asignaciones).some(c => c > 0);
    if (!tieneItems) return false;
    const restante = subtotalPersona(idx) - sumaPagos(persona.pagos);
    if (Math.abs(restante) >= TOLERANCIA) return false;
    return persona.pagos.every(p => parseFloat(p.monto) > 0);
  }

  function todasPersonasConfirmadas() {
    return personas.length >= 2 && personas.every(p => p.confirmada);
  }

  function validarTodo() {
    if (modo === 'completo') {
      if (Math.abs(TOTAL_PEDIDO - sumaPagos(pagosCompletos)) >= TOLERANCIA) return false;
      return pagosCompletos.every(p => parseFloat(p.monto) > 0);
    }

    if (personas.length < 2) return false;

    let totalUnidades = 0, asignados = 0;
    ITEMS.forEach(item => {
      totalUnidades += item.cantidad;
      asignados += asignadoTotalItem(claveItem(item));
    });
    if (asignados !== totalUnidades) return false;

    // Cada persona debe haber sido cobrada explícitamente (botón "Cobrar
    // [Nombre]"), no basta con que los números cuadren solos.
    return personas.every((persona, idx) => persona.confirmada && personaListaParaCobrar(idx));
  }

  // El botón grande de abajo cambia de función según el modo y el progreso:
  // pedido completo -> confirma directo; dividir cuenta -> primero "cobra" a
  // cada persona una por una y solo al final habilita el cobro total.
  function actualizarBotonConfirmar() {
    const btn = document.getElementById('cbBtnConfirmar');
    const texto = document.getElementById('cbBtnConfirmarTexto');

    if (modo === 'completo' || personas.length < 2) {
      btn.disabled = !validarTodo();
      texto.textContent = `Confirmar · $${fmt(TOTAL_PEDIDO)}`;
      return;
    }

    if (todasPersonasConfirmadas()) {
      btn.disabled = !validarTodo();
      texto.textContent = `Confirmar cobro total · $${fmt(TOTAL_PEDIDO)}`;
      return;
    }

    const persona = personas[personaActiva];
    btn.disabled = !personaListaParaCobrar(personaActiva);
    texto.textContent = `Cobrar ${persona.nombre} · $${fmt(subtotalPersona(personaActiva))}`;
  }

  // Acción del botón grande: si ya está todo cobrado (o es pedido completo),
  // confirma de una vez. Si no, marca a la persona activa como cobrada y
  // salta automáticamente a la siguiente persona pendiente.
  function cbAccionPrincipal() {
    if (modo === 'completo' || todasPersonasConfirmadas()) {
      cbConfirmarCobro();
      return;
    }
    if (!personaListaParaCobrar(personaActiva)) return;
    personas[personaActiva].confirmada = true;
    const siguiente = personas.findIndex(p => !p.confirmada);
    if (siguiente !== -1) {
      cbSeleccionarPersona(siguiente);
    } else {
      renderIzquierda();
      renderDerecha();
    }
  }

  function construirPayload() {
    if (modo === 'completo') {
      return {
        dividir: false,
        pagos: pagosCompletos.map(p => ({ metodo: p.metodo, monto: parseFloat(p.monto) || 0 })),
      };
    }
    return {
      dividir: true,
      personas: personas.map(p => ({
        nombre: p.nombre,
        asignaciones: Object.keys(p.asignaciones).map(clave => {
          const [tipo, id] = clave.split(':');
          return { tipo, id: parseInt(id, 10), cantidad: p.asignaciones[clave] };
        }),
        pagos: p.pagos.map(pg => ({ metodo: pg.metodo, monto: parseFloat(pg.monto) || 0 })),
      })),
    };
  }

  function cbConfirmarCobro() {
    if (!validarTodo()) {
      alert('Revisa que todos los productos estén asignados y que los pagos coincidan con el total antes de confirmar.');
      return;
    }

    const btn = document.getElementById('cbBtnConfirmar');
    btn.disabled = true;

    fetch(window.PZ_URLS.procesarCobro, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
      body: JSON.stringify(construirPayload()),
    })
      .then(r => r.json())
      .then(data => {
        if (data.status === 'ok') {
          window.location.href = window.PZ_URLS.ordenes;
        } else {
          alert('Error: ' + data.message);
          btn.disabled = false;
        }
      })
      .catch(() => {
        alert('Error inesperado al procesar el cobro');
        btn.disabled = false;
      });
  }

  function renderTodo() {
    renderIzquierda();
    renderDerecha();
  }

  window.cbCambiarModo = cbCambiarModo;
  window.cbToggleDividir = cbToggleDividir;
  window.cbImprimir = cbImprimir;
  window.cbCancelarPedido = cbCancelarPedido;
  window.cbAgregarPersona = cbAgregarPersona;
  window.cbQuitarPersona = cbQuitarPersona;
  window.cbSeleccionarPersona = cbSeleccionarPersona;
  window.cbRenombrarPersona = cbRenombrarPersona;
  window.cbAsignarItem = cbAsignarItem;
  window.cbCambiarCantidadItem = cbCambiarCantidadItem;
  window.cbSeleccionarMetodoPrincipal = cbSeleccionarMetodoPrincipal;
  window.cbToggleMixto = cbToggleMixto;
  window.cbCambiarMontoMixto = cbCambiarMontoMixto;
  window.cbLlenarRestanteMixto = cbLlenarRestanteMixto;
  window.cbCambiarMontoRecibido = cbCambiarMontoRecibido;
  window.cbSetMontoRecibidoRapido = cbSetMontoRecibidoRapido;
  window.cbConfirmarCobro = cbConfirmarCobro;
  window.cbAccionPrincipal = cbAccionPrincipal;

  renderTodo();
})();
