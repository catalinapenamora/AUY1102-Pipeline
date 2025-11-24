from django.utils import timezone
import uuid
import logging
import json
from datetime import datetime
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from django.contrib.auth import login
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from transbank.webpay.webpay_plus.transaction import Transaction,WebpayOptions
from transbank.common.integration_type import IntegrationType
from .models import Pedido, Producto, Vehiculo, Categoria, Carrito, CarritoItem, PerfilUsuario, Factura, PedidoItem
from .serializers import ProductoSerializer, VehiculoSerializer, CategoriaSerializer, PedidoSerializer
from django.contrib.auth import logout
from .chilexpress import generar_envio_chilexpress, obtener_regiones, obtener_comunas_por_region, calcular_tarifas_envio
import requests
import re, os
import random
import string
from django.db.models import Q
from django.conf import settings
# Configurar logger
logger = logging.getLogger(__name__)

CommerCode = settings.TRANSBANK_COMMERCE_CODE
ApiKeySecret = settings.TRANSBANK_API_KEY
options = WebpayOptions(CommerCode,ApiKeySecret,IntegrationType.TEST)
transaction = Transaction(options)
# Create your views here.

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request,'productos.html', {'productos':productos})
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    try:
        # Intentar obtener el perfil del usuario
        perfil = PerfilUsuario.objects.get(user=request.user)
        rut = perfil.rut or "Sin especificar"
    except PerfilUsuario.DoesNotExist:
        # Si no existe el perfil, crear uno vacío
        perfil = PerfilUsuario.objects.create(user=request.user)
        rut = "Sin especificar"
    
    return Response({
        "usuario": request.user.username,
        "email": request.user.email,
        "rut": rut
    })
