"""
Miniaturas de imagenes subidas por el usuario.

Las fotos de canchas y premios suelen subirse en su tamano original (varios
megabytes). Para que la landing y el catalogo carguen rapido, este tag genera
una copia reducida la primera vez que se pide y la reutiliza despues
(se guarda en MEDIA_ROOT/miniaturas/<ancho>/). Si algo falla, devuelve la
URL de la imagen original para no romper la pagina.

Uso en un template:
    {% load imagenes %}
    <img src="{% miniatura espacio.foto_principal 720 %}" alt="...">
"""
import io
import os

from django import template
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageOps

register = template.Library()


@register.simple_tag
def miniatura(campo, ancho=720):
    if not campo:
        return ''
    try:
        ancho = int(ancho)
        destino = f"miniaturas/{ancho}/{os.path.splitext(campo.name)[0]}.jpg"
        if not default_storage.exists(destino):
            with default_storage.open(campo.name) as archivo:
                imagen = ImageOps.exif_transpose(Image.open(archivo)).convert('RGB')
            imagen.thumbnail((ancho, ancho * 4), Image.LANCZOS)
            buffer = io.BytesIO()
            imagen.save(buffer, 'JPEG', quality=78, optimize=True, progressive=True)
            default_storage.save(destino, ContentFile(buffer.getvalue()))
        return default_storage.url(destino)
    except Exception:
        return campo.url
