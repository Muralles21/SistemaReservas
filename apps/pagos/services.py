"""
Flujo del pago con tarjeta al reservar:

  1. iniciar_pago_tarjeta: la reservacion queda PENDIENTE (reteniendo el
     horario), se crea un Pago PENDIENTE y se obtiene la URL de pago de la
     pasarela.
  2. El cliente paga en la pagina de la pasarela y regresa al sistema.
  3. conciliar_pago: se consulta a la pasarela desde el servidor; si el cobro
     esta aprobado, el Pago pasa a APROBADO y la reservacion se CONFIRMA.
     Si fallo o expiro, el Pago queda RECHAZADO y la reservacion se cancela
     para liberar el horario.

`conciliar_pago` es idempotente: puede invocarse desde el retorno del
cliente o desde el comando de limpieza sin duplicar nada.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from apps.core import notificaciones
from apps.pagos.models import Pago
from apps.pagos.pasarelas import ErrorPasarela, FALLIDO, PAGADO, obtener_pasarela
from apps.reservaciones import services as reservaciones_services
from apps.reservaciones.models import Reservacion

logger = logging.getLogger(__name__)


def iniciar_pago_tarjeta(reservacion, usuario):
    """Crea el cobro en la pasarela y devuelve (pago, url_de_pago)."""
    pasarela = obtener_pasarela()
    pago = Pago.objects.create(
        reservacion=reservacion, tipo=Pago.TIPO_FINAL, monto=reservacion.precio_total,
        metodo_pago=Pago.METODO_TARJETA, estado=Pago.ESTADO_PENDIENTE,
        proveedor=pasarela.nombre, referencia='Pago con tarjeta en línea (pendiente)',
        usuario_registro=usuario,
    )
    exito = settings.SITE_URL + reverse('pagos:retorno', args=[pago.pk])
    cancelar = settings.SITE_URL + reverse('pagos:cancelado', args=[pago.pk])
    try:
        cobro = pasarela.crear_cobro(pago, exito, cancelar)
    except ErrorPasarela:
        pago.estado = Pago.ESTADO_RECHAZADO
        pago.referencia = 'No se pudo iniciar el cobro en la pasarela'
        pago.save(update_fields=['estado', 'referencia'])
        raise
    pago.id_externo = cobro['id']
    pago.save(update_fields=['id_externo'])
    return pago, cobro['url']


def _rechazar(pago, motivo):
    """Marca el pago como rechazado y libera el horario. Debe correr dentro de atomic."""
    pago.estado = Pago.ESTADO_RECHAZADO
    pago.referencia = motivo[:100]
    pago.save(update_fields=['estado', 'referencia'])
    reservacion = pago.reservacion
    sin_otro_pago = not reservacion.pagos.filter(estado=Pago.ESTADO_APROBADO).exists()
    if reservacion.estado == Reservacion.ESTADO_PENDIENTE and sin_otro_pago:
        reservaciones_services.cancelar_reservacion(
            reservacion, pago.usuario_registro, 'Pago con tarjeta no completado', notificar=False)
        notificaciones.pago_rechazado(reservacion, pago, motivo)


def conciliar_pago(pago_id, parametros=None, forzar_rechazo=False):
    """
    Consulta el estado real del cobro y actualiza pago y reservacion.
    Devuelve el estado final del Pago ('APROBADO', 'PENDIENTE' o 'RECHAZADO').
    `forzar_rechazo` se usa cuando el cliente cancela o vence el plazo: solo
    rechaza si, tras consultar, el cobro no esta pagado.
    """
    with transaction.atomic():
        pago = (Pago.objects.select_for_update().select_related('reservacion', 'reservacion__espacio',
                                                                'reservacion__cliente').get(pk=pago_id))
        if pago.estado != Pago.ESTADO_PENDIENTE:
            return pago.estado
        try:
            resultado = obtener_pasarela(pago.proveedor).verificar(pago, parametros)
        except ErrorPasarela:
            logger.exception('No se pudo verificar el pago %s', pago.pk)
            return pago.estado  # se reintentara; no se toma ninguna decision a ciegas

        if resultado == PAGADO:
            pago.estado = Pago.ESTADO_APROBADO
            pago.referencia = f'Pago en línea · {pago.proveedor} · {pago.id_externo}'[:100]
            pago.save(update_fields=['estado', 'referencia'])
            reservacion = pago.reservacion
            if reservacion.estado == Reservacion.ESTADO_PENDIENTE:
                reservaciones_services.confirmar_reservacion(
                    reservacion, pago.usuario_registro, notificar=False)
                notificaciones.reservacion_confirmada(reservacion, pago=pago)
                notificaciones.aviso_personal(reservacion, pago=pago)
            else:
                # El horario ya habia sido liberado (p. ej. vencio el plazo) pero el
                # cliente si pago: se deja constancia para que el personal devuelva el dinero.
                logger.warning('Pago %s aprobado con la reservacion %s en estado %s: requiere revision manual',
                               pago.pk, reservacion.pk, reservacion.estado)
        elif resultado == FALLIDO:
            _rechazar(pago, 'Cobro rechazado o expirado en la pasarela')
        elif forzar_rechazo:
            _rechazar(pago, 'Pago cancelado por el cliente o plazo vencido')
        return pago.estado


def expirar_pagos_pendientes():
    """Concilia los pagos con tarjeta que llevan mas del plazo sin resolverse."""
    limite = timezone.now() - timedelta(minutes=settings.PAGO_MINUTOS_RETENCION)
    ids = list(Pago.objects.filter(
        estado=Pago.ESTADO_PENDIENTE, metodo_pago=Pago.METODO_TARJETA, fecha__lt=limite
    ).values_list('pk', flat=True))
    for pk in ids:
        conciliar_pago(pk, forzar_rechazo=True)
    return len(ids)
