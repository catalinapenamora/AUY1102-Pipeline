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

// Función para agregar producto al carrito
async function agregarAlCarrito(productoId, cantidad = 1) {
    try {
        const resultado = await window.authManager.agregarAlCarrito(productoId, cantidad);
        
        if (resultado.success) {
            if (resultado.type === 'authenticated') {
                alert("Producto agregado al carrito");
            } else {
                alert("Producto agregado al carrito de invitado. Inicia sesión para finalizar tu compra.");
            }
        } else {
            alert(resultado.error || "Error al agregar al carrito");
        }
    } catch (error) {
        console.error("Error al agregar al carrito:", error);
        alert("Error al agregar al carrito");
    }
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
