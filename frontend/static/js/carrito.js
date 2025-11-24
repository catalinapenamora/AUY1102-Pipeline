/**
 * Carrito - Funcionalidad específica del carrito
 * Maneja tanto carrito autenticado como carrito de invitado
 */

// Función para formatear precios con separadores de miles (formato chileno)
function formatPrice(price) {
    return `$${Math.round(price).toLocaleString('es-CL')}`;
}

// Variables globales para el envío
window.costoEnvioSeleccionado = 0;
window.opcionesEnvio = null;
window.opcionEnvioSeleccionada = null;

document.addEventListener("DOMContentLoaded", async () => {
  console.log("🔍 CARRITO: Iniciando carga de página del carrito");
  
  // Esperar a que AuthManager esté disponible
  if (!window.authManager) {
    console.log("⏳ CARRITO: Esperando AuthManager...");
    await new Promise(resolve => {
      const checkAuthManager = () => {
        if (window.authManager) {
          resolve();
        } else {
          setTimeout(checkAuthManager, 100);
        }
      };
      checkAuthManager();
    });
  }
  
  console.log("✅ CARRITO: AuthManager disponible");
  
  // Verificar si el usuario está autenticado
  const isAuthenticated = await window.authManager.isAuthenticated();
  console.log("🔍 CARRITO: Usuario autenticado:", isAuthenticated);
  
  if (isAuthenticated) {
    // Usuario autenticado - migrar carrito de invitado si existe
    await window.authManager.migrarCarritoInvitado();
    await inicializarCarritoAutenticado();
  } else {
    // Usuario invitado - mostrar carrito local
    await inicializarCarritoInvitado();
  }

  // Configurar evento para el botón "Ir a pagar"
  const btnConfirmarPago = document.getElementById("btnConfirmarPago");
  if (btnConfirmarPago) {
    btnConfirmarPago.addEventListener("click", async () => {
      await finalizarCompra();
    });
  }

  // Escuchar cambios en el estado de autenticación (por ejemplo, después del login)
  window.addEventListener('storage', async (e) => {
    if (e.key === 'token') {
      // El token cambió, recargar la página del carrito
      console.log("🔄 Token cambió, recargando carrito...");
      location.reload();
    }
  });

  // También escuchar eventos personalizados de login
  window.addEventListener('userLoggedIn', async () => {
    console.log("🔄 Usuario logueado, recargando carrito...");
    location.reload();
  });

  // Inicializar estado de campos de envío
  toggleCamposEnvio(false);
});

async function inicializarCarritoAutenticado() {
  // Mostrar información del usuario autenticado
  await mostrarInformacionUsuario();

  // Evento de logout usando AuthManager
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await window.authManager.cerrarSesion();
    });
  }

  // Cargar carrito autenticado
  await cargarCarritoAutenticado();
}

async function mostrarInformacionUsuario() {
  try {
    // Obtener información del perfil del usuario
    const token = await window.authManager.getTokenIfAvailable();
    if (token) {
      const perfil = await window.authManager.obtenerPerfil(token);
      
      const perfilSection = document.querySelector('.perfil-section');
      if (perfilSection && perfil) {
        perfilSection.innerHTML = `
          <div class="alert alert-success text-center">
            <h5><i class="fas fa-user-check"></i> Usuario: ${perfil.usuario}</h5>
            <p><i class="fas fa-envelope"></i> ${perfil.email}</p>
            <p class="mb-0">¡Tu carrito se guarda automáticamente!</p>
          </div>
        `;
      }
    }
  } catch (error) {
    console.error("Error al mostrar información del usuario:", error);
  }
}

async function inicializarCarritoInvitado() {
  // Mostrar mensaje de invitado
  mostrarMensajeInvitado();
  
  // Cargar carrito de invitado
  await cargarCarritoInvitado();
}

function mostrarMensajeInvitado() {
  // Buscar un contenedor para mostrar el mensaje
  const perfilSection = document.querySelector('.perfil-section');
  if (perfilSection) {
    perfilSection.innerHTML = `
      <div class="alert alert-info text-center">
        <h5><i class="fas fa-user-guest"></i> Carrito de Invitado</h5>
        <p>Para finalizar tu compra necesitas <a href="/login/" class="alert-link">iniciar sesión</a></p>
        <p>¿No tienes cuenta? <a href="/registro/" class="alert-link">Regístrate aquí</a></p>
      </div>
    `;
  }
}

async function cargarCarritoAutenticado() {
  try {
    const res = await window.authManager.fetchAutenticado("/api/carrito/");
    if (!res.ok) throw new Error("Error al obtener el carrito");

    const data = await res.json();
    const carrito = data.carrito;
    
    mostrarCarrito(carrito, 'authenticated');

  } catch (err) {
    console.error("❌ Error cargando carrito autenticado:", err);
  }
}

