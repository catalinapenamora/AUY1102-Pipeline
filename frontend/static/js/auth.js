/**
 * Sistema de Autenticación Unificado para AutoParts
 * Este archivo centraliza toda la lógica de autenticación
 */

class AuthManager {
  constructor() {
    this.apiBase = '';
    this.loginUrl = '/login/';
    this.perfilUrl = '/perfil/';
  }

  /**
   * Obtiene o genera un token válido
   * @returns {Promise<string|null>} Token válido o null si falla
   */
  async asegurarToken() {
    let token = localStorage.getItem("token");
    
    // Verificar si el token está vacío o es inválido
    if (!token || token === "undefined" || token === "null" || token.trim() === "") {
      console.log("🔄 Token no encontrado, intentando obtener desde sesión...");
      return await this.obtenerTokenDesdeSesion();
    }

    // Verificar si el token actual es válido
    if (await this.validarToken(token)) {
      return token;
    } else {
      console.log("🔄 Token inválido, intentando obtener nuevo token...");
      return await this.obtenerTokenDesdeSesion();
    }
  }

  /**
   * Obtiene un token desde la sesión del servidor
   * @returns {Promise<string|null>}
   */
  async obtenerTokenDesdeSesion() {
    try {
      // Evitar múltiples llamadas simultáneas
      if (this._obteniendoToken) {
        return null;
      }
      
      this._obteniendoToken = true;
      
      const response = await fetch("/api/login/from-session/", {
        method: "GET",
        credentials: "include"
      });

      if (response.ok) {
        const data = await response.json();
        const token = data.token;
        localStorage.setItem("token", token);
        console.log("✅ Token obtenido desde sesión");
        return token;
      } else {
        console.log("❌ No se pudo obtener token desde sesión");
        this.limpiarYRedirigir();
        return null;
      }
    } catch (error) {
      console.error("❌ Error al obtener token desde sesión:", error);
      this.limpiarYRedirigir();
      return null;
    } finally {
      this._obteniendoToken = false;
    }
  }

  /**
   * Valida si un token es válido haciendo una llamada al API
   * @param {string} token 
   * @returns {Promise<boolean>}
   */
  async validarToken(token) {
    try {
      const response = await fetch("/api/perfil/", {
        headers: {
          "Authorization": `Token ${token}`
        }
      });
      return response.ok;
    } catch (error) {
      console.error("❌ Error al validar token:", error);
      return false;
    }
  }

  /**
   * Obtiene información del perfil del usuario
   * @param {string} token 
   * @returns {Promise<Object|null>}
   */
  async obtenerPerfil(token) {
    try {
      const response = await fetch("/api/perfil/", {
        headers: {
          "Authorization": `Token ${token}`
        }
      });

      if (response.ok) {
        return await response.json();
      } else {
        console.log("❌ Error al obtener perfil");
        this.limpiarYRedirigir();
        return null;
      }
    } catch (error) {
      console.error("❌ Error al obtener perfil:", error);
      this.limpiarYRedirigir();
      return null;
    }
  }

  /**
   * Realiza una petición autenticada
   * @param {string} url 
   * @param {Object} options 
   * @returns {Promise<Response>}
   */
  async fetchAutenticado(url, options = {}) {
    const token = await this.asegurarToken();
    if (!token) {
      throw new Error("No se pudo obtener token válido");
    }

    const headers = {
      "Authorization": `Token ${token}`,
      "Content-Type": "application/json",
      ...options.headers
    };

    return fetch(url, {
      ...options,
      headers
    });
  }

  /**
   * Alias para fetchAutenticado - para compatibilidad
   */
  async authenticatedFetch(url, options = {}) {
    return await this.fetchAutenticado(url, options);
  }

  /**
   * Verifica si el usuario está autenticado y redirige si no lo está
   * @returns {Promise<boolean>} true si está autenticado, false si no
   */
  async ensureAuthenticated() {
    try {
      const token = await this.asegurarToken();
      if (!token) {
        return false;
      }

      // Verificar que el token sea válido haciendo una petición al perfil
      const isValid = await this.validarToken(token);
      if (!isValid) {
        this.limpiarYRedirigir();
        return false;
      }

      return true;
    } catch (error) {
      console.error("❌ Error en ensureAuthenticated:", error);
      this.limpiarYRedirigir();
      return false;
    }
  }

