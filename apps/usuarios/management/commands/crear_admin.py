"""
Comando de arranque: crea (o reutiliza) un superusuario y le asigna
automáticamente el rol "Administrador", en un solo paso. Resuelve la
pregunta de "¿cómo obtengo el primer usuario administrador?": el registro
público (autenticacion:registro) es exclusivamente para clientes, así que
la cuenta de administrador se crea una única vez desde la terminal con
este comando.

Uso:
    python manage.py crear_admin
    python manage.py crear_admin --username admin --email admin@correo.com --noinput
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.management.commands.createsuperuser import (
    Command as CreateSuperuserCommand,
)

from apps.usuarios.models import Rol


class Command(CreateSuperuserCommand):
    help = (
        'Crea un superusuario y le asigna automáticamente el rol '
        '"Administrador" del sistema, en un solo paso.'
    )

    def handle(self, *args, **options):
        Usuario = get_user_model()
        usuarios_antes = set(Usuario.objects.values_list('pk', flat=True))

        super().handle(*args, **options)

        username_field = Usuario.USERNAME_FIELD
        username = options.get(username_field)
        if username:
            usuario = Usuario.objects.filter(**{username_field: username}).first()
        else:
            # Modo interactivo: el usuario recien creado es el de mayor pk
            # que no existia antes de ejecutar el comando.
            usuario = Usuario.objects.exclude(pk__in=usuarios_antes).order_by('-pk').first()

        if not usuario:
            self.stderr.write(self.style.WARNING(
                'No se pudo determinar el usuario recién creado; '
                'asigna el rol manualmente desde el módulo Usuarios.'
            ))
            return

        rol_admin, _ = Rol.objects.get_or_create(
            clave=Rol.CLAVE_ADMINISTRADOR, defaults={'nombre': 'Administrador'}
        )
        usuario.rol = rol_admin
        usuario.save(update_fields=['rol'])
        self.stdout.write(self.style.SUCCESS(
            f'Listo: "{usuario}" es superusuario y tiene el rol Administrador.'
        ))
