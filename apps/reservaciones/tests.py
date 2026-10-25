import json
import threading
from unittest import mock

from django.core import mail
from django.core.exceptions import ValidationError
from django.db import connection, connections
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse

from apps.core.tests_utils import (crear_cliente, crear_espacio, crear_personal, crear_roles,
                                   horario)
from apps.pagos.models import Pago
from apps.reservaciones import services
from apps.reservaciones.models import Reservacion


def _crear(cliente, espacio, inicio, fin, usuario=None):
    r = Reservacion(cliente=cliente, espacio=espacio, fecha_inicio=inicio, fecha_fin=fin,
                    precio_total=espacio.precio_por_evento,
                    usuario_registro=usuario or cliente.usuario)
    r.full_clean()
    r.save()
    return r


def _datos_formulario(espacio, inicio, fin, metodo='EFECTIVO'):
    return {'espacio': espacio.pk, 'metodo_pago': metodo, 'observaciones': '',
            'fecha_inicio': inicio.strftime('%Y-%m-%dT%H:%M'),
            'fecha_fin': fin.strftime('%Y-%m-%dT%H:%M')}


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   PASARELA_PAGO='simulada', SITE_URL='http://testserver')
class SolicitudClienteTests(TestCase):
    def setUp(self):
        self.cliente = crear_cliente()
        self.espacio = crear_espacio()
        self.personal = crear_personal('RECEPCION', 'recepcion@ejemplo.com')
        self.client.force_login(self.cliente.usuario)

    def test_doble_reservacion_es_rechazada(self):
        inicio, fin = horario()
        _crear(self.cliente, self.espacio, inicio, fin)
        otro = crear_cliente()
        with self.assertRaises(ValidationError):
            _crear(otro, self.espacio, inicio, fin)
        # traslape parcial tambien
        with self.assertRaises(ValidationError):
            _crear(otro, self.espacio, inicio + (fin - inicio) / 2, fin + (fin - inicio))

    def test_cancelada_libera_el_horario(self):
        inicio, fin = horario()
        r = _crear(self.cliente, self.espacio, inicio, fin)
        services.cancelar_reservacion(r, self.cliente.usuario)
        _crear(crear_cliente(), self.espacio, inicio, fin)  # ya no debe fallar

    def test_efectivo_crea_pendiente_y_envia_correos(self):
        inicio, fin = horario()
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(reverse('reservaciones:solicitar'),
                                 _datos_formulario(self.espacio, inicio, fin, 'EFECTIVO'))
        self.assertRedirects(r, reverse('clientes:mi_cuenta'), fetch_redirect_response=False)
        reserva = Reservacion.objects.get()
        self.assertEqual(reserva.estado, 'PENDIENTE')
        destinos = sorted(c for m in mail.outbox for c in m.to)
        self.assertIn(self.cliente.usuario.email, destinos)       # aviso al cliente
        self.assertIn('recepcion@ejemplo.com', destinos)           # aviso al personal
        self.assertEqual(len(mail.outbox), 2)

    def test_fecha_pasada_es_rechazada(self):
        inicio, fin = horario(dias=-1)
        r = self.client.post(reverse('reservaciones:solicitar'), _datos_formulario(self.espacio, inicio, fin))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Reservacion.objects.count(), 0)

    def test_horario_ocupado_muestra_error_y_no_crea(self):
        inicio, fin = horario()
        _crear(crear_cliente(), self.espacio, inicio, fin)
        r = self.client.post(reverse('reservaciones:solicitar'), _datos_formulario(self.espacio, inicio, fin))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'ya se encuentra reservado')
        self.assertEqual(Reservacion.objects.count(), 1)

    def test_formulario_ya_no_pide_datos_de_tarjeta(self):
        r = self.client.get(reverse('reservaciones:solicitar'))
        for campo in ('numero_tarjeta', 'cvv', 'vencimiento'):
            self.assertNotContains(r, campo)
        self.assertContains(r, 'Disponibilidad')

    def test_prellenado_desde_catalogo(self):
        r = self.client.get(reverse('reservaciones:solicitar') + f'?espacio={self.espacio.pk}')
        self.assertContains(r, f'id="esp-{self.espacio.pk}"')
        self.assertContains(r, 'checked')

    def test_personal_no_entra_a_solicitar(self):
        self.client.force_login(self.personal)
        r = self.client.get(reverse('reservaciones:solicitar'))
        self.assertEqual(r.status_code, 302)

    def test_cliente_cancela_y_se_notifica(self):
        inicio, fin = horario()
        r = _crear(self.cliente, self.espacio, inicio, fin)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse('reservaciones:mi_cancelar', args=[r.pk]))
        r.refresh_from_db()
        self.assertEqual(r.estado, 'CANCELADA')
        self.assertEqual(len(mail.outbox), 2)  # cliente + personal


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class DisponibilidadTests(TestCase):
    def setUp(self):
        self.cliente = crear_cliente()
        self.espacio = crear_espacio()
        self.client.force_login(self.cliente.usuario)
        self.inicio, self.fin = horario(dias=2, hora=14, duracion=2)
        _crear(crear_cliente(), self.espacio, self.inicio, self.fin)

    def _consultar(self, **extra):
        mes = self.inicio.strftime('%Y-%m')
        params = {'espacio': self.espacio.pk, 'mes': mes, **extra}
        return self.client.get(reverse('reservaciones:disponibilidad_json'), params)

    def test_devuelve_horas_ocupadas_sin_datos_personales(self):
        r = self._consultar()
        datos = r.json()
        franjas = datos['dias'][self.inicio.date().isoformat()]
        self.assertEqual(franjas, [{'inicio': '14:00', 'fin': '16:00'}])
        cuerpo = r.content.decode()
        self.assertNotIn('Cliente', cuerpo)
        self.assertNotIn('Prueba', cuerpo)

    def test_las_canceladas_no_aparecen(self):
        Reservacion.objects.update(estado='CANCELADA')
        self.assertEqual(self._consultar().json()['dias'], {})

    def test_parametros_invalidos(self):
        self.assertEqual(self.client.get(reverse('reservaciones:disponibilidad_json'),
                                         {'espacio': 'x', 'mes': 'y'}).status_code, 400)

    def test_requiere_login(self):
        self.client.logout()
        self.assertEqual(self._consultar().status_code, 302)

    def test_reserva_que_cruza_medianoche_se_parte_por_dia(self):
        e2 = crear_espacio('Salón noche')
        ini, fin = horario(dias=3, hora=22, duracion=4)
        _crear(self.cliente, e2, ini, fin)
        r = self.client.get(reverse('reservaciones:disponibilidad_json'),
                            {'espacio': e2.pk, 'mes': ini.strftime('%Y-%m')}).json()['dias']
        self.assertEqual(r[ini.date().isoformat()][0]['inicio'], '22:00')
        sig = (ini + (fin - ini)).date().isoformat()
        self.assertIn(sig, r)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ConcurrenciaTests(TransactionTestCase):
    """
    Dos clientes intentan reservar el mismo horario exactamente al mismo
    tiempo. Solo una debe tener exito. Requiere una base de datos con
    bloqueo de filas (PostgreSQL, SQL Server); SQLite se omite.
    """

    def test_solo_una_reserva_gana_la_carrera(self):
        if connection.vendor == 'sqlite':
            self.skipTest('SQLite no soporta bloqueo de filas (select_for_update).')
        crear_roles()
        espacio = crear_espacio()
        clientes = [crear_cliente() for _ in range(6)]
        inicio, fin = horario()
        barrera = threading.Barrier(len(clientes))
        resultados = []

        def intentar(cliente):
            try:
                barrera.wait()
                _crear(cliente, espacio, inicio, fin)
                resultados.append('ok')
            except ValidationError:
                resultados.append('rechazada')
            except Exception as e:  # noqa: BLE001
                resultados.append(f'error:{e!r}')
            finally:
                connections.close_all()

        hilos = [threading.Thread(target=intentar, args=(c,)) for c in clientes]
        [h.start() for h in hilos]
        [h.join() for h in hilos]
        self.assertEqual(resultados.count('ok'), 1, resultados)
        self.assertEqual(resultados.count('rechazada'), len(clientes) - 1, resultados)
        self.assertEqual(Reservacion.objects.count(), 1)
