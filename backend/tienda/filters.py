import django_filters
from .models import Producto

class ProductoFiltro(django_filters.FilterSet):
    marca = django_filters.CharFilter(field_name='marca__nombre', lookup_expr='icontains')
    categoria = django_filters.CharFilter(field_name='categoria__nombre', lookup_expr='icontains')
    nombre = django_filters.CharFilter(field_name='nombre', lookup_expr='icontains')

    class Meta:
        model = Producto
        fields = ['marca', 'categoria', 'nombre']

