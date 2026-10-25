"""
Notificaciones por correo del sistema.

Todas las funciones son "a prueba de fallos": si el servidor de correo no
responde, se registra el error en el log pero NO se interrumpe la operacion
del usuario (una reservacion no debe perderse porque fallo un correo).
Los envios se programan con transaction.on_commit para no avisar de algo que
luego se revierta por un error en la base de datos.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _enviar_ahora(asunto, plantilla, contexto, destinatarios):
    destinatarios = [d for d in dict.fromkeys(destinatarios) if d]
    if not destinatarios:
        return False
    contexto = {'NOMBRE_SISTEMA': getattr(settings, 'NOMBRE_SISTEMA', 'EventSpace'),
                'SITE_URL': settings.SITE_URL, **contexto}
    try:
        html = render_to_string(f'correos/{plantilla}.html', contexto)
        texto = strip_tags(html.split('</style>')[-1]).strip()
        mensaje = EmailMultiAlternatives(asunto, texto, settings.DEFAULT_FROM_EMAIL, destinatarios)
        mensaje.attach_alternative(html, 'text/html')
        mensaje.send(fail_silently=False)
        return True
    except Exception:  # noqa: BLE001 - un fallo de correo nunca debe romper el flujo
        logger.exception('No se pudo enviar el correo "%s" a %s', asunto, destinatarios)
        return False


def enviar(asunto, plantilla, contexto, destinatarios):
    """Programa el envio al confirmarse la transaccion actual (si hay una)."""
    transaction.on_commit(lambda: _enviar_ahora(asunto, plantilla, contexto, list(destinatarios)))


def _correo_cliente(cliente):
    if cliente.usuario_id and cliente.usuario.email:
        return cliente.usuario.email
    return cliente.correo


def _correos_personal():
    if not getattr(settings, 'NOTIFICAR_PERSONAL', True):
        return []
    from apps.usuarios.models import Usuario
    return list(Usuario.objects.filter(
        is_active=True, rol__clave__in=['ADMINISTRADOR', 'RECEPCION']
    ).exclude(email='').values_list('email', flat=True))


# ---- Cuenta -----------------------------------------------------------

def bienvenida_cliente(usuario, cliente):
    enviar(f'¡Tu cuenta fue creada! · {getattr(settings, "NOMBRE_SISTEMA", "EventSpace")}',
           'bienvenida', {'cliente': cliente, 'usuario': usuario}, [usuario.email or cliente.correo])


# ---- Reservaciones ----------------------------------------------------

def reservacion_creada(reservacion, avisar_personal=True):
    """Aviso al cliente de que su solicitud fue recibida y, opcionalmente, al personal."""
    enviar(f'Recibimos tu solicitud de reservación #{reservacion.pk}',
           'reservacion_creada', {'r': reservacion, 'cliente': reservacion.cliente},
           [_correo_cliente(reservacion.cliente)])
    if avisar_personal:
        aviso_personal(reservacion)


def aviso_personal(reservacion, pago=None):
    """Aviso interno (Administrador y Recepción) de una nueva reservación hecha por un cliente."""
    enviar(f'Nueva reservación #{reservacion.pk} · {reservacion.espacio.nombre}',
           'aviso_personal', {'r': reservacion, 'cliente': reservacion.cliente, 'pago': pago},
           _correos_personal())


def reservacion_confirmada(reservacion, pago=None):
    enviar(f'Tu reservación #{reservacion.pk} está confirmada',
           'reservacion_confirmada', {'r': reservacion, 'cliente': reservacion.cliente, 'pago': pago},
           [_correo_cliente(reservacion.cliente)])


def reservacion_cancelada(reservacion, motivo='', por_cliente=False):
    ctx = {'r': reservacion, 'cliente': reservacion.cliente, 'motivo': motivo, 'por_cliente': por_cliente}
    enviar(f'Reservación #{reservacion.pk} cancelada', 'reservacion_cancelada', ctx,
           [_correo_cliente(reservacion.cliente)])
    if por_cliente:
        enviar(f'El cliente canceló la reservación #{reservacion.pk}', 'aviso_cancelacion', ctx,
               _correos_personal())


def reservacion_reprogramada(reservacion):
    enviar(f'Tu reservación #{reservacion.pk} fue reprogramada',
           'reservacion_reprogramada', {'r': reservacion, 'cliente': reservacion.cliente},
           [_correo_cliente(reservacion.cliente)])


# ---- Pagos ------------------------------------------------------------

def pago_rechazado(reservacion, pago, motivo=''):
    enviar(f'No pudimos procesar tu pago · reservación #{reservacion.pk}',
           'pago_rechazado', {'r': reservacion, 'cliente': reservacion.cliente, 'pago': pago,
                              'motivo': motivo},
           [_correo_cliente(reservacion.cliente)])
