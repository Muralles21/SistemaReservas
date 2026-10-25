from django.contrib import admin
from .models import Reservacion, HistorialReservacion


class HistorialInline(admin.TabularInline):
    model = HistorialReservacion
    extra = 0
    readonly_fields = ('estado_anterior', 'estado_nuevo', 'comentario', 'usuario', 'fecha')


@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
    list_display = ('espacio', 'cliente', 'fecha_inicio', 'fecha_fin', 'estado', 'precio_total')
    list_filter = ('estado', 'espacio')
    inlines = [HistorialInline]
