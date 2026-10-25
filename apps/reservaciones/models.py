from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction

from apps.clientes.models import Cliente
from apps.core.models import ModeloBase
from apps.espacios.models import Espacio


class Reservacion(ModeloBase):
    ESTADO_PENDIENTE = 'PENDIENTE'
    ESTADO_CONFIRMADA = 'CONFIRMADA'
    ESTADO_CANCELADA = 'CANCELADA'
    ESTADO_FINALIZADA = 'FINALIZADA'
    OPCIONES_ESTADO = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_CONFIRMADA, 'Confirmada'),
        (ESTADO_CANCELADA, 'Cancelada'),
        (ESTADO_FINALIZADA, 'Finalizada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='reservaciones')
    espacio = models.ForeignKey(Espacio, on_delete=models.PROTECT, related_name='reservaciones')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    estado = models.CharField(max_length=15, choices=OPCIONES_ESTADO, default=ESTADO_PENDIENTE)
    observaciones = models.TextField(blank=True)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='reservaciones_registradas')
    puntos_acreditados = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Reservación'
        verbose_name_plural = 'Reservaciones'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f'{self.espacio} - {self.cliente} ({self.fecha_inicio:%d/%m/%Y %H:%M})'

    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio >= self.fecha_fin:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        if self.espacio_id and self.fecha_inicio and self.fecha_fin:
            if not self.espacio.disponible_en(self.fecha_inicio, self.fecha_fin, excluir_reservacion_id=self.pk):
                raise ValidationError(
                    'El espacio ya se encuentra reservado en el horario seleccionado.'
                )

    ESTADOS_ACTIVOS = ('PENDIENTE', 'CONFIRMADA')
    CAMPOS_QUE_OCUPAN_HORARIO = {'espacio', 'espacio_id', 'fecha_inicio', 'fecha_fin', 'estado'}

    def save(self, *args, **kwargs):
        """
        Guarda la reservacion garantizando que no se duplique el horario,
        incluso si dos personas reservan el mismo espacio al mismo tiempo.

        Dentro de una transaccion se bloquea la fila del espacio
        (SELECT ... FOR UPDATE) antes de verificar la disponibilidad: la
        segunda solicitud simultanea espera a que termine la primera y, al
        verificar, ya encuentra el horario ocupado y es rechazada. Solo se
        bloquea cuando el cambio puede ocupar horario (alta, cambio de
        fechas/espacio o reactivacion), para no frenar cambios simples.
        """
        campos = kwargs.get('update_fields')
        ocupa_horario = (
            self.estado in self.ESTADOS_ACTIVOS and self.espacio_id
            and (campos is None or self.CAMPOS_QUE_OCUPAN_HORARIO & set(campos))
        )
        if not ocupa_horario:
            return super().save(*args, **kwargs)
        with transaction.atomic():
            Espacio.objects.select_for_update().filter(pk=self.espacio_id).first()
            self.clean()
            return super().save(*args, **kwargs)

    @property
    def saldo_pendiente(self):
        total_pagado = self.pagos.filter(estado='APROBADO').aggregate(
            total=models.Sum('monto'))['total'] or 0
        return self.precio_total - total_pagado


class HistorialReservacion(models.Model):
    """Bitacora especifica de cambios de estado de una reservacion."""
    reservacion = models.ForeignKey(Reservacion, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=15)
    estado_nuevo = models.CharField(max_length=15)
    comentario = models.CharField(max_length=255, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Historial de reservación'
        verbose_name_plural = 'Historial de reservaciones'

    def __str__(self):
        return f'{self.reservacion} : {self.estado_anterior} -> {self.estado_nuevo}'
