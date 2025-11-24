# Configuración de Comuna de Origen - Chilexpress

## 🏢 Comuna de Origen del Proyecto

**Comuna**: Santiago Centro  
**Dirección**: Diez de Julio 525, Santiago Centro  
**Códigos utilizados**:
- Para API de Tarifas: `"STGO"`
- Para API de Órdenes: `"13101"`

## 📍 ¿Por qué importa la comuna de origen?

Las tarifas de Chilexpress **SÍ VARÍAN** según la distancia entre la comuna de origen y destino, incluso dentro de la misma región. Por ejemplo:

### Desde Santiago Centro a:
- **Ñuñoa**: $3.500 ⭐ (cercano)
- **Providencia**: $3.200 ⭐ (muy cercano)  
- **Maipú**: $4.800 💰 (más lejos)
- **Puente Alto**: $5.200 💰 (distante)
- **Melipilla**: $7.500 💸 (muy distante)

## 🔧 Configuración actual

### 1. **API de Cálculo de Tarifas** (`calcular_tarifas_envio`)
```python
"originCountyCode": "STGO"  # Santiago Centro
```

### 2. **API de Generación de Órdenes** (`generar_envio_chilexpress`)
```python  
"origin_commune_code": "13101"  # Santiago Centro
```

## 📊 Códigos de Comunas Frecuentes

| Comuna | Código Rating API | Código Transport API |
|--------|------------------|---------------------|
| Santiago Centro | `STGO` | `13101` |
| Providencia | `PROV` | `13115` |
| Las Condes | `LCON` | `13114` |
| Ñuñoa | `NUNO` | `13120` |
| Maipú | `MAIP` | `13119` |

## ⚙️ Cambiar Comuna de Origen

Si necesitas cambiar la comuna de origen, modifica:

### En `chilexpress.py`:
```python
def obtener_codigo_origen():
    return "STGO"  # Cambiar aquí el código
```

### En `chilexpress.js`:
```javascript
<strong>Dirección:</strong> Nueva Dirección, Nueva Comuna<br>
<strong>Comuna:</strong> Nueva Comuna<br>
```

## 🧪 Para Probar Variaciones de Precio

1. **Elige comunas cercanas**: Santiago, Providencia, Ñuñoa
   - Tarifas más bajas ($3.000 - $4.000)

2. **Elige comunas lejanas**: Puente Alto, Maipú, San Bernardo  
   - Tarifas más altas ($5.000 - $8.000)

3. **Elige comunas rurales**: Melipilla, Talagante
   - Tarifas más altas ($7.000 - $12.000)

## 🎯 Resultado Esperado

Con **Santiago Centro** como origen:
- ✅ Tarifas precisas basadas en distancia real
- ✅ Mejor experiencia para clientes (precios competitivos para zonas céntricas)
- ✅ Coherencia con la dirección física de retiro

## 📝 Notas Importantes

1. **Chilexpress usa 2 APIs diferentes** con códigos distintos
2. **Las tarifas SÍ varían** por comuna, no son fijas por región
3. **El código debe coincidir** con la dirección real de la tienda
4. **Testing**: Probar con varias comunas para verificar variaciones
