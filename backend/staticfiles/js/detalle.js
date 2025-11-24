/**
 * Detalle de Producto - Funcionalidad específica
 * Usa el AuthManager centralizado para autenticación
 */

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
// muestra el toast verde de "añadido"
function mostrarAlertaCarrito() {
  const s = document.getElementById('alerta-carrito');
  s.style.display = 'block';
  setTimeout(ocultarAlertaCarrito, 2500);
}
function ocultarAlertaCarrito() {
  document.getElementById('alerta-carrito').style.display = 'none';
}

// muestra el toast rojo de "stock"
function mostrarAlertaStock() {
  const s = document.getElementById('alerta-stock');
  s.style.display = 'block';
  setTimeout(ocultarAlertaStock, 2500);
}
function ocultarAlertaStock() {
  document.getElementById('alerta-stock').style.display = 'none';
}
// Función para agregar producto al carrito
function agregarAlCarrito(productoId) {
  fetch(`/api/carrito/agregar/${productoId}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': (document.querySelector('[name=csrfmiddlewaretoken]')||{}).value
    },
    body: JSON.stringify({ cantidad: 1 })
  })
  .then(async res => {
    const data = await res.json();
    if (!res.ok || data.error) {
      // si el backend devuelve error (por falta de stock u otro)
      mostrarAlertaStock();
    } else {
      mostrarAlertaCarrito();
      // actualizar contador si existe
      if (window.authManager?.actualizarContadorCarrito) {
        window.authManager.actualizarContadorCarrito();
      }
    }
  })
  .catch(() => {
    // en caso de fallo de red
    mostrarAlertaStock();
  });
}

document.addEventListener("DOMContentLoaded", async () => {
    // Verificar autenticación de forma no invasiva
    const isAuthenticated = await window.authManager.isAuthenticated();
    
    const btnAgregar = document.getElementById("btn-agregar-carrito");
    
    if (!isAuthenticated) {
        // Usuario no autenticado - pero PUEDE agregar al carrito como invitado
        if (btnAgregar) {
            btnAgregar.disabled = false;
            btnAgregar.textContent = "Agregar al carrito";
            // El botón funciona normal, AuthManager maneja el carrito de invitado
        }
        console.log("👤 Usuario no autenticado - carrito de invitado habilitado");
        return;
    }

    // Si está autenticado, migrar carrito de invitado si existe
    await window.authManager.migrarCarritoInvitado();
    
    // Habilitar funcionalidades completas para usuario autenticado
    if (btnAgregar) {
        btnAgregar.disabled = false;
        btnAgregar.textContent = "Agregar al carrito";
    }
    
    console.log("✅ Usuario autenticado en página de detalle");
});