async function cargarCarritoInvitado() {
  console.log("🔍 CARRITO: Cargando carrito de invitado");
  try {
    const carrito = await window.authManager.obtenerCarritoInvitado();
    console.log("🔍 CARRITO: Carrito de invitado obtenido:", carrito);
    mostrarCarrito(carrito, 'guest');
  } catch (err) {
    console.error("❌ Error cargando carrito de invitado:", err);
  }
}

function mostrarCarrito(carrito, tipo) {
  console.log("🔍 CARRITO: Mostrando carrito", { carrito, tipo });
  const tbody = document.getElementById("carrito-body");
  const mensajeVacio = document.getElementById("mensaje-vacio");

  if (!tbody) {
    console.error("❌ No se encontró el elemento carrito-body");
    return;
  }

  console.log("🔍 CARRITO: Elemento tbody encontrado:", tbody);
  tbody.innerHTML = "";

  if (carrito.length === 0) {
    console.log("🔍 CARRITO: Carrito vacío, mostrando mensaje");
    if (mensajeVacio) mensajeVacio.style.display = "block";
    
    // Actualizar resumen del carrito a valores vacíos
    actualizarResumenCarrito(0, 0, 0, 0);
    
    // Limpiar opciones de envío
    window.costoEnvioSeleccionado = 0;
    window.opcionesEnvio = null;
    window.opcionEnvioSeleccionada = null;
    
    return;
  }

  console.log("🔍 CARRITO: Carrito tiene", carrito.length, "productos");
  if (mensajeVacio) mensajeVacio.style.display = "none";

  carrito.forEach(item => {
    const fila = document.createElement("tr");
    
    if (tipo === 'authenticated') {
      fila.innerHTML = `
        <td>${item.producto}</td>
        <td>
          <div class="price-info">
            <strong>${formatPrice(item.precio)}</strong><br>
            <small class="text-muted">IVA incluido</small>
          </div>
        </td>
        <td>
          <div class="cantidad-control">
            <button class="btn-cantidad" onclick="cambiarCantidadAutenticado(${item.producto_id}, -1)">-</button>
            <span>${item.cantidad}</span>
            <button class="btn-cantidad" onclick="cambiarCantidadAutenticado(${item.producto_id}, 1)">+</button>
          </div>
        </td>
        <td>
          <div class="price-info">
            <strong>${formatPrice(item.precio * item.cantidad)}</strong><br>
            <small class="text-muted">IVA incluido</small>
          </div>
        </td>
        <td>
          <button class="btn btn-eliminar btn-sm" onclick="eliminarProductoAutenticado(${item.producto_id})">
            <i class="fas fa-trash"></i>
          </button>
        </td>
      `;
    } else {
      fila.innerHTML = `
        <td>${item.producto.nombre}</td>
        <td>
          <div class="price-info">
            <strong>${formatPrice(item.producto.precio)}</strong><br>
            <small class="text-muted">IVA incluido</small>
          </div>
        </td>
        <td>
          <div class="cantidad-control">
            <button class="btn-cantidad" onclick="cambiarCantidadInvitado(${item.id}, -1)">-</button>
            <span>${item.cantidad}</span>
            <button class="btn-cantidad" onclick="cambiarCantidadInvitado(${item.id}, 1)">+</button>
          </div>
        </td>
        <td>
          <div class="price-info">
            <strong>${formatPrice(item.subtotal)}</strong><br>
            <small class="text-muted">IVA incluido</small>
          </div>
        </td>
        <td>
          <button class="btn btn-eliminar btn-sm" onclick="eliminarProductoInvitado(${item.id})">
            <i class="fas fa-trash"></i>
          </button>
        </td>
      `;
    }
    
    tbody.appendChild(fila);
  });

  // Calcular totales con IVA y envío
  const { subtotal, iva, costoEnvio, total } = calcularTotalesCarrito(carrito);
  
  // Actualizar elementos en el DOM
  actualizarResumenCarrito(subtotal, iva, costoEnvio, total);

  // Mostrar/ocultar botón de compra según el tipo
  const btnCompra = document.getElementById("btn-finalizar-compra");
  if (btnCompra) {
    if (tipo === 'guest') {
      btnCompra.textContent = "Iniciar sesión para comprar";
      btnCompra.onclick = () => window.location.href = "/login/";
    } else {
      btnCompra.textContent = "Finalizar compra";
      btnCompra.onclick = finalizarCompra;
    }
  }

  // Agregar event listeners para actualizar totales cuando cambie el tipo de entrega
  const tipoEntregaInputs = document.querySelectorAll('input[name="tipo_entrega"]');
  tipoEntregaInputs.forEach(input => {
    input.addEventListener('change', () => {
      // Mostrar/ocultar campos de dirección
      toggleCamposEnvio(input.value === 'envio');
      
      // Si cambia a "retiro", limpiar costo de envío y opciones
      if (input.value === 'retiro') {
        window.costoEnvioSeleccionado = 0;
        window.opcionesEnvio = null;
        window.opcionEnvioSeleccionada = null;
        
        // Limpiar opciones de envío mostradas
        const shippingOptions = document.getElementById("shippingOptions");
        if (shippingOptions) {
          shippingOptions.innerHTML = `
            <div class="alert alert-info" role="alert">
              <i class="fas fa-store"></i> Has seleccionado retiro en tienda. No se aplicarán costos de envío.
            </div>
          `;
        }
      } else if (input.value === 'envio') {
        // Si cambia a envío, mostrar mensaje para calcular
        const shippingOptions = document.getElementById("shippingOptions");
        if (shippingOptions && !window.opcionesEnvio) {
          shippingOptions.innerHTML = `
            <div class="alert alert-warning" role="alert">
              <i class="fas fa-calculator"></i> Completa los datos de dirección y haz clic en "Calcular costo de envío" para ver las opciones disponibles.
            </div>
          `;
        }
      }
      
      // Recalcular totales
      if (window.carritoActual) {
        const { subtotal, iva, costoEnvio, total } = calcularTotalesCarrito(window.carritoActual);
        actualizarResumenCarrito(subtotal, iva, costoEnvio, total);
      }
    });
  });

  // NO agregar event listeners automáticos para campos de dirección
  // Esto causaba que se reseteara el costo cada vez que el usuario escribía
  // El cálculo se hará solo cuando el usuario haga clic en "Calcular envío"

  // Agregar event listener para el botón de calcular envío
  const btnCalcularEnvio = document.getElementById("calcularEnvio");
  if (btnCalcularEnvio) {
    btnCalcularEnvio.addEventListener('click', () => {
      calcularCostoEnvio();
    });
  }

  // Guardar referencia al carrito actual para recálculos
  window.carritoActual = carrito;
}

