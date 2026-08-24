/* Carrito flotante (barra inferior + hoja deslizable) para las pantallas de
   pedido de Pizzería, en tablet vertical y móvil (≤1023px). Sincroniza la
   barra con el carrito real vía MutationObserver, sin tocar la lógica de
   precios/armado de pedido de cada pantalla. */
(function () {
  function moverAlBodyEnMobile(el) {
    if (!el) return;
    var originalParent = el.parentNode;
    var originalNext = el.nextSibling;
    var enBody = false;

    function actualizarPosicion() {
      var esAngosto = window.innerWidth <= 1023;
      if (esAngosto && !enBody) {
        document.body.appendChild(el);
        enBody = true;
      } else if (!esAngosto && enBody) {
        originalParent.insertBefore(el, originalNext);
        enBody = false;
      }
    }

    actualizarPosicion();
    window.addEventListener('resize', actualizarPosicion);
  }

  // La altura real del navbar inferior (--pz-bottomnav-h) la fija
  // components/pizzeria_bottom_nav.html, que es quien conoce ese elemento.

  window.pzInitCartBar = function (config) {
    var itemsEl = document.getElementById(config.itemsId);
    var totalEl = document.getElementById(config.totalId);
    var sheetEl = document.getElementById(config.sheetId);
    var bar = document.getElementById('pzCartBar');
    var barBtn = document.getElementById('pzCartBarBtn');
    var barCount = document.getElementById('pzCartBarCount');
    var barTotal = document.getElementById('pzCartBarTotal');
    var backdrop = document.getElementById('pzSheetBackdrop');
    var closeBtn = config.closeId ? document.getElementById(config.closeId) : null;

    if (!itemsEl || !totalEl || !sheetEl || !bar || !backdrop) return;

    function cerrarHoja() {
      sheetEl.classList.remove('pz-cart-sheet-open');
      backdrop.classList.remove('active');
    }

    function abrirHoja() {
      sheetEl.classList.add('pz-cart-sheet-open');
      backdrop.classList.add('active');
    }

    barBtn.addEventListener('click', function () {
      if (sheetEl.classList.contains('pz-cart-sheet-open')) {
        cerrarHoja();
      } else {
        abrirHoja();
      }
    });
    backdrop.addEventListener('click', cerrarHoja);
    if (closeBtn) closeBtn.addEventListener('click', cerrarHoja);

    function sincronizar() {
      var count = itemsEl.querySelectorAll(config.itemSelector).length;
      barCount.textContent = count === 1 ? '1 item' : count + ' items';
      barTotal.textContent = totalEl.textContent.trim();
      bar.classList.toggle('pz-cartbar-visible', count > 0);
      if (count === 0) cerrarHoja();
    }

    new MutationObserver(sincronizar).observe(itemsEl, { childList: true, subtree: true, characterData: true });
    new MutationObserver(sincronizar).observe(totalEl, { childList: true, characterData: true, subtree: true });
    sincronizar();

    moverAlBodyEnMobile(bar);
    moverAlBodyEnMobile(backdrop);
    moverAlBodyEnMobile(sheetEl);
  };
})();
