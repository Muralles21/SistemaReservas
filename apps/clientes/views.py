from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView

from apps.core.mixins import RolRequeridoMixin, AuditoriaMixin
from apps.core.models import Bitacora
from .forms import ClienteForm
from .models import Cliente


class ClienteListView(RolRequeridoMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_lista.html'
    context_object_name = 'clientes'
    paginate_by = 12
    roles_permitidos = []

    def get_queryset(self):
        qs = Cliente.objects.filter(activo=True).order_by('nombres')
        busqueda = self.request.GET.get('q')
        if busqueda:
            qs = qs.filter(nombres__icontains=busqueda) | qs.filter(
                apellidos__icontains=busqueda) | qs.filter(dpi__icontains=busqueda)
        return qs


class ClienteDetailView(RolRequeridoMixin, DetailView):
    model = Cliente
    template_name = 'clientes/cliente_detalle.html'
    context_object_name = 'cliente'
    roles_permitidos = []

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['reservaciones'] = self.object.reservaciones.order_by('-fecha_inicio')[:20]
        contexto['movimientos_puntos'] = self.object.movimientos_puntos.order_by('-fecha')[:20]
        from apps.fidelizacion.models import Premio
        contexto['premios_disponibles'] = Premio.objects.filter(
            activo=True, stock__gt=0, costo_puntos__lte=self.object.puntos_disponibles or 0)
        return contexto


class ClienteCreateView(RolRequeridoMixin, AuditoriaMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:lista')
    roles_permitidos = []
    modulo_bitacora = 'Clientes'
    accion_bitacora = Bitacora.ACCION_CREAR

    def form_valid(self, form):
        messages.success(self.request, 'Cliente registrado correctamente.')
        return super().form_valid(form)


class ClienteUpdateView(RolRequeridoMixin, AuditoriaMixin, UpdateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:lista')
    roles_permitidos = []
    modulo_bitacora = 'Clientes'
    accion_bitacora = Bitacora.ACCION_EDITAR

    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado correctamente.')
        return super().form_valid(form)


class ClienteDeleteView(RolRequeridoMixin, AuditoriaMixin, DeleteView):
    model = Cliente
    template_name = 'clientes/cliente_confirmar_eliminar.html'
    success_url = reverse_lazy('clientes:lista')
    roles_permitidos = []
    modulo_bitacora = 'Clientes'

    def delete(self, request, *args, **kwargs):
        """Borrado logico en lugar de fisico: conserva el historial."""
        self.object = self.get_object()
        self.object.eliminar_logico()
        self.accion_bitacora = Bitacora.ACCION_ELIMINAR
        self.registrar_bitacora(str(self.object))
        messages.success(request, 'Cliente eliminado correctamente.')
        from django.shortcuts import redirect
        return redirect(self.success_url)


class MiCuentaView(LoginRequiredMixin, TemplateView):
    """
    Portal de autoservicio del cliente: su propio perfil, historial de
    reservaciones, puntos y catálogo de premios canjeables. Exclusivo para
    usuarios con un perfil de Cliente vinculado (creado vía registro público
    o vinculado manualmente por un administrador).
    """
    template_name = 'clientes/mi_cuenta.html'

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'cliente'):
            messages.error(request, 'Esta sección está disponible únicamente para clientes.')
            return redirect('dashboard:inicio')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from apps.fidelizacion.models import Premio
        from apps.espacios.models import Espacio

        contexto = super().get_context_data(**kwargs)
        cliente = self.request.user.cliente
        contexto['cliente'] = cliente
        contexto['reservaciones'] = cliente.reservaciones.select_related('espacio').order_by('-fecha_inicio')[:20]
        contexto['movimientos_puntos'] = cliente.movimientos_puntos.order_by('-fecha')[:10]
        contexto['premios_disponibles'] = Premio.objects.filter(
            activo=True, stock__gt=0, costo_puntos__lte=cliente.puntos_disponibles or 0)
        contexto['espacios_disponibles'] = Espacio.objects.filter(
            activo=True, estado=Espacio.ESTADO_DISPONIBLE)
        return contexto