  /**
   * Verifica autenticación de forma silenciosa (sin redirigir automáticamente)
   * @returns {Promise<boolean>} true si está autenticado, false si no
   */
  async isAuthenticated() {
    try {
      const token = localStorage.getItem("token");
      if (!token || token === "undefined" || token === "null" || token.trim() === "") {
        return false;
      }

      // Verificar si el token es válido
      return await this.validarToken(token);
    } catch (error) {
      console.error("❌ Error al verificar autenticación:", error);
      return false;
    }
  }

  /**
   * Obtiene un token válido para páginas públicas (sin forzar login)
   * @returns {Promise<string|null>} Token válido o null si no hay
   */
  async getTokenIfAvailable() {
    try {
      const token = localStorage.getItem("token");
      if (!token || token === "undefined" || token === "null" || token.trim() === "") {
        return null;
      }

      // Verificar si el token es válido
      const isValid = await this.validarToken(token);
      return isValid ? token : null;
    } catch (error) {
      console.error("❌ Error al obtener token:", error);
      return null;
    }
  }

  /**
   * Cierra sesión completamente
   */
  async cerrarSesion() {
    try {
      // Intentar cerrar sesión en el servidor
      await fetch('/logout/', { 
        method: 'GET', 
        credentials: 'include' 
      });
    } catch (e) {
      console.warn("No se pudo cerrar sesión en el backend:", e);
    }

    // Limpiar datos locales
    localStorage.clear();
    sessionStorage.clear();
    
    // Redirigir al home
    window.location.href = "/";
  }

  /**
   * Alias para cerrarSesion() - para compatibilidad
   */
  async logout() {
    return await this.cerrarSesion();
  }

  /**
   * Limpia autenticación local sin redirigir
   */
  clearAuthentication() {
    localStorage.removeItem("token");
    sessionStorage.clear();
  }

  /**
   * Limpia datos locales y redirige al login
   */
  limpiarYRedirigir() {
    // Evitar múltiples redirecciones
    if (this._redirigiendo) {
      return;
    }
    
    this._redirigiendo = true;
    
    localStorage.removeItem("token");
    
    // Solo redirigir si no estamos ya en login
    if (!window.location.pathname.includes('/login')) {
      console.log("🔄 Redirigiendo al login...");
      window.location.href = this.loginUrl;
    }
  }

  /**
   * Verifica sesión y redirige a una página específica
   * @param {Event} event 
   * @param {string} destino 
   */
  async verificarSesionYRedirigir(event, destino) {
    if (event) event.preventDefault();

    // Intentar obtener token de forma agresiva para páginas protegidas
    const token = await this.asegurarToken();
    if (!token) return;

    try {
      const validar = await fetch("/api/perfil/", {
        headers: { "Authorization": `Token ${token}` }
      });

      if (validar.ok) {
        window.location.href = destino;
      } else {
        this.limpiarYRedirigir();
      }
    } catch (error) {
      console.error("❌ Error al validar token:", error);
      this.limpiarYRedirigir();
    }
  }

  /**
   * Inicializa eventos de autenticación en el header
   */
  inicializarEventosHeader() {
    // Evento para el icono de login/perfil - NO forzar autenticación
    const loginIcon = document.getElementById("login-icon");
    if (loginIcon) {
      loginIcon.addEventListener("click", async (e) => {
        e.preventDefault();
        // Solo verificar si ya hay un token válido, no forzar obtenerlo
        const token = localStorage.getItem("token");
        if (token && await this.validarToken(token)) {
          window.location.href = this.perfilUrl;
        } else {
          // Si no hay token válido, ir al login
          window.location.href = this.loginUrl;
        }
      });
    }

    // Eventos para el carrito - PERMITIR acceso sin autenticación
    const carritoLink = document.getElementById("carrito-link");
    const carritoIcon = document.getElementById("carrito-icon");

    if (carritoLink) {
      carritoLink.addEventListener("click", (e) => {
        e.preventDefault();
        window.location.href = "/carrito/";
      });
    }

    if (carritoIcon) {
      carritoIcon.addEventListener("click", (e) => {
        e.preventDefault();
        window.location.href = "/carrito/";
      });
    }

    // Actualizar contador del carrito (autenticado + invitado)
    this.actualizarContadorCarritoHibrido();
  }

