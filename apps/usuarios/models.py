from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils import timezone

from apps.core.models import ModeloBase


class Rol(ModeloBase):
    """
    Rol del sistema (Administrador, Recepción, Cajero, etc.). Los permisos
    especificos se apoyan en el sistema de permisos nativo de Django
    (django.contrib.auth.Permission) para no reinventar la administracion
    de permisos granulares.
    """
    CLAVE_ADMINISTRADOR = 'ADMINISTRADOR'
    CLAVE_RECEPCION = 'RECEPCION'
    CLAVE_CAJERO = 'CAJERO'
    CLAVE_CLIENTE = 'CLIENTE'
    OPCIONES_CLAVE = [
        (CLAVE_ADMINISTRADOR, 'Administrador'),
        (CLAVE_RECEPCION, 'Recepción'),
        (CLAVE_CAJERO, 'Cajero'),
        (CLAVE_CLIENTE, 'Cliente (portal de autoservicio)'),
    ]

    nombre = models.CharField(max_length=50, unique=True)
    clave = models.CharField(max_length=20, choices=OPCIONES_CLAVE, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)
    permisos = models.ManyToManyField(Permission, blank=True, related_name='roles')

    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    """
    Usuario del sistema (personal administrativo/operativo). Extiende
    AbstractUser para reutilizar autenticacion, hashing de contraseñas y
    permisos nativos de Django (evita reinventar seguridad ya resuelta).
    """
    rol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name='usuarios',
                             null=True, blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to='usuarios/', blank=True, null=True)

    intentos_fallidos = models.PositiveSmallIntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['first_name', 'last_name']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def esta_bloqueado(self):
        return bool(self.bloqueado_hasta and self.bloqueado_hasta > timezone.now())

    def registrar_intento_fallido(self, max_intentos, minutos_bloqueo):
        from datetime import timedelta
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= max_intentos:
            self.bloqueado_hasta = timezone.now() + timedelta(minutes=minutos_bloqueo)
        self.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])

    def reiniciar_intentos(self):
        if self.intentos_fallidos or self.bloqueado_hasta:
            self.intentos_fallidos = 0
            self.bloqueado_hasta = None
            self.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