// Funciones para carrito autenticado
async function cambiarCantidadAutenticado(productoId, cambio) {
  try {
    const endpoint = cambio > 0 ? "aumentar" : "disminuir";
    const response = await window.authManager.fetchAutenticado(`/api/carrito/${endpoint}/${productoId}/`, {
      method: 'POST'
    });

    if (response.ok) {
      await cargarCarritoAutenticado(); // Recargar carrito
      await window.authManager.actualizarContadorCarrito();
    } else {
      console.error("Error al cambiar cantidad");
    }
  } catch (error) {
    console.error("Error:", error);
  }
}

async function eliminarProductoAutenticado(productoId) {
  try {
    const response = await window.authManager.fetchAutenticado(`/api/carrito/remover/${productoId}/`, {
      method: 'POST'
    });

    if (response.ok) {
      await cargarCarritoAutenticado(); // Recargar carrito
      await window.authManager.actualizarContadorCarrito();
    } else {
      console.error("Error al eliminar producto");
    }
  } catch (error) {
    console.error("Error:", error);
  }
}

// Funciones para carrito de invitado
function cambiarCantidadInvitado(productoId, cambio) {
  const carritoLocal = JSON.parse(localStorage.getItem("carrito_invitado") || "{}");
  const nuevaCantidad = (carritoLocal[productoId] || 0) + cambio;
  
  window.authManager.actualizarCantidadCarritoLocal(productoId, nuevaCantidad);
  cargarCarritoInvitado(); // Recargar carrito
}

function eliminarProductoInvitado(productoId) {
  window.authManager.eliminarDelCarritoLocal(productoId);
  cargarCarritoInvitado(); // Recargar carrito
}

