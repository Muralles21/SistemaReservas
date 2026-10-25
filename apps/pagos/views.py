from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView

from apps.core.mixins import RolRequeridoMixin, AuditoriaMixin
from apps.core.models import Bitacora
from apps.reservaciones.models import Reservacion
from .forms import PagoForm
from .models import Pago


class PagoListView(RolRequeridoMixin, ListView):
    model = Pago
    template_name = 'pagos/pago_lista.html'
    context_object_name = 'pagos'
    paginate_by = 20
    roles_permitidos = []

    def get_queryset(self):
        return Pago.objects.select_related('reservacion', 'reservacion__cliente').order_by('-fecha')


class PagoCreateView(RolRequeridoMixin, AuditoriaMixin, CreateView):
    model = Pago
    form_class = PagoForm
    template_name = 'pagos/pago_form.html'
    roles_permitidos = []
    modulo_bitacora = 'Pagos'
    accion_bitacora = Bitacora.ACCION_CREAR

    def dispatch(self, request, *args, **kwargs):
        self.reservacion = get_object_or_404(Reservacion, pk=kwargs['reservacion_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['reservacion'] = self.reservacion
        return kwargs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['reservacion'] = self.reservacion
        return contexto

    def form_valid(self, form):
        form.instance.reservacion = self.reservacion
        form.instance.usuario_registro = self.request.user
        messages.success(self.request, 'Pago registrado correctamente.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('reservaciones:detalle', kwargs={'pk': self.reservacion.pk})


# ----------------------------------------------------------------------
# Pago con tarjeta en linea (retorno desde la pasarela)
# ----------------------------------------------------------------------

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.views import View
from django.views.generic import TemplateView

from apps.pagos import services as pagos_services
from apps.pagos.pasarelas import PasarelaSimulada


def _pago_del_usuario(request, pk):
    """El pago solo es visible para el cliente dueño o para el personal."""
    pago = get_object_or_404(Pago.objects.select_related('reservacion__cliente', 'reservacion__espacio'), pk=pk)
    cliente = getattr(request.user, 'cliente', None)
    es_dueno = cliente is not None and pago.reservacion.cliente_id == cliente.id
    if not (es_dueno or request.user.is_superuser or (
            request.user.rol and request.user.rol.clave != 'CLIENTE')):
        raise Http404
    return pago


def _destino(request, pago):
    if hasattr(request.user, 'cliente'):
        return redirect('clientes:mi_cuenta')
    return redirect('reservaciones:detalle', pk=pago.reservacion_id)


class RetornoPagoView(LoginRequiredMixin, View):
    """A donde regresa el cliente despues de pagar en la pasarela."""

    def get(self, request, pk):
        pago = _pago_del_usuario(request, pk)
        estado = pagos_services.conciliar_pago(pago.pk, parametros=request.GET)
        if estado == Pago.ESTADO_APROBADO:
            messages.success(request, '¡Pago aprobado! Tu reservación quedó confirmada. '
                                      'Te enviamos un correo con los detalles.')
        elif estado == Pago.ESTADO_RECHAZADO:
            messages.error(request, 'El pago no se completó y el horario fue liberado. Puedes intentarlo de nuevo.')
        else:
            return render(request, 'pagos/pago_procesando.html', {'pago': pago})
        return _destino(request, pago)


class CancelarPagoView(LoginRequiredMixin, View):
    """El cliente cancela o abandona la pantalla de pago de la pasarela."""

    def get(self, request, pk):
        pago = _pago_del_usuario(request, pk)
        estado = pagos_services.conciliar_pago(pago.pk, parametros=request.GET, forzar_rechazo=True)
        if estado == Pago.ESTADO_APROBADO:
            messages.success(request, 'Tu pago ya había sido aprobado y la reservación está confirmada.')
        else:
            messages.warning(request, 'Cancelaste el pago. La reservación no se realizó y el horario quedó libre.')
        return _destino(request, pago)


class PagoSimuladoView(LoginRequiredMixin, TemplateView):
    """Pantalla de pago de demostracion (solo con PASARELA_PAGO='simulada')."""
    template_name = 'pagos/pago_simulado.html'

    def dispatch(self, request, *args, **kwargs):
        if settings.PASARELA_PAGO != 'simulada':
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        pago = _pago_del_usuario(self.request, self.kwargs['pk'])
        contexto['pago'] = pago
        contexto['token'] = PasarelaSimulada.token_aprobacion(pago)
        return contexto
