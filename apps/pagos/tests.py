import json
from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.core.tests_utils import crear_cliente, crear_espacio, crear_personal, horario
from apps.pagos import pasarelas, services
from apps.pagos.models import Pago
from apps.pagos.pasarelas import ErrorPasarela
from apps.reservaciones.models import Reservacion

CORREO = dict(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', SITE_URL='http://testserver')


def _solicitar(client, espacio, metodo='TARJETA'):
    inicio, fin = horario()
    return client.post(reverse('reservaciones:solicitar'), {
        'espacio': espacio.pk, 'metodo_pago': metodo, 'observaciones': '',
        'fecha_inicio': inicio.strftime('%Y-%m-%dT%H:%M'), 'fecha_fin': fin.strftime('%Y-%m-%dT%H:%M')})


@override_settings(PASARELA_PAGO='simulada', **CORREO)
class PagoTarjetaSimuladoTests(TestCase):
    def setUp(self):
        self.cliente = crear_cliente()
        self.espacio = crear_espacio(precio='450.00')
        crear_personal('ADMINISTRADOR', 'admin@ejemplo.com')
        self.client.force_login(self.cliente.usuario)

    def _iniciar(self):
        r = _solicitar(self.client, self.espacio)
        pago = Pago.objects.get()
        return r, pago

    def test_tarjeta_crea_reserva_pendiente_y_pago_pendiente(self):
        r, pago = self._iniciar()
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r['Location'].endswith(reverse('pagos:simulada', args=[pago.pk])))
        self.assertEqual(pago.estado, 'PENDIENTE')
        self.assertEqual(pago.monto, 450)
        self.assertEqual(pago.reservacion.estado, 'PENDIENTE')
        self.assertTrue(pago.id_externo.startswith('sim_'))
        self.assertEqual(len(mail.outbox), 0)  # aun no se avisa: falta el pago

    def test_el_horario_queda_apartado_mientras_se_paga(self):
        self._iniciar()
        r = _solicitar(self.client, self.espacio)  # segundo intento al mismo horario
        self.assertContains(r, 'ya se encuentra reservado')

    def test_pago_aprobado_confirma_y_notifica(self):
        _, pago = self._iniciar()
        token = pasarelas.PasarelaSimulada.token_aprobacion(pago)
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.get(reverse('pagos:retorno', args=[pago.pk]) + f'?sim={token}')
        self.assertRedirects(r, reverse('clientes:mi_cuenta'), fetch_redirect_response=False)
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'APROBADO')
        self.assertEqual(pago.reservacion.estado, 'CONFIRMADA')
        self.assertEqual(pago.reservacion.saldo_pendiente, 0)
        asuntos = [m.subject for m in mail.outbox]
        self.assertTrue(any('confirmada' in a for a in asuntos), asuntos)   # cliente
        self.assertTrue(any('Nueva reservación' in a for a in asuntos), asuntos)  # personal

    def test_retorno_es_idempotente(self):
        _, pago = self._iniciar()
        token = pasarelas.PasarelaSimulada.token_aprobacion(pago)
        url = reverse('pagos:retorno', args=[pago.pk]) + f'?sim={token}'
        with self.captureOnCommitCallbacks(execute=True):
            self.client.get(url)
            self.client.get(url)
        self.assertEqual(Pago.objects.filter(estado='APROBADO').count(), 1)
        self.assertEqual(len([m for m in mail.outbox if 'confirmada' in m.subject]), 1)

    def test_token_falso_no_aprueba(self):
        _, pago = self._iniciar()
        r = self.client.get(reverse('pagos:retorno', args=[pago.pk]) + '?sim=falso')
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'RECHAZADO')
        self.assertEqual(pago.reservacion.estado, 'CANCELADA')

    def test_sin_token_queda_procesando(self):
        _, pago = self._iniciar()
        r = self.client.get(reverse('pagos:retorno', args=[pago.pk]))
        self.assertContains(r, 'verificando tu pago')
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'PENDIENTE')

    def test_cancelar_en_la_pasarela_libera_el_horario(self):
        _, pago = self._iniciar()
        self.client.get(reverse('pagos:cancelado', args=[pago.pk]))
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'RECHAZADO')
        self.assertEqual(pago.reservacion.estado, 'CANCELADA')
        r = _solicitar(self.client, self.espacio)  # el horario vuelve a estar libre
        self.assertEqual(r.status_code, 302)

    def test_otro_cliente_no_puede_ver_ni_conciliar_el_pago(self):
        _, pago = self._iniciar()
        self.client.force_login(crear_cliente().usuario)
        self.assertEqual(self.client.get(reverse('pagos:retorno', args=[pago.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse('pagos:simulada', args=[pago.pk])).status_code, 404)

    def test_pagos_vencidos_se_liberan_con_el_comando(self):
        _, pago = self._iniciar()
        Pago.objects.filter(pk=pago.pk).update(fecha=timezone.now() - timedelta(minutes=90))
        self.assertEqual(services.expirar_pagos_pendientes(), 1)
        pago.refresh_from_db()
        self.assertEqual((pago.estado, pago.reservacion.estado), ('RECHAZADO', 'CANCELADA'))

    def test_pagos_recientes_no_se_tocan(self):
        self._iniciar()
        self.assertEqual(services.expirar_pagos_pendientes(), 0)

    def test_abrir_reservar_libera_pagos_abandonados(self):
        _, pago = self._iniciar()
        Pago.objects.filter(pk=pago.pk).update(fecha=timezone.now() - timedelta(minutes=90))
        self.assertEqual(self.client.get(reverse('reservaciones:solicitar')).status_code, 200)
        pago.refresh_from_db()
        self.assertEqual((pago.estado, pago.reservacion.estado), ('RECHAZADO', 'CANCELADA'))