async function finalizarCompra() {
  try {
    // Validar formulario antes de proceder
    if (!validarFormularioCompra()) {
      return; // No proceder si la validación falla
    }

    // Verificar que el usuario está autenticado
    const isAuthenticated = await window.authManager.ensureAuthenticated();
    if (!isAuthenticated) {
      alert("Debes iniciar sesión para finalizar la compra");
      return;
    }

    // Migrar carrito de invitado si existe
    await window.authManager.migrarCarritoInvitado();

    // Verificar que hay productos en el carrito
    const carrito = await obtenerCarritoActual();
    if (!carrito || carrito.length === 0) {
      alert("No hay productos en el carrito");
      return;
    }

    // Calcular total del carrito con IVA y envío (forzar cálculo de envío para el pedido final)
    const { total } = calcularTotalesCarrito(carrito, true);
    
    // Obtener datos del formulario
    const metodoPago = document.getElementById("metodoPago").value;
    const tipoEntrega = document.querySelector('input[name="tipo_entrega"]:checked').value;
    
    // Obtener email del usuario
    const token = await window.authManager.asegurarToken();
    const perfilResponse = await fetch("/api/perfil/", {
      headers: { "Authorization": `Token ${token}` }
    });
    
    let email = "usuario@ejemplo.com"; // valor por defecto
    if (perfilResponse.ok) {
      const perfil = await perfilResponse.json();
      email = perfil.email || email;
    }

    // Preparar datos del pedido
    const datosCrearPedido = {
      email: email,
      monto: total,
      metodo_pago: metodoPago,
      tipo_entrega: tipoEntrega
    };

    // Si es envío, agregar datos de dirección y opción de envío seleccionada
    if (tipoEntrega === 'envio') {
      // Validar que se haya calculado el envío
      if (!window.costoEnvioSeleccionado || window.costoEnvioSeleccionado <= 0) {
        alert("Debes calcular el costo de envío antes de finalizar la compra");
        return;
      }
      
      datosCrearPedido.direccion = document.getElementById("direccion").value;
      datosCrearPedido.comuna = document.getElementById("comuna").value;
      datosCrearPedido.region = document.getElementById("region").value;
      datosCrearPedido.codigo_comuna_chilexpress = "13101"; // Por ahora fijo
      datosCrearPedido.costo_envio = window.costoEnvioSeleccionado;
      
      // Si hay una opción específica seleccionada, incluir sus datos
      if (window.opcionEnvioSeleccionada) {
        datosCrearPedido.opcion_envio = window.opcionEnvioSeleccionada;
      }
    }

    console.log("🔍 CARRITO: Creando pedido con datos:", datosCrearPedido);

    const response = await window.authManager.fetchAutenticado("/crear_pedido/", {
      method: "POST",
      body: JSON.stringify(datosCrearPedido)
    });

    if (response.ok) {
      const data = await response.json();
      const orderId = data.order_id;
      
      console.log("✅ CARRITO: Pedido creado exitosamente con ID:", orderId);
      
      // NO limpiar el carrito aquí - se limpiará en pago_exitoso después del pago
      // await limpiarCarritoDespuesDeCompra();
      
      console.log("✅ CARRITO: Redirigiendo a pago (carrito se mantendrá hasta completar pago)...");
      
      // Redirigir al endpoint de pago que conecta con Transbank
      window.location.href = `/pagar/${orderId}/`;
    } else {
      const errorData = await response.json();
      console.error("❌ CARRITO: Error al crear pedido:", errorData);
      alert(`Error al crear el pedido: ${errorData.error || "Error desconocido"}`);
    }
  } catch (error) {
    console.error("❌ CARRITO: Error al finalizar compra:", error);
    alert("Error al procesar la compra. Por favor, intenta nuevamente.");
  }
}

async function obtenerCarritoActual() {
  const isAuthenticated = await window.authManager.isAuthenticated();
  if (isAuthenticated) {
    try {
      const res = await window.authManager.fetchAutenticado("/api/carrito/");
      if (res.ok) {
        const data = await res.json();
        return data.carrito;
      }
    } catch (error) {
      console.error("Error al obtener carrito autenticado:", error);
    }
  } else {
    return await window.authManager.obtenerCarritoInvitado();
  }
  return [];
}

