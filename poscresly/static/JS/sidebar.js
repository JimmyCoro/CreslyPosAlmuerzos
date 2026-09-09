// ===== SIDEBAR RESPONSIVE =====
// Compartido entre base.html y movil/base_movil.html: mismo sidebar,
// mismo comportamiento, en cualquier pantalla que lo incluya. openSidebar
// y closeSidebar quedan como funciones globales — components/pizzeria_header.html
// las llama directamente al tocar el menú.
var sidebarToggle = document.getElementById('sidebarToggle');
var mainSidebar = document.getElementById('mainSidebar');
var sidebarOverlay = document.getElementById('sidebarOverlay');

function openSidebar() {
  mainSidebar.classList.add('sidebar-open');
  sidebarOverlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeSidebar() {
  mainSidebar.classList.remove('sidebar-open');
  sidebarOverlay.classList.remove('active');
  document.body.style.overflow = '';
}

if (sidebarToggle) {
  sidebarToggle.addEventListener('click', function () {
    mainSidebar.classList.contains('sidebar-open') ? closeSidebar() : openSidebar();
  });
}

if (sidebarOverlay) {
  sidebarOverlay.addEventListener('click', closeSidebar);
}

// Cierra el sidebar al navegar en móvil (excepto el toggle de grupos,
// que solo expande/colapsa y no debe cerrar el panel deslizable)
document.querySelectorAll('.sidebar-link:not(.sidebar-group-toggle)').forEach(function (link) {
  link.addEventListener('click', function () {
    if (window.innerWidth <= 1024) closeSidebar();
  });
});
