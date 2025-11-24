"""
Context processors para AutoParts
=================================

Agregan información adicional a todos los templates
"""

def user_permissions(request):
    """
    Agrega información de permisos del usuario a todos los templates
    """
    context = {
        'is_trabajador': False,
        'is_empresa': False,
        'user_rut': None
    }
    
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfilusuario
            context.update({
                'is_trabajador': perfil.trabajador,
                'is_empresa': perfil.empresa,
                'user_rut': perfil.rut
            })
        except:
            # Si no tiene perfil, valores por defecto
            pass
    
    return context