async function procesarPago() {
  console.log("🔍 CARRITO: Procesando pago...");
  
  // Verificar autenticación
  const isAuthenticated = await window.authManager.isAuthenticated();
  if (!isAuthenticated) {
    alert("Debes iniciar sesión para realizar el pago");
    window.location.href = "/login/";
    return;
  }

  // Verificar que hay productos en el carrito
  const carrito = await obtenerCarritoActual();
  if (!carrito || carrito.length === 0) {
    alert("No hay productos en el carrito para procesar el pago");
    return;
  }

  // Verificar que se seleccionó un método de pago
  const metodoPago = document.getElementById("metodoPago").value;
  if (!metodoPago) {
    alert("Por favor selecciona un método de pago");
    return;
  }

  // Verificar tipo de entrega
  const tipoEntrega = document.querySelector('input[name="tipo_entrega"]:checked');
  if (!tipoEntrega) {
    alert("Por favor selecciona el tipo de entrega");
    return;
  }

  try {
    // Construir datos del pedido
    const datosEnvio = {};
    if (tipoEntrega.value === "envio") {
      datosEnvio.direccion = document.getElementById("direccion").value;
      datosEnvio.region = document.getElementById("region").value;
      datosEnvio.comuna = document.getElementById("comuna").value;
      datosEnvio.telefono = document.querySelector('input[name="telefono"]').value;
      
      if (!datosEnvio.direccion || !datosEnvio.region || !datosEnvio.comuna || !datosEnvio.telefono) {
        alert("Por favor completa todos los datos de envío");
        return;
      }
    }

    const datosPedido = {
      metodo_pago: metodoPago,
      tipo_entrega: tipoEntrega.value,
      datos_envio: datosEnvio
    };

    console.log("🔍 CARRITO: Enviando datos del pedido:", datosPedido);

    // Enviar solicitud al backend
    const response = await window.authManager.fetchAutenticado("/api/checkout/", {
      method: "POST",
      body: JSON.stringify(datosPedido)
    });

    if (response.ok) {
      const result = await response.json();
      console.log("✅ CARRITO: Respuesta del checkout:", result);
      
      if (metodoPago === "tarjeta" && result.redirect_url) {
        // Redirigir a Webpay
        window.location.href = result.redirect_url;
      } else if (metodoPago === "transferencia") {
        // Mostrar información de transferencia y confirmar pedido
        alert("Pedido creado exitosamente. Revisa los datos de transferencia.");
        window.location.href = "/pedidos/";
      } else {
        // Otro caso
        window.location.href = "/pago-exitoso/";
      }
    } else {
      const error = await response.json();
      console.error("❌ CARRITO: Error en checkout:", error);
      alert(error.error || "Error al procesar el pago");
    }
  } catch (error) {
    console.error("❌ CARRITO: Error al procesar pago:", error);
    alert("Error al procesar el pago. Inténtalo nuevamente.");
  }
}

/**
 * Valida el formulario antes de proceder con la compra
 */
function validarFormularioCompra() {
  const metodoPago = document.getElementById("metodoPago").value;
  const tipoEntrega = document.querySelector('input[name="tipo_entrega"]:checked');
  
  // Validar método de pago
  if (!metodoPago) {
    alert("Por favor selecciona un método de pago");
    document.getElementById("metodoPago").focus();
    return false;
  }
  
  // Validar tipo de entrega
  if (!tipoEntrega) {
    alert("Por favor selecciona el tipo de entrega");
    return false;
  }
  
  // Si es envío, validar datos de dirección y que se haya calculado el costo
  if (tipoEntrega.value === 'envio') {
    const direccion = document.getElementById("direccion");
    const comuna = document.getElementById("comuna");
    const region = document.getElementById("region");
    
    if (!direccion || !direccion.value.trim()) {
      alert("Por favor ingresa la dirección de envío");
      if (direccion) direccion.focus();
      return false;
    }
    
    if (!comuna || !comuna.value.trim()) {
      alert("Por favor selecciona la comuna");
      if (comuna) comuna.focus();
      return false;
    }
    
    if (!region || !region.value.trim()) {
      alert("Por favor selecciona la región");
      if (region) region.focus();
      return false;
    }
    
    // Validar que se haya calculado el costo de envío
    if (!window.costoEnvioSeleccionado || window.costoEnvioSeleccionado <= 0) {
      alert("Debes calcular el costo de envío antes de finalizar la compra. Haz clic en 'Calcular costo de envío'.");
      const btnCalcularEnvio = document.getElementById("calcularEnvio");
      if (btnCalcularEnvio) btnCalcularEnvio.focus();
      return false;
    }
  }
  
  return true;
}

/**
 * Calcula totales del carrito (los precios YA incluyen IVA)
 */
function calcularTotalesCarrito(carrito, forzarEnvio = false) {
  let totalConIva = 0;
  
  // Calcular total (los precios ya incluyen IVA)
  carrito.forEach(item => {
    if (item.precio !== undefined && item.cantidad !== undefined) {
      totalConIva += item.precio * item.cantidad;
    } else if (item.subtotal !== undefined) {
      totalConIva += item.subtotal;
    } else if (item.producto && item.producto.precio && item.cantidad) {
      totalConIva += item.producto.precio * item.cantidad;
    }
  });
  
  // Calcular el neto (sin IVA) desde el total con IVA
  const neto = Math.round(totalConIva / 1.19);
  const iva = Math.round(totalConIva - neto);
  
  // Calcular costo de envío 
  let costoEnvio = 0;
  const tipoEntrega = document.querySelector('input[name="tipo_entrega"]:checked');
  
  if (tipoEntrega && tipoEntrega.value === 'envio') {
    // Usar el costo de envío calculado por la API de Chilexpress
    if (window.costoEnvioSeleccionado > 0) {
      costoEnvio = window.costoEnvioSeleccionado;
    } else if (forzarEnvio) {
      // Solo usar valor por defecto si se fuerza y no hay costo calculado
      costoEnvio = 0; // No usar valor fijo, requerir cálculo
    }
  }
  
  // Total final (ya incluye IVA de productos + costo envío)
  const total = totalConIva + costoEnvio;
  
  return { 
    subtotal: neto,      // Precio sin IVA (para mostrar desglosado)
    iva: iva,           // IVA calculado
    costoEnvio: costoEnvio, 
    total: total        // Total final
  };
}

