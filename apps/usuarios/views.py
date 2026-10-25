from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.shortcuts import redirect, get_object_or_404

from apps.core.mixins import RolRequeridoMixin, AuditoriaMixin
from apps.core.models import Bitacora
from .forms import RolForm, UsuarioCreacionForm, UsuarioEdicionForm
from .models import Rol, Usuario

ROLES_ADMIN = [Rol.CLAVE_ADMINISTRADOR]


# ---------- Usuarios ----------

class UsuarioListView(RolRequeridoMixin, ListView):
    model = Usuario
    template_name = 'usuarios/usuario_lista.html'
    context_object_name = 'usuarios'
    paginate_by = 10
    roles_permitidos = ROLES_ADMIN

    def get_queryset(self):
        qs = Usuario.objects.select_related('rol').order_by('first_name')
        busqueda = self.request.GET.get('q')
        if busqueda:
            qs = qs.filter(username__icontains=busqueda) | qs.filter(email__icontains=busqueda)
        return qs


class UsuarioCreateView(RolRequeridoMixin, AuditoriaMixin, CreateView):
    model = Usuario
    form_class = UsuarioCreacionForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:lista')
    roles_permitidos = ROLES_ADMIN
    modulo_bitacora = 'Usuarios'
    accion_bitacora = Bitacora.ACCION_CREAR

    def form_valid(self, form):
        messages.success(self.request, 'Usuario creado correctamente.')
        return super().form_valid(form)


class UsuarioUpdateView(RolRequeridoMixin, AuditoriaMixin, UpdateView):
    model = Usuario
    form_class = UsuarioEdicionForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuarios:lista')
    roles_permitidos = ROLES_ADMIN
    modulo_bitacora = 'Usuarios'
    accion_bitacora = Bitacora.ACCION_EDITAR

    def form_valid(self, form):
        messages.success(self.request, 'Usuario actualizado correctamente.')
        return super().form_valid(form)


class UsuarioDeleteView(RolRequeridoMixin, AuditoriaMixin, DeleteView):
    model = Usuario
    template_name = 'usuarios/usuario_confirmar_eliminar.html'
    success_url = reverse_lazy('usuarios:lista')
    roles_permitidos = ROLES_ADMIN
    modulo_bitacora = 'Usuarios'


class UsuarioDesbloquearView(RolRequeridoMixin, View):
    roles_permitidos = ROLES_ADMIN

    def post(self, request, pk):
        usuario = get_object_or_404(Usuario, pk=pk)
        usuario.reiniciar_intentos()
        messages.success(request, f'Se desbloqueó la cuenta de {usuario}.')
        return redirect('usuarios:lista')


# ---------- Roles ----------

class RolListView(RolRequeridoMixin, ListView):
    model = Rol
    template_name = 'usuarios/rol_lista.html'
    context_object_name = 'roles'
    roles_permitidos = ROLES_ADMIN


class RolCreateView(RolRequeridoMixin, AuditoriaMixin, CreateView):
    model = Rol
    form_class = RolForm
    template_name = 'usuarios/rol_form.html'
    success_url = reverse_lazy('usuarios:rol_lista')
    roles_permitidos = ROLES_ADMIN
    modulo_bitacora = 'Roles'
    accion_bitacora = Bitacora.ACCION_CREAR


class RolUpdateView(RolRequeridoMixin, AuditoriaMixin, UpdateView):
    model = Rol
    form_class = RolForm
    template_name = 'usuarios/rol_form.html'
    success_url = reverse_lazy('usuarios:rol_lista')
    roles_permitidos = ROLES_ADMIN
    modulo_bitacora = 'Roles'
    accion_bitacora = Bitacora.ACCION_EDITAR


class RolDeleteView(RolRequeridoMixin, AuditoriaMixin, DeleteView):
    model = Rol
    template_name = 'usuarios/rol_confirmar_eliminar.html'
    success_url = reverse_lazy('usuarios:rol_lista')
    roles_permitidos = ROLES_ADMIN
    modulo_bitacora = 'Roles'


# ---------- Bitácora ----------

class BitacoraListView(RolRequeridoMixin, ListView):
    model = Bitacora
    template_name = 'usuarios/bitacora_lista.html'
    context_object_name = 'registros'
    paginate_by = 25
    roles_permitidos = ROLES_ADMIN

    def get_queryset(self):
        return Bitacora.objects.select_related('usuario').order_by('-fecha')
