// Sesión expirada en medio de un fetch(): LoginObligatorioMiddleware responde
// 401 con {login_url}. En vez de que cada pantalla lo maneje, se envuelve
// window.fetch una sola vez y se manda al login volviendo a esta misma página.
(function () {
  if (!window.fetch || window.__sesionFetch) return;
  window.__sesionFetch = true;
  var fetchOriginal = window.fetch.bind(window);

  window.fetch = function () {
    return fetchOriginal.apply(null, arguments).then(function (res) {
      if (res.status !== 401) return res;
      return res.clone().json().then(function (data) {
        if (data && data.login_url) {
          var destino = data.login_url;
          if (destino.indexOf('/login/') !== -1) {
            destino += '?next=' + encodeURIComponent(location.pathname + location.search);
          }
          location.href = destino;
        }
        return res;
      }, function () { return res; });
    });
  };
})();
