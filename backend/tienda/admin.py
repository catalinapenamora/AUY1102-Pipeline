from django.contrib import admin
from .models import Producto, Categoria, Marca, Carrito, PerfilUsuario, Pedido, PedidoItem
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
# Register your models here.

admin.site.register(Producto)
admin.site.register(Categoria)
admin.site.register(Marca)
admin.site.register(Carrito)

admin.site.unregister(Producto)
admin.site.unregister(Carrito)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'fecha_creacion')
    readonly_fields = ('fecha_creacion',)

@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'creado', 'is_active')
    list_filter = ('is_active', 'creado')
    search_fields = ('user__username',)

class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'trabajador')
    list_editable = ('trabajador',)
    search_fields = ('user__username', 'user__email')

admin.site.register(PerfilUsuario, PerfilUsuarioAdmin)

class PerfilInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False 
    verbose_name_plural = 'Perfil' 


class CustomUserAdmin(UserAdmin):
    inlines = (PerfilInline,) 


admin.site.unregister(User)

admin.site.register(User, CustomUserAdmin)

# Configuración para PedidoItem como inline de Pedido
class PedidoItemInline(admin.TabularInline):
    model = PedidoItem
    extra = 0
    readonly_fields = ('producto', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal')

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'email', 'monto', 'estado', 'fecha', 'retiro_en_tienda', 'envio_domicilio')
    list_filter = ('estado', 'retiro_en_tienda', 'envio_domicilio', 'fecha')
    search_fields = ('order_id', 'email')
    readonly_fields = ('order_id', 'fecha')
    inlines = [PedidoItemInline]

@admin.register(PedidoItem)
class PedidoItemAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'nombre_producto', 'cantidad', 'precio_unitario', 'subtotal')
    search_fields = ('pedido__order_id', 'nombre_producto')
    list_filter = ('pedido__fecha',)