# =======================================
# CONFIGURACIÓN DE FACTURACIÓN ELECTRÓNICA
# =======================================

# Agregar estas variables a tu archivo settings.py o .env

# Configuración de Tributi
TRIBUTI_API_KEY = 'tu_api_key_de_tributi'  # Obtener de https://tributi.com/
TRIBUTI_RUT_EMPRESA = '76.123.456-7'  # RUT de tu empresa
TRIBUTI_TEST_MODE = True  # Cambiar a False en producción

# Configuración de email para envío de facturas
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # O tu proveedor de email
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_email@empresa.com'
EMAIL_HOST_PASSWORD = 'tu_password'
DEFAULT_FROM_EMAIL = 'tu_email@empresa.com'

# Configuración para archivos PDF
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# =======================================
# PASOS PARA CONFIGURAR TRIBUTI
# =======================================

"""
1. Registrarse en Tributi:
   - Ir a https://tributi.com/
   - Crear cuenta empresarial
   - Verificar RUT con SII

2. Obtener credenciales:
   - API Key desde el panel de Tributi
   - Configurar datos de la empresa

3. Configurar en Django:
   - Agregar las variables arriba en settings.py
   - Instalar dependencias: pip install reportlab requests

4. Hacer migraciones:
   python manage.py makemigrations
   python manage.py migrate

5. Probar en modo sandbox:
   - TRIBUTI_TEST_MODE = True
   - Realizar compras de prueba

6. Activar producción:
   - TRIBUTI_TEST_MODE = False
   - Verificar que todo funcione correctamente
"""

# =======================================
# ALTERNATIVAS GRATUITAS SI TRIBUTI NO FUNCIONA
# =======================================

"""
1. SimpleFact:
   - 20 documentos/mes gratis
   - API similar a Tributi
   - URL: https://simplefact.cl/

2. LibreDTE (Open Source):
   - Completamente gratis
   - Requiere más configuración
   - URL: https://libredte.cl/

3. Solución custom:
   - Solo PDFs de comprobante (no válidos SII)
   - Usar solo ReportLab
   - Sin límites
"""
