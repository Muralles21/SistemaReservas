"""
Pasarela de pago con tarjeta (simulada, para demostracion).

El sistema NUNCA recibe ni guarda numeros de tarjeta: el cliente es llevado a
una pantalla de pago aparte y el sistema solo acepta un token firmado que
prueba la aprobacion; nunca confia en los parametros sueltos de la URL.

Para agregar otra pasarela basta con crear una clase con los metodos
`crear_cobro` y `verificar` y registrarla en `obtener_pasarela`.
"""
from django.conf import settings
from django.core import signing
from django.urls import reverse

PAGADO = 'pagado'
PENDIENTE = 'pendiente'
FALLIDO = 'fallido'


class ErrorPasarela(Exception):
    """La pasarela no pudo crear o consultar el cobro."""


class PasarelaSimulada:
    """
    Pasarela de demostracion para desarrollo y pruebas. Muestra una pantalla
    con botones "Pagar" / "Rechazar" (sin capturar datos de tarjeta) y emite
    un token firmado que prueba la aprobacion. NO cobra dinero real.
    """
    nombre = 'simulada'

    def crear_cobro(self, pago, url_exito, url_cancelar):
        import uuid
        id_cobro = f'sim_{uuid.uuid4().hex[:16]}'
        return {'id': id_cobro, 'url': settings.SITE_URL + reverse('pagos:simulada', args=[pago.pk])}

    @staticmethod
    def token_aprobacion(pago):
        return signing.dumps({'pago': pago.pk, 'cobro': pago.id_externo, 'ok': True}, salt='pago-simulado')

    def verificar(self, pago, parametros=None):
        token = (parametros or {}).get('sim')
        if not token:
            return PENDIENTE
        try:
            datos = signing.loads(token, salt='pago-simulado', max_age=3600)
        except signing.BadSignature:
            return FALLIDO
        if datos.get('pago') == pago.pk and datos.get('cobro') == pago.id_externo and datos.get('ok'):
            return PAGADO
        return FALLIDO


def obtener_pasarela(nombre=None):
    nombre = nombre or settings.PASARELA_PAGO
    if nombre == 'simulada':
        return PasarelaSimulada()
    raise ErrorPasarela(f'Pasarela de pago desconocida: {nombre}')
