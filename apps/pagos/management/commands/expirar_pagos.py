from django.core.management.base import BaseCommand

from apps.pagos.services import expirar_pagos_pendientes


class Command(BaseCommand):
    help = ('Libera los horarios de reservaciones cuyo pago con tarjeta no se completo '
            'dentro del plazo. Tambien se ejecuta solo al abrir la pantalla de reservar.')

    def handle(self, *args, **opciones):
        total = expirar_pagos_pendientes()
        self.stdout.write(self.style.SUCCESS(f'Pagos pendientes revisados: {total}'))
