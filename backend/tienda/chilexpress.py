import requests
import logging

# Configuración de logging
logger = logging.getLogger(__name__)

from django.conf import settings
API_KEY = settings.CHILEXPRESS_API_KEY

# Modo simulación para desarrollo (cambiar a False en producción)
MODO_SIMULACION = True

# Códigos de comuna más comunes para referencia
CODIGOS_COMUNAS_COMUNES = {
    "Santiago": "STGO",  # Santiago Centro
    "Providencia": "PROV",
    "Las Condes": "LCON", 
    "Vitacura": "VITA",
    "Ñuñoa": "NUNO",
    "La Reina": "LREI",
    "Maipú": "MAIP",
    "Puente Alto": "PUAL",
    "La Florida": "LFLO",
    # Agregar más según se necesiten
}

def obtener_regiones():
    """Obtiene todas las regiones disponibles desde Chilexpress"""
    url = "https://testservices.wschilexpress.com/georeference/api/v1.0/regions"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('regions', [])
        else:
            raise Exception(f"Error al obtener regiones: {response.status_code}")
    except Exception as e:
        raise Exception(f"Error conectando con Chilexpress: {str(e)}")

def obtener_comunas_por_region(region_id):
    """Obtiene las comunas de una región específica"""
    url = f"https://testservices.wschilexpress.com/georeference/api/v1.0/coverage-areas?RegionCode={region_id}&type=0"
    headers = {"Ocp-Apim-Subscription-Key": API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('coverageAreas', [])
        else:
            raise Exception(f"Error al obtener comunas: {response.status_code}")
    except Exception as e:
        raise Exception(f"Error conectando con Chilexpress: {str(e)}")

def calcular_tarifas_envio(carrito_items, comuna_destino, subtotal):
    """
    Calcula las tarifas de envío basándose en los productos del carrito
    Adaptado de tu código JavaScript
    """
    # Calcular dimensiones del paquete
    
    total_peso = 0
    max_alto = 0
    max_ancho = 0
    total_largo = 0
    
    for item in carrito_items:
        cantidad = item.get('cantidad', 1)
        peso = float(item.get('peso', 0))
        largo = item.get('largo', 0)
        ancho = item.get('ancho', 0)
        alto = item.get('alto', 0)

        total_peso += peso * cantidad
        total_largo += largo * cantidad
        max_ancho = max(max_ancho, ancho)
        max_alto = max(max_alto, alto)
    
    # Validar dimensiones
    if total_peso == 0 or total_largo == 0 or max_ancho == 0 or max_alto == 0:
        raise Exception("Las dimensiones del paquete no son válidas")
    
    # Preparar datos para la API
    datos_envio = {
        "originCountyCode": obtener_codigo_origen(),  # Santiago Centro
        "destinationCountyCode": comuna_destino,
        "package": {
            "weight": round(total_peso, 2),
            "height": round(max_alto, 2),
            "width": round(max_ancho, 2),
            "length": round(total_largo, 2)
        },
        "productType": 3,
        "contentType": 1,
        "declaredWorth": str(int(subtotal)),
        "deliveryTime": 0
    }
    
    url = "https://testservices.wschilexpress.com/rating/api/v1.0/rates/courier"
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": API_KEY
    }
    
    try:
        response = requests.post(url, headers=headers, json=datos_envio)
        if response.status_code == 200:
            data = response.json()
            opciones = data.get('data', {}).get('courierServiceOptions', [])
            
            # Formatear opciones para el frontend
            opciones_formateadas = []
            for opcion in opciones:
                opciones_formateadas.append({
                    'descripcion': opcion.get('serviceDescription', ''),
                    'precio': int(opcion.get('serviceValue', 0)),
                    'precio_formateado': f"${int(opcion.get('serviceValue', 0)):,}".replace(',', '.')
                })
            
            return opciones_formateadas
        else:
            raise Exception(f"Error en API Chilexpress: {response.status_code} - {response.text}")
    except Exception as e:
        raise Exception(f"Error calculando tarifas: {str(e)}")

def generar_envio_chilexpress(pedido):
    """
    Función para generar orden de transporte en Chilexpress
    Nota: Esta función requiere configuración específica de producción
    """
    # Por ahora, simular una respuesta exitosa para desarrollo
    # En producción, esta función debería usar las credenciales reales de Chilexpress
    
    if not pedido.envio_domicilio:
        raise Exception("Este pedido es para retiro en tienda, no requiere envío")
    
    if not all([pedido.codigo_comuna_chilexpress, pedido.peso_total]):
        raise Exception("Faltan datos necesarios para generar el envío")
    
    # Simulación para desarrollo (comentar en producción)
    import random
    ot_simulada = f"CX{random.randint(100000, 999999)}"
    
    return {
        "transport_order_number": ot_simulada,
        "label_url": f"https://etiquetas.chilexpress.cl/{ot_simulada}.pdf",
        "status": "created"
    }
    
    # Código real para producción (descomentar cuando tengas credenciales):
    """
    api_key = API_KEY
    url = "https://api.chilexpress.cl/v1/transport-orders"  # URL de producción

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "client_tcc": "TU_TCC_REAL",  # Necesitas el TCC real de producción
        "reference": str(pedido.order_id),
        "origin_commune_code": "13101",  # Santiago Centro
        "destination_commune_code": pedido.codigo_comuna_chilexpress,
        "package": {
            "weight": float(pedido.peso_total),
            "length": pedido.largo or 20,
            "width": pedido.ancho or 15,
            "height": pedido.alto or 10
        },
        "content_description": f"Pedido #{pedido.order_id} - Autoparts"
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        return response.json()
    else:
        raise Exception(f"Error al generar envío: {response.status_code} - {response.text}")
    """

def obtener_codigo_origen():
    """
    Retorna el código de la comuna de origen para los envíos
    Por defecto: Santiago Centro
    """
    return "STGO"  # Santiago Centro