from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.clientes.models import Cliente
from apps.core.tests_utils import crear_roles


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', SITE_URL='http://testserver')
class RegistroTests(TestCase):
    DATOS = {
        'nombres': 'Ana', 'apellidos': 'López', 'dpi': '1234567890123', 'telefono': '55551234',
        'direccion': 'Zona 10', 'correo': 'ana@ejemplo.com', 'username': 'ana',
        'password1': 'Clave-segura-987', 'password2': 'Clave-segura-987',
    }

    def setUp(self):
        crear_roles()

    def test_registro_envia_correo_de_confirmacion(self):
        with self.captureOnCommitCallbacks(execute=True):
            r = self.client.post(reverse('autenticacion:registro'), self.DATOS)
        self.assertRedirects(r, reverse('clientes:mi_cuenta'), fetch_redirect_response=False)
        self.assertEqual(Cliente.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ['ana@ejemplo.com'])
        self.assertIn('cuenta fue creada', correo.subject)
        self.assertIn('ana', correo.body)
        self.assertIn('http://testserver/cuenta/login/', correo.alternatives[0][0])

    def test_registro_invalido_no_envia_correo(self):
        datos = {**self.DATOS, 'password2': 'otra'}
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse('autenticacion:registro'), datos)
        self.assertEqual(len(mail.outbox), 0)

    def test_fallo_del_servidor_de_correo_no_rompe_el_registro(self):
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
                               EMAIL_HOST='127.0.0.1', EMAIL_PORT=1):
            with self.captureOnCommitCallbacks(execute=True):
                r = self.client.post(reverse('autenticacion:registro'), self.DATOS)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(Cliente.objects.count(), 1)
