"""
API Externa para Catálogo de Productos - AutoParts
=================================================

Esta API permite a sistemas externos (como talleres, distribuidores, etc.)
consultar el catálogo de productos de AutoParts de forma programática.

Casos de uso:
- Talleres mecánicos que quieren consultar disponibilidad de repuestos
- Sistemas de inventario de otras empresas
- Integraciones B2B para pedidos automáticos

Autenticación:
- API Key en headers para sistemas registrados
- Rate limiting para prevenir abuso

Endpoints disponibles:
- GET /api/external/catalog/ - Listar todos los productos
- GET /api/external/catalog/{id}/ - Detalle de un producto
- GET /api/external/search/ - Búsqueda de productos
- GET /api/external/categories/ - Listar categorías
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Producto, Categoria
from .serializers import ProductoSerializer, CategoriaSerializer
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ================================
# Autenticación y Rate Limiting
# ================================

def validate_api_key(request):
    """
    Valida la API Key para acceso externo
    En producción, las keys se almacenarían en la base de datos
    """
    api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')
    
    # API Keys válidas (en producción estas estarían en la BD)
    valid_keys = {
        'TALLER_MANOLO_2024': 'Taller de Manolo',
        'DISTRIBUIDORA_CENTRAL_2024': 'Distribuidora Central',
        'AUTOPARTES_CHILE_2024': 'AutoPartes Chile Ltda',
        'DEMO_KEY_2024': 'Cuenta Demo'  # Para testing
    }
    
    if not api_key or api_key not in valid_keys:
        return False, None
    
    return True, valid_keys[api_key]

def api_response(data=None, message="", success=True, status_code=200, meta=None):
    """
    Formato estándar para respuestas de la API externa
    """
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat(),
        'message': message,
        'data': data
    }
    
    if meta:
        response['meta'] = meta
    
    return JsonResponse(response, status=status_code)

# ================================
# Endpoints de la API Externa
# ================================

@api_view(['GET'])
@permission_classes([AllowAny])
def external_catalog_list(request):
    """
    GET /api/external/catalog/
    
    Obtiene el catálogo completo de productos con paginación
    
    Parámetros de consulta:
    - page: número de página (default: 1)
    - limit: productos por página (default: 20, max: 100)
    - category: filtrar por ID de categoría
    - search: búsqueda por nombre o descripción
    - min_price: precio mínimo
    - max_price: precio máximo
    - in_stock: true/false para filtrar por stock
    """
    try:
        # Validar API Key
        is_valid, client_name = validate_api_key(request)
        if not is_valid:
            return api_response(
                message="API Key inválida o faltante. Incluya 'X-API-Key' en headers.",
                success=False,
                status_code=401
            )
        
        logger.info(f"🔑 API Externa accedida por: {client_name}")
        
        # Parámetros de consulta
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 20)), 100)  # Máximo 100 por página
        category_id = request.GET.get('category')
        search = request.GET.get('search', '').strip()
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        in_stock = request.GET.get('in_stock')
        
        # Consulta base - todos los productos (no hay campo activo en Producto)
        productos = Producto.objects.select_related('categoria').prefetch_related('marca')
        
        # Aplicar filtros
        if category_id:
            productos = productos.filter(categoria_id=category_id)
        
        if search:
            productos = productos.filter(
                Q(nombre__icontains=search) | 
                Q(descripcion__icontains=search) |
                Q(marca__nombre__icontains=search)  # Buscar en el nombre de las marcas relacionadas
            )
        
        if min_price:
            productos = productos.filter(precio__gte=float(min_price))
        
        if max_price:
            productos = productos.filter(precio__lte=float(max_price))
        
        if in_stock == 'true':
            productos = productos.filter(stock__gt=0)
        elif in_stock == 'false':
            productos = productos.filter(stock=0)
        
        # Ordenar por nombre
        productos = productos.order_by('nombre')
        
        # Paginación
        paginator = Paginator(productos, limit)
        page_obj = paginator.get_page(page)
        
        # Serializar productos
        productos_data = []
        for producto in page_obj:
            # Obtener marcas (ManyToMany)
            marcas = list(producto.marca.values_list('nombre', flat=True))
            marca_str = ', '.join(marcas) if marcas else 'Sin marca'
            
            productos_data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'marca': marca_str,
                'precio': float(producto.precio),
                'precio_mayorista': float(producto.precio_mayorista) if producto.precio_mayorista else None,
                'stock': producto.stock,
                'categoria': {
                    'id': producto.categoria.id,
                    'nombre': producto.categoria.nombre
                } if producto.categoria else None,
                'peso': float(producto.peso) if producto.peso else None,
                'dimensiones': {
                    'largo': float(producto.largo) if producto.largo else None,
                    'ancho': float(producto.ancho) if producto.ancho else None,
                    'alto': float(producto.alto) if producto.alto else None
                },
                'imagen_url': request.build_absolute_uri(producto.imagen.url) if producto.imagen else None,
                'disponible': producto.stock > 0,
                'activo': True  # Asumimos que todos están activos ya que no hay campo
            })
        
        # Metadatos de paginación
        meta = {
            'pagination': {
                'current_page': page,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'items_per_page': limit,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous()
            },
            'filters_applied': {
                'category': category_id,
                'search': search,
                'min_price': min_price,
                'max_price': max_price,
                'in_stock': in_stock
            }
        }
        
        return api_response(
            data=productos_data,
            message=f"Catálogo obtenido exitosamente. {paginator.count} productos encontrados.",
            meta=meta
        )
        
    except Exception as e:
        logger.error(f"❌ Error en API externa - catalog_list: {str(e)}")
        return api_response(
            message=f"Error interno del servidor: {str(e)}",
            success=False,
            status_code=500
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def external_product_detail(request, product_id):
    """
    GET /api/external/catalog/{product_id}/
    
    Obtiene los detalles completos de un producto específico
    """
    try:
        # Validar API Key
        is_valid, client_name = validate_api_key(request)
        if not is_valid:
            return api_response(
                message="API Key inválida o faltante",
                success=False,
                status_code=401
            )
        
        # Buscar producto
        try:
            producto = Producto.objects.select_related('categoria').prefetch_related('marca').get(
                id=product_id
            )
        except Producto.DoesNotExist:
            return api_response(
                message="Producto no encontrado o no disponible",
                success=False,
                status_code=404
            )
        
        # Obtener marcas (ManyToMany)
        marcas = list(producto.marca.values_list('nombre', flat=True))
        marca_str = ', '.join(marcas) if marcas else 'Sin marca'
        
        # Datos detallados del producto
        producto_data = {
            'id': producto.id,
            'nombre': producto.nombre,
            'descripcion': producto.descripcion,
            'marca': marca_str,
            'precio': float(producto.precio),
            'precio_mayorista': float(producto.precio_mayorista) if producto.precio_mayorista else None,
            'stock': producto.stock,
            'categoria': {
                'id': producto.categoria.id,
                'nombre': producto.categoria.nombre,
                'descripcion': producto.categoria.descripcion
            } if producto.categoria else None,
            'especificaciones': {
                'peso': float(producto.peso) if producto.peso else None,
                'dimensiones': {
                    'largo': float(producto.largo) if producto.largo else None,
                    'ancho': float(producto.ancho) if producto.ancho else None,
                    'alto': float(producto.alto) if producto.alto else None
                },
                'material': getattr(producto, 'material', None),
                'origen': getattr(producto, 'origen', None)
            },
            'imagenes': {
                'principal': request.build_absolute_uri(producto.imagen.url) if producto.imagen else None,
                'adicionales': []  # Para futuras implementaciones
            },
            'disponibilidad': {
                'en_stock': producto.stock > 0,
                'cantidad_disponible': producto.stock,
                'estado': 'disponible' if producto.stock > 0 else 'agotado'
            },
            'precios': {
                'precio_unitario': float(producto.precio),
                'precio_mayorista': float(producto.precio_mayorista) if producto.precio_mayorista else None,
                'incluye_iva': True,
                'moneda': 'CLP'
            },
            'metadatos': {
                'fecha_actualizacion': producto.fecha_creacion.isoformat() if hasattr(producto, 'fecha_creacion') else None,
                'activo': True
            }
        }
        
        logger.info(f"📦 Producto {product_id} consultado por {client_name}")
        
        return api_response(
            data=producto_data,
            message="Detalles del producto obtenidos exitosamente"
        )
        
    except Exception as e:
        logger.error(f"❌ Error en API externa - product_detail: {str(e)}")
        return api_response(
            message=f"Error interno del servidor: {str(e)}",
            success=False,
            status_code=500
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def external_categories_list(request):
    """
    GET /api/external/categories/
    
    Obtiene la lista de todas las categorías disponibles
    """
    try:
        # Validar API Key
        is_valid, client_name = validate_api_key(request)
        if not is_valid:
            return api_response(
                message="API Key inválida o faltante",
                success=False,
                status_code=401
            )
        
        # Obtener categorías con conteo de productos
        categorias = Categoria.objects.filter(activa=True).prefetch_related('productos')
        
        categorias_data = []
        for categoria in categorias:
            productos_count = categoria.productos.count()  # Usar related_name 'productos'
            
            categorias_data.append({
                'id': categoria.id,
                'nombre': categoria.nombre,
                'descripcion': categoria.descripcion,
                'total_productos': productos_count,
                'activa': categoria.activa
            })
        
        return api_response(
            data=categorias_data,
            message=f"{len(categorias_data)} categorías obtenidas exitosamente"
        )
        
    except Exception as e:
        logger.error(f"❌ Error en API externa - categories_list: {str(e)}")
        return api_response(
            message=f"Error interno del servidor: {str(e)}",
            success=False,
            status_code=500
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def external_search(request):
    """
    GET /api/external/search/
    
    Búsqueda avanzada de productos
    
    Parámetros:
    - q: término de búsqueda (obligatorio)
    - category: filtrar por categoría
    - limit: límite de resultados (default: 10, max: 50)
    """
    try:
        # Validar API Key
        is_valid, client_name = validate_api_key(request)
        if not is_valid:
            return api_response(
                message="API Key inválida o faltante",
                success=False,
                status_code=401
            )
        
        query = request.GET.get('q', '').strip()
        if not query:
            return api_response(
                message="Parámetro 'q' (consulta) es obligatorio",
                success=False,
                status_code=400
            )
        
        category_id = request.GET.get('category')
        limit = min(int(request.GET.get('limit', 10)), 50)
        
        # Búsqueda en productos
        productos = Producto.objects.filter(
            Q(nombre__icontains=query) | 
            Q(descripcion__icontains=query) |
            Q(marca__nombre__icontains=query)  # Buscar en el nombre de las marcas relacionadas
        ).select_related('categoria').prefetch_related('marca')
        
        if category_id:
            productos = productos.filter(categoria_id=category_id)
        
        productos = productos[:limit]
        
        # Formatear resultados
        resultados = []
        for producto in productos:
            # Obtener marcas (ManyToMany)
            marcas = list(producto.marca.values_list('nombre', flat=True))
            marca_str = ', '.join(marcas) if marcas else 'Sin marca'
            
            resultados.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'marca': marca_str,
                'precio': float(producto.precio),
                'stock': producto.stock,
                'categoria': producto.categoria.nombre if producto.categoria else None,
                'disponible': producto.stock > 0,
                'imagen_url': request.build_absolute_uri(producto.imagen.url) if producto.imagen else None
            })
        
        logger.info(f"🔍 Búsqueda '{query}' realizada por {client_name} - {len(resultados)} resultados")
        
        return api_response(
            data=resultados,
            message=f"Búsqueda completada. {len(resultados)} productos encontrados.",
            meta={
                'search_query': query,
                'total_results': len(resultados),
                'category_filter': category_id
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Error en API externa - search: {str(e)}")
        return api_response(
            message=f"Error interno del servidor: {str(e)}",
            success=False,
            status_code=500
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def external_api_info(request):
    """
    GET /api/external/info/
    
    Información sobre la API y su uso
    """
    info = {
        'api_name': 'AutoParts External Catalog API',
        'version': '1.0',
        'description': 'API para consulta externa del catálogo de productos AutoParts',
        'endpoints': {
            'catalog': '/api/external/catalog/ - Lista de productos',
            'product_detail': '/api/external/catalog/{id}/ - Detalle de producto',
            'categories': '/api/external/categories/ - Lista de categorías',
            'search': '/api/external/search/ - Búsqueda de productos',
            'info': '/api/external/info/ - Esta información'
        },
        'authentication': {
            'method': 'API Key',
            'header': 'X-API-Key',
            'alternative': 'GET parameter: api_key'
        },
        'rate_limits': {
            'requests_per_minute': 60,
            'requests_per_hour': 1000
        },
        'supported_formats': ['JSON'],
        'contact': {
            'email': 'api@autoparts.cl',
            'support': 'soporte@autoparts.cl'
        }
    }
    
    return api_response(
        data=info,
        message="Información de la API obtenida exitosamente"
    )
