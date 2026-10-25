from django.db import models

from apps.core.models import ModeloBase


class Espacio(ModeloBase):
    TIPO_RECREATIVO = 'RECREATIVO'
    TIPO_SALON = 'SALON'
    OPCIONES_TIPO = [
        (TIPO_RECREATIVO, 'Cancha de fútbol'),
        (TIPO_SALON, 'Salón de eventos'),
    ]

    ESTADO_DISPONIBLE = 'DISPONIBLE'
    ESTADO_MANTENIMIENTO = 'MANTENIMIENTO'
    ESTADO_INACTIVO = 'INACTIVO'
    OPCIONES_ESTADO = [
        (ESTADO_DISPONIBLE, 'Disponible'),
        (ESTADO_MANTENIMIENTO, 'En mantenimiento'),
        (ESTADO_INACTIVO, 'Inactivo'),
    ]

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=15, choices=OPCIONES_TIPO)
    descripcion = models.TextField(blank=True)
    precio_por_evento = models.DecimalField(max_digits=10, decimal_places=2)
    capacidad = models.PositiveIntegerField(help_text='Número máximo de personas')
    estado = models.CharField(max_length=15, choices=OPCIONES_ESTADO, default=ESTADO_DISPONIBLE)
    foto_principal = models.ImageField(upload_to='espacios/', blank=True, null=True)

    class Meta:
        verbose_name = 'Espacio / salón'
        verbose_name_plural = 'Espacios y salones'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    def disponible_en(self, fecha_inicio, fecha_fin, excluir_reservacion_id=None):
        """
        Verifica disponibilidad real contra las reservaciones activas,
        evitando reservas duplicadas por solapamiento de horario.
        """
        if self.estado != self.ESTADO_DISPONIBLE:
            return False
        qs = self.reservaciones.filter(
            estado__in=['PENDIENTE', 'CONFIRMADA'],
            fecha_inicio__lt=fecha_fin,
            fecha_fin__gt=fecha_inicio,
        )
        if excluir_reservacion_id:
            qs = qs.exclude(pk=excluir_reservacion_id)
        return not qs.exists()


class EspacioFoto(models.Model):
    """Galería de fotografías adicionales de un espacio (uno a muchos)."""
    espacio = models.ForeignKey(Espacio, on_delete=models.CASCADE, related_name='fotos')
    imagen = models.ImageField(upload_to='espacios/galeria/')

    class Meta:
        verbose_name = 'Fotografía de espacio'
        verbose_name_plural = 'Fotografías de espacios'

    def __str__(self):
        return f'Foto de {self.espacio.nombre}'
