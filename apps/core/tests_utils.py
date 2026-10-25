"""Datos de prueba compartidos por las pruebas de los distintos modulos."""
from datetime import timedelta
from decimal import Decimal
from itertools import count

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.clientes.models import Cliente
from apps.espacios.models import Espacio
from apps.usuarios.models import Rol

Usuario = get_user_model()
_n = count(1)


def crear_roles():
    for clave, nombre in [('ADMINISTRADOR', 'Administrador'), ('RECEPCION', 'Recepción'),
                          ('CAJERO', 'Cajero'), ('CLIENTE', 'Cliente')]:
        Rol.objects.get_or_create(clave=clave, defaults={'nombre': nombre})


def crear_espacio(nombre='Cancha 1', precio='300.00', **extra):
    return Espacio.objects.create(nombre=nombre, tipo=Espacio.TIPO_RECREATIVO, capacidad=14,
                                  precio_por_evento=Decimal(precio), **extra)


def crear_personal(clave='RECEPCION', email=None):
    crear_roles()
    i = next(_n)
    return Usuario.objects.create_user(
        username=f'staff{i}', password='Clave-segura-123', email=email or f'staff{i}@ejemplo.com',
        rol=Rol.objects.get(clave=clave))


def crear_cliente(email=None):
    crear_roles()
    i = next(_n)
    usuario = Usuario.objects.create_user(
        username=f'cliente{i}', password='Clave-segura-123', email=email or f'cliente{i}@ejemplo.com',
        rol=Rol.objects.get(clave='CLIENTE'))
    return Cliente.objects.create(
        usuario=usuario, nombres=f'Cliente{i}', apellidos='Prueba', dpi=f'{i:013d}',
        telefono='55551234', direccion='Zona 1', correo=usuario.email)


def horario(dias=2, hora=14, duracion=2):
    """(inicio, fin) con fecha futura, a la hora local indicada."""
    base = timezone.localtime() + timedelta(days=dias)
    inicio = base.replace(hour=hora, minute=0, second=0, microsecond=0)
    return inicio, inicio + timedelta(hours=duracion)
