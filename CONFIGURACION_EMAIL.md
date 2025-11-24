# Configuración de Email para AutoParts

## Opciones de Configuración

### Opción 1: Gmail (Recomendado para desarrollo/testing)

1. **Configurar Gmail App Password:**
   - Ve a tu cuenta de Google → Seguridad
   - Habilita verificación en 2 pasos
   - Ve a "Contraseñas de aplicaciones"
   - Genera una contraseña para "Mail"
   - Usa esa contraseña (NO tu contraseña normal)

2. **Configuración en settings.py:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'
EMAIL_HOST_PASSWORD = 'tu-app-password-de-16-caracteres'
DEFAULT_FROM_EMAIL = 'AutoParts <tu-email@gmail.com>'
```

### Opción 2: Servidor SMTP Personalizado (Producción)

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'mail.tudominio.com'
EMAIL_PORT = 587  # o 465 para SSL
EMAIL_USE_TLS = True  # o EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'ventas@autoparts.cl'
EMAIL_HOST_PASSWORD = 'tu-password-smtp'
DEFAULT_FROM_EMAIL = 'AutoParts <ventas@autoparts.cl>'
```

### Opción 3: Solo Consola (Para desarrollo sin emails reales)

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Configuración de Variables de Entorno (Recomendado)

Para seguridad, usa variables de entorno:

1. **Crear archivo `.env` en la raíz del proyecto:**
```
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
ADMIN_EMAIL=admin@autoparts.cl
```

2. **Instalar python-decouple:**
```bash
pip install python-decouple
```

3. **Actualizar settings.py:**
```python
from decouple import config

EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@autoparts.cl')
```

## Uso del Sistema

### Automático
Los emails se envían automáticamente al generar comprobantes:

```python
# En views.py - ya implementado
resultado_pdf = generar_factura_automatica(
    pedido, 
    productos, 
    cliente_data, 
    perfil_usuario, 
    enviar_email=True  # ← Esto activa el envío automático
)
```

### Manual via API
```bash
# Reenviar comprobante
curl -X POST http://localhost:8000/api/factura/reenviar-email/ \
  -H "Authorization: Token tu-token" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORDER123",
    "email_destino": "cliente@email.com"
  }'
```

### Manual desde el shell de Django
```python
python manage.py shell

>>> from tienda.email_manager import enviar_comprobante_automatico
>>> from tienda.models import Pedido
>>> pedido = Pedido.objects.get(order_id='ORDER123')
>>> resultado = enviar_comprobante_automatico(
...     pedido=pedido,
...     pdf_path='/path/to/comprobante.pdf',
...     numero_comprobante='COMP-123'
... )
>>> print(resultado)
```

## Pruebas

### Prueba básica:
```bash
cd backend
python manage.py shell < test_email.py
```

### Prueba con pedido real:
```python
python manage.py shell

>>> from tienda.models import Pedido, Factura
>>> pedido = Pedido.objects.filter(estado='pagado').first()
>>> factura = Factura.objects.get(pedido=pedido)
>>> from tienda.views import reenviar_comprobante_email
>>> # Usar la API o el email_manager directamente
```

## Solución de Problemas

### Error: "SMTPAuthenticationError"
- Verifica que uses App Password, no la contraseña normal
- Verifica que la verificación en 2 pasos esté habilitada

### Error: "Connection refused"
- Verifica el host y puerto SMTP
- Verifica tu conexión a internet
- Algunos ISPs bloquean puerto 587

### Error: "File not found" (PDF)
- Verifica que el archivo PDF existe en MEDIA_ROOT
- Verifica permisos de lectura del archivo

### Emails no llegan
- Revisa la carpeta de spam
- Verifica la dirección del remitente
- Usa un dominio con SPF/DKIM configurado para producción

## Logs

Los logs del sistema se guardan en:
- Console: errores de SMTP
- Django logs: `logger.info()` y `logger.error()`
- Notificaciones automáticas al admin cuando hay errores

## Seguridad

- ✅ Nunca hardcodees passwords en el código
- ✅ Usa variables de entorno
- ✅ Usa App Passwords para Gmail
- ✅ Habilita TLS/SSL
- ✅ Valida direcciones de email antes de enviar
- ✅ Limita la frecuencia de envío para evitar spam
