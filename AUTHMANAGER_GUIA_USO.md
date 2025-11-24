# 🛡️ AuthManager - Guía de Uso

## 📋 Métodos Disponibles

### 🔴 Métodos INVASIVOS (para páginas que REQUIEREN autenticación)
- `ensureAuthenticated()` - Verifica autenticación y redirige al login si falla
- `asegurarToken()` - Obtiene token válido (puede generar llamadas al servidor)
- `fetchAutenticado()` / `authenticatedFetch()` - Hace peticiones autenticadas

### 🟡 Métodos NO INVASIVOS (para páginas públicas)
- `isAuthenticated()` - Verifica autenticación silenciosamente
- `getTokenIfAvailable()` - Obtiene token si existe, sin forzar obtenerlo

### 🔵 Métodos de UTILIDAD
- `logout()` / `cerrarSesion()` - Cierra sesión completamente
- `clearAuthentication()` - Limpia datos locales sin redirigir
- `actualizarContadorCarrito()` - Actualiza contador híbrido (autenticado + invitado)

### 🛒 Métodos de CARRITO HÍBRIDO
- `agregarAlCarrito(productoId, cantidad)` - Agrega producto (autenticado o invitado)
- `obtenerCarritoInvitado()` - Obtiene productos del carrito de invitado
- `migrarCarritoInvitado()` - Migra carrito de invitado al autenticado
- `actualizarCantidadCarritoLocal(productoId, cantidad)` - Actualiza cantidad en carrito local
- `eliminarDelCarritoLocal(productoId)` - Elimina producto del carrito local

## ✅ Cuándo usar cada método

### Páginas que REQUIEREN autenticación (perfil)
```javascript
// Al cargar la página
const isAuth = await window.AuthManager.ensureAuthenticated();
if (!isAuth) return; // AuthManager maneja la redirección

// Para hacer peticiones
const response = await window.AuthManager.authenticatedFetch("/api/perfil/");
```

### Páginas PÚBLICAS (home, catálogo, detalle de producto)
```javascript
// Al cargar la página
const isAuth = await window.AuthManager.isAuthenticated();
if (isAuth) {
    // Habilitar funciones de usuario logueado
    enableLoggedInFeatures();
} else {
    // Mostrar página en modo público
    showPublicMode();
}

// Para agregar al carrito (funciona para ambos)
const resultado = await window.AuthManager.agregarAlCarrito(productoId, cantidad);
if (resultado.success) {
    if (resultado.type === 'authenticated') {
        alert("Producto agregado al carrito");
    } else {
        alert("Producto agregado al carrito de invitado. Inicia sesión para finalizar tu compra.");
    }
}
```

### Páginas de CARRITO (híbrido - autenticado + invitado)
```javascript
// Al cargar la página
const isAuth = await window.AuthManager.isAuthenticated();
if (isAuth) {
    // Migrar carrito de invitado al autenticado
    await window.AuthManager.migrarCarritoInvitado();
    // Mostrar carrito autenticado
    await cargarCarritoAutenticado();
} else {
    // Mostrar carrito de invitado
    await cargarCarritoInvitado();
}
```

## 🚫 Errores Comunes

❌ **NO HACER:** Usar `asegurarToken()` en páginas públicas
```javascript
// MALO - Fuerza obtener token en página pública
const token = await window.AuthManager.asegurarToken();
```

✅ **SÍ HACER:** Usar `isAuthenticated()` en páginas públicas
```javascript
// BUENO - Verifica sin forzar autenticación
const isAuth = await window.AuthManager.isAuthenticated();
```

## 🎯 Ejemplos por Página

- **Home/Catálogo:** Solo `isAuthenticated()` para mostrar/ocultar elementos
- **Detalle Producto:** `agregarAlCarrito()` funciona para ambos tipos de usuario
- **Perfil:** `ensureAuthenticated()` al inicio (redirige si no está logueado)
- **Carrito:** Híbrido - permite ver y gestionar carrito sin login, pero pide login para comprar

## 🛒 Sistema de Carrito Híbrido

### Características:
- **Usuarios no autenticados:** Pueden agregar productos al carrito local (localStorage)
- **Usuarios autenticados:** Productos se guardan en el servidor
- **Migración automática:** Al hacer login, el carrito local se migra al servidor
- **Contador unificado:** Muestra total de productos independiente del tipo de carrito
- **Compra protegida:** Solo usuarios autenticados pueden finalizar compras
