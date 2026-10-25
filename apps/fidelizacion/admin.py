from django.contrib import admin
from .models import Premio, MovimientoPuntos, Canje, ConfiguracionFidelizacion


@admin.register(Premio)
class PremioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'costo_puntos', 'stock', 'activo')


@admin.register(MovimientoPuntos)
class MovimientoPuntosAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'puntos', 'fecha')
    list_filter = ('tipo',)


@admin.register(Canje)
class CanjeAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'premio', 'puntos_utilizados', 'estado', 'fecha')


@admin.register(ConfiguracionFidelizacion)
class ConfiguracionFidelizacionAdmin(admin.ModelAdmin):
    list_display = ('puntos_por_reservacion', 'monto_por_punto_extra', 'dias_expiracion_puntos')
