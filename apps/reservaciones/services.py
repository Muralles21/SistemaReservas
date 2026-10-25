"""
Capa de servicios del modulo de reservaciones: concentra las reglas de
negocio (cambios de estado, acreditacion de puntos) para que las vistas
permanezcan delgadas y no se duplique logica entre la version web y una
futura API (principio DRY / Single Responsibility).
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.core import notificaciones
from apps.fidelizacion.services import acreditar_puntos_por_reservacion
from .models import HistorialReservacion, Reservacion


def _registrar_cambio(reservacion, estado_anterior, estado_nuevo, usuario, comentario=''):
    HistorialReservacion.objects.create(
        reservacion=reservacion,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        comentario=comentario,
        usuario=usuario,
    )


@transaction.atomic
def confirmar_reservacion(reservacion, usuario, notificar=True, pago=None):
    if reservacion.estado != Reservacion.ESTADO_PENDIENTE:
        raise ValidationError('Solo una reservación pendiente puede confirmarse.')
    estado_anterior = reservacion.estado
    reservacion.estado = Reservacion.ESTADO_CONFIRMADA
    reservacion.save(update_fields=['estado'])
    _registrar_cambio(reservacion, estado_anterior, reservacion.estado, usuario)
    if notificar:
        notificaciones.reservacion_confirmada(reservacion, pago=pago)
    return reservacion


@transaction.atomic
def cancelar_reservacion(reservacion, usuario, motivo='', por_cliente=False, notificar=True):
    if reservacion.estado in (Reservacion.ESTADO_CANCELADA, Reservacion.ESTADO_FINALIZADA):
        raise ValidationError('La reservación ya no puede cancelarse.')
    estado_anterior = reservacion.estado
    reservacion.estado = Reservacion.ESTADO_CANCELADA
    reservacion.save(update_fields=['estado'])
    _registrar_cambio(reservacion, estado_anterior, reservacion.estado, usuario, motivo)
    if notificar:
        notificaciones.reservacion_cancelada(reservacion, motivo=motivo, por_cliente=por_cliente)
    return reservacion


@transaction.atomic
def reprogramar_reservacion(reservacion, nueva_fecha_inicio, nueva_fecha_fin, usuario):
    if reservacion.estado not in (Reservacion.ESTADO_PENDIENTE, Reservacion.ESTADO_CONFIRMADA):
        raise ValidationError('Solo reservaciones pendientes o confirmadas pueden reprogramarse.')
    if not reservacion.espacio.disponible_en(
        nueva_fecha_inicio, nueva_fecha_fin, excluir_reservacion_id=reservacion.pk
    ):
        raise ValidationError('El espacio no está disponible en el nuevo horario.')
    estado_anterior = reservacion.estado
    reservacion.fecha_inicio = nueva_fecha_inicio
    reservacion.fecha_fin = nueva_fecha_fin
    reservacion.full_clean()
    reservacion.save(update_fields=['fecha_inicio', 'fecha_fin'])
    _registrar_cambio(reservacion, estado_anterior, reservacion.estado, usuario,
                       'Reprogramación de fecha/hora')
    notificaciones.reservacion_reprogramada(reservacion)
    return reservacion


@transaction.atomic
def finalizar_reservacion(reservacion, usuario):
    """
    Marca la reservacion como finalizada y acredita automaticamente los
    puntos de fidelizacion (una sola vez por reservacion).
    """
    if reservacion.estado != Reservacion.ESTADO_CONFIRMADA:
        raise ValidationError('Solo una reservación confirmada puede finalizarse.')
    estado_anterior = reservacion.estado
    reservacion.estado = Reservacion.ESTADO_FINALIZADA
    reservacion.save(update_fields=['estado'])
    _registrar_cambio(reservacion, estado_anterior, reservacion.estado, usuario)

    if not reservacion.puntos_acreditados:
        acreditar_puntos_por_reservacion(reservacion)
        reservacion.puntos_acreditados = True
        reservacion.save(update_fields=['puntos_acreditados'])
    return reservacion
