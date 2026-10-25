from django.contrib import admin
from .models import Espacio, EspacioFoto


class EspacioFotoInline(admin.TabularInline):
    model = EspacioFoto
    extra = 1


@admin.register(Espacio)
class EspacioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'capacidad', 'precio_por_evento', 'estado')
    list_filter = ('tipo', 'estado')
    inlines = [EspacioFotoInline]
