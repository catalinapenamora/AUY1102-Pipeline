import pytz
from rest_framework import serializers
from .models import Producto, Marca, Categoria, Vehiculo, Carrito, CarritoItem, MarcaVehiculo, ModeloVehiculo, CompatibilidadVehiculo
import json

class CompatibilidadVehiculoSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.SerializerMethodField()
    modelo_nombre = serializers.SerializerMethodField()
    todas = serializers.BooleanField(default=False)  # <-- Añadir este campo

    class Meta:
        model = CompatibilidadVehiculo
        fields = ['id', 'modelo_vehiculo', 'año_desde', 'año_hasta', 'notas', 'marca_nombre', 'modelo_nombre', 'todas']

    def get_marca_nombre(self, obj):
        if getattr(obj, 'todas', False):
            return None
        return obj.modelo_vehiculo.marca_vehiculo.nombre

    def get_modelo_nombre(self, obj):
        if getattr(obj, 'todas', False):
            return None
        return obj.modelo_vehiculo.nombre

class ProductoSerializer(serializers.ModelSerializer):
    imagen = serializers.ImageField(required=False)
    marca = serializers.PrimaryKeyRelatedField(queryset=Marca.objects.all(), many=True)
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())
    compatibilidades = serializers.SerializerMethodField()
    
    nombre_categoria = serializers.SerializerMethodField()
    nombre_marcas = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'precio','precio_mayorista','descripcion', 'stock', 'imagen',
            'marca', 'categoria', 'fecha_creacion',
            'peso', 'largo', 'ancho', 'alto',
            'nombre_categoria', 'nombre_marcas', 'compatibilidades'
        ]

    def get_nombre_categoria(self, obj):
        return obj.categoria.nombre if obj.categoria else None

    def get_nombre_marcas(self, obj):
        return [marca.nombre for marca in obj.marca.all()]

    def get_compatibilidades(self, obj):
        # Si existe una compatibilidad total, devolver solo esa
        total = obj.compatibilidades.filter(todas=True).first()
        if total:
            return [{"todas": True}]
        # Si no, devolver las compatibilidades normales
        return CompatibilidadVehiculoSerializer(obj.compatibilidades.all(), many=True).data

    def create(self, validated_data):
        # Procesar compatibilidades si están en el request
        compatibilidades_data = self.context.get('compatibilidades', [])
        print(f"🔍 CREATE - Compatibilidades recibidas: {compatibilidades_data}")
        print(f"🔍 CREATE - Tipo de compatibilidades: {type(compatibilidades_data)}")
        print(f"🔍 CREATE - Longitud: {len(compatibilidades_data) if compatibilidades_data else 0}")
        
        producto = super().create(validated_data)
        print(f"🔍 CREATE - Producto creado: {producto.id} - {producto.nombre}")
        
        self._save_compatibilidades(producto, compatibilidades_data)
        return producto

    def update(self, instance, validated_data):
        compatibilidades_data = self.context.get('compatibilidades', [])
        producto = super().update(instance, validated_data)
        self._save_compatibilidades(producto, compatibilidades_data)
        return producto

    def _save_compatibilidades(self, producto, compatibilidades_data):
        """Guardar compatibilidades de vehículos para el producto"""
        print(f"🔍 DEBUG _save_compatibilidades - Datos recibidos: {compatibilidades_data}")
        
        # Eliminar compatibilidades existentes
        CompatibilidadVehiculo.objects.filter(producto=producto).delete()
        if not compatibilidades_data:
            return
        # Compatibilidad total
        if len(compatibilidades_data) == 1 and compatibilidades_data[0].get('todas'):
            CompatibilidadVehiculo.objects.create(producto=producto, todas=True)
            return
        # Compatibilidades normales
        for comp_data in compatibilidades_data:
            marca_nombre = comp_data.get('marca_nombre', '')
            modelo_nombre = comp_data.get('modelo_nombre', '')
            if not marca_nombre or not modelo_nombre:
                continue
            año_desde = int(comp_data['año_desde']) if comp_data.get('año_desde') else None
            año_hasta = int(comp_data['año_hasta']) if comp_data.get('año_hasta') else None
            marca_vehiculo, _ = MarcaVehiculo.objects.get_or_create(nombre=marca_nombre)
            modelo_vehiculo, _ = ModeloVehiculo.objects.get_or_create(
                nombre=modelo_nombre,
                marca_vehiculo=marca_vehiculo,
                defaults={
                    'año_inicio': año_desde,
                    'año_fin': año_hasta if año_hasta != año_desde else None
                }
            )
            CompatibilidadVehiculo.objects.create(
                producto=producto,
                modelo_vehiculo=modelo_vehiculo,
                año_desde=año_desde,
                año_hasta=año_hasta,
                notas=comp_data.get('notas', ''),
                todas=False,
                creado_por=self.context.get('request').user if self.context.get('request') else None
            )
    
class MarcaSerializer(serializers.ModelSerializer):
    class  Meta:
        model = Marca
        fields = '__all__'

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

class VehiculoSerializer(serializers.Serializer):
    producto = ProductoSerializer()
    marca = MarcaSerializer()

    class Meta:
        model = Vehiculo
        fields = '__all__'

class CarritoItemSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = CarritoItem
        fields = ['id', 'producto', 'cantidad']

class CarritoSerializer(serializers.ModelSerializer):
    items = CarritoItemSerializer(many=True, read_only=True)

    class Meta:
        model = Carrito
        fields = ['id', 'user', 'is_active', 'items']

class MarcaVehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarcaVehiculo
        fields = ['id', 'nombre', 'pais_origen', 'activa']

class ModeloVehiculoSerializer(serializers.ModelSerializer):
    marca_nombre = serializers.SerializerMethodField()

    class Meta:
        model = ModeloVehiculo
        fields = ['id', 'marca_vehiculo', 'nombre', 'año_inicio', 'año_fin', 'tipo_vehiculo', 'marca_nombre']

    def get_marca_nombre(self, obj):
        return obj.marca_vehiculo.nombre
    

from .models import Pedido

class PedidoSerializer(serializers.ModelSerializer):
    fecha = serializers.DateTimeField(
        format="%d/%m/%Y %H:%M",
        default_timezone=pytz.timezone('America/Santiago'),
        read_only=True
    )
    email = serializers.CharField(source='cliente.email', read_only=True)

    class Meta:
        model = Pedido
        fields = [
            'order_id',
            'email',
            'monto',
            'metodo_pago',
            'retiro_en_tienda',
            'envio_domicilio',
            'direccion',
            'comuna',
            'region',
            'codigo_comuna_chilexpress',
            'costo_envio',
            'fecha',  # <-- Agregado para evitar el error
            # si quieres, agrega aquí otros campos (estado, productos, etc.)
        ]
