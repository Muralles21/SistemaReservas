from django.contrib import admin
from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('reservacion', 'tipo', 'monto', 'metodo_pago', 'estado', 'fecha')
    list_filter = ('tipo', 'metodo_pago', 'estado')