/**
 * Calcula el total del carrito (precios ya incluyen IVA)
 */
function calcularTotalCarrito(carrito) {
  if (!carrito || carrito.length === 0) return 0;
  
  return carrito.reduce((total, item) => {
    // Para carrito autenticado
    if (item.precio !== undefined && item.cantidad !== undefined) {
      return total + (item.precio * item.cantidad);
    }
    // Para carrito de invitado
    if (item.subtotal !== undefined) {
      return total + item.subtotal;
    }
    // Para carrito de invitado con producto anidado
    if (item.producto && item.producto.precio && item.cantidad) {
      return total + (item.producto.precio * item.cantidad);
    }
    return total;
  }, 0);
}

/**
 * Actualiza el resumen del carrito con subtotal, IVA, envío y total
 */
function actualizarResumenCarrito(subtotal, iva, costoEnvio, total) {
  // Actualizar valores directamente (el contenedor ya existe en el HTML)
  const subtotalElem = document.getElementById("subtotal-carrito");
  const ivaElem = document.getElementById("iva-carrito");
  const envioElem = document.getElementById("envio-carrito");
  const envioRow = document.getElementById("envio-row");
  const totalElem = document.getElementById("total-carrito");
  
  if (subtotalElem) subtotalElem.textContent = formatPrice(subtotal);
  if (ivaElem) ivaElem.textContent = formatPrice(iva);
  if (envioElem) envioElem.textContent = formatPrice(costoEnvio);
  if (totalElem) totalElem.textContent = formatPrice(total);
  
  // Mostrar/ocultar fila de envío
  if (envioRow) {
    envioRow.style.display = costoEnvio > 0 ? 'flex' : 'none';
  }
  
  console.log("🔍 RESUMEN: Actualizado", { subtotal, iva, costoEnvio, total });
}

/**
 * Muestra u oculta los campos de dirección según el tipo de entrega
 */
function toggleCamposEnvio(mostrar) {
  const camposEnvio = document.getElementById("envioContainer");
  if (camposEnvio) {
    camposEnvio.style.display = mostrar ? "block" : "none";
  }
}

/**
 * Calcula el costo de envío basado en los datos ingresados usando la API de Chilexpress
 */
