from django.urls import path, re_path
from . import views
from .views import ProductoAPIView, HomeView, LoginView, ProductoMayoristaAPIView, cerrar_sesion, login_page, catalogo_view, RegistroView, registro_page, PerfilUsuarioView, perfil_page, detalle_producto, CarritoView, AgregarCarritoView, RemoverDelCarritoView, carrito_page, CarritoContadorView, TrabajadoresAdminView, gestion_page, TrabajadorUpdateView, ProductoDetalleAPIView, gestion_prod_page, CategoriaDetalleAPIView, CategoriasCrudView, gestion_cat_page, obtener_regiones_chilexpress, obtener_comunas_chilexpress, calcular_envio_chilexpress
from tienda.views import TokenDesdeSesionView
# Importar API externa
from . import external_api

urlpatterns=[
    path('', HomeView.as_view(), name='home'),
    path('api/productos/', ProductoAPIView.as_view(), name='lista-productos-api'),
    path('api/login/', LoginView.as_view(), name='api-login' ),
    path('login/', login_page, name='login'),
    path('catalogo/', catalogo_view, name='catalogo'),
    path('registro/', registro_page, name='registro'),
    path('api/registro/', RegistroView.as_view(), name='api-registro'),
    path('api/perfil/', PerfilUsuarioView.as_view(), name='api-perfil'),
    path('perfil', perfil_page, name='perfil'),
    path('producto/<int:producto_id>', detalle_producto, name='detalle_producto'),
    path('api/carrito/', CarritoView.as_view(), name='api-carrito'),
    path('carrito/agregar/', AgregarCarritoView.as_view(), name='agregar-carrito'),
    path('carrito/remover/<int:producto_id>/', RemoverDelCarritoView.as_view(), name='remover-carrito'),
    path('carrito/', carrito_page, name='carrito'),
    path('carrito/contador/', CarritoContadorView.as_view(), name='contador-carrito'),
    path('api/admin/trabajadores/', TrabajadoresAdminView.as_view(), name='admin-trabajadores'),
    path('gestion_trabajadores', gestion_page, name='gestion_trabajadores'),
    path('api/admin/trabajadores/<int:user_id>/', TrabajadorUpdateView.as_view(), name='trabajador-update'),
    path('api/productos/<int:pk>/', ProductoDetalleAPIView.as_view(), name='producto-detalle'),
    path('gestion_productos', gestion_prod_page, name='gestion_productos'),
    path("api/login/from-session/", TokenDesdeSesionView.as_view(), name="token_desde_sesion"),
    path("login/form/", views.login_con_sesion, name="login-con-sesion"),
    path('logout/', cerrar_sesion, name='logout'),
    path('api/carrito/aumentar/<int:producto_id>/', views.aumentar_producto, name='carrito-aumentar'),
    path('api/carrito/disminuir/<int:producto_id>/', views.disminuir_producto, name='carrito-disminuir'),
    path('api/carrito/remover/<int:producto_id>/', views.remover_producto, name='carrito-remover'),
    path('api/carrito/limpiar/', views.limpiar_carrito, name='carrito-limpiar'),
    path('pago_exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path("crear_pedido/", views.crear_pedido, name="crear_pedido"),
    path("pagar/<str:order_id>/", views.pagar_view, name="pagar_transbank"),
    path('api/productos/mayorista/', ProductoMayoristaAPIView.as_view(), name='api_productos_mayorista'),
    path('productos/mayorista/', views.productos_mayoristas_page, name='productos_mayorista_page'),
    path('api/categorias/', CategoriasCrudView.as_view(), name='lista_categorias'),
    path('api/categorias/<int:pk>/', CategoriaDetalleAPIView.as_view(), name='detalle_categoria'),
    path('gestion_categorias', gestion_cat_page, name='gestion_categorias'),
    # APIs de Chilexpress
    path('api/chilexpress/regiones/', obtener_regiones_chilexpress, name='chilexpress-regiones'),
    path('api/chilexpress/comunas/<str:region_id>/', obtener_comunas_chilexpress, name='chilexpress-comunas'),
    path('api/chilexpress/calcular-envio/', calcular_envio_chilexpress, name='chilexpress-calcular'),
    
    # APIs para compatibilidad de vehículos
    path('api/marcas-vehiculos/', views.MarcasVehiculosAPIView.as_view(), name='marcas-vehiculos-api'),
    path('api/modelos-vehiculos/', views.ModelosVehiculosAPIView.as_view(), name='modelos-vehiculos-api'),
    
    # Pagos por Transferencia
    path('pago-transferencia/<str:order_id>/', views.pago_transferencia, name='pago-transferencia'),
    path('api/crear-pedido-transferencia/', views.crear_pedido_transferencia, name='crear-pedido-transferencia'),
    
    # APIs de Pedidos y Historial
    path('api/historial-pedidos/', views.historial_pedidos, name='historial-pedidos'),
    path('api/pedido/<str:order_id>/', views.detalle_pedido, name='detalle-pedido'),
    path('api/detalle-pedido/<str:order_id>/', views.detalle_pedido, name='detalle-pedido-alt'),
    
    # Dashboard de Gestión de Pedidos
    path('dashboard-pedidos/', views.dashboard_pedidos_page, name='dashboard-pedidos'),
    path('api/dashboard/pedidos/', views.lista_pedidos_dashboard, name='api-dashboard-pedidos'),
    path('api/dashboard/pedidos/<str:order_id>/', views.detalle_pedido_dashboard, name='api-dashboard-detalle-pedido'),
    path('api/dashboard/pedidos/<str:order_id>/estado/', views.actualizar_estado_pedido, name='api-actualizar-estado-pedido'),
    
    # Manejo de Pagos Rechazados
    path('pago-rechazado/<str:order_id>/', views.pago_rechazado_page, name='pago-rechazado'),

    
    # ================================
    # API EXTERNA para sistemas externos (Taller de Manolo, etc.)
    # ================================
    path('api/external/info/', external_api.external_api_info, name='external-api-info'),
    path('api/external/catalog/', external_api.external_catalog_list, name='external-catalog-list'),
    path('api/external/catalog/<int:product_id>/', external_api.external_product_detail, name='external-product-detail'),
    path('api/external/categories/', external_api.external_categories_list, name='external-categories-list'),
    path('api/external/search/', external_api.external_search, name='external-search'),
    
    # Documentación de la API Externa
    path('api-externa/', views.api_externa_page, name='api-externa'),
    
    # Vista simulada del Taller de Manolo (demo de integración)
    path('taller-manolo/', views.taller_manolo_page, name='taller-manolo'),
]

urlpatterns += [
    re_path(r'^.*/$', views.error_404_view),
]