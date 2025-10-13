// Función para controlar dropdowns en móviles
function toggleDropdown(dropdownId) {
  // Solo funciona en móviles
  if (window.innerWidth >= 768) {
    return;
  }
  
  const content = document.getElementById(dropdownId + '-content');
  const icon = document.getElementById(dropdownId + '-icon');
  
  if (content && icon) {
    if (content.classList.contains('show')) {
      // Si está abierto, cerrarlo
      content.classList.remove('show');
      icon.classList.remove('rotated');
    } else {
      // Si está cerrado, abrirlo y cerrar los otros
      // Cerrar todos los otros dropdowns
      const allDropdowns = document.querySelectorAll('.dropdown-content');
      const allIcons = document.querySelectorAll('.dropdown-icon');
      
      allDropdowns.forEach(dropdown => {
        dropdown.classList.remove('show');
      });
      
      allIcons.forEach(icon => {
        icon.classList.remove('rotated');
      });
      
      // Abrir el seleccionado
      content.classList.add('show');
      icon.classList.add('rotated');
    }
  }
}

// Inicializar dropdowns al cargar la página
document.addEventListener('DOMContentLoaded', function() {
  // En desktop, asegurar que el contenido esté visible
  if (window.innerWidth >= 768) {
    const dropdowns = document.querySelectorAll('.dropdown-content');
    dropdowns.forEach(dropdown => {
      dropdown.classList.add('show');
    });
  } else {
    // En móviles, abrir "Datos del pedido" por defecto
    const datosPedidoContent = document.getElementById('datos-pedido-content');
    const datosPedidoIcon = document.getElementById('datos-pedido-icon');
    
    if (datosPedidoContent && datosPedidoIcon) {
      datosPedidoContent.classList.add('show');
      datosPedidoIcon.classList.add('rotated');
    }
  }
});

// Manejar redimensionamiento de ventana
window.addEventListener('resize', function() {
  if (window.innerWidth >= 768) {
    // En desktop, mostrar todo
    const dropdowns = document.querySelectorAll('.dropdown-content');
    const icons = document.querySelectorAll('.dropdown-icon');
    
    dropdowns.forEach(dropdown => {
      dropdown.classList.add('show');
    });
    
    icons.forEach(icon => {
      icon.classList.remove('rotated');
    });
  } else {
    // En móviles, colapsar todo excepto "Datos del pedido"
    const dropdowns = document.querySelectorAll('.dropdown-content');
    const icons = document.querySelectorAll('.dropdown-icon');
    
    dropdowns.forEach(dropdown => {
      dropdown.classList.remove('show');
    });
    
    icons.forEach(icon => {
      icon.classList.remove('rotated');
    });
    
    // Abrir "Datos del pedido" por defecto en móviles
    const datosPedidoContent = document.getElementById('datos-pedido-content');
    const datosPedidoIcon = document.getElementById('datos-pedido-icon');
    
    if (datosPedidoContent && datosPedidoIcon) {
      datosPedidoContent.classList.add('show');
      datosPedidoIcon.classList.add('rotated');
    }
  }
});