async function calcularCostoEnvio() {
  const direccion = document.getElementById("direccion");
  const comuna = document.getElementById("comuna");
  const region = document.getElementById("region");
  
  // Validar que todos los campos estén completos
  if (!direccion || !direccion.value.trim()) {
    alert("Por favor ingresa la dirección de envío");
    if (direccion) direccion.focus();
    return;
  }
  
  if (!comuna || !comuna.value.trim()) {
    alert("Por favor selecciona la comuna");
    if (comuna) comuna.focus();
    return;
  }
  
  if (!region || !region.value.trim()) {
    alert("Por favor selecciona la región");
    if (region) region.focus();
    return;
  }
  
  // Mostrar mensaje de cálculo
  const btnCalcularEnvio = document.getElementById("calcularEnvio");
  if (btnCalcularEnvio) {
    btnCalcularEnvio.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Calculando...';
    btnCalcularEnvio.disabled = true;
  }
  
  try {
    // Obtener carrito actual para calcular peso/volumen
    const carrito = await obtenerCarritoActual();
    if (!carrito || carrito.length === 0) {
      throw new Error("No hay productos en el carrito");
    }
    
    // Preparar datos para la API de Chilexpress
    const datosEnvio = {
      comuna_destino: comuna.value,
      region_destino: region.value,
      direccion_destino: direccion.value.trim(),
      productos: carrito.map(item => ({
        id: item.producto_id || item.id,
        nombre: item.producto?.nombre || item.nombre,
        precio: item.precio || item.producto?.precio,
        cantidad: item.cantidad,
        peso: item.peso || 1, // peso por defecto en kg
        largo: item.largo || 10, // dimensiones por defecto en cm
        ancho: item.ancho || 10,
        alto: item.alto || 10
      }))
    };
    
    console.log("🔍 ENVÍO: Calculando costo con datos:", datosEnvio);
    
    // Decidir si usar autenticación o no
    const isAuthenticated = await window.authManager.isAuthenticated();
    let response;
    
    if (isAuthenticated) {
      // Usuario autenticado - usar fetchAutenticado
      response = await window.authManager.fetchAutenticado("/api/chilexpress/calcular-envio/", {
        method: "POST",
        body: JSON.stringify(datosEnvio)
      });
    } else {
      // Usuario invitado - hacer fetch normal
      response = await fetch("/api/chilexpress/calcular-envio/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''
        },
        body: JSON.stringify(datosEnvio)
      });
    }
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Error al calcular el envío");
    }
    
    const data = await response.json();
    console.log("✅ ENVÍO: Respuesta de Chilexpress:", data);
    
    if (data.success && data.opciones && data.opciones.length > 0) {
      // Guardar opciones de envío globalmente
      window.opcionesEnvio = data.opciones;
      
      // Mostrar opciones de envío disponibles
      mostrarOpcionesEnvio(data.opciones);
      
      // Usar la primera opción por defecto para el cálculo
      const opcionSeleccionada = data.opciones[0];
      window.costoEnvioSeleccionado = opcionSeleccionada.costo || opcionSeleccionada.total;
      window.opcionEnvioSeleccionada = {
        index: 0,
        costo: window.costoEnvioSeleccionado,
        nombre: opcionSeleccionada.nombre || opcionSeleccionada.servicio
      };
      
      // Recalcular totales con el costo real de envío
      if (window.carritoActual) {
        const { subtotal, iva } = calcularTotalesCarrito(window.carritoActual);
        const total = subtotal + iva + window.costoEnvioSeleccionado;
        actualizarResumenCarrito(subtotal, iva, window.costoEnvioSeleccionado, total);
      }
      
      // NO llamar a mostrarMensajeEnvio aquí porque sobrescribe las opciones
      console.log(`✅ ENVÍO: ${data.opciones.length} opciones calculadas exitosamente`);
    } else {
      throw new Error(data.error || "No se encontraron opciones de envío para esta comuna");
    }
    
  } catch (error) {
    console.error("❌ ENVÍO: Error al calcular costo:", error);
    
    // Mostrar error al usuario
    mostrarMensajeEnvio(`Error: ${error.message}`, "danger");
    
    // Limpiar opciones de envío
    window.opcionesEnvio = null;
    window.costoEnvioSeleccionado = 0;
    
    // Recalcular totales sin envío
    if (window.carritoActual) {
      const { subtotal, iva } = calcularTotalesCarrito(window.carritoActual);
      actualizarResumenCarrito(subtotal, iva, 0, subtotal + iva);
    }
    
  } finally {
    // Restaurar botón
    if (btnCalcularEnvio) {
      btnCalcularEnvio.innerHTML = '<i class="fas fa-calculator"></i> Recalcular envío';
      btnCalcularEnvio.disabled = false;
    }
  }
}

/**
 * Muestra las opciones de envío disponibles para que el usuario pueda elegir
 */
function mostrarOpcionesEnvio(opciones) {
  const shippingOptions = document.getElementById("shippingOptions");
  if (!shippingOptions || !opciones || opciones.length === 0) return;
  
  let html = `
    <div class="alert alert-success mb-3" role="alert">
      <h6><i class="fas fa-check-circle"></i> ¡Envío calculado exitosamente!</h6>
      <small>Se encontraron ${opciones.length} opciones de envío. Selecciona la que prefieras:</small>
    </div>
  `;
  
  opciones.forEach((opcion, index) => {
    const precio = opcion.costo || opcion.total || 0;
    const nombre = opcion.nombre || opcion.servicio || `Opción ${index + 1}`;
    const tiempo = opcion.tiempo_entrega || opcion.dias || 'No especificado';
    
    html += `
      <div class="form-check mb-2 p-3 border rounded ${index === 0 ? 'border-primary bg-light' : ''}">
        <input class="form-check-input" type="radio" name="opcion_envio" 
               id="envio_${index}" value="${index}" ${index === 0 ? 'checked' : ''}
               data-costo="${precio}" data-nombre="${nombre}">
        <label class="form-check-label d-flex justify-content-between w-100" for="envio_${index}">
          <div>
            <strong>${nombre}</strong><br>
            <small class="text-muted">Tiempo estimado: ${tiempo}</small>
            ${index === 0 ? '<small class="text-primary"><i class="fas fa-star"></i> Opción seleccionada</small>' : ''}
          </div>
          <div class="text-end">
            <strong class="text-success">${formatPrice(precio)}</strong>
          </div>
        </label>
      </div>
    `;
  });
  
  shippingOptions.innerHTML = html;
  
  // Agregar event listeners para cambio de opción
  const radios = shippingOptions.querySelectorAll('input[name="opcion_envio"]');
  radios.forEach(radio => {
    radio.addEventListener('change', function() {
      if (this.checked) {
        const nuevoCosto = parseFloat(this.dataset.costo);
        const nombreOpcion = this.dataset.nombre;
        
        // Actualizar costo global
        window.costoEnvioSeleccionado = nuevoCosto;
        window.opcionEnvioSeleccionada = {
          index: parseInt(this.value),
          costo: nuevoCosto,
          nombre: nombreOpcion
        };
        
        // Actualizar estilos visuales
        radios.forEach(r => {
          const container = r.closest('.form-check');
          container.classList.remove('border-primary', 'bg-light');
          const selectedLabel = container.querySelector('.text-primary');
          if (selectedLabel) selectedLabel.remove();
        });
        
        const selectedContainer = this.closest('.form-check');
        selectedContainer.classList.add('border-primary', 'bg-light');
        const labelDiv = selectedContainer.querySelector('label > div');
        labelDiv.innerHTML += '<br><small class="text-primary"><i class="fas fa-star"></i> Opción seleccionada</small>';
        
        // Recalcular totales
        if (window.carritoActual) {
          const { subtotal, iva } = calcularTotalesCarrito(window.carritoActual);
          const total = subtotal + iva + nuevoCosto;
          actualizarResumenCarrito(subtotal, iva, nuevoCosto, total);
        }
        
        console.log(`📦 ENVÍO: Opción seleccionada: ${nombreOpcion} - ${formatPrice(nuevoCosto)}`);
      }
    });
  });
}

