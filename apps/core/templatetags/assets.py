import os
from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def static_v(ruta):
    """Como {% static %}, pero agrega ?v=<fecha de modificación> para que el
    navegador no use una copia vieja del CSS/JS tras actualizar el proyecto."""
    url = static(ruta)
    try:
        archivo = finders.find(ruta)
        if archivo:
            return f"{url}?v={int(os.path.getmtime(archivo))}"
    except Exception:
        pass
    return url
