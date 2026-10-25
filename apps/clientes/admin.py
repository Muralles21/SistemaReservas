from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'dpi', 'telefono', 'correo', 'activo')
    search_fields = ('nombres', 'apellidos', 'dpi', 'correo')