class ProductoAPIView(APIView):
    def get_permissions(self):
        # GET es público, POST/PUT/DELETE requieren staff o trabajador
        if self.request.method in ['POST', 'PUT', 'DELETE']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        from django.core.paginator import Paginator
        
        productos = Producto.objects.all()
        categoria_id = request.GET.get("categoria")
        orden = request.GET.get("orden")
        page = request.GET.get("page", 1)
        per_page = int(request.GET.get("per_page", 12))  # 12 productos por página por defecto

        # Filtros
        if categoria_id:
            productos = productos.filter(categoria_id=categoria_id)

        # Filtro de búsqueda por nombre o descripción
        busqueda = request.GET.get("busqueda")
        if busqueda:
            productos = productos.filter(
                Q(nombre__icontains=busqueda) | Q(descripcion__icontains=busqueda)
            )

        # Filtro por marca y modelo de vehículo (compatibilidad)
        marca_vehiculo = request.GET.get("marca")
        modelo_vehiculo = request.GET.get("modelo")
        if marca_vehiculo:
            productos = productos.filter(compatibilidades__modelo_vehiculo__marca_vehiculo__nombre__iexact=marca_vehiculo)
        if modelo_vehiculo:
            productos = productos.filter(compatibilidades__modelo_vehiculo__nombre__iexact=modelo_vehiculo)
        productos = productos.distinct()

        # Ordenamiento
        if orden == "precio_asc":
            productos = productos.order_by("precio")
        elif orden == "precio_desc":
            productos = productos.order_by("-precio")
        elif orden == "nombre_asc":
            productos = productos.order_by("nombre")
        elif orden == "nombre_desc":
            productos = productos.order_by("-nombre")
        else:
            productos = productos.order_by("id")  # Orden por defecto

        # Paginación
        paginator = Paginator(productos, per_page)
        page_obj = paginator.get_page(page)

        serializer = ProductoSerializer(page_obj, many=True)
        
        # Los precios ya incluyen IVA, no necesitamos modificarlos
        data = serializer.data
        
        # Agregar información de paginación
        response_data = {
            'productos': data,
            'pagination': {
                'current_page': page_obj.number,
                'total_pages': paginator.num_pages,
                'total_items': paginator.count,
                'per_page': per_page,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
                'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
            }
        }
        
        return Response(response_data)

    def post(self, request):
        # Verificar permisos para crear productos - permitir staff o trabajadores
        if not request.user.is_authenticated or not (request.user.is_staff or hasattr(request.user, 'trabajador')):
            return Response({'error': 'No tienes permisos para crear productos'}, status=status.HTTP_403_FORBIDDEN)
        
        # Extraer compatibilidades del request si existen
        compatibilidades_data = []
        if 'compatibilidades' in request.data:
            try:
                # Puede venir como string JSON o como lista directamente
                compatibilidades_raw = request.data['compatibilidades']
                if isinstance(compatibilidades_raw, str):
                    compatibilidades_data = json.loads(compatibilidades_raw)
                else:
                    compatibilidades_data = compatibilidades_raw
            except (json.JSONDecodeError, TypeError):
                compatibilidades_data = []
        
        # Crear el serializer con contexto de compatibilidades
        serializer = ProductoSerializer(
            data=request.data, 
            context={
                'compatibilidades': compatibilidades_data,
                'request': request
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProductoMayoristaAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not hasattr(request.user, 'perfilusuario') or not request.user.perfilusuario.empresa:
            return Response({'error': 'Acceso restringido a cuentas mayoristas'}, status=403)

        productos = Producto.objects.all()

        data = []
        for producto in productos:
            data.append({
                "id": producto.id,
                "nombre": producto.nombre,
                "descripcion": producto.descripcion,
                "imagen": producto.imagen.url if producto.imagen else None,
                "precio_mayorista": producto.precio_mayorista,  # Ya incluye IVA
                "stock": producto.stock,
                "categoria": producto.categoria.nombre
            })

        return Response(data)
def productos_mayoristas_page(request):
    token, _ = Token.objects.get_or_create(user=request.user)
    return render(request, 'mayorista_productos.html', {
        'token': token.key
    })
    
class HomeView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        productos = Producto.objects.all()[:8] 
        es_empresa = False
        if request.user.is_authenticated and hasattr(request.user, 'perfilusuario'):
            es_empresa = request.user.perfilusuario.empresa

        return render(request, 'home.html', {
            'productos': productos,
            'es_empresa': es_empresa,
        })
def cerrar_sesion(request):
    logout(request)  # Elimina la sesión del lado del servidor
    response = JsonResponse({'mensaje': 'Sesión cerrada'})
    response.delete_cookie('sessionid')  # Elimina la cookie en el navegador
    return response

def generar_order_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):  
        email = request.data.get('usuario')  
        password = request.data.get('contraseña')
        if not email or not password:
            return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=email, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response({'error': 'Usuario o contraseña incorrectos'}, status=status.HTTP_401_UNAUTHORIZED)
    
def login_page(request):
    return render(request, 'login.html')

class VehiculoView(APIView):
    def get(self, request):
        compatibles = Vehiculo.objects.all()
        serializer = VehiculoSerializer(compatibles, many=True)
        return Response(serializer.data)
    
def catalogo_view(request):
    categoria_id = request.GET.get('categoria')
    productos = Producto.objects.all()
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    categorias = Categoria.objects.all()

    es_empresa = False
    if request.user.is_authenticated and hasattr(request.user, 'perfilusuario'):
        es_empresa = request.user.perfilusuario.empresa  # o .trabajador si usas otro flag

    return render(request, 'catalogo.html', {
        'productos': productos,
        'categorias': categorias,
        'es_empresa': es_empresa,  # ← esto es importante
    })


@method_decorator(csrf_exempt, name='dispatch')
class RegistroView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('usuario')
        password = request.data.get('contraseña')
        email = request.data.get('email')
        rut = request.data.get('rut') 

        if not username or not password or not email:
            return Response({'error': 'Faltan datos'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Usuario ya existe'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'El correo electrónico ya está en uso'}, status=status.HTTP_400_BAD_REQUEST)

        if not re.search(r'[A-Z]', password):
            return Response({'error': 'La contraseña debe contener al menos una letra mayúscula'}, status=status.HTTP_400_BAD_REQUEST)

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return Response({'error': 'La contraseña debe contener al menos un símbolo'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear el usuario
        user = User.objects.create_user(username=username, password=password, email=email)

        # ✅ Crear el perfil asociado con RUT
        # Limpiar el RUT: si está vacío, es None, o es 'None' como string, guardarlo como None
        rut_limpio = None
        if rut and rut.strip() and rut.strip().lower() != 'none':
            rut_limpio = rut.strip()
        
        PerfilUsuario.objects.create(user=user, rut=rut_limpio)

        # Crear token
        token = Token.objects.create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)
def registro_page(request):
    return render(request, 'registro.html')

class PerfilUsuarioView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user 
            
            # Verificar que el usuario está autenticado
            if not user.is_authenticated:
                return Response({'error': 'Usuario no autenticado'}, status=401)
            
            # Obtener RUT del perfil
            rut = "Sin especificar"
            
            if hasattr(user, 'perfilusuario'):
                perfil = user.perfilusuario
                
                # Verificar que el RUT no sea None, null, 'None' como string, o vacío
                if perfil.rut and perfil.rut.strip() and perfil.rut != 'None':
                    rut = perfil.rut.strip()
            
            return Response({
                'usuario': user.username,
                'email': user.email,
                'rut': rut,
                'is_staff': user.is_staff,
                'is_empresa': hasattr(user, 'perfilusuario') and user.perfilusuario.empresa,
                'is_trabajador': hasattr(user, 'perfilusuario') and user.perfilusuario.trabajador,
            })
        except Exception as e:
            return Response({'error': 'Error interno del servidor'}, status=500)

def perfil_page(request):
    return render(request, 'perfil.html')
def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    es_empresa = False
    if request.user.is_authenticated and hasattr(request.user, 'perfilusuario'):
        es_empresa = request.user.perfilusuario.empresa
    
    # Los precios ya incluyen IVA, usar directamente
    
    return render(request, "detalle.html", {
        "producto": producto,
        "es_empresa": es_empresa,
    })

class CarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        carrito, created = Carrito.objects.get_or_create(user=request.user, is_active=True)
        items = CarritoItem.objects.filter(carrito=carrito)
        data = [
            {
                "producto": item.producto.nombre,
                "producto_id": item.producto.id,
                "cantidad": item.cantidad,
                "precio": item.precio, 
            }
            for item in items
        ]
        return Response({"carrito": data})

    
class AgregarCarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        producto_id = request.data.get('producto_id')
        cantidad = int(request.data.get('cantidad', 1))

        if not producto_id:
            return Response({'error': 'Falta producto_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if producto.stock < cantidad:
            return Response({'error': 'No hay suficiente stock disponible'}, status=status.HTTP_400_BAD_REQUEST)

        carrito, _ = Carrito.objects.get_or_create(user=user, is_active=True)

        # Precio según tipo de usuario
        if hasattr(user, 'perfilusuario') and user.perfilusuario.empresa:
            precio = producto.precio_mayorista
        else:
            precio = producto.precio

        carrito_item, created = CarritoItem.objects.get_or_create(
            carrito=carrito, producto=producto,
            defaults={'cantidad': cantidad, 'precio': precio}
        )

        if not created:
            nueva_cantidad = carrito_item.cantidad + cantidad
            if nueva_cantidad > producto.stock:
                return Response({'error': 'Stock máximo alcanzado'}, status=status.HTTP_400_BAD_REQUEST)
            carrito_item.cantidad = nueva_cantidad
            carrito_item.precio = precio
            carrito_item.save()

        return Response({'message': 'Producto agregado al carrito'}, status=status.HTTP_200_OK)
class RemoverDelCarritoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, producto_id):
        user = request.user

        carrito, created = Carrito.objects.get_or_create(user=user, is_active=True)

        print("=== DEBUG ELIMINAR PRODUCTO DEL CARRITO ===")
        print("Usuario autenticado:", user.username)
        print("Producto ID recibido:", producto_id)
        print("Carrito ID:", carrito.id)
        print("Items en el carrito del usuario:")
        for item in CarritoItem.objects.filter(carrito=carrito):
            print(f" - Producto ID: {item.producto.id}, Nombre: {item.producto.nombre}, Cantidad: {item.cantidad}")

        try:
            item = CarritoItem.objects.get(carrito=carrito, producto_id=producto_id)
        except CarritoItem.DoesNotExist:
            print("⚠️ Producto no encontrado en el carrito del usuario.")
            return Response({'error': 'El producto no está en el carrito'}, status=status.HTTP_404_NOT_FOUND)

        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
        else:
            item.delete()

        return redirect('carrito')
    
def carrito_page(request):
    # Permitir acceso tanto a usuarios autenticados como no autenticados
    # El frontend manejará el carrito híbrido (autenticado vs invitado)
    
    carrito_items = []
    if request.user.is_authenticated:
        try:
            carrito = Carrito.objects.get(user=request.user, is_active=True)
            carrito_items = CarritoItem.objects.filter(carrito=carrito)
        except Carrito.DoesNotExist:
            carrito_items = []

    return render(request, 'carrito.html', {
        'carrito_items': carrito_items
    })

class CarritoContadorView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({'count': 0})
            
            carrito = Carrito.objects.filter(user=request.user, is_active=True).first()
            if not carrito:
                return JsonResponse({'count': 0})
            
            count = sum(item.cantidad for item in CarritoItem.objects.filter(carrito=carrito))
            return JsonResponse({'count': count})
        except Exception as e:
            return JsonResponse({'count': 0})

class TrabajadoresAdminView(APIView):
    permission_classes = [IsAdminUser]  # Solo admins

    def get(self, request):
        perfiles = PerfilUsuario.objects.select_related('user').all()
        data = []
        for perfil in perfiles:
            data.append({
                'id': perfil.user.id,
                'username': perfil.user.username,
                'email': perfil.user.email,
                'trabajador': perfil.trabajador,
                'empresa': perfil.empresa,
            })
        return Response(data)

    def patch(self, request):
        user_id = request.data.get('user_id')
        trabajador = request.data.get('trabajador')
        empresa = request.data.get('empresa')

        if user_id is None:
            return Response({'error': 'Falta user_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            perfil = PerfilUsuario.objects.get(user_id=user_id)
        except PerfilUsuario.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if trabajador is not None:
            perfil.trabajador = trabajador
        if empresa is not None:
            perfil.empresa = empresa

        perfil.save()
        return Response({'success': True})

def admin_required(user):
    return user.is_authenticated and user.is_staff 

@login_required
@user_passes_test(admin_required)
def gestion_page(request):
    return render(request, 'gestion_trabajadores.html')

class TrabajadorUpdateView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            perfil = user.perfilusuario  # Relación OneToOne
        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except PerfilUsuario.DoesNotExist:
            return Response({'error': 'Perfil no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        actualizado = False

        trabajador = request.data.get('trabajador')
        if trabajador is not None:
            perfil.trabajador = trabajador
            actualizado = True

        empresa = request.data.get('empresa')
        if empresa is not None:
            perfil.empresa = empresa
            actualizado = True

        if not actualizado:
            return Response({'error': 'No se proporcionó ningún campo válido'}, status=status.HTTP_400_BAD_REQUEST)

        perfil.save()
        return Response({'success': 'Estado actualizado'}, status=status.HTTP_200_OK)
    
class EsTrabajador(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and 
                    request.user.is_authenticated and 
                    hasattr(request.user, 'perfilusuario') and 
                    request.user.perfilusuario.trabajador)
    
class ProductoCrudView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated, EsTrabajador]

    def get(self, request):
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        print(f"🔍 POST ProductoCrudView - Request data keys: {list(request.data.keys())}")
        
        # Extraer compatibilidades del request si existen
        compatibilidades_data = []
        if 'compatibilidades' in request.data:
            try:
                # Puede venir como string JSON o como lista directamente
                compatibilidades_raw = request.data['compatibilidades']
                print(f"🔍 POST - Compatibilidades raw: {compatibilidades_raw}")
                print(f"🔍 POST - Tipo raw: {type(compatibilidades_raw)}")
                
                if isinstance(compatibilidades_raw, str):
                    compatibilidades_data = json.loads(compatibilidades_raw)
                    print(f"🔍 POST - Parsed from JSON: {compatibilidades_data}")
                else:
                    compatibilidades_data = compatibilidades_raw
                    print(f"🔍 POST - Used directly: {compatibilidades_data}")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"❌ POST - Error parsing compatibilidades: {e}")
                compatibilidades_data = []
        else:
            print("🔍 POST - No compatibilidades field found")

        print(f"🔍 POST - Final compatibilidades_data: {compatibilidades_data}")

        serializer = ProductoSerializer(
            data=request.data,
            context={
                'compatibilidades': compatibilidades_data,
                'request': request
            }
        )
        if serializer.is_valid():
            producto = serializer.save()
            print(f"✅ POST - Producto guardado: {producto.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(f"❌ POST - Errores de validación: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoriasCrudView(APIView):
    permission_classes = [permissions.IsAuthenticated, EsTrabajador]

    def get(self, request):
        categorias = Categoria.objects.all()
        serializer = CategoriaSerializer(categorias, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CategoriaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class ProductoDetalleAPIView(APIView):
    # Permitir acceso público para que invitados puedan ver productos
    permission_classes = []

    def get_object(self, pk):
        try:
            return Producto.objects.get(pk=pk)
        except Producto.DoesNotExist:
            return None

    def get(self, request, pk):
        producto = self.get_object(pk)
        if not producto:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductoSerializer(producto)
        data = serializer.data
        
        # Los precios ya incluyen IVA, no necesitamos modificarlos
        
        return Response(data)

    # Mantener restricciones solo para modificaciones (PUT/DELETE)
    def put(self, request, pk):
        # Verificar permisos para modificación - permitir staff o trabajadores
        if not request.user.is_authenticated or not (request.user.is_staff or hasattr(request.user, 'trabajador')):
            return Response({'error': 'No tienes permisos para modificar productos'}, status=status.HTTP_403_FORBIDDEN)
            
        producto = self.get_object(pk)
        if not producto:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        print(f"🔍 PUT ProductoDetalleAPIView - Request data keys: {list(request.data.keys())}")

        # Extraer compatibilidades del request si existen
        compatibilidades_data = []
        if 'compatibilidades' in request.data:
            try:
                # Puede venir como string JSON o como lista directamente
                compatibilidades_raw = request.data['compatibilidades']
                print(f"🔍 PUT - Compatibilidades raw: {compatibilidades_raw}")
                print(f"🔍 PUT - Tipo raw: {type(compatibilidades_raw)}")
                
                if isinstance(compatibilidades_raw, str):
                    compatibilidades_data = json.loads(compatibilidades_raw)
                    print(f"🔍 PUT - Parsed from JSON: {compatibilidades_data}")
                else:
                    compatibilidades_data = compatibilidades_raw
                    print(f"🔍 PUT - Used directly: {compatibilidades_data}")
            except (json.JSONDecodeError, TypeError) as e:
                print(f"❌ PUT - Error parsing compatibilidades: {e}")
                compatibilidades_data = []
        else:
            print("🔍 PUT - No compatibilidades field found")

        print(f"🔍 PUT - Final compatibilidades_data: {compatibilidades_data}")

        serializer = ProductoSerializer(
            producto, 
            data=request.data,
            context={
                'compatibilidades': compatibilidades_data,
                'request': request
            }
        )
        if serializer.is_valid():
            producto_updated = serializer.save()
            print(f"✅ PUT - Producto actualizado: {producto_updated.id}")
            return Response(serializer.data)
        else:
            print(f"❌ PUT - Errores de validación: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Verificar permisos para eliminación - permitir staff o trabajadores
        if not request.user.is_authenticated or not (request.user.is_staff or hasattr(request.user, 'trabajador')):
            return Response({'error': 'No tienes permisos para eliminar productos'}, status=status.HTTP_403_FORBIDDEN)
            
        producto = self.get_object(pk)
        if not producto:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        producto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
class CategoriaDetalleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, EsTrabajador]

    def get_object(self, pk):
        return get_object_or_404(Categoria, pk=pk)

    def get(self, request, pk):
        categoria = self.get_object(pk)
        serializer = CategoriaSerializer(categoria)
        return Response(serializer.data)

    def put(self, request, pk):
        categoria = self.get_object(pk)
        serializer = CategoriaSerializer(categoria, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        categoria = self.get_object(pk)
        categoria.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)  
    
def gestion_prod_page(request):
    categorias = Categoria.objects.all()
    return render(request, 'gestion_productos.html', {'categorias': categorias})

def gestion_cat_page(request):
    categorias = Categoria.objects.all()
    return render(request, 'gestion_categorias.html')

class TokenDesdeSesionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Verificar que el usuario está autenticado mediante sesión
            if not request.user.is_authenticated:
                return Response({'error': 'Usuario no autenticado'}, status=401)
            
            # Crear o obtener el token para el usuario
            token, created = Token.objects.get_or_create(user=request.user)
            
            return Response({'token': token.key})
        except Exception as e:
            return Response({'error': 'Error interno del servidor'}, status=500)
    
from django.contrib.auth import login  # Asegúrate de tener esto importado

@csrf_exempt
def login_con_sesion(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)  # ← esto crea la sesión
            return redirect('/')  # redirige donde quieras
        else:
            return render(request, 'login.html', {'error': 'Credenciales inválidas'})

    return render(request, 'login.html')
def cerrar_sesion(request):
    logout(request)
    return render(request, 'logout.html')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def aumentar_producto(request, producto_id):
    print("➡️ aumentar_producto()")
    carrito, _ = Carrito.objects.get_or_create(user=request.user, is_active=True)

    # Verificar si ya existe el producto en el carrito
    items_existentes = CarritoItem.objects.filter(carrito=carrito, producto_id=producto_id)
    
    if items_existentes.exists():
        # Si hay múltiples items del mismo producto, consolidarlos
        if items_existentes.count() > 1:
            print(f"⚠️ Se encontraron {items_existentes.count()} items duplicados. Consolidando...")
            
            # Sumar todas las cantidades
            cantidad_total = sum(item.cantidad for item in items_existentes)
            precio = items_existentes.first().precio
            
            # Eliminar todos los items
            items_existentes.delete()
            
            # Crear un nuevo item consolidado
            item = CarritoItem.objects.create(
                carrito=carrito,
                producto_id=producto_id,
                cantidad=cantidad_total,
                precio=precio
            )
            print(f"✅ Items consolidados. Cantidad total: {cantidad_total}")
        else:
            item = items_existentes.first()
        
        # Aumentar cantidad
        producto = item.producto
        if item.cantidad < producto.stock:
            item.cantidad += 1
            item.save()
            print(f"🟢 Cantidad actualizada: {item.cantidad}")
            return JsonResponse({'success': True, 'message': 'Cantidad actualizada'})
        else:
            print("❌ No se puede aumentar: stock máximo alcanzado")
            return JsonResponse({'error': 'Stock máximo alcanzado'}, status=400)
    else:
        # Crear nuevo item
        try:
            producto = Producto.objects.get(id=producto_id)
            precio = producto.precio_mayorista if (hasattr(request.user, 'perfilusuario') and request.user.perfilusuario.empresa) else producto.precio
            
            item = CarritoItem.objects.create(
                carrito=carrito,
                producto=producto,
                cantidad=1,
                precio=precio
            )
            print("🆕 Producto agregado al carrito")
            return JsonResponse({'success': True, 'message': 'Producto agregado al carrito'})
        except Producto.DoesNotExist:
            print(f"❌ Producto {producto_id} no encontrado")
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def disminuir_producto(request, producto_id):
    print("➡️ disminuir_producto()")
    
    # Buscar todos los items del producto en carritos activos del usuario
    items = CarritoItem.objects.filter(
        carrito__user=request.user, 
        carrito__is_active=True,
        producto_id=producto_id
    )
    
    if not items.exists():
        print(f"❌ No se encontró el producto {producto_id} en el carrito")
        return JsonResponse({'error': 'Producto no encontrado en el carrito'}, status=404)
    
    # Si hay múltiples items del mismo producto, procesarlos todos
    if items.count() > 1:
        print(f"⚠️ Se encontraron {items.count()} items del producto {producto_id}. Consolidando...")
        
        # Sumar todas las cantidades
        cantidad_total = sum(item.cantidad for item in items)
        primer_item = items.first()
        
        # Eliminar todos los items excepto el primero
        items.exclude(id=primer_item.id).delete()
        
        # Actualizar el primer item con la cantidad total
        primer_item.cantidad = cantidad_total
        primer_item.save()
        
        item = primer_item
        print(f"✅ Items consolidados. Cantidad total: {cantidad_total}")
    else:
        item = items.first()

    # Procesar la disminución
    if item.cantidad > 1:
        item.cantidad -= 1
        item.save()
        print(f"🔽 Cantidad disminuida a: {item.cantidad}")
    else:
        item.delete()
        print("🗑️ Producto eliminado por cantidad = 0")

    # Devolver JSON success para que el frontend sepa que funcionó
    return JsonResponse({'success': True, 'message': 'Cantidad actualizada'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remover_producto(request, producto_id):
    print("➡️ remover_producto()")
    
    # Buscar todos los items del producto en carritos activos del usuario
    items = CarritoItem.objects.filter(
        carrito__user=request.user, 
        carrito__is_active=True,
        producto_id=producto_id
    )
    
    if not items.exists():
        print(f"❌ No se encontró el producto {producto_id} en el carrito")
        return redirect('carrito')
    
    # Eliminar todos los items del producto (en caso de duplicados)
    cantidad_eliminada = items.count()
    items.delete()
    print(f"🧹 {cantidad_eliminada} item(s) del producto eliminado(s) del carrito")

    # Devolver JSON success para que el frontend sepa que funcionó
    return JsonResponse({'success': True, 'message': 'Producto eliminado del carrito'})

def pagar_transbank(request, order_id):
    cart = request.session.get("cart", [])
    user_id = request.user.get("user_id")
    cliente = request.session.get("cliente", {})
    resumen = request.session.get("resumen", {})
    session_id = f"{user_id}-{uuid.uuid4()}"
    return_url = request.build_absolute_uri(f"/carrito/confirmar/")  # Donde llegará después del pago

    if not cart or not user_id:
        return Response({"error": "Datos de sesión no encontrados"}, status=400)

    # Calcula total
    total = sum(item["precio"] * item["cantidad"] for item in cart)

    tx = Transaction()
    tx.configure_for_testing()  # ⚠️ Cambia a producción cuando estés listo

    response = tx.create(buy_order=order_id, session_id=session_id, amount=total, return_url=return_url)

    url = response["url"] + "?token_ws=" + response["token"]
    return Response({"url": url})
CODIGOS_COMUNAS = {
    "Santiago": "13101",
    "Ñuñoa": "13114",
    "Providencia": "13115",
    "Puente Alto": "13201",
    "La Florida": "13120",
    "Maipú": "13119",
    # agrega más según necesites
}
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_pedido(request):
    data = request.data
    user = request.user

    # Debug: Imprimir datos recibidos
    print("🔍 Datos recibidos para crear pedido:", data)

    email = data.get("email")
    monto = data.get("monto")
    metodo = data.get("metodo_pago")
    tipo_entrega = data.get("tipo_entrega")

    # Validaciones básicas
    if not email or not monto or not metodo or not tipo_entrega:
        error_msg = f"Faltan datos requeridos. Email: {bool(email)}, Monto: {bool(monto)}, Método: {bool(metodo)}, Tipo: {bool(tipo_entrega)}"
        print("❌", error_msg)
        return Response({"error": error_msg}, status=400)

    if tipo_entrega not in ["retiro", "envio"]:
        print("❌ Método de entrega inválido:", tipo_entrega)
        return Response({"error": "Método de entrega inválido"}, status=400)

    # Obtener carrito activo
    carrito = Carrito.objects.filter(user=user, is_active=True).first()
    if not carrito:
        return Response({"error": "No se encontró carrito activo"}, status=400)

    items = CarritoItem.objects.filter(carrito=carrito)
    if not items.exists():
        return Response({"error": "Carrito vacío"}, status=400)
    
    print(f"🔍 Debug crear_pedido - Carrito encontrado: {carrito.id}, Items: {items.count()}")
    for item in items:
        print(f"  - {item.producto.nombre}: {item.cantidad} x ${item.precio}")

    # Calcular peso total y dimensiones
    peso_total = sum(item.producto.peso * item.cantidad for item in items)
    
    # Calcular dimensiones del paquete (igual que en calcular_tarifas_envio)
    max_alto = 0
    max_ancho = 0
    total_largo = 0
    
    for item in items:
        cantidad = item.cantidad
        producto = item.producto
        
        total_largo += (producto.largo or 0) * cantidad
        max_ancho = max(max_ancho, producto.ancho or 0)
        max_alto = max(max_alto, producto.alto or 0)

    # Crear pedido
    order_id = generar_order_id()
    pedido = Pedido.objects.create(
        order_id=order_id,
        email=email,
        monto=monto,
        estado="pendiente",
        retiro_en_tienda=(tipo_entrega == "retiro"),
        envio_domicilio=(tipo_entrega == "envio"),
        peso_total=peso_total,
        alto=max_alto,
        ancho=max_ancho,
        largo=total_largo,
        costo_envio=data.get("costo_envio", 0)  # Asegúrate de que este campo exista en tu modelo Pedido
    )

    if tipo_entrega == "envio":
        pedido.direccion = data.get("direccion")
        pedido.comuna = data.get("comuna")
        pedido.region = data.get("region")
        pedido.codigo_comuna_chilexpress = data.get("codigo_comuna_chilexpress")

        print(f"🚚 Datos de envío - Dirección: {pedido.direccion}, Comuna: {pedido.comuna}, Región: {pedido.region}, Código: {pedido.codigo_comuna_chilexpress}")

        if not all([pedido.direccion, pedido.comuna, pedido.region, pedido.codigo_comuna_chilexpress]):
            pedido.delete()
            error_msg = f"Faltan datos de envío. Dirección: {bool(pedido.direccion)}, Comuna: {bool(pedido.comuna)}, Región: {bool(pedido.region)}, Código: {bool(pedido.codigo_comuna_chilexpress)}"
            print("❌", error_msg)
            return Response({"error": error_msg}, status=400)

    pedido.save()
    serializer = PedidoSerializer(pedido)
    
    # ✅ CREAR LOS PEDIDO ITEMS - esto faltaba!
    print(f"📝 Creando PedidoItems para pedido {order_id}...")
    for item in items:
        pedido_item = PedidoItem.objects.create(
            pedido=pedido,
            producto=item.producto,
            nombre_producto=item.producto.nombre,
            cantidad=item.cantidad,
            precio_unitario=item.precio,
            subtotal=item.precio * item.cantidad
        )
        print(f"  ✅ PedidoItem creado: {pedido_item.nombre_producto} x{pedido_item.cantidad}")
    
    print(f"✅ {items.count()} PedidoItems creados exitosamente")

    # Guardar en sesión
    request.session["order_id"] = order_id
    request.session["email"] = email
    request.session["monto"] = monto
    request.session["metodo_pago"] = metodo
    request.session["user_id"] = user.id
    request.session["tipo_entrega"] = tipo_entrega

    return Response(serializer.data, status=201)
@login_required
def pagar_view(request, order_id):
    print("💡 order_id recibido:", order_id)

    email = request.session.get("email")
    monto = request.session.get("monto")
    metodo = request.session.get("metodo_pago")

    if not email or not monto or not metodo:
        print("❌ Datos de sesión incompletos:")
        print("email:", email)
        print("monto:", monto)
        print("metodo:", metodo)
        return redirect("/carrito/")

    try:
        session_id = f"{request.user.id}-{uuid.uuid4()}"
        return_url = request.build_absolute_uri("/pago_exitoso/")

        response = transaction.create(
            buy_order=order_id,
            session_id=session_id,
            amount=int(monto),
            return_url=return_url
        )

        # Redirige a la URL que devuelve Transbank
        url = response["url"] + "?token_ws=" + response["token"]
        return redirect(url)

    except Exception as e:
        print("❌ Error al crear la transacción:", e)
        return redirect("/carrito/")
    
def pago_exitoso(request):
    # Log de entrada para detectar múltiples llamadas
    print(f"🚀 === INICIO PAGO_EXITOSO === (timestamp: {datetime.now()})")
    
    token_ws = request.GET.get('token_ws')
    tbk_token = request.GET.get('TBK_TOKEN')

    # Si no hay token_ws, significa que el pago fue rechazado o anulado
    if not token_ws:
        print("❌ Pago rechazado o anulado - No se recibió token_ws")
        
        # Obtener order_id de la sesión para redirigir a página de rechazo
        order_id = request.session.get("order_id")
        if order_id:
            print(f"🔴 Redirigiendo a página de pago rechazado para order {order_id}")
            return redirect(f"/pago-rechazado/{order_id}/")
        else:
            messages.error(request, "El pago fue anulado o rechazado. Puedes intentar nuevamente.")
            return redirect("/carrito/")

    transaction = Transaction(options)  # Asegúrate de que 'options' esté definido globalmente o importado
    result = transaction.commit(token_ws)

    if result['status'] == 'AUTHORIZED':
        # Obtener datos de la sesión
        email = request.session.get("email", "")
        monto = request.session.get("monto", "")
        metodo = request.session.get("metodo_pago", "")
        order_id = request.session.get("order_id", "")
        user_id = request.session.get("user_id", "")

        print(f"🔍 Debug pago_exitoso - Order ID: {order_id}, User ID: {user_id}, Email: {email}")
        print(f"🔍 Debug request.user: {request.user} (autenticado: {request.user.is_authenticated})")

        # Crear/obtener pedido y actualizar estado (no duplicar reducción de stock)
        try:
            pedido = Pedido.objects.get(order_id=order_id)
            print(f"🔍 Debug pedido encontrado: {pedido.id}, estado actual: {pedido.estado}")
            
            # Solo procesar stock si el pedido no estaba ya pagado
            stock_ya_procesado = (pedido.estado == 'pagado')
            print(f"🔍 Debug stock_ya_procesado (antes): {stock_ya_procesado}")
            
            # Actualizar estado del pedido a pagado
            pedido.estado = 'pagado'
            pedido.save()
            
            print(f"✅ Pedido actualizado a 'pagado'. Stock ya procesado: {stock_ya_procesado}")
            
        except Pedido.DoesNotExist:
            # Si no existe, crear el pedido (caso excepcional)
            pedido = Pedido.objects.create(
                order_id=order_id,
                email=email,
                monto=monto,
                estado='pagado'
            )
            stock_ya_procesado = False
            print("✅ Pedido creado como 'pagado'")

        # Si es envío a domicilio y no tiene OT generada, intentar generarla
        if pedido.envio_domicilio and not pedido.ot_codigo:
            try:
                from .chilexpress import generar_envio_chilexpress
                resultado_envio = generar_envio_chilexpress(pedido)
                
                # Guardar información del envío
                pedido.ot_codigo = resultado_envio.get('transport_order_number')
                pedido.etiqueta_url = resultado_envio.get('label_url')
                pedido.estado_envio = 'generado'
                pedido.save()
                
                print(f"✅ Envío generado exitosamente: {pedido.ot_codigo}")
                
            except Exception as e:
                print(f"⚠️ No se pudo generar el envío automáticamente: {str(e)}")
                # No fallar el pago por problemas de envío

        # Obtener productos del carrito de la base de datos
        productos = []
        
        try:
            # Intentar obtener el carrito por usuario
            if user_id:
                from django.contrib.auth.models import User
                user = User.objects.get(id=user_id)
                
                # Buscar CUALQUIER carrito del usuario (activo o inactivo)
                carrito_activo = Carrito.objects.filter(user=user, is_active=True).first()
                carrito_inactivo = Carrito.objects.filter(user=user, is_active=False).order_by('-id').first()
                
                print(f"🔍 Debug carritos - Activo: {carrito_activo}, Inactivo reciente: {carrito_inactivo}")
                
                # Si no hay carrito activo pero hay uno inactivo reciente, usarlo
                carrito = carrito_activo or carrito_inactivo
            else:
                # Si no hay user_id, buscar por el usuario actual de la request
                carrito_activo = Carrito.objects.filter(user=request.user, is_active=True).first()
                carrito_inactivo = Carrito.objects.filter(user=request.user, is_active=False).order_by('-id').first()
                
                print(f"🔍 Debug carritos current user - Activo: {carrito_activo}, Inactivo reciente: {carrito_inactivo}")
                carrito = carrito_activo or carrito_inactivo
            
            print(f"🔍 Debug carrito encontrado: {carrito}")
            
            if carrito:
                items = CarritoItem.objects.filter(carrito=carrito)
                print(f"🔍 Debug items del carrito: {items.count()} productos")
                
                # Procesar todos los productos ANTES de marcar el carrito como inactivo
                for item in items:
                    try:
                        producto = item.producto
                        
                        # Agregar producto a la lista
                        productos.append({
                            "producto": producto.nombre,
                            "precio": item.precio,
                            "cantidad": item.cantidad,
                            "subtotal": item.precio * item.cantidad,
                            "imagen": producto.imagen
                        })
                        
                        # Guardar item del pedido para referencia futura (solo si no se procesó antes el stock)
                        if not stock_ya_procesado:
                            # Log específico para reducción de stock
                            print(f"🔽 === PROCESANDO STOCK === Producto: {producto.nombre}, Stock actual: {producto.stock}, Cantidad a reducir: {item.cantidad}")
                            
                            # Reducir stock solo si el pedido no estaba ya pagado
                            if producto.stock >= item.cantidad:
                                stock_antes = producto.stock
                                producto.stock -= item.cantidad
                                producto.save()
                                print(f"✅ Stock reducido para {producto.nombre}: {stock_antes} -> {producto.stock} (redujo {item.cantidad} unidades)")
                            else:
                                messages.warning(request, f"No hay suficiente stock para {producto.nombre}")
                                
                            # Crear PedidoItem solo si no existe
                            pedido_item, item_creado = PedidoItem.objects.get_or_create(
                                pedido=pedido,
                                producto=producto,
                                defaults={
                                    'nombre_producto': producto.nombre,
                                    'cantidad': item.cantidad,
                                    'precio_unitario': item.precio,
                                    'subtotal': item.precio * item.cantidad
                                }
                            )
                            if item_creado:
                                print(f"✅ Item del pedido guardado: {producto.nombre}")
                            else:
                                print(f"ℹ️ Item del pedido ya existía: {producto.nombre}")
                        else:
                            print(f"ℹ️ Stock ya procesado para {producto.nombre}, no se modifica")
                        
                    except Exception as e:
                        print(f"❌ Error procesando item del carrito: {str(e)}")
                
                # Marcar carrito como inactivo DESPUÉS de procesar todos los productos (solo si estaba activo y no se procesó antes)
                if carrito.is_active and not stock_ya_procesado:
                    carrito.is_active = False
                    carrito.save()
                    print("✅ Carrito marcado como inactivo")
                elif not carrito.is_active:
                    print("ℹ️ Carrito ya estaba inactivo, no se modifica")
                elif stock_ya_procesado:
                    print("ℹ️ Stock ya procesado, carrito no se modifica")
                    
            # Si no se encontraron productos del carrito, buscar desde PedidoItem
            if not productos:
                print("🔍 No se encontraron productos en carrito, buscando en PedidoItem...")
                pedido_items = PedidoItem.objects.filter(pedido=pedido)
                
                for item in pedido_items:
                    try:
                        productos.append({
                            "producto": item.nombre_producto,
                            "precio": item.precio_unitario,
                            "cantidad": item.cantidad,
                            "subtotal": item.subtotal,
                            "imagen": item.producto.imagen if item.producto else None
                        })
                    except Exception as e:
                        print(f"❌ Error procesando PedidoItem: {str(e)}")
                
                print(f"✅ Productos obtenidos desde PedidoItem: {len(productos)}")
                
            if not productos:
                print("❌ No se encontraron productos ni en carrito ni en PedidoItem")
                messages.warning(request, "No se encontraron productos en el pedido")
                
        except Exception as e:
            print(f"❌ Error obteniendo productos del carrito: {str(e)}")
            messages.error(request, "Error procesando los productos del pedido")

        print(f"🔍 Debug productos finales: {len(productos)} productos encontrados")

        # 🆕 GENERAR FACTURA ELECTRÓNICA SIMPLIFICADA
        factura_generada = False
        pdf_factura_url = None
        
        try:
            # Buscar factura existente primero
            factura_existente = None
            try:
                factura_existente = Factura.objects.get(pedido=pedido)
                print(f"📄 Factura ya existe: {factura_existente.numero_factura}")
                factura_generada = True
                pdf_factura_url = factura_existente.pdf_url
            except Factura.DoesNotExist:
                pass
            
            # Generar factura solo si no existe y tenemos productos
            if not factura_existente and productos:
                print("📄 Generando comprobante de compra...")
                
                # Crear factura en la base de datos
                factura = Factura.objects.create(
                    pedido=pedido,
                    numero_factura=f"COMP-{pedido.order_id}",
                    tipo_documento=39,  # Boleta Electrónica / Comprobante
                    estado='borrador',  # Usar estado válido del modelo
                    nombre_cliente=f"Cliente {pedido.email}",  # Usar email como nombre
                    email_cliente=pedido.email,  # Usar campo email del modelo
                    neto=int(float(pedido.monto) / 1.19),  # Calcular neto desde total
                    iva=int(float(pedido.monto) - (float(pedido.monto) / 1.19)),  # Calcular IVA
                    total=int(float(pedido.monto))
                )
                
                # Generar PDF usando facturacion_simple.py
                try:
                    from .facturacion_simple import generar_factura_automatica
                    
                    # Obtener perfil de usuario si está disponible
                    perfil_usuario = None
                    if request.user.is_authenticated and hasattr(request.user, 'perfilusuario'):
                        perfil_usuario = request.user.perfilusuario
                    
                    # Datos del cliente para el PDF
                    cliente_data = {
                        'nombre': perfil_usuario.user.username if perfil_usuario else f'Cliente {pedido.email}',
                        'email': perfil_usuario.user.email if perfil_usuario else pedido.email,
                        'rut': perfil_usuario.rut if (perfil_usuario and perfil_usuario.rut) else 'Sin RUT',
                        'costo_envio': float(pedido.costo_envio) if hasattr(pedido, 'costo_envio') and pedido.costo_envio else 0
                    }
                    
                    resultado_pdf = generar_factura_automatica(pedido, productos, cliente_data, perfil_usuario)
                    
                    if resultado_pdf.get('success'):
                        factura.pdf_url = resultado_pdf.get('pdf_url')
                        factura.save()
                        factura_generada = True
                        pdf_factura_url = resultado_pdf.get('pdf_url')
                        print(f"✅ Comprobante PDF generado: {pdf_factura_url}")
                    else:
                        print(f"⚠️ Error generando PDF: {resultado_pdf.get('error')}")
                        
                except ImportError:
                    print("⚠️ Módulo facturacion_simple no disponible, generando factura básica")
                
                # Marcar como generada aunque no tengamos PDF
                if not factura_generada:
                    factura_generada = True
                    print("✅ Comprobante de compra registrado en base de datos")
            
            elif not productos:
                print("⚠️ No se puede generar factura sin productos")
                    
        except Exception as e:
            print(f"❌ Error en sistema de facturación: {e}")
            # No fallar la compra por errores de facturación

        print(f"🔍 Debug productos finales: {len(productos)} productos encontrados")

        print(f"🏁 === FIN PAGO_EXITOSO === (timestamp: {datetime.now()})")
        
        return render(request, "pago_exitoso.html", {
            "email": email,
            "monto": monto,
            "order_id": order_id,
            "metodo": metodo,
            "productos": productos,
            "pedido": pedido,
            "factura_generada": factura_generada,
            "pdf_factura_url": pdf_factura_url
        })

    else:
        # Pago rechazado por el banco
        print(f"❌ Pago rechazado por Transbank - Status: {result.get('status', 'UNKNOWN')}")
        
        # Obtener order_id de la sesión para redirigir a página de rechazo
        order_id = request.session.get("order_id")
        if order_id:
            print(f"🔴 Redirigiendo a página de pago rechazado para order {order_id}")
            return redirect(f"/pago-rechazado/{order_id}/")
        else:
            messages.error(request, "El pago fue rechazado o anulado. Puedes intentar nuevamente.")
            return redirect("/carrito/")
@login_required
def pago_transferencia(request, order_id):
    """
    Vista para mostrar datos de transferencia bancaria y marcar pedido como pendiente
    """
    try:
        # Obtener el pedido
        pedido = Pedido.objects.get(order_id=order_id)
        
        # Verificar que el pedido pertenece al usuario actual o es accesible
        if hasattr(request.user, 'perfilusuario'):
            # Para usuarios autenticados, verificar que el email coincida
            if pedido.email != request.user.email:
                return render(request, 'error.html', {
                    'mensaje': 'No tienes permisos para acceder a este pedido'
                })
        
        # Marcar pedido como pendiente si no está ya procesado
        if pedido.estado == 'pagado':
            # Si ya está pagado, redirigir a página de éxito
            return redirect('pago_exitoso')
        elif pedido.estado != 'pendiente':
            pedido.estado = 'pendiente'
            pedido.save()
            print(f"✅ Pedido {order_id} marcado como pendiente (transferencia)")
        
        # Obtener productos del pedido
        productos = []
        pedido_items = PedidoItem.objects.filter(pedido=pedido)
        
        for item in pedido_items:
            productos.append({
                'producto': item.nombre_producto,
                'cantidad': item.cantidad,
                'precio': item.precio_unitario,
                'subtotal': item.subtotal
            })
        
        # Calcular totales para mostrar
        total_con_iva = float(pedido.monto)
        subtotal = round(total_con_iva / 1.19)
        iva = round(total_con_iva - subtotal)
        costo_envio = 0  # Por ahora, el envío ya está incluido en el monto
        
        context = {
            'order_id': order_id,
            'pedido': pedido,
            'productos': productos,
            'total': total_con_iva,
            'subtotal': subtotal,
            'iva': iva,
            'costo_envio': costo_envio,
        }
        
        return render(request, 'pago_transferencia.html', context)
        
    except Pedido.DoesNotExist:
        return render(request, 'error.html', {
            'mensaje': 'Pedido no encontrado'
        })
    except Exception as e:
        print(f"❌ Error en pago_transferencia: {str(e)}")
        return render(request, 'error.html', {
            'mensaje': 'Error al procesar el pago por transferencia'
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_pedido_transferencia(request):
    """
    API para crear pedido con método de pago transferencia
    """
    try:
        data = request.data
        user = request.user

        # Debug: Imprimir datos recibidos
        print("🔍 Datos recibidos para pedido transferencia:", data)

        email = data.get("email")
        monto = data.get("monto")
        metodo = data.get("metodo_pago")
        tipo_entrega = data.get("tipo_entrega")

        # Validaciones básicas
        if not email or not monto or metodo != "transferencia" or not tipo_entrega:
            error_msg = f"Faltan datos requeridos. Email: {bool(email)}, Monto: {bool(monto)}, Método: {metodo}, Tipo: {bool(tipo_entrega)}"
            print("❌", error_msg)
            return Response({"error": error_msg}, status=400)

        if tipo_entrega not in ["retiro", "envio"]:
            print("❌ Método de entrega inválido:", tipo_entrega)
            return Response({"error": "Método de entrega inválido"}, status=400)

        # Obtener carrito activo
        carrito = Carrito.objects.filter(user=user, is_active=True).first()
        if not carrito:
            return Response({"error": "No se encontró carrito activo"}, status=400)

        items = CarritoItem.objects.filter(carrito=carrito)
        if not items.exists():
            return Response({"error": "Carrito vacío"}, status=400)
        
        print(f"🔍 Debug crear_pedido_transferencia - Carrito encontrado: {carrito.id}, Items: {items.count()}")

        # Calcular peso total y dimensiones (para envío)
        peso_total = sum(item.producto.peso * item.cantidad for item in items)
        
        max_alto = 0
        max_ancho = 0
        total_largo = 0
        
        for item in items:
            cantidad = item.cantidad
            producto = item.producto
            
            total_largo += (producto.largo or 0) * cantidad
            max_ancho = max(max_ancho, producto.ancho or 0)
            max_alto = max(max_alto, producto.alto or 0)

        # Crear pedido con estado pendiente
        order_id = generar_order_id()
        pedido = Pedido.objects.create(
            order_id=order_id,
            email=email,
            monto=monto,
            estado="pendiente",  # Estado pendiente para transferencia
            metodo_pago="transferencia",  # Marcar como transferencia
            retiro_en_tienda=(tipo_entrega == "retiro"),
            envio_domicilio=(tipo_entrega == "envio"),
            peso_total=peso_total,
            alto=max_alto,
            ancho=max_ancho,
            largo=total_largo
        )

        if tipo_entrega == "envio":
            pedido.direccion = data.get("direccion")
            pedido.comuna = data.get("comuna")
            pedido.region = data.get("region")
            pedido.codigo_comuna_chilexpress = data.get("codigo_comuna_chilexpress")

            print(f"🚚 Datos de envío - Dirección: {pedido.direccion}, Comuna: {pedido.comuna}, Región: {pedido.region}")

            if not all([pedido.direccion, pedido.comuna, pedido.region]):
                pedido.delete()
                error_msg = f"Faltan datos de envío. Dirección: {bool(pedido.direccion)}, Comuna: {bool(pedido.comuna)}, Región: {bool(pedido.region)}"
                print("❌", error_msg)
                return Response({"error": error_msg}, status=400)

        pedido.save()

        # Crear los PedidoItems
        print(f"📝 Creando PedidoItems para pedido transferencia {order_id}...")
        for item in items:
            pedido_item = PedidoItem.objects.create(
                pedido=pedido,
                producto=item.producto,
                nombre_producto=item.producto.nombre,
                cantidad=item.cantidad,
                precio_unitario=item.precio,
                subtotal=item.precio * item.cantidad
            )
            print(f"  ✅ PedidoItem creado: {pedido_item.nombre_producto} x{pedido_item.cantidad}")
        
        print(f"✅ {items.count()} PedidoItems creados exitosamente para transferencia")

        # Marcar carrito como inactivo (reservar productos)
        carrito.is_active = False
        carrito.save()

        # Guardar en sesión para la página de transferencia
        request.session["order_id"] = order_id
        request.session["email"] = email
        request.session["monto"] = monto
        request.session["metodo_pago"] = metodo
        request.session["user_id"] = user.id
        request.session["tipo_entrega"] = tipo_entrega

        return Response({
            "success": True,
            "order_id": order_id,
            "redirect_url": f"/pago-transferencia/{order_id}/"
        })

    except Exception as e:
        print(f"❌ Error creando pedido transferencia: {str(e)}")
        return Response({
            "error": f"Error interno del servidor: {str(e)}"
        }, status=500)

# ================================
# APIs de Chilexpress
# ================================

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_regiones_chilexpress(request):
    """
    API para obtener todas las regiones disponibles desde Chilexpress
    """
    try:
        from .chilexpress import obtener_regiones
        regiones = obtener_regiones()
        return Response({
            "success": True,
            "regiones": regiones
        })
    except Exception as e:
        logger.error(f"Error obteniendo regiones: {str(e)}")
        return Response({
            "success": False,
            "error": str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_comunas_chilexpress(request, region_id):
    """
    API para obtener comunas de una región específica
    """
    try:
        from .chilexpress import obtener_comunas_por_region
        comunas = obtener_comunas_por_region(region_id)
        return Response({
            "success": True,
            "comunas": comunas
        })
    except Exception as e:
        logger.error(f"Error obteniendo comunas: {str(e)}")
        return Response({
            "success": False,
            "error": str(e)
        }, status=500)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def calcular_envio_chilexpress(request):
    """
    API para calcular tarifas de envío usando Chilexpress
    """
    try:
        from .chilexpress import calcular_tarifas_envio
        
        # Obtener datos del request
        data = request.data
        logger.info(f"📦 Calculando envío con datos: {data}")
        
        # Validar datos mínimos
        if not data.get('comuna_destino') or not data.get('productos'):
            return Response({
                "success": False,
                "error": "Faltan datos requeridos: comuna_destino y productos"
            }, status=400)
        
        # Calcular totales de peso y dimensiones de los productos
        productos = data.get('productos', [])
        peso_total = 0
        max_alto = 0
        max_ancho = 0
        total_largo = 0
        
        for producto in productos:
            cantidad = producto.get('cantidad', 1)
            peso_total += (producto.get('peso', 1) * cantidad)
            total_largo += (producto.get('largo', 10) * cantidad)
            max_ancho = max(max_ancho, producto.get('ancho', 10))
            max_alto = max(max_alto, producto.get('alto', 10))

        # Configurar datos para la API de Chilexpress
        datos_envio = {
            'comuna_destino': data.get('comuna_destino'),
            'region_destino': data.get('region_destino'),
            'peso_total': peso_total,
            'largo': total_largo,
            'ancho': max_ancho,
            'alto': max_alto
        }
        
        logger.info(f"📦 Datos de envío calculados: {datos_envio}")
        
        # Llamar a la función de cálculo de tarifas
        resultado = calcular_tarifas_envio(
                    productos,
                    data.get('comuna_destino'),
                    data.get('subtotal', 0)
                )
        
        return Response({
            "success": True,
            "opciones": resultado
        })
        
    except Exception as e:
        logger.error(f"❌ Error calculando envío: {str(e)}")
        return Response({
            "success": False,
            "error": str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def limpiar_carrito(request):
    """
    API para limpiar completamente el carrito del usuario autenticado
    """
    try:
        user = request.user
        
        # Obtener carrito activo
        carrito = Carrito.objects.filter(user=user, is_active=True).first()
        if not carrito:
            return Response({
                "success": True,
                "message": "No hay carrito activo para limpiar"
            })
        
        # Eliminar todos los items del carrito
        CarritoItem.objects.filter(carrito=carrito).delete()
        
        logger.info(f"🧹 Carrito limpiado para usuario {user.username}")
        
        return Response({
            "success": True,
            "message": "Carrito limpiado exitosamente"
        })
        
    except Exception as e:
        logger.error(f"❌ Error limpiando carrito: {str(e)}")
        return Response({
            "success": False,
            "error": f"Error interno del servidor: {str(e)}"
        }, status=500)

# ================================
# APIs de Pedidos y Historial
# ================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_pedidos(request):
    """
    API para obtener el historial de pedidos del usuario autenticado
    """
    try:
        user = request.user
        
        # Obtener pedidos del usuario por email
        pedidos = Pedido.objects.filter(email=user.email).order_by('-fecha')
        
        pedidos_data = []
        for pedido in pedidos:
            # Obtener items del pedido
            items = PedidoItem.objects.filter(pedido=pedido)
            
            items_data = []
            for item in items:
                items_data.append({
                    'nombre_producto': item.nombre_producto,
                    'cantidad': item.cantidad,
                    'precio_unitario': item.precio_unitario,
                    'subtotal': item.subtotal,
                    'imagen': item.producto.imagen.url if item.producto and item.producto.imagen else None
                })
            
            # Calcular totales
            total_con_iva = float(pedido.monto)
            subtotal = round(total_con_iva / 1.19)
            iva = round(total_con_iva - subtotal)
            
            pedidos_data.append({
                'order_id': pedido.order_id,
                'fecha': pedido.fecha.strftime('%d/%m/%Y %H:%M'),
                'estado': pedido.estado,
                'monto': pedido.monto,
                'subtotal': subtotal,
                'iva': iva,
                'total': total_con_iva,
                'tipo_entrega': 'Retiro en tienda' if pedido.retiro_en_tienda else 'Envío a domicilio',
                'direccion': pedido.direccion if pedido.envio_domicilio else None,
                'comuna': pedido.comuna if pedido.envio_domicilio else None,
                'items': items_data,
                'items_count': len(items_data)
            })
        
        logger.info(f"📊 Historial pedidos para {user.email}: {len(pedidos_data)} pedidos encontrados")
        
        return Response({
            'success': True,
            'pedidos': pedidos_data
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo historial de pedidos: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_pedido(request, order_id):
    """
    API para obtener el detalle de un pedido específico
    """
    try:
        user = request.user
        
        # Buscar el pedido por order_id y verificar que pertenece al usuario
        try:
            pedido = Pedido.objects.get(order_id=order_id, email=user.email)
        except Pedido.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Pedido no encontrado o no pertenece al usuario'
            }, status=404)
        
        # Obtener items del pedido
        items = PedidoItem.objects.filter(pedido=pedido)
        
        items_data = []
        for item in items:
            items_data.append({
                'nombre': item.nombre_producto,
                'cantidad': item.cantidad,
                'precio_unitario': item.precio_unitario,
                'subtotal': item.subtotal,
                'imagen': item.producto.imagen.url if item.producto and item.producto.imagen else None
            })
        
        # Calcular totales
        total_con_iva = float(pedido.monto)
        subtotal = round(total_con_iva / 1.19)
        iva = round(total_con_iva - subtotal)
        
        # Información de envío si aplica
        direccion_completa = None
        envio_info = None
        if pedido.envio_domicilio:
            direccion_completa = {
                'direccion': pedido.direccion,
                'comuna': pedido.comuna,
                'region': pedido.region
            }
            envio_info = {
                'direccion': pedido.direccion,
                'comuna': pedido.comuna,
                'region': pedido.region,
                'ot_codigo': pedido.ot_codigo,
                'estado_envio': pedido.estado_envio
            }
        
        # Información de factura si existe
        factura_info = None
        if hasattr(pedido, 'factura'):
            factura = pedido.factura
            factura_info = {
                'numero_factura': factura.numero_factura,
                'tipo_documento': factura.get_tipo_documento_display_short(),
                'estado': factura.estado,
                'pdf_url': factura.pdf_url
            }
        
        # Información de transferencia si aplica
        transferencia_info = None
        if pedido.metodo_pago == 'transferencia' and pedido.estado == 'pendiente':
            transferencia_info = {
                'banco': 'Banco Santander',
                'tipo_cuenta': 'Cuenta Corriente',
                'numero_cuenta': '0 000 85 73422 9',
                'titular': 'AutoParts SpA',
                'rut_titular': '20.654.445-7',
                'email_confirmacion': 'transferencias@autoparts.cl',
                'monto': pedido.monto,
                'order_id': pedido.order_id
            }
        
        pedido_data = {
            'order_id': pedido.order_id,
            'fecha': pedido.fecha.strftime('%d/%m/%Y %H:%M'),
            'estado': pedido.estado,
            'metodo_pago': pedido.metodo_pago,
            'monto': pedido.monto,
            'subtotal': subtotal,
            'iva': iva,
            'total': total_con_iva,
            'tipo_entrega': 'Retiro en tienda' if pedido.retiro_en_tienda else 'Envío a domicilio',
            'productos': items_data,  # Cambiado de 'items' a 'productos'
            'direccion_completa': direccion_completa,
            'envio': envio_info,
            'factura': factura_info,
            'transferencia': transferencia_info
        };
        
        logger.info(f"📄 Detalle pedido {order_id} obtenido para {user.email}")
        
        return Response({
            'success': True,
            'pedido': pedido_data
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalle del pedido {order_id}: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ================================
# Dashboard de Gestión de Pedidos
# ================================

def dashboard_pedidos_page(request):
    """
    Página del dashboard para gestión de pedidos (solo trabajadores/admin)
    """
    # Verificar que el usuario sea trabajador o admin
    if not request.user.is_authenticated:
        return redirect('login')
    
    es_trabajador = False
    es_admin = request.user.is_staff
    
    if hasattr(request.user, 'perfilusuario'):
        es_trabajador = request.user.perfilusuario.trabajador
    
    if not es_trabajador and not es_admin:
        return render(request, 'error.html', {
            'mensaje': 'No tienes permisos para acceder a esta sección'
        })
    
    return render(request, 'dashboard_pedidos.html', {
        'es_admin': es_admin,
        'es_trabajador': es_trabajador
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lista_pedidos_dashboard(request):
    """
    API para obtener todos los pedidos para el dashboard de gestión
    """
    try:
        user = request.user
        
        # Verificar permisos
        es_admin = user.is_staff
        es_trabajador = False
        
        if hasattr(user, 'perfilusuario'):
            es_trabajador = user.perfilusuario.trabajador
        
        if not es_trabajador and not es_admin:
            return Response({
                'success': False,
                'error': 'No tienes permisos para acceder a esta información'
            }, status=403)
        
        # Obtener parámetros de filtro
        estado_filtro = request.GET.get('estado', '')
        metodo_pago_filtro = request.GET.get('metodo_pago', '')
        fecha_desde = request.GET.get('fecha_desde', '')
        fecha_hasta = request.GET.get('fecha_hasta', '')
        search = request.GET.get('search', '')
        
        # Consulta base
        pedidos = Pedido.objects.all().order_by('-fecha')
        
        # Aplicar filtros
        if estado_filtro:
            pedidos = pedidos.filter(estado=estado_filtro)
        
        if metodo_pago_filtro:
            pedidos = pedidos.filter(metodo_pago=metodo_pago_filtro)
        
        if fecha_desde:
            from datetime import datetime
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d')
            pedidos = pedidos.filter(fecha__gte=fecha_desde_obj)
        
        if fecha_hasta:
            from datetime import datetime
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            # Agregar 23:59:59 para incluir todo el día
            fecha_hasta_obj = fecha_hasta_obj.replace(hour=23, minute=59, second=59)
            pedidos = pedidos.filter(fecha__lte=fecha_hasta_obj)
        
        if search:
            from django.db import models
            pedidos = pedidos.filter(
                models.Q(order_id__icontains=search) |
                models.Q(email__icontains=search) |
               
                models.Q(direccion__icontains=search)
            )
        
        # Preparar datos para respuesta
        pedidos_data = []
        for pedido in pedidos:
            # Contar productos
            total_productos = PedidoItem.objects.filter(pedido=pedido).count()
            cantidad_productos = sum(item.cantidad for item in PedidoItem.objects.filter(pedido=pedido))
            fecha_local = timezone.localtime(pedido.fecha, timezone.get_default_timezone())
            
            # Información de envío
            tipo_entrega = 'Retiro en tienda' if pedido.retiro_en_tienda else 'Envío a domicilio'
            
            pedidos_data.append({
                'order_id': pedido.order_id,
                'fecha': fecha_local.strftime('%d/%m/%Y %H:%M'),
                'estado': pedido.estado,
                'monto': pedido.monto,
                'email': pedido.email,
                'metodo_pago': pedido.metodo_pago,
                'tipo_entrega': tipo_entrega,
                'direccion': pedido.direccion if pedido.envio_domicilio else None,
                'comuna': pedido.comuna if pedido.envio_domicilio else None,
                'total_productos': total_productos,
                'cantidad_productos': cantidad_productos,
                'ot_codigo': pedido.ot_codigo if pedido.ot_codigo else None,
                'estado_envio': pedido.estado_envio if pedido.estado_envio else None,
                'costo_envio': pedido.costo_envio if hasattr(pedido, 'costo_envio') else None
            })
        
        # Estadísticas básicas
        estados_ventas_completadas = ['pagado', 'listo_retiro', 'retirado', 'preparacion', 'enviado']
        pedidos_ventas = Pedido.objects.filter(estado__in=estados_ventas_completadas)
        
        stats = {
            'total_pedidos': Pedido.objects.count(),
            'pedidos_pendientes': Pedido.objects.filter(estado='pendiente').count(),
            'pedidos_pagados': Pedido.objects.filter(estado='pagado').count(),
            'pedidos_fallidos': Pedido.objects.filter(estado='fallido').count(),
            'pedidos_listo_retiro': Pedido.objects.filter(estado='listo_retiro').count(),
            'pedidos_retirados': Pedido.objects.filter(estado='retirado').count(),
            'pedidos_preparacion': Pedido.objects.filter(estado='preparacion').count(),
            'pedidos_enviados': Pedido.objects.filter(estado='enviado').count(),
            'pedidos_cancelados': Pedido.objects.filter(estado='cancelado').count(),
            'total_ventas': sum(float(p.monto) for p in pedidos_ventas),
            'pedidos_transferencia': Pedido.objects.filter(metodo_pago='transferencia').count(),
            'pedidos_webpay': Pedido.objects.filter(metodo_pago='webpay').count(),
        }
        
        return Response({
            'success': True,
            'pedidos': pedidos_data,
            'estadisticas': stats,
            'total': len(pedidos_data)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo lista de pedidos: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def actualizar_estado_pedido(request, order_id):
    """
    API para actualizar el estado de un pedido
    """
    try:
        user = request.user
        
        # Verificar permisos
        es_admin = user.is_staff
        es_trabajador = False
        
        if hasattr(user, 'perfilusuario'):
            es_trabajador = user.perfilusuario.trabajador
        
        if not es_trabajador and not es_admin:
            return Response({
                'success': False,
                'error': 'No tienes permisos para actualizar pedidos'
            }, status=403)
        
        # Obtener pedido
        try:
            pedido = Pedido.objects.get(order_id=order_id)
        except Pedido.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Pedido no encontrado'
            }, status=404)
        
        # Obtener nuevo estado
        nuevo_estado = request.data.get('estado')
        
        if not nuevo_estado:
            return Response({
                'success': False,
                'error': 'Estado requerido'
            }, status=400)
        
        # Validar estado usando las opciones del modelo
        estados_validos = [opcion[0] for opcion in Pedido.ESTADOS_PEDIDO]
        if nuevo_estado not in estados_validos:
            return Response({
                'success': False,
                'error': f'Estado inválido. Estados válidos: {", ".join(estados_validos)}'
            }, status=400)
        
        # Actualizar estado
        estado_anterior = pedido.estado
        pedido.estado = nuevo_estado
        pedido.save()
        
        logger.info(f"✅ Pedido {order_id} actualizado de '{estado_anterior}' a '{nuevo_estado}' por {user.username}")
        
        return Response({
            'success': True,
            'message': f'Estado actualizado de "{estado_anterior}" a "{nuevo_estado}"',
            'pedido': {
                'order_id': pedido.order_id,
                'estado': pedido.estado,
                'fecha': pedido.fecha.strftime('%d/%m/%Y %H:%M')
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error actualizando estado del pedido {order_id}: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_pedido_dashboard(request, order_id):
    """
    API para obtener detalles completos de un pedido en el dashboard
    """
    try:
        user = request.user
        
        # Verificar permisos
        es_admin = user.is_staff
        es_trabajador = False
        
        if hasattr(user, 'perfilusuario'):
            es_trabajador = user.perfilusuario.trabajador
        
        if not es_trabajador and not es_admin:
            return Response({
                'success': False,
                'error': 'No tienes permisos para ver los detalles del pedido'
            }, status=403)
        
        # Buscar el pedido
        try:
            pedido = Pedido.objects.get(order_id=order_id)
        except Pedido.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Pedido no encontrado'
            }, status=404)
        
        # Obtener items del pedido
        items = PedidoItem.objects.filter(pedido=pedido)
        
        items_data = []
        for item in items:
            items_data.append({
                'nombre': item.nombre_producto,
                'cantidad': item.cantidad,
                'precio_unitario': item.precio_unitario,
                'subtotal': item.subtotal,
                'imagen': item.producto.imagen.url if item.producto and item.producto.imagen else None
            })

        
        # Calcular totales
        total_con_iva = float(pedido.monto)
        subtotal = round(total_con_iva / 1.19)
        iva = round(total_con_iva - subtotal)
        
        # Información de cliente
        cliente_info = {
            'email': pedido.email
        }
        
        # Buscar información adicional del usuario si existe
        try:
            from django.contrib.auth.models import User
            usuario = User.objects.get(email=pedido.email)
            if hasattr(usuario, 'perfilusuario'):
                perfil = usuario.perfilusuario
                cliente_info.update({
                    'nombre': usuario.username,
                    'rut': perfil.rut if perfil.rut else 'No especificado',
                    'es_empresa': perfil.empresa,
                    'es_trabajador': perfil.trabajador
                })
        except User.DoesNotExist:
            pass
        
        # Información de envío si aplica
        direccion_completa = None
        envio_info = None
        if pedido.envio_domicilio:
            direccion_completa = {
                'direccion': pedido.direccion,
                'comuna': pedido.comuna,
                'region': pedido.region
            }
            envio_info = {
                'direccion': pedido.direccion,
                'comuna': pedido.comuna,
                'region': pedido.region,
                'ot_codigo': pedido.ot_codigo,
                'estado_envio': pedido.estado_envio,
                'peso_total': pedido.peso_total,
                'dimensiones': f"{pedido.alto}x{pedido.ancho}x{pedido.largo} cm" if all([pedido.alto, pedido.ancho, pedido.largo]) else None
            }
        
        # Información de factura si existe
        factura_info = None
        if hasattr(pedido, 'factura'):
            factura = pedido.factura
            factura_info = {
                'numero_factura': factura.numero_factura,
                'tipo_documento': factura.get_tipo_documento_display_short(),
                'estado': factura.estado,
                'pdf_url': factura.pdf_url
            }
        
        # Información de transferencia si aplica
        transferencia_info = None
        if pedido.metodo_pago == 'transferencia':
            transferencia_info = {
                'banco': 'Banco Santander',
                'tipo_cuenta': 'Cuenta Corriente',
                'numero_cuenta': '0 000 85 73422 9',
                'titular': 'AutoParts SpA',
                'rut_titular': '20.654.445-7',
                'email_confirmacion': 'transferencias@autoparts.cl',
                'monto': pedido.monto,
                'order_id': pedido.order_id
            }
        
        pedido_data = {
            'order_id': pedido.order_id,
            'fecha': pedido.fecha.strftime('%d/%m/%Y %H:%M'),
            'estado': pedido.estado,
            'metodo_pago': pedido.metodo_pago,
            'monto': pedido.monto,
            'subtotal': subtotal,
            'iva': iva,
            'total': total_con_iva,
            'tipo_entrega': 'Retiro en tienda' if pedido.retiro_en_tienda else 'Envío a domicilio',
            'productos': items_data,
            'cliente': cliente_info,
            'direccion_completa': direccion_completa,
            'envio': envio_info,
            'factura': factura_info,
            'transferencia': transferencia_info
        }
        
        logger.info(f"📄 Detalle pedido {order_id} obtenido para dashboard por {user.username}")
        
        return Response({
            'success': True,
            'pedido': pedido_data
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalle del pedido {order_id} para dashboard: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)

# ================================
# Manejo de Pagos Rechazados
# ================================

def pago_rechazado_page(request, order_id):
    """
    Página que se muestra cuando un pago por WebPay es rechazado
    """
    try:
        # Buscar el pedido
        pedido = Pedido.objects.get(order_id=order_id)
        
        # Verificar que el pedido pertenece al usuario o permitir acceso a admin
        if not (request.user.is_authenticated and 
                (pedido.email == request.user.email or request.user.is_staff)):
            return redirect('login')
        
        # Marcar el pedido como fallido si no lo está ya
        if pedido.estado != 'fallido':
            pedido.estado = 'fallido'
            pedido.save()
            logger.info(f"🔴 Pedido {order_id} marcado como fallido")
        
        context = {
            'order_id': pedido.order_id,
            'monto': pedido.monto,
            'email': pedido.email,
            'fecha': pedido.fecha.strftime('%d/%m/%Y %H:%M'),
            'user_id': request.user.id if request.user.is_authenticated else None
        }
        
        return render(request, 'pago_rechazado.html', context)
        
    except Pedido.DoesNotExist:
        logger.error(f"❌ Pedido {order_id} no encontrado para pago rechazado")
        return redirect('carrito')
    except Exception as e:
        logger.error(f"❌ Error en pago_rechazado_page: {str(e)}")
        return redirect('carrito')

def api_externa_page(request):
    """
    Página de documentación de la API Externa
    """
    return render(request, 'api_externa.html')

def taller_manolo_page(request):
    """
    Vista simulada del Sistema del Taller de Manolo
    Demuestra cómo se vería la integración desde el lado del cliente
    """
    return render(request, 'taller_manolo.html')

# ================================
# APIs para Compatibilidad de Vehículos
# ================================

class MarcasVehiculosAPIView(APIView):
    """
    API para obtener las marcas de vehículos desde CarAPI
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            from .car_api import car_api_client
            # Obtener marcas desde CarAPI
            marcas = car_api_client.get_makes()
            if marcas is None:
                return Response({
                    'error': 'Error al obtener marcas de vehículos'
                }, status=500)
            # Formatear respuesta
            data = []
            for marca in marcas:
                data.append({
                    'id': marca['id'],
                    'nombre': marca['name'],
                    'pais_origen': marca.get('country', ''),
                })
            logger.info(f"✅ {len(data)} marcas de vehículos enviadas desde CarAPI")
            return Response(data, status=200)
        except Exception as e:
            logger.error(f"❌ Error obteniendo marcas de vehículos: {str(e)}")
            return Response({
                'error': 'Error interno del servidor'
            }, status=500)

class ModelosVehiculosAPIView(APIView):
    """
    API para obtener los modelos de vehículos de una marca específica desde CarAPI
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            from .car_api import car_api_client
            marca_nombre = request.GET.get('marca')
            print(f"🔍 DEBUG: Parámetro marca recibido: '{marca_nombre}'")
            if not marca_nombre:
                return Response({
                    'error': 'El parámetro marca es requerido'
                }, status=400)
            # Obtener modelos desde CarAPI
            print(f"🚗 Buscando modelos para marca: {marca_nombre}")
            modelos = car_api_client.search_models_by_make_name(marca_nombre)
            print(f"📊 Modelos recibidos de CarAPI: {len(modelos) if modelos else 0}")
            if modelos:
                print(f"🔍 Primer modelo como ejemplo: {modelos[0] if modelos else 'N/A'}")
            if modelos is None:
                return Response({
                    'error': 'Error al obtener modelos de vehículos'
                }, status=500)
            # Formatear respuesta
            data = []
            for modelo in modelos:
                data.append({
                    'id': modelo['id'],
                    'nombre': modelo['name'],
                    'año_inicio': modelo.get('year_start'),
                    'año_fin': modelo.get('year_end'),
                    'marca_nombre': modelo.get('make', marca_nombre)
                })
            print(f"✅ {len(data)} modelos formateados para envío")
            logger.info(f"✅ {len(data)} modelos de vehículos enviados para marca {marca_nombre}")
            return Response(data, status=200)
        except Exception as e:
            logger.error(f"❌ Error obteniendo modelos de vehículos: {str(e)}")
            return Response({
                'error': 'Error interno del servidor'
            }, status=500)

def error_404_view(request, exception=None):
    return render(request, '404.html', status=404)