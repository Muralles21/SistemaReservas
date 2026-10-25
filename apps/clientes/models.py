from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from apps.core.models import ModeloBase

validador_dpi = RegexValidator(r'^\d{13}$', 'El DPI debe contener 13 dígitos numéricos.')
validador_telefono = RegexValidator(r'^\d{8}$', 'El teléfono debe contener 8 dígitos.')


class Cliente(ModeloBase):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='cliente',
        help_text='Cuenta de acceso al portal de autoservicio (si el cliente se registró en línea).'
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    dpi = models.CharField(max_length=13, unique=True, validators=[validador_dpi])
    telefono = models.CharField(max_length=8, validators=[validador_telefono])
    direccion = models.CharField(max_length=255)
    correo = models.EmailField(unique=True)
    foto = models.ImageField(upload_to='clientes/', blank=True, null=True)

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombres', 'apellidos']

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f'{self.nombres} {self.apellidos}'

    @property
    def puntos_disponibles(self):
        """Suma de movimientos de fidelizacion (acumulados - canjeados)."""
        agregados = self.movimientos_puntos.aggregate(total=models.Sum('puntos'))
        return agregados['total'] or 0
