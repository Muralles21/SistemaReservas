from django.conf import settings
from django.db import models


class ModeloBase(models.Model):
    """
    Modelo abstracto reutilizable (DRY): todo modelo del sistema hereda
    fecha de creacion, fecha de modificacion y borrado logico (soft delete),
    en lugar de repetir estos campos en cada entidad.
    """
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def eliminar_logico(self):
        self.activo = False
        self.save(update_fields=['activo'])


class Bitacora(models.Model):
    """
    Registro de auditoria: quien hizo que accion, cuando y sobre que modulo.
    """
    ACCION_CREAR = 'CREAR'
    ACCION_EDITAR = 'EDITAR'
    ACCION_ELIMINAR = 'ELIMINAR'
    ACCION_LOGIN = 'LOGIN'
    ACCION_LOGIN_FALLIDO = 'LOGIN_FALLIDO'
    ACCION_LOGOUT = 'LOGOUT'
    ACCIONES = [
        (ACCION_CREAR, 'Creación'),
        (ACCION_EDITAR, 'Edición'),
        (ACCION_ELIMINAR, 'Eliminación'),
        (ACCION_LOGIN, 'Inicio de sesión'),
        (ACCION_LOGIN_FALLIDO, 'Intento fallido de inicio de sesión'),
        (ACCION_LOGOUT, 'Cierre de sesión'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bitacoras'
    )
    accion = models.CharField(max_length=20, choices=ACCIONES)
    modulo = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de bitácora'
        verbose_name_plural = 'Bitácora del sistema'

    def __str__(self):
        return f'{self.fecha:%Y-%m-%d %H:%M} - {self.usuario} - {self.accion}'
