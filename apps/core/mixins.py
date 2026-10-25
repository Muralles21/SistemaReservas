from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from apps.core.models import Bitacora


class RolRequeridoMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin reutilizable para restringir vistas por rol (DRY: evita repetir
    "if request.user.rol == ..." en cada vista). Se usa declarando
    roles_permitidos = ['ADMINISTRADOR', 'RECEPCION'] en la vista hija.
    Los superusuarios siempre tienen acceso.
    """
    roles_permitidos = []

    def test_func(self):
        usuario = self.request.user
        if not usuario.is_authenticated:
            return False
        if usuario.is_superuser:
            return True
        if self.roles_permitidos:
            return bool(usuario.rol) and usuario.rol.clave in self.roles_permitidos
        # Sin roles explicitos: la vista es para personal interno (no clientes).
        # Se evalua de forma perezosa para evitar import circular con apps.usuarios.
        from apps.usuarios.models import Rol
        return bool(usuario.rol) and usuario.rol.clave != Rol.CLAVE_CLIENTE

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, 'No tienes permisos para acceder a este módulo.')
        from apps.usuarios.models import Rol
        usuario = self.request.user
        if usuario.rol and usuario.rol.clave == Rol.CLAVE_CLIENTE:
            return redirect('clientes:mi_cuenta')
        return redirect('dashboard:inicio')


class AuditoriaMixin:
    """
    Mixin para vistas basadas en clases (CreateView/UpdateView/DeleteView)
    que registra automaticamente la accion en la Bitacora, evitando repetir
    esta logica en cada vista de cada modulo (DRY).
    """
    modulo_bitacora = 'General'
    accion_bitacora = Bitacora.ACCION_CREAR

    def registrar_bitacora(self, descripcion):
        Bitacora.objects.create(
            usuario=self.request.user if self.request.user.is_authenticated else None,
            accion=self.accion_bitacora,
            modulo=self.modulo_bitacora,
            descripcion=descripcion,
            ip=getattr(self.request, 'ip_cliente', None),
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        self.registrar_bitacora(str(self.object))
        return response

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        descripcion = str(self.object)
        response = super().delete(request, *args, **kwargs)
        self.accion_bitacora = Bitacora.ACCION_ELIMINAR
        self.registrar_bitacora(descripcion)
        return response
