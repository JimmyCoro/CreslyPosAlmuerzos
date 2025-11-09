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

// ===== WEBSOCKET PARA TIEMPO REAL =====

class WebSocketManager {
  constructor() {
    this.socket = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // 1 segundo
    this.isConnected = false;
  }

  connect() {
    try {
      // Construir URL del WebSocket
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/pedidos/`;
      
      console.log('[WEBSOCKET] Conectando a:', wsUrl);
      
      this.socket = new WebSocket(wsUrl);
      
      // Eventos del WebSocket
      this.socket.onopen = (event) => {
        console.log('[WEBSOCKET] Conectado exitosamente');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.showConnectionStatus('Conectado', 'success');
      };
      
      this.socket.onmessage = (event) => {
        this.handleMessage(event);
      };
      
      this.socket.onclose = (event) => {
        console.log('[WEBSOCKET] Conexión cerrada:', event.code, event.reason);
        this.isConnected = false;
        this.showConnectionStatus('Desconectado', 'error');
        this.attemptReconnect();
      };
      
      this.socket.onerror = (error) => {
        console.error('[WEBSOCKET] Error:', error);
        this.showConnectionStatus('Error de conexión', 'error');
      };
      
    } catch (error) {
      console.error('[WEBSOCKET] Error al conectar:', error);
      this.showConnectionStatus('Error de conexión', 'error');
    }
  }

  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log('[WEBSOCKET] Mensaje recibido:', data);
      
      switch (data.type) {
        case 'connection_established':
          console.log('[WEBSOCKET] Conexión establecida:', data.message);
          break;
          
        case 'pedido_creado':
          this.handlePedidoCreado(data.pedido);
          break;
          
        case 'pedido_actualizado':
          this.handlePedidoActualizado(data.pedido);
          break;
          
        case 'pedido_eliminado':
          this.handlePedidoEliminado(data.pedido);
          break;
          
        case 'pedidos_marcados_completados':
          this.handlePedidosMarcadosCompletados(data);
          break;
          
        case 'pedidos_data':
          this.handlePedidosData(data.pedidos);
          break;
          
        case 'error':
          console.error('[WEBSOCKET] Error del servidor:', data.message);
          break;
          
        default:
          console.log('[WEBSOCKET] Tipo de mensaje desconocido:', data.type);
      }
    } catch (error) {
      console.error('[WEBSOCKET] Error al procesar mensaje:', error);
    }
  }

  handlePedidoCreado(pedido) {
    console.log('[WEBSOCKET] Nuevo pedido creado:', pedido);
    
    // Mostrar notificación
    this.showNotification('Nuevo pedido creado', `Pedido #${pedido.numero_pedido_completo}`, 'success');
    
    // Recargar la lista de pedidos
    this.reloadPedidos();
  }

  handlePedidoActualizado(pedido) {
    console.log('[WEBSOCKET] Pedido actualizado:', pedido);
    
    // Mostrar notificación
    this.showNotification('Pedido actualizado', `Pedido #${pedido.numero_pedido_completo}`, 'info');
    
    // Recargar la lista de pedidos
    this.reloadPedidos();
  }

  handlePedidoEliminado(pedido) {
    console.log('[WEBSOCKET] Pedido eliminado:', pedido);
    
    // Mostrar notificación
    this.showNotification('Pedido eliminado', `Pedido #${pedido.numero_pedido_completo}`, 'warning');
    
    // Recargar la lista de pedidos
    this.reloadPedidos();
  }

  handlePedidosMarcadosCompletados(data) {
    console.log('[WEBSOCKET] Pedidos marcados como completados:', data);
    
    // Mostrar notificación
    this.showNotification(
      'Pedidos completados', 
      `${data.cantidad} pedidos marcados como listos`, 
      'success'
    );
    
    // Recargar la lista de pedidos
    this.reloadPedidos();
  }

  handlePedidosData(pedidos) {
    console.log('[WEBSOCKET] Datos de pedidos recibidos:', pedidos);
    // Aquí podrías actualizar la interfaz directamente sin recargar
  }

  reloadPedidos() {
    // Verificar si hay un modal abierto (más específico)
    const modalAbierto = document.querySelector('.modal.show') || 
                        document.querySelector('#tomarPedidoModal.show') ||
                        document.querySelector('.modal[style*="display: block"]');
    
    if (modalAbierto) {
      // Usuario está trabajando - NO interrumpir
      console.log('[WEBSOCKET] Modal abierto detectado - NO recargando página');
      console.log('[WEBSOCKET] Modal detectado:', modalAbierto.id || modalAbierto.className);
      
      // Solo actualizar contadores sin recargar
      this.actualizarSoloContadores();
      
      // Mostrar notificación de que hay nuevos pedidos
      this.showNotification(
        'Nuevo pedido creado', 
        'Hay nuevos pedidos disponibles. La página se actualizará cuando cierres el modal.', 
        'info'
      );
    } else {
      // Usuario no está trabajando - recargar normalmente
      console.log('[WEBSOCKET] No hay modal abierto - recargando página');
      setTimeout(() => {
        window.location.reload();
      }, 1000); // Esperar 1 segundo para que el usuario vea la notificación
    }
  }

  actualizarSoloContadores() {
    // Actualizar solo los contadores de tabs sin recargar la página
    console.log('[WEBSOCKET] Actualizando contadores...');
    
    // Llamar a la función existente para actualizar contadores
    if (typeof actualizarContadoresTabs === 'function') {
      actualizarContadoresTabs();
    }
  }

  showNotification(title, message, type = 'info') {
    // Crear notificación visual
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
      <strong>${title}</strong><br>
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remover después de 5 segundos
    setTimeout(() => {
      if (notification.parentNode) {
        notification.parentNode.removeChild(notification);
      }
    }, 5000);
  }

  showConnectionStatus(message, type) {
    // Mostrar estado de conexión en la consola
    console.log(`[WEBSOCKET] Estado: ${message}`);
    
    // Aquí podrías agregar un indicador visual en la interfaz
    // Por ejemplo, un pequeño punto verde/rojo en la esquina
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`[WEBSOCKET] Intentando reconectar... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('[WEBSOCKET] Máximo de intentos de reconexión alcanzado');
      this.showConnectionStatus('Conexión perdida', 'error');
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.isConnected = false;
    }
  }

  sendMessage(message) {
    if (this.socket && this.isConnected) {
      this.socket.send(JSON.stringify(message));
    } else {
      console.warn('[WEBSOCKET] No hay conexión activa');
    }
  }
}

// Crear instancia global del WebSocket
const wsManager = new WebSocketManager();

// Conectar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
  // Solo conectar si estamos en la página de inicio
  if (window.location.pathname === '/' || window.location.pathname === '/inicio/') {
    console.log('[WEBSOCKET] Iniciando conexión...');
    wsManager.connect();
    
    // Detectar cuando se cierra un modal para recargar la página
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
      modal.addEventListener('hidden.bs.modal', function() {
        console.log('[WEBSOCKET] Modal cerrado - verificando si hay actualizaciones pendientes');
        
        // Verificar si hay notificaciones de actualizaciones pendientes
        const notificacionesPendientes = document.querySelectorAll('.alert-info');
        if (notificacionesPendientes.length > 0) {
          console.log('[WEBSOCKET] Recargando página después de cerrar modal');
          setTimeout(() => {
            window.location.reload();
          }, 500); // Pequeño delay para que el modal se cierre completamente
        }
      });
    });
  }
});

// Desconectar cuando se cierra la página
window.addEventListener('beforeunload', function() {
  wsManager.disconnect();
});