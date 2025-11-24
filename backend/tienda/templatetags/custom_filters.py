from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def formato_clp(value):
    """
    Formatea números como moneda chilena con separadores de miles
    Ejemplo: 25000 -> $25.000
    """
    try:
        # Convertir a entero y formatear con separadores de miles
        value = int(float(value))
        formatted = f"{value:,}".replace(",", ".")
        return mark_safe(f"${formatted}")
    except (ValueError, TypeError):
        return value
