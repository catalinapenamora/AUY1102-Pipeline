# API Externa AutoParts

## 📋 Descripción

La API Externa de AutoParts permite a sistemas externos (como talleres, distribuidores, y otros negocios) consultar nuestro catálogo de productos de forma programática.

## 🎯 Casos de Uso

- **Talleres Mecánicos**: Consultar disponibilidad de repuestos en tiempo real
- **Sistemas de Inventario**: Sincronizar catálogos automáticamente  
- **Distribuidores**: Obtener precios y stock actualizados
- **Aplicaciones Móviles**: Mostrar productos de AutoParts

## 🔑 Autenticación

Todas las peticiones requieren una API Key válida que debe incluirse en:

### Opción 1: Header HTTP (Recomendado)
```http
X-API-Key: TU_API_KEY
```

### Opción 2: Parámetro GET
```
?api_key=TU_API_KEY
```

### API Keys de Prueba
- `DEMO_KEY_2024` - Para testing general
- `TALLER_MANOLO_2024` - Ejemplo del Taller de Manolo

## 📡 Endpoints

### Base URL
```
http://localhost:8000/api/external
```

### 1. Información de la API
```http
GET /api/external/info/
```

### 2. Catálogo de Productos
```http
GET /api/external/catalog/
```

**Parámetros de consulta:**
- `page` - Número de página (default: 1)
- `limit` - Productos por página (default: 20, max: 100)
- `category` - Filtrar por ID de categoría
- `search` - Búsqueda por nombre o descripción
- `min_price` - Precio mínimo
- `max_price` - Precio máximo
- `in_stock` - true/false para filtrar por stock

### 3. Detalle de Producto
```http
GET /api/external/catalog/{product_id}/
```

### 4. Lista de Categorías
```http
GET /api/external/categories/
```

### 5. Búsqueda de Productos
```http
GET /api/external/search/?q=filtro&category=1&limit=10
```

## 📝 Ejemplos de Uso

### Python
```python
import requests

API_BASE = "http://localhost:8000/api/external"
API_KEY = "DEMO_KEY_2024"

headers = {"X-API-Key": API_KEY}

# Buscar filtros de aceite
response = requests.get(
    f"{API_BASE}/search/", 
    headers=headers,
    params={"q": "filtro aceite", "limit": 5}
)

if response.status_code == 200:
    data = response.json()
    productos = data["data"]
    for producto in productos:
        print(f"{producto['nombre']}: ${producto['precio']:,.0f}")
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

const api = axios.create({
    baseURL: 'http://localhost:8000/api/external',
    headers: { 'X-API-Key': 'DEMO_KEY_2024' }
});

// Obtener catálogo
async function obtenerCatalogo() {
    try {
        const response = await api.get('/catalog/', {
            params: { in_stock: true, limit: 10 }
        });
        
        console.log('Productos disponibles:', response.data.data.length);
    } catch (error) {
        console.error('Error:', error.response?.data?.message);
    }
}
```

### cURL
```bash
# Buscar productos
curl -H "X-API-Key: DEMO_KEY_2024" \
     "http://localhost:8000/api/external/search/?q=filtro&limit=5"

# Obtener catálogo con filtros
curl -H "X-API-Key: DEMO_KEY_2024" \
     "http://localhost:8000/api/external/catalog/?category=1&in_stock=true"
```

## 🧪 Pruebas

### Script de Prueba Incluido
```bash
# Ejecutar demo completo
python test_api_externa.py

# Modo manual interactivo
python test_api_externa.py --manual
```

### Documentación Web
Visita: `http://localhost:8000/api-externa/`

## 📊 Formato de Respuesta

Todas las respuestas siguen este formato estándar:

```json
{
  "success": true,
  "timestamp": "2024-12-27T10:30:00.000Z",
  "message": "Operación exitosa",
  "data": [...],
  "meta": {
    "pagination": {...},
    "filters_applied": {...}
  }
}
```

## 🚦 Rate Limiting

- **60 requests por minuto**
- **1000 requests por hora**

## 🛠️ Desarrollo Local

### Requisitos
- Django 4.x
- Python 3.8+
- Base de datos con productos

### Instalación
1. Clona el repositorio
2. Instala dependencias: `pip install -r requirements.txt`
3. Ejecuta migraciones: `python manage.py migrate`
4. Inicia el servidor: `python manage.py runserver`
5. Accede a: `http://localhost:8000/api-externa/`

## 📞 Soporte

### Contacto
- **API**: api@autoparts.cl
- **Soporte Técnico**: soporte@autoparts.cl
- **Horario**: Lunes a Viernes, 9:00 - 18:00

### Solicitar API Key de Producción
Envía un email a `api@autoparts.cl` con:
- Nombre de tu empresa/taller
- Descripción del caso de uso
- Volumen estimado de requests
- Información de contacto

## 🔐 Seguridad

- Las API Keys son únicas por cliente
- Se recomienda usar HTTPS en producción
- Implementar rate limiting en el cliente
- No compartir API Keys públicamente

## 📈 Próximas Funcionalidades

- [ ] Webhooks para notificaciones de stock
- [ ] API para crear pedidos automáticos
- [ ] Autenticación OAuth2
- [ ] Documentación OpenAPI/Swagger
- [ ] SDKs para diferentes lenguajes

## 📄 Licencia

Esta API es propiedad de AutoParts SpA. El uso está sujeto a términos y condiciones específicos.
