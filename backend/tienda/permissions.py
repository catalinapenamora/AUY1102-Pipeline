from .models import PerfilUsuario
from rest_framework import permissions

class EsTrabajador(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        try:
            return request.user.perfilusuario.trabajador
        except PerfilUsuario.DoesNotExist:
            return False