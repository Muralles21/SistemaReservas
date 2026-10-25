from django.db import models

from apps.clientes.models import Cliente
from apps.core.models import ModeloBase


class ConfiguracionFidelizacion(models.Model):
    """
    Configuracion unica (singleton) del programa de puntos, administrable
    desde el modulo de Configuracion sin tocar codigo.
    """
    puntos_por_reservacion = models.PositiveIntegerField(default=10)
    monto_por_punto_extra = models.DecimalField(
        max_digits=10, decimal_places=2, default=100,
        help_text='Por cada este monto gastado se otorga 1 punto adicional')
    dias_expiracion_puntos = models.PositiveIntegerField(
        default=0, help_text='0 = los puntos no expiran')

    class Meta:
        verbose_name = 'Configuración de fidelización'
        verbose_name_plural = 'Configuración de fidelización'

    def __str__(self):
        return 'Configuración del programa de fidelización'

    @classmethod
    def obtener(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class Premio(ModeloBase):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    costo_puntos = models.PositiveIntegerField()
    stock = models.PositiveIntegerField(default=0)
    foto = models.ImageField(upload_to='premios/', blank=True, null=True)

    class Meta:
        verbose_name = 'Premio'
        verbose_name_plural = 'Catálogo de premios'
        ordering = ['costo_puntos']

    def __str__(self):
        return self.nombre


class MovimientoPuntos(models.Model):
    TIPO_ACUMULACION = 'ACUMULACION'
    TIPO_CANJE = 'CANJE'
    TIPO_EXPIRACION = 'EXPIRACION'
    OPCIONES_TIPO = [
        (TIPO_ACUMULACION, 'Acumulación'),
        (TIPO_CANJE, 'Canje'),
        (TIPO_EXPIRACION, 'Expiración'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='movimientos_puntos')
    tipo = models.CharField(max_length=15, choices=OPCIONES_TIPO)
    puntos = models.IntegerField(help_text='Positivo en acumulación, negativo en canje/expiración')
    reservacion = models.ForeignKey(
        'reservaciones.Reservacion', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='movimientos_puntos')
    descripcion = models.CharField(max_length=255, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de puntos'
        verbose_name_plural = 'Historial de movimientos de puntos'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.cliente} - {self.tipo} ({self.puntos})'


class Canje(models.Model):
    ESTADO_ENTREGADO = 'ENTREGADO'
    ESTADO_PENDIENTE = 'PENDIENTE'
    OPCIONES_ESTADO = [
        (ESTADO_PENDIENTE, 'Pendiente de entrega'),
        (ESTADO_ENTREGADO, 'Entregado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='canjes')
    premio = models.ForeignKey(Premio, on_delete=models.PROTECT, related_name='canjes')
    puntos_utilizados = models.PositiveIntegerField()
    estado = models.CharField(max_length=15, choices=OPCIONES_ESTADO, default=ESTADO_PENDIENTE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Canje'
        verbose_name_plural = 'Canjes'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.cliente} canjeó {self.premio}'