/**
 * Muestra un mensaje sobre el cálculo de envío (solo para errores)
 */
function mostrarMensajeEnvio(mensaje, tipo = "info") {
  const shippingOptions = document.getElementById("shippingOptions");
  if (shippingOptions) {
    // Solo mostrar mensajes de error, no sobrescribir opciones exitosas
    if (tipo === "danger" || tipo === "warning") {
      shippingOptions.innerHTML = `
        <div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
          <i class="fas fa-exclamation-triangle"></i> ${mensaje}
          <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
      `;
    }
  }
}

/**
 * Limpia el carrito después de una compra exitosa
 * Funciona tanto para usuarios autenticados como invitados
 */
async function limpiarCarritoDespuesDeCompra() {
  try {
    console.log("🧹 CARRITO: Limpiando carrito después de compra exitosa...");
    
    const isAuthenticated = await window.authManager.isAuthenticated();
    
    if (isAuthenticated) {
      // Usuario autenticado - limpiar carrito en el servidor
      console.log("🧹 CARRITO: Limpiando carrito de usuario autenticado");
      
      try {
        const response = await window.authManager.fetchAutenticado("/api/carrito/limpiar/", {
          method: "POST"
        });
        
        if (!response.ok) {
          // Si no existe el endpoint, intentar vaciar manualmente
          console.log("🧹 CARRITO: Endpoint de limpiar no existe, vaciando manualmente...");
          await vaciarCarritoAutenticadoManualmente();
        } else {
          console.log("✅ CARRITO: Carrito de usuario autenticado limpiado exitosamente");
        }
      } catch (error) {
        console.log("🧹 CARRITO: Error con endpoint, vaciando manualmente...");
        await vaciarCarritoAutenticadoManualmente();
      }
    } else {
      // Usuario invitado - limpiar carrito local
      console.log("🧹 CARRITO: Limpiando carrito de usuario invitado");
      localStorage.removeItem("carrito_invitado");
      console.log("✅ CARRITO: Carrito de invitado limpiado exitosamente");
    }
    
    // Limpiar variables globales de envío
    window.costoEnvioSeleccionado = 0;
    window.opcionesEnvio = null;
    window.opcionEnvioSeleccionada = null;
    window.carritoActual = [];
    
    // Actualizar contador del carrito en el header
    await window.authManager.actualizarContadorCarrito();
    
    console.log("✅ CARRITO: Limpieza completa finalizada");
    
  } catch (error) {
    console.error("❌ CARRITO: Error al limpiar carrito:", error);
    // No lanzar error para no interrumpir el flujo de compra
  }
}

/**
 * Vacia el carrito autenticado manualmente eliminando todos los productos
 */
async function vaciarCarritoAutenticadoManualmente() {
  try {
    // Obtener todos los productos del carrito
    const response = await window.authManager.fetchAutenticado("/api/carrito/");
    if (response.ok) {
      const data = await response.json();
      const carrito = data.carrito;
      
      // Eliminar cada producto del carrito
      for (const item of carrito) {
        try {
          await window.authManager.fetchAutenticado(`/api/carrito/remover/${item.producto_id}/`, {
            method: 'POST'
          });
        } catch (error) {
          console.warn(`Error eliminando producto ${item.producto_id}:`, error);
        }
      }
      
      console.log("✅ CARRITO: Carrito autenticado vaciado manualmente");
    }
  } catch (error) {
    console.error("❌ CARRITO: Error vaciando carrito manualmente:", error);
  }
}

