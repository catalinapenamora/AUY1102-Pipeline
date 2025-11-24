# 🔐 Sistema de Autenticación Unificado - AutoParts

## 📋 **Resumen de Cambios**

Hemos refactorizado completamente el sistema de autenticación del proyecto AutoParts para eliminar inconsistencias y centralizar toda la lógica de manejo de tokens y sesiones.

## 🏗️ **Arquitectura Nueva**

### 1. **AuthManager Centralizado** (`auth.js`)
- **Ubicación**: `/frontend/static/js/auth.js`
- **Propósito**: Clase única que maneja toda la autenticación
- **Funcionalidades**:
  - ✅ Gestión automática de tokens
  - ✅ Validación de tokens
  - ✅ Obtención de tokens desde sesión
  - ✅ Peticiones autenticadas
  - ✅ Manejo de errores consistente
  - ✅ Limpieza de sesión al cerrar

### 2. **Scripts Actualizados**
Todos los scripts de JavaScript ahora usan el `AuthManager`:

- **`header.js`**: Simplificado, solo maneja eventos específicos del header
- **`carrito.js`**: Usa `window.authManager.fetchAutenticado()` para todas las peticiones
- **`perfil.js`**: Usa `window.authManager.obtenerPerfil()` 
- **`detalle.js`**: Usa `window.authManager.fetchAutenticado()` para agregar productos

### 3. **Templates Actualizados**
- **`base/header.html`**: Incluye `auth.js` ANTES que otros scripts
- **`carrito.html`**: Incluye scripts en orden correcto
- **`perfil.html`**: Incluye `auth.js` y `perfil.js`
- **`detalle.html`**: Incluye `auth.js` y `detalle.js`

### 4. **Backend Mejorado**
- **`TokenDesdeSesionView`**: Mejor manejo de errores y logging
- **`PerfilUsuarioView`**: Información más completa y manejo de errores
- **`CarritoContadorView`**: Autenticación consistente

## 🔧 **Problemas Solucionados**

### ❌ **Antes**:
1. **Duplicación de código**: Función `asegurarToken()` en múltiples archivos
2. **Inconsistencias**: Diferentes maneras de manejar tokens y errores
3. **Mezcla de sistemas**: Token y Session authentication sin coordinación
4. **Rutas inconsistentes**: `/login/` vs `/login`
5. **Manejo de errores**: Cada archivo manejaba errores diferente
6. **Sin centralización**: No había un punto único de control

### ✅ **Después**:
1. **Código centralizado**: Una sola clase `AuthManager` 
2. **Consistencia total**: Todos los archivos usan la misma lógica
3. **Sistema híbrido coordinado**: Token y Session trabajan juntos
4. **Rutas consistentes**: Todas apuntan a `/login/`
5. **Manejo unificado**: Todos los errores se manejan igual
6. **Control centralizado**: `AuthManager` controla todo

## 🚀 **Uso del Nuevo Sistema**

### **Para obtener un token válido**:
```javascript
const token = await window.authManager.asegurarToken();
if (!token) {
    // Usuario será redirigido automáticamente al login
    return;
}
```

### **Para hacer peticiones autenticadas**:
```javascript
const response = await window.authManager.fetchAutenticado("/api/carrito/", {
    method: "POST",
    body: JSON.stringify(data)
});
```

### **Para obtener perfil del usuario**:
```javascript
const perfil = await window.authManager.obtenerPerfil(token);
```

### **Para cerrar sesión**:
```javascript
await window.authManager.cerrarSesion();
```

### **Para verificar sesión y redirigir**:
```javascript
loginIcon.addEventListener("click", async (e) => {
    await window.authManager.verificarSesionYRedirigir(e, "/perfil/");
});
```

## 📁 **Estructura de Archivos**

```
frontend/static/js/
├── auth.js          ← 🆕 AuthManager centralizado
├── header.js        ← ✅ Simplificado
├── carrito.js       ← ✅ Refactorizado
├── perfil.js        ← ✅ Refactorizado  
└── detalle.js       ← ✅ Refactorizado

frontend/templates/
├── base/header.html ← ✅ Incluye auth.js
├── carrito.html     ← ✅ Scripts actualizados
├── perfil.html      ← ✅ Scripts actualizados
└── detalle.html     ← ✅ Scripts actualizados

backend/tienda/
└── views.py         ← ✅ Vistas mejoradas
```

## 🔄 **Flujo de Autenticación**

1. **Usuario accede a página** → `AuthManager` se inicializa automáticamente
2. **Página necesita autenticación** → Llama a `asegurarToken()`
3. **Si hay token en localStorage** → Lo valida con el servidor
4. **Si token es válido** → Lo devuelve
5. **Si no hay token o es inválido** → Intenta obtener desde sesión
6. **Si obtiene token desde sesión** → Lo guarda en localStorage
7. **Si falla todo** → Redirige a login automáticamente

## 🐛 **Debugging**

El sistema incluye logging extensivo en consola:
- ✅ `"Token obtenido desde sesión"`
- ✅ `"Usuario autenticado en página de detalle"`
- ❌ `"Error al validar token:"`
- 🔄 `"Token no encontrado, intentando obtener desde sesión..."`

## 🎯 **Ventajas del Nuevo Sistema**

1. **Mantenibilidad**: Un solo archivo que cambiar para autenticación
2. **Consistencia**: Comportamiento idéntico en toda la app
3. **Robustez**: Mejor manejo de errores y casos edge
4. **Escalabilidad**: Fácil agregar nuevas funcionalidades
5. **Debug**: Logging centralizado y claro
6. **UX**: Transiciones suaves entre estados de autenticación

## 🔄 **Próximos Pasos**

1. **Probar en diferentes navegadores**
2. **Verificar en modo incógnito**
3. **Testear con sesiones expiradas**
4. **Verificar funcionamiento con múltiples pestañas**
5. **Optimizar performance si es necesario**

---

¡El sistema de autenticación ahora es mucho más robusto y mantenible! 🎉
