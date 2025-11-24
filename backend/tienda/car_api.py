"""
Integración con CarAPI para obtener datos de vehículos
https://carapi.app/docs/
"""
import requests
import logging
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class CarAPIClient:
    BASE_URL = "https://carapi.app/api"
    
    def __init__(self):
        # Configurar autenticación con JWT
        self.jwt_token = None
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': 'AutoParts-Django/1.0',
            'Content-Type': 'application/json'
        }
        
        # Intentar autenticarse al inicializar
        self._authenticate()
    
    def _authenticate(self):
        """
        Obtiene un JWT token desde CarAPI
        """
        try:
            # Estas credenciales deberían estar en settings.py o variables de entorno
            auth_data = {
                "api_token": getattr(settings, 'CARAPI_TOKEN', None),
                "api_secret": getattr(settings, 'CARAPI_SECRET', None)
            }
            
            if not auth_data["api_token"] or not auth_data["api_secret"]:
                logger.warning("CarAPI credentials not configured. Using free tier.")
                return
            
            auth_url = f"{self.BASE_URL}/auth/login"
            response = requests.post(auth_url, json=auth_data, timeout=10)
            
            if response.status_code == 200:
                # CarAPI devuelve directamente el token JWT como texto plano, no JSON
                jwt_token = response.text.strip()
                
                # Verificar que parece un JWT válido (tiene 3 partes separadas por puntos)
                if jwt_token and jwt_token.count('.') == 2:
                    self.jwt_token = jwt_token
                    self.headers['Authorization'] = f'Bearer {self.jwt_token}'
                    logger.info("CarAPI authentication successful")
                else:
                    logger.error("CarAPI authentication failed: Invalid JWT token format")
            else:
                logger.error(f"CarAPI authentication failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"CarAPI authentication error: {str(e)}")
    
    def _ensure_authenticated(self):
        """
        Verifica que tengamos un token válido
        """
        if not self.jwt_token:
            self._authenticate()
    
    def _make_request(self, endpoint, params=None):
        """
        Realiza una petición a la API de CarAPI
        """
        try:
            # Asegurar que estemos autenticados
            self._ensure_authenticated()
            
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as e:
                    logger.error(f"Error parseando JSON: {str(e)}")
                    logger.error(f"Raw response: {response.text}")
                    return None
            elif response.status_code == 401:
                logger.warning("Token expirado, reautenticando...")
                self._authenticate()
                # Reintentar con nuevo token
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError as e:
                        logger.error(f"❌ Error parseando JSON después de reauth: {str(e)}")
                        return None
                else:
                    logger.error(f"Error en CarAPI después de reautenticación: {response.status_code} - {response.text}")
                    return None
            else:
                logger.error(f"Error en CarAPI: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error de conexión con CarAPI: {str(e)}")
            return None
    
    def get_makes(self, limit=100):
        """
        Obtiene todas las marcas de vehículos disponibles
        """
        cache_key = "carapi_makes"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        logger.info("🚗 Obteniendo marcas de vehículos desde CarAPI...")
        
        # Obtener marcas con paginación
        all_makes = []
        page = 1
        
        while True:
            params = {
                'page': page,
                'limit': limit,
                'sort': 'name',
                'direction': 'asc'
            }
            
            data = self._make_request('makes', params)
            
            if not data or 'data' not in data:
                break
            
            makes = data['data']
            if not makes:
                break
                
            all_makes.extend(makes)
            
            # Verificar si hay más páginas
            collection = data.get('collection', {})
            if not collection.get('next'):
                break
                
            page += 1
            
            # Limitar a un máximo razonable para evitar demasiadas requests
            if page > 10:
                break
        
        # Procesar datos para nuestro formato
        processed_makes = []
        for make in all_makes:
            processed_makes.append({
                'id': make.get('id'),
                'name': make.get('name'),
                'common_name': make.get('common_name'),
                'country': make.get('country')
            })
        
        logger.info(f"✅ {len(processed_makes)} marcas obtenidas desde CarAPI")
        
        # Cachear por 24 horas
        cache.set(cache_key, processed_makes, 60 * 60 * 24)
        
        return processed_makes
    
    def get_models(self, make=None, limit=100):
        """
        Obtiene modelos de vehículos, opcionalmente filtrados por marca
        Actualizado para usar el endpoint v2
        """
        cache_key = f"carapi_models_v2_{make or 'all'}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        logger.info(f"🚙 Obteniendo modelos de vehículos para marca: {make or 'todas'} (usando v2)")
        
        params = {
            'limit': limit,
            'sort': 'name',
            'direction': 'asc'
        }
        
        # Filtrar por marca si se especifica
        if make:
            params['make'] = make
        
        all_models = []
        page = 1
        
        while True:
            params['page'] = page
            data = self._make_request('models/v2', params)
            
            if not data or 'data' not in data:
                break
            
            models = data['data']
            if not models:
                break
                
            all_models.extend(models)
            
            # Verificar si hay más páginas
            collection = data.get('collection', {})
            if not collection.get('next'):
                break
                
            page += 1
            
            # Limitar para evitar demasiadas requests
            if page > 20:
                break
        
        # Procesar datos para nuestro formato
        processed_models = []
        for model in all_models:
            processed_models.append({
                'id': model.get('id'),
                'name': model.get('name'),
                'make': model.get('make'),
                'year': model.get('year')
            })
        
        logger.info(f"✅ {len(processed_models)} modelos obtenidos desde CarAPI")
        
        # Cachear por 24 horas
        cache.set(cache_key, processed_models, 60 * 60 * 24)
        
        return processed_models
    
    def search_models_by_make_name(self, make_name, limit=100):
        """
        Busca modelos por nombre de marca específico
        Actualizado para usar el endpoint v2
        """
        cache_key = f"carapi_models_by_make_v2_{make_name}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        logger.info(f"🔍 Buscando modelos para marca: {make_name} (usando v2)")
        
        # Usar filtro JSON para buscar por nombre exacto de marca
        json_filter = [{
            "field": "make",
            "op": "=",
            "val": make_name
        }]
        
        params = {
            'json': str(json_filter).replace("'", '"'),
            'limit': limit,
            'sort': 'name',
            'direction': 'asc'
        }
        
        all_models = []
        page = 1
        
        while True:
            params['page'] = page
            data = self._make_request('models/v2', params)
            
            if not data or 'data' not in data:
                break
            
            models = data['data']
            if not models:
                break
                
            all_models.extend(models)
            
            # Verificar si hay más páginas
            collection = data.get('collection', {})
            if not collection.get('next'):
                break
                
            page += 1
            
            # Limitar para evitar demasiadas requests
            if page > 20:
                break
        
        # Procesar y agrupar modelos únicos
        unique_models = {}
        for model in all_models:
            model_name = model.get('name')
            if model_name and model_name not in unique_models:
                unique_models[model_name] = {
                    'id': f"{make_name}_{model_name}".lower().replace(' ', '_'),
                    'name': model_name,
                    'make': model.get('make'),
                    'year_start': model.get('year'),
                    'year_end': model.get('year')
                }
            elif model_name in unique_models:
                # Actualizar rango de años
                year = model.get('year')
                if year:
                    current = unique_models[model_name]
                    if not current['year_start'] or year < current['year_start']:
                        current['year_start'] = year
                    if not current['year_end'] or year > current['year_end']:
                        current['year_end'] = year
        
        processed_models = list(unique_models.values())
        
        logger.info(f"✅ {len(processed_models)} modelos únicos para marca {make_name}")
        
        # Cachear por 24 horas
        cache.set(cache_key, processed_models, 60 * 60 * 24)
        
        return processed_models

# Instancia global del cliente
car_api_client = CarAPIClient()