  /**
   * Actualiza el contador de productos en el carrito SOLO si hay autenticación
   */
  async actualizarContadorCarritoSiEstaAutenticado() {
    try {
      // Verificar si hay token sin forzar obtenerlo
      const token = localStorage.getItem("token");
      if (!token || token === "undefined" || token === "null" || token.trim() === "") {
        // No hay token, ocultar contador
        const contador = document.getElementById("carrito-count");
        if (contador) {
          contador.style.display = "none";
        }
        return;
      }

      // Si hay token, intentar obtener contador
      const response = await fetch("/carrito/contador/", {
        headers: {
          "Authorization": `Token ${token}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        const contador = document.getElementById("carrito-count");
        if (contador) {
          contador.textContent = data.count || 0;
          contador.style.display = data.count > 0 ? "inline" : "none";
        }
      } else {
        // Token inválido, ocultar contador
        const contador = document.getElementById("carrito-count");
        if (contador) {
          contador.style.display = "none";
        }
      }
    } catch (error) {
      // Error en la petición, ocultar contador
      const contador = document.getElementById("carrito-count");
      if (contador) {
        contador.style.display = "none";
      }
    }
  }

  /**
   * Actualiza el contador híbrido (autenticado + invitado)
   */
  async actualizarContadorCarritoHibrido() {
    try {
      const totalItems = await this.obtenerContadorCarritoTotal();
      
      const contador = document.getElementById("carrito-count");
      if (contador) {
        contador.textContent = totalItems;
        contador.style.display = totalItems > 0 ? "inline" : "none";
      }
    } catch (error) {
      console.error("Error al actualizar contador híbrido:", error);
    }
  }

  /**
   * Método público para actualizar contador (para usar desde otras páginas)
   */
  async actualizarContadorCarrito() {
    return await this.actualizarContadorCarritoHibrido();
  }

  /**
   * Agrega producto al carrito (autenticado o invitado)
   */
  async agregarAlCarrito(productoId, cantidad = 1) {
    try {
      // Verificar si hay autenticación
      const token = await this.getTokenIfAvailable();
      
      if (token) {
        // Usuario autenticado - agregar al carrito del servidor
        const response = await fetch("/carrito/agregar/", {
          method: "POST",
          headers: {
            "Authorization": `Token ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            producto_id: productoId,
            cantidad: cantidad
          })
        });

        if (response.ok) {
          // Actualizar contador del servidor
          await this.actualizarContadorCarrito();
          return { success: true, type: 'authenticated' };
        } else {
          const errorData = await response.json();
          return { success: false, error: errorData.error || "Error al agregar al carrito" };
        }
      } else {
        // Usuario invitado - agregar al carrito local
        this.agregarAlCarritoLocal(productoId, cantidad);
        this.actualizarContadorCarritoLocal();
        return { success: true, type: 'guest' };
      }
    } catch (error) {
      console.error("Error al agregar al carrito:", error);
      return { success: false, error: "Error al agregar al carrito" };
    }
  }

  /**
   * Agrega producto al carrito local (invitado)
   */
  agregarAlCarritoLocal(productoId, cantidad = 1) {
    let carritoLocal = JSON.parse(localStorage.getItem("carrito_invitado") || "{}");
    
    if (carritoLocal[productoId]) {
      carritoLocal[productoId] += cantidad;
    } else {
      carritoLocal[productoId] = cantidad;
    }
    
    localStorage.setItem("carrito_invitado", JSON.stringify(carritoLocal));
    console.log("✅ Producto agregado al carrito de invitado");
  }

  /**
   * Actualiza el contador del carrito local
   */
  actualizarContadorCarritoLocal() {
    const carritoLocal = JSON.parse(localStorage.getItem("carrito_invitado") || "{}");
    const totalItems = Object.values(carritoLocal).reduce((sum, cantidad) => sum + cantidad, 0);
    
    const contador = document.getElementById("carrito-count");
    if (contador) {
      contador.textContent = totalItems;
      contador.style.display = totalItems > 0 ? "inline" : "none";
    }
  }

  /**
   * Obtiene el conteo total del carrito (autenticado + invitado)
   */
  async obtenerContadorCarritoTotal() {
    const token = await this.getTokenIfAvailable();
    
    if (token) {
      // Usuario autenticado - obtener del servidor
      try {
        const response = await fetch("/carrito/contador/", {
          headers: { "Authorization": `Token ${token}` }
        });
        
        if (response.ok) {
          const data = await response.json();
          return data.count || 0;
        }
      } catch (error) {
        console.error("Error al obtener contador del servidor:", error);
      }
    }
    
    // Usuario invitado - obtener del localStorage
    const carritoLocal = JSON.parse(localStorage.getItem("carrito_invitado") || "{}");
    return Object.values(carritoLocal).reduce((sum, cantidad) => sum + cantidad, 0);
  }

  /**
   * Migra carrito de invitado al carrito autenticado
   */
  async migrarCarritoInvitado() {
    const carritoLocal = JSON.parse(localStorage.getItem("carrito_invitado") || "{}");
    
    if (Object.keys(carritoLocal).length === 0) {
      return; // No hay productos en carrito local
    }

    const token = await this.getTokenIfAvailable();
    if (!token) {
      console.warn("No se puede migrar carrito sin autenticación");
      return;
    }

    try {
      // Agregar cada producto del carrito local al carrito autenticado
      for (const [productoId, cantidad] of Object.entries(carritoLocal)) {
        await fetch("/carrito/agregar/", {
          method: "POST",
          headers: {
            "Authorization": `Token ${token}`,
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            producto_id: parseInt(productoId),
            cantidad: cantidad
          })
        });
      }

      // Limpiar carrito local después de migrar
      localStorage.removeItem("carrito_invitado");
      console.log("✅ Carrito de invitado migrado al carrito autenticado");
      
      // Actualizar contador
      await this.actualizarContadorCarrito();
    } catch (error) {
      console.error("Error al migrar carrito de invitado:", error);
    }
  }

  /**
   * Obtiene los productos del carrito de invitado con información completa
   */
  async obtenerCarritoInvitado() {
    const carritoLocal = JSON.parse(localStorage.getItem("carrito_invitado") || "{}");
    const productosCarrito = [];

    console.log("🔍 CARRITO INVITADO: Carrito local:", carritoLocal);

    for (const [productoId, cantidad] of Object.entries(carritoLocal)) {
      try {
        console.log(`🔍 CARRITO INVITADO: Obteniendo producto ${productoId}...`);
        // Obtener información del producto desde la API pública
        const response = await fetch(`/api/productos/${productoId}/`);
        console.log(`🔍 CARRITO INVITADO: Respuesta para producto ${productoId}:`, response.status);
        
        if (response.ok) {
          const producto = await response.json();
          console.log(`✅ CARRITO INVITADO: Producto ${productoId} obtenido:`, producto);
          productosCarrito.push({
            id: parseInt(productoId),
            producto: producto,
            cantidad: cantidad,
            subtotal: producto.precio * cantidad
          });
        } else {
          console.error(`❌ CARRITO INVITADO: Error al obtener producto ${productoId}:`, response.status);
        }
      } catch (error) {
        console.error(`❌ CARRITO INVITADO: Error al obtener producto ${productoId}:`, error);
      }
    }

    console.log("🔍 CARRITO INVITADO: Productos finales:", productosCarrito);
    return productosCarrito;
  }

  /**
   * Actualiza cantidad de producto en carrito de invitado
   */
  actualizarCantidadCarritoLocal(productoId, nuevaCantidad) {
    let carritoLocal = JSON.parse(localStorage.getItem("carrito_invitado") || "{}");
    
    if (nuevaCantidad <= 0) {
      delete carritoLocal[productoId];
    } else {
      carritoLocal[productoId] = nuevaCantidad;
    }
    
    localStorage.setItem("carrito_invitado", JSON.stringify(carritoLocal));
    this.actualizarContadorCarritoLocal();
  }

  /**
   * Elimina producto del carrito de invitado
   */
  eliminarDelCarritoLocal(productoId) {
    let carritoLocal = JSON.parse(localStorage.getItem("carrito_invitado") || "{}");
    delete carritoLocal[productoId];
    localStorage.setItem("carrito_invitado", JSON.stringify(carritoLocal));
    this.actualizarContadorCarritoLocal();
  }
}



// Auto-inicialización para el header
document.addEventListener("DOMContentLoaded", function() {
  window.authManager.inicializarEventosHeader();
});

if (!window.authManager) {
  window.authManager = new AuthManager();
  window.AuthManager = window.authManager; // Alias opcional
}