from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

# Create your models here.
    
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500, blank=True, null=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre
    
class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=500)
    logo = models.ImageField(upload_to='logos', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.PositiveIntegerField(default=1)
    precio_mayorista = models.PositiveIntegerField(default=1)
    descripcion = models.CharField(max_length=500)
    stock =  models.PositiveIntegerField()
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    marca = models.ManyToManyField(Marca, related_name='productos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    peso = models.DecimalField( max_digits=5, decimal_places=2)
    largo = models.PositiveIntegerField()
    ancho = models.PositiveIntegerField()
    alto = models.PositiveIntegerField()
    

    def __str__(self):
        return self.nombre
    
class MarcaVehiculo(models.Model):
    """Marcas de vehículos (separadas de marcas de productos)"""
    nombre = models.CharField(max_length=100, unique=True)
    pais_origen = models.CharField(max_length=50, blank=True, null=True)
    activa = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Marca de Vehículo"
        verbose_name_plural = "Marcas de Vehículos"
        ordering = ['nombre']

class ModeloVehiculo(models.Model):
    """Modelos específicos de cada marca"""
    marca_vehiculo = models.ForeignKey(MarcaVehiculo, on_delete=models.CASCADE, related_name='modelos')
    nombre = models.CharField(max_length=100)
    año_inicio = models.IntegerField()
    año_fin = models.IntegerField(null=True, blank=True)  # null = sigue en producción
    tipo_vehiculo = models.CharField(max_length=50, choices=[
        ('sedan', 'Sedán'),
        ('hatchback', 'Hatchback'),
        ('suv', 'SUV'),
        ('pickup', 'Pick-up'),
        ('coupe', 'Coupé'),
        ('convertible', 'Convertible'),
        ('wagon', 'Station Wagon'),
        ('minivan', 'Minivan'),
        ('otro', 'Otro')
    ], default='sedan')
    cilindrada = models.CharField(max_length=20, blank=True, null=True)  # ej: "1.6L", "2.0L"
    combustible = models.CharField(max_length=20, choices=[
        ('gasolina', 'Gasolina'),
        ('diesel', 'Diésel'),
        ('hibrido', 'Híbrido'),
        ('electrico', 'Eléctrico'),
        ('gnv', 'GNV'),
        ('otro', 'Otro')
    ], default='gasolina')
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        fin = self.año_fin if self.año_fin else "presente"
        return f"{self.marca_vehiculo.nombre} {self.nombre} ({self.año_inicio}-{fin})"

    class Meta:
        verbose_name = "Modelo de Vehículo"
        verbose_name_plural = "Modelos de Vehículos"
        ordering = ['marca_vehiculo__nombre', 'nombre', 'año_inicio']
        unique_together = ['marca_vehiculo', 'nombre', 'año_inicio']

class CompatibilidadVehiculo(models.Model):
    """Relación mejorada entre productos y vehículos compatibles"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='compatibilidades')
    modelo_vehiculo = models.ForeignKey(ModeloVehiculo, null=True, blank=True, on_delete=models.SET_NULL)
    año_desde = models.IntegerField(null=True, blank=True)
    año_hasta = models.IntegerField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True, help_text="Notas adicionales sobre la compatibilidad")
    verificado = models.BooleanField(default=False, help_text="Compatibilidad verificada por técnico")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    todas = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.producto.nombre} - {self.modelo_vehiculo} ({self.año_desde}-{self.año_hasta})"

    class Meta:
        verbose_name = "Compatibilidad de Vehículo"
        verbose_name_plural = "Compatibilidades de Vehículos"
        unique_together = ['producto', 'modelo_vehiculo', 'año_desde', 'año_hasta']
        ordering = ['producto__nombre', 'modelo_vehiculo__marca_vehiculo__nombre']

class Vehiculo(models.Model):
    """Mantener por compatibilidad - DEPRECATED"""
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    modelo_auto = models.CharField(max_length=100)
    año_desde = models.IntegerField()
    año_hasta = models.IntegerField()

    def __str__(self):
        return f"{self.producto.nombre} - {self.marca.nombre} {self.modelo_auto} ({self.año_desde}-{self.año_hasta})"
    
class Carrito(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True)
    creado = models.DateTimeField(auto_now_add=True)  
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Carrito de {self.user.username} - Activo {self.is_active}"
    
class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.PositiveIntegerField(default=1) 

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"
    
    def subtotal(self):
        return self.precio * self.cantidad 
    

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    trabajador = models.BooleanField(default=False)
    empresa = models.BooleanField(default=False)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    rut = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.user.username
    

class Pedido(models.Model):
    METODOS_PAGO = (
        ('webpay', 'WebPay'),
        ('transferencia', 'Transferencia Bancaria'),
    )
    
    ESTADOS_PEDIDO = (
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('fallido', 'Fallido'),
        ('cancelado', 'Cancelado'),
        ('listo_retiro', 'Listo para Retiro'),
        ('retirado', 'Retirado'),
        ('preparacion', 'En Preparación'),
        ('enviado', 'Enviado'),
    )
    
    order_id = models.CharField(max_length=26, unique=True)  # ID alfanumérico para Transbank
    email = models.EmailField()
    monto = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default="pendiente")
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default='webpay')
    fecha = models.DateTimeField(auto_now_add=True)
    retiro_en_tienda = models.BooleanField( default=False)
    envio_domicilio = models.BooleanField( default=False )
    direccion = models.CharField(max_length=225, blank=True, null=True)
    comuna = models.CharField(max_length=100, blank=True, null=True)
    codigo_comuna_chilexpress = models.CharField(max_length=10, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    peso_total = models.FloatField(blank=True, null=True)
    alto = models.PositiveIntegerField(blank=True, null=True)
    ancho = models.PositiveIntegerField(blank=True, null=True)
    largo = models.PositiveIntegerField(blank=True, null=True)
    costo_envio = models.PositiveIntegerField(default=0, blank=True, null=True)  # Costo de envío si aplica
    # Campos para seguimiento de Chilexpress
    ot_codigo = models.CharField(max_length=50, blank=True, null=True)  # Orden de transporte
    etiqueta_url = models.URLField(blank=True, null=True)  # URL de la etiqueta
    estado_envio = models.CharField(max_length=50, blank=True, null=True)  # Estado del envío

    def __str__(self):
        return f"Pedido {self.order_id} - {self.email} - {self.estado}"
    
class PedidoItem(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    nombre_producto = models.CharField(max_length=200)  # Guardar nombre por si el producto se elimina
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.PositiveIntegerField()  # Precio al momento de la compra
    subtotal = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.cantidad} x {self.nombre_producto} - Pedido {self.pedido.order_id}"

    class Meta:
        verbose_name = "Item de Pedido"
        verbose_name_plural = "Items de Pedido"

class Factura(models.Model):
    """Modelo para gestionar facturas electrónicas"""
    TIPOS_DOCUMENTO = (
        (33, 'Factura Electrónica'),
        (39, 'Boleta Electrónica'),
        (56, 'Nota de Débito Electrónica'),
        (61, 'Nota de Crédito Electrónica'),
    )
    
    ESTADOS_FACTURA = (
        ('borrador', 'Borrador'),
        ('generada', 'Generada'),
        ('enviada_sii', 'Enviada al SII'),
        ('aceptada_sii', 'Aceptada por SII'),
        ('rechazada_sii', 'Rechazada por SII'),
        ('anulada', 'Anulada'),
    )
    
    # Relación con pedido
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='factura')
    
    # Datos del documento
    tipo_documento = models.IntegerField(choices=TIPOS_DOCUMENTO, default=39)
    numero_factura = models.CharField(max_length=20, blank=True, null=True)
    folio = models.CharField(max_length=20, blank=True, null=True)
    fecha_emision = models.DateTimeField(auto_now_add=True)
    
    # Datos del cliente
    rut_cliente = models.CharField(max_length=12, default='66666666-6')
    nombre_cliente = models.CharField(max_length=200)
    email_cliente = models.EmailField()
    direccion_cliente = models.CharField(max_length=255, blank=True, null=True)
    
    # Montos
    neto = models.PositiveIntegerField()
    iva = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    
    # Estado y seguimiento
    estado = models.CharField(max_length=20, choices=ESTADOS_FACTURA, default='borrador')
    
    # URLs y archivos
    pdf_url = models.URLField(blank=True, null=True)
    xml_url = models.URLField(blank=True, null=True)
    
    # Integración con Tributi
    tributi_id = models.CharField(max_length=50, blank=True, null=True)
    estado_sii = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        tipo_doc = dict(self.TIPOS_DOCUMENTO).get(self.tipo_documento, 'Documento')
        return f"{tipo_doc} {self.numero_factura or 'Sin número'} - {self.pedido.order_id}"
    
    def get_tipo_documento_display_short(self):
        """Retorna versión corta del tipo de documento"""
        mapping = {
            33: 'Factura',
            39: 'Boleta',
            56: 'N. Débito',
            61: 'N. Crédito',
        }
        return mapping.get(self.tipo_documento, 'Documento')
    
    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ['-created_at']