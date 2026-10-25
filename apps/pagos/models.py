from django.conf import settings
from django.db import models

from apps.core.models import ModeloBase
from apps.reservaciones.models import Reservacion


class Pago(ModeloBase):
    TIPO_ANTICIPO = 'ANTICIPO'
    TIPO_PARCIAL = 'PARCIAL'
    TIPO_FINAL = 'FINAL'
    OPCIONES_TIPO = [
        (TIPO_ANTICIPO, 'Anticipo'),
        (TIPO_PARCIAL, 'Pago parcial'),
        (TIPO_FINAL, 'Pago final'),
    ]

    METODO_EFECTIVO = 'EFECTIVO'
    METODO_TARJETA = 'TARJETA'
    METODO_TRANSFERENCIA = 'TRANSFERENCIA'
    OPCIONES_METODO = [
        (METODO_EFECTIVO, 'Efectivo'),
        (METODO_TARJETA, 'Tarjeta'),
        (METODO_TRANSFERENCIA, 'Transferencia bancaria'),
    ]

    ESTADO_APROBADO = 'APROBADO'
    ESTADO_PENDIENTE = 'PENDIENTE'
    ESTADO_RECHAZADO = 'RECHAZADO'
    OPCIONES_ESTADO = [
        (ESTADO_APROBADO, 'Aprobado'),
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_RECHAZADO, 'Rechazado'),
    ]

    reservacion = models.ForeignKey(Reservacion, on_delete=models.PROTECT, related_name='pagos')
    tipo = models.CharField(max_length=10, choices=OPCIONES_TIPO)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(max_length=15, choices=OPCIONES_METODO)
    estado = models.CharField(max_length=10, choices=OPCIONES_ESTADO, default=ESTADO_APROBADO)
    referencia = models.CharField(max_length=100, blank=True, help_text='No. de recibo, voucher, etc.')
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    proveedor = models.CharField(
        max_length=20, blank=True, help_text='Pasarela que proceso el cobro (vacio = pago manual).')
    id_externo = models.CharField(
        max_length=100, blank=True, db_index=True, help_text='Identificador del cobro en la pasarela.')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.reservacion} - Q{self.monto} ({self.get_tipo_display()})'
