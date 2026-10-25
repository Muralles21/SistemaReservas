from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from apps.core.models import Bitacora


@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):
    Bitacora.objects.create(
        usuario=user,
        accion=Bitacora.ACCION_LOGIN,
        modulo='Autenticación',
        descripcion=f'Inicio de sesión de {user.get_full_name() or user.username}',
        ip=getattr(request, 'ip_cliente', None),
    )


@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):
    if user is None:
        return
    Bitacora.objects.create(
        usuario=user,
        accion=Bitacora.ACCION_LOGOUT,
        modulo='Autenticación',
        descripcion=f'Cierre de sesión de {user.get_full_name() or user.username}',
        ip=getattr(request, 'ip_cliente', None),
    )
