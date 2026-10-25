from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View

from apps.clientes.models import Cliente
from apps.core.mixins import RolRequeridoMixin, AuditoriaMixin
from apps.core.models import Bitacora
from apps.usuarios.models import Rol
from .forms import PremioForm, ConfiguracionFidelizacionForm, CanjeForm
from .models import Premio, MovimientoPuntos, Canje, ConfiguracionFidelizacion
from .services import canjear_premio


class PremioListView(RolRequeridoMixin, ListView):
    model = Premio
    template_name = 'fidelizacion/premio_lista.html'
    context_object_name = 'premios'
    roles_permitidos = []

    def get_queryset(self):
        return Premio.objects.filter(activo=True).order_by('costo_puntos')


class PremioCreateView(RolRequeridoMixin, AuditoriaMixin, CreateView):
    model = Premio
    form_class = PremioForm
    template_name = 'fidelizacion/premio_form.html'
    success_url = reverse_lazy('fidelizacion:premios')
    roles_permitidos = []
    modulo_bitacora = 'Fidelización'
    accion_bitacora = Bitacora.ACCION_CREAR


class PremioUpdateView(RolRequeridoMixin, AuditoriaMixin, UpdateView):
    model = Premio
    form_class = PremioForm
    template_name = 'fidelizacion/premio_form.html'
    success_url = reverse_lazy('fidelizacion:premios')
    roles_permitidos = []
    modulo_bitacora = 'Fidelización'
    accion_bitacora = Bitacora.ACCION_EDITAR


class PremioDeleteView(RolRequeridoMixin, AuditoriaMixin, DeleteView):
    model = Premio
    template_name = 'fidelizacion/premio_confirmar_eliminar.html'
    success_url = reverse_lazy('fidelizacion:premios')
    roles_permitidos = []
    modulo_bitacora = 'Fidelización'


class HistorialPuntosListView(RolRequeridoMixin, ListView):
    model = MovimientoPuntos
    template_name = 'fidelizacion/historial_puntos.html'
    context_object_name = 'movimientos'
    paginate_by = 20
    roles_permitidos = []

    def get_queryset(self):
        qs = MovimientoPuntos.objects.select_related('cliente').order_by('-fecha')
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            qs = qs.filter(cliente_id=cliente_id)
        return qs


class RealizarCanjeView(LoginRequiredMixin, View):
    """
    Permite canjear un premio tanto al personal interno (desde la ficha de
    cualquier cliente) como al propio cliente autenticado (desde su portal
    de autoservicio), verificando que solo pueda canjear a nombre propio.
    """

    def post(self, request, cliente_id):
        cliente = get_object_or_404(Cliente, pk=cliente_id)

        es_su_propio_perfil = hasattr(request.user, 'cliente') and request.user.cliente.id == cliente.id
        es_personal_interno = request.user.is_superuser or (
            request.user.rol and request.user.rol.clave != Rol.CLAVE_CLIENTE)

        if not (es_su_propio_perfil or es_personal_interno):
            messages.error(request, 'No tienes permiso para realizar esta acción.')
            return redirect('dashboard:inicio')

        form = CanjeForm(request.POST)
        if form.is_valid():
            try:
                canjear_premio(cliente, form.cleaned_data['premio'].pk, usuario=request.user)
                messages.success(request, 'Canje realizado correctamente.')
            except ValidationError as error:
                messages.error(request, error.message)
        else:
            messages.error(request, 'Selecciona un premio válido.')

        if es_su_propio_perfil:
            return redirect('clientes:mi_cuenta')
        return redirect('clientes:detalle', pk=cliente.pk)


class CanjeListView(RolRequeridoMixin, ListView):
    model = Canje
    template_name = 'fidelizacion/canje_lista.html'
    context_object_name = 'canjes'
    paginate_by = 20
    roles_permitidos = []

    def get_queryset(self):
        return Canje.objects.select_related('cliente', 'premio').order_by('-fecha')


class ConfiguracionFidelizacionView(RolRequeridoMixin, UpdateView):
    model = ConfiguracionFidelizacion
    form_class = ConfiguracionFidelizacionForm
    template_name = 'fidelizacion/configuracion.html'
    success_url = reverse_lazy('fidelizacion:configuracion')
    roles_permitidos = ['ADMINISTRADOR']

    def get_object(self, queryset=None):
        return ConfiguracionFidelizacion.obtener()

    def form_valid(self, form):
        messages.success(self.request, 'Configuración de fidelización actualizada.')
        return super().form_valid(form)
