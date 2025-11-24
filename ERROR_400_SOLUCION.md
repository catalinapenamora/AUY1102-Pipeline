# Corrección Error 400 - Crear Pedido

## 🔍 Análisis del problema

**Error**: `Bad Request: /crear_pedido/ HTTP/1.1 400`

**Causa identificada**: Faltan datos requeridos o hay inconsistencias en el formato de datos enviados desde el frontend al backend.

## 🛠️ Correcciones realizadas

### 1. **Problema con códigos de comuna**
**Antes**: El backend usaba un diccionario limitado de comunas hardcodeado
```python
CODIGOS_COMUNAS = {
    "Santiago": "13101",
    "Ñuñoa": "13114",
    # Solo pocas comunas...
}
```

**Después**: Ahora se envía el código de comuna directamente desde el frontend
```javascript
datos.codigo_comuna_chilexpress = comunaSelect?.value || "";
```

### 2. **Problema con nombres de región/comuna**
**Antes**: Se enviaba el `value` (ID numérico) de los selects
```javascript
datos.comuna = document.getElementById("comuna")?.value || "";
datos.region = document.getElementById("region")?.value || "";
```

**Después**: Se envía el texto descriptivo (nombre real)
```javascript
datos.comuna = comunaSelect?.options[comunaSelect.selectedIndex]?.text || "";
datos.region = regionSelect?.options[regionSelect.selectedIndex]?.text || "";
```

### 3. **Mejores validaciones y debugging**
**Backend**: Agregado logging detallado
```python
print("🔍 Datos recibidos para crear pedido:", data)
print(f"🚚 Datos de envío - Dirección: {pedido.direccion}, Comuna: {pedido.comuna}...")
```

**Frontend**: Agregado logging en consola
```javascript
console.log("📋 Datos base del pedido:", datos);
console.log("📤 Enviando datos al servidor:", datos);
```

### 4. **Procesamiento mejorado del monto**
**Antes**: Regex simple que podía fallar
```javascript
const monto = Number(totalTexto.replace(/[^0-9]/g, ''));
```

**Después**: Limpieza más robusta del formato monetario
```javascript
const montoFinal = Number(montoTexto.replace(/[$\s\.,]/g, ''));
```

## 📋 Datos que ahora se envían correctamente

### Para **Retiro en tienda**:
```json
{
  "email": "usuario@email.com",
  "metodo_pago": "tarjeta",
  "monto": 50000,
  "tipo_entrega": "retiro"
}
```

### Para **Envío a domicilio**:
```json
{
  "email": "usuario@email.com",
  "metodo_pago": "tarjeta", 
  "monto": 55000,
  "tipo_entrega": "envio",
  "direccion": "Av. Principal 123",
  "comuna": "Santiago",
  "region": "Región Metropolitana de Santiago",
  "codigo_comuna_chilexpress": "13101"
}
```

## ✅ Validaciones del backend

El backend ahora valida:
1. ✅ Presencia de campos obligatorios (email, monto, método, tipo)
2. ✅ Tipo de entrega válido ("retiro" o "envio")
3. ✅ Para envíos: dirección, comuna, región y código de comuna
4. ✅ Carrito activo y con productos

## 🧪 Para verificar que funciona

1. **Abrir consola del navegador** (F12)
2. **Agregar productos al carrito**
3. **Seleccionar tipo de entrega**:
   - **Retiro**: Debería mostrar info de la tienda
   - **Envío**: Completar formulario y calcular costo
4. **Hacer clic en "Ir a pagar"**
5. **Verificar en consola**:
   - Logs de datos enviados
   - Respuesta del servidor
   - En caso de error, mensaje detallado

## 🎯 Resultado esperado

✅ **Status 200**: Pedido creado correctamente, redirige a pago
❌ **Status 400**: Error específico mostrado en consola y alerta

Los logs te ayudarán a identificar exactamente qué dato está faltando o es incorrecto.
