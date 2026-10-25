"""
Reglas de negocio del programa de fidelizacion: acumulacion automatica y
canje de puntos, aisladas del resto del sistema para evitar dependencias
circulares y facilitar su prueba unitaria.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import ConfiguracionFidelizacion, MovimientoPuntos, Canje, Premio


def acreditar_puntos_por_reservacion(reservacion):
    """
    Acumulacion automatica: se ejecuta cuando una reservacion se marca
    como finalizada (ver apps.reservaciones.services.finalizar_reservacion).
    """
    config = ConfiguracionFidelizacion.obtener()
    puntos = config.puntos_por_reservacion
    if config.monto_por_punto_extra:
        puntos += int(reservacion.precio_total // config.monto_por_punto_extra)

    return MovimientoPuntos.objects.create(
        cliente=reservacion.cliente,
        tipo=MovimientoPuntos.TIPO_ACUMULACION,
        puntos=puntos,
        reservacion=reservacion,
        descripcion=f'Puntos por reservación #{reservacion.pk} en {reservacion.espacio}',
    )


@transaction.atomic
def canjear_premio(cliente, premio_id, usuario=None):
    premio = Premio.objects.select_for_update().get(pk=premio_id, activo=True)

    if premio.stock <= 0:
        raise ValidationError('El premio seleccionado no tiene existencias disponibles.')
    if cliente.puntos_disponibles < premio.costo_puntos:
        raise ValidationError('El cliente no cuenta con puntos suficientes para este canje.')

    premio.stock -= 1
    premio.save(update_fields=['stock'])

    canje = Canje.objects.create(
        cliente=cliente, premio=premio, puntos_utilizados=premio.costo_puntos
    )
    MovimientoPuntos.objects.create(
        cliente=cliente,
        tipo=MovimientoPuntos.TIPO_CANJE,
        puntos=-premio.costo_puntos,
        descripcion=f'Canje de premio: {premio.nombre}',
    )
    return canje
