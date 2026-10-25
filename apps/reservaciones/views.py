import json
import logging
from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView

from apps.core import notificaciones
from apps.core.mixins import RolRequeridoMixin, AuditoriaMixin
from apps.core.models import Bitacora
from apps.espacios.models import Espacio
from apps.usuarios.models import Rol
from . import services
from .forms import ReservacionForm, ReprogramarForm, CancelarForm, SolicitudReservacionForm
from .models import Reservacion

logger = logging.getLogger(__name__)

COLOR_ESTADO = {
    Reservacion.ESTADO_PENDIENTE: '#EF9F27',
    Reservacion.ESTADO_CONFIRMADA: '#1D9E75',
    Reservacion.ESTADO_CANCELADA: '#E24B4A',
    Reservacion.ESTADO_FINALIZADA: '#7F77DD',
}


class ReservacionListView(RolRequeridoMixin, ListView):
    model = Reservacion
    template_name = 'reservaciones/reservacion_lista.html'
    context_object_name = 'reservaciones'
    paginate_by = 15
    roles_permitidos = []

    def get_queryset(self):
        qs = Reservacion.objects.select_related('cliente', 'espacio').order_by('-fecha_inicio')
        estado = self.request.GET.get('estado')
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['estados'] = Reservacion.OPCIONES_ESTADO
        return contexto


class ReservacionDetailView(RolRequeridoMixin, DetailView):
    model = Reservacion
    template_name = 'reservaciones/reservacion_detalle.html'
    context_object_name = 'reservacion'
    roles_permitidos = []

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['form_reprogramar'] = ReprogramarForm()
        contexto['form_cancelar'] = CancelarForm()
        contexto['pagos'] = self.object.pagos.order_by('-fecha')
        return contexto


class ReservacionCreateView(RolRequeridoMixin, AuditoriaMixin, CreateView):
    model = Reservacion
    form_class = ReservacionForm
    template_name = 'reservaciones/reservacion_form.html'
    success_url = reverse_lazy('reservaciones:lista')
    roles_permitidos = []
    modulo_bitacora = 'Reservaciones'
    accion_bitacora = Bitacora.ACCION_CREAR

    def form_valid(self, form):
        form.instance.usuario_registro = self.request.user
        try:
            respuesta = super().form_valid(form)
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        notificaciones.reservacion_creada(self.object, avisar_personal=False)
        messages.success(self.request, 'Reservación creada correctamente.')
        return respuesta


class ReservacionUpdateView(RolRequeridoMixin, AuditoriaMixin, UpdateView):
    model = Reservacion
    form_class = ReservacionForm
    template_name = 'reservaciones/reservacion_form.html'
    success_url = reverse_lazy('reservaciones:lista')
    roles_permitidos = []
    modulo_bitacora = 'Reservaciones'
    accion_bitacora = Bitacora.ACCION_EDITAR

    def form_valid(self, form):
        try:
            respuesta = super().form_valid(form)
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)
        messages.success(self.request, 'Reservación actualizada correctamente.')
        return respuesta


class ConfirmarReservacionView(RolRequeridoMixin, View):
    roles_permitidos = []

    def post(self, request, pk):
        reservacion = get_object_or_404(Reservacion, pk=pk)
        try:
            services.confirmar_reservacion(reservacion, request.user)
            messages.success(request, 'Reservación confirmada.')
        except ValidationError as error:
            messages.error(request, error.message)
        return redirect('reservaciones:detalle', pk=pk)


class CancelarReservacionView(RolRequeridoMixin, View):
    roles_permitidos = []

    def post(self, request, pk):
        reservacion = get_object_or_404(Reservacion, pk=pk)
        form = CancelarForm(request.POST)
        motivo = form.data.get('motivo', '') if form.is_valid() else ''
        try:
            services.cancelar_reservacion(reservacion, request.user, motivo)
            messages.success(request, 'Reservación cancelada.')
        except ValidationError as error:
            messages.error(request, error.message)
        return redirect('reservaciones:detalle', pk=pk)


class ReprogramarReservacionView(RolRequeridoMixin, View):
    roles_permitidos = []

    def post(self, request, pk):
        reservacion = get_object_or_404(Reservacion, pk=pk)
        form = ReprogramarForm(request.POST)
        if form.is_valid():
            try:
                services.reprogramar_reservacion(
                    reservacion, form.cleaned_data['fecha_inicio'],
                    form.cleaned_data['fecha_fin'], request.user)
                messages.success(request, 'Reservación reprogramada correctamente.')
            except ValidationError as error:
                messages.error(request, error.message)
        else:
            messages.error(request, 'Verifica las fechas ingresadas.')
        return redirect('reservaciones:detalle', pk=pk)


class FinalizarReservacionView(RolRequeridoMixin, View):
    roles_permitidos = []

    def post(self, request, pk):
        reservacion = get_object_or_404(Reservacion, pk=pk)
        try:
            services.finalizar_reservacion(reservacion, request.user)
            messages.success(request, 'Reservación finalizada y puntos acreditados al cliente.')
        except ValidationError as error:
            messages.error(request, error.message)
        return redirect('reservaciones:detalle', pk=pk)


class CalendarioView(LoginRequiredMixin, TemplateView):
    """
    Calendario de disponibilidad. Accesible tanto para personal interno como
    para clientes autenticados: un cliente necesita poder ver qué horarios
    están ocupados antes de solicitar una reservación, sin depender de que
    un empleado se la confirme primero para saber si el horario es válido.
    """
    template_name = 'reservaciones/calendario.html'


class EventosCalendarioView(LoginRequiredMixin, View):
    """
    Fuente de datos del calendario. El personal interno ve el detalle
    completo (espacio + cliente); un cliente ve sus propias reservaciones
    identificadas y las de los demás solo como "Ocupado", para no exponer
    datos personales de otros clientes.
    """

    def get(self, request):
        reservaciones = Reservacion.objects.select_related('cliente', 'espacio').exclude(
            estado=Reservacion.ESTADO_CANCELADA)

        es_personal_interno = request.user.is_superuser or (
            request.user.rol and request.user.rol.clave != Rol.CLAVE_CLIENTE)
        cliente_actual = request.user.cliente if hasattr(request.user, 'cliente') else None

        eventos = []
        for r in reservaciones:
            es_propia = cliente_actual and r.cliente_id == cliente_actual.id
            if es_personal_interno:
                titulo = f'{r.espacio.nombre} · {r.cliente.nombre_completo}'
                url = f'/reservaciones/{r.pk}/'
            elif es_propia:
                titulo = f'{r.espacio.nombre} · Tu reserva ({r.get_estado_display()})'
                url = f'/reservaciones/{r.pk}/'
            else:
                titulo = f'{r.espacio.nombre} · Ocupado'
                url = ''
            eventos.append({
                'id': r.pk,
                'title': titulo,
                'start': r.fecha_inicio.isoformat(),
                'end': r.fecha_fin.isoformat(),
                'color': COLOR_ESTADO.get(r.estado, '#888780'),
                'url': url,
            })
        return JsonResponse(eventos, safe=False)


def _liberar_pagos_vencidos():
    """Libera los horarios de pagos con tarjeta abandonados (sin necesidad de tareas programadas)."""
    from apps.pagos.services import expirar_pagos_pendientes
    try:
        expirar_pagos_pendientes()
    except Exception:  # nunca debe romper la pantalla de reservar
        logging.getLogger(__name__).exception('No se pudieron liberar pagos vencidos')


class DisponibilidadView(LoginRequiredMixin, View):
    """
    Horarios ocupados de un espacio en un mes, para el mini calendario de la
    pantalla de reservar. Solo expone horas ocupadas (nunca quien reservo).
    GET ?espacio=<id>&mes=AAAA-MM  ->  {"dias": {"2026-10-17": [{"inicio": "14:00", "fin": "16:00"}]}}
    """

    def get(self, request):
        _liberar_pagos_vencidos()
        try:
            espacio = Espacio.objects.get(pk=int(request.GET.get('espacio', '')), activo=True)
            anio, mes = [int(x) for x in request.GET.get('mes', '').split('-')]
            primero = datetime(anio, mes, 1)
        except (ValueError, TypeError, Espacio.DoesNotExist):
            return JsonResponse({'error': 'Parámetros inválidos.'}, status=400)

        zona = timezone.get_current_timezone()
        desde = timezone.make_aware(primero, zona)
        hasta = timezone.make_aware(
            datetime(anio + (mes == 12), 1 if mes == 12 else mes + 1, 1), zona)
        reservas = espacio.reservaciones.filter(
            estado__in=Reservacion.ESTADOS_ACTIVOS,
            fecha_inicio__lt=hasta, fecha_fin__gt=desde).order_by('fecha_inicio')

        dias = {}
        for r in reservas:
            inicio = timezone.localtime(r.fecha_inicio)
            fin = timezone.localtime(r.fecha_fin)
            dia = inicio.date()
            while dia <= fin.date():
                ini_dia = max(inicio, timezone.make_aware(datetime.combine(dia, time.min), zona))
                fin_dia = min(fin, timezone.make_aware(datetime.combine(dia, time.max), zona))
                if desde.date() <= dia < hasta.date() and fin_dia > ini_dia:
                    dias.setdefault(dia.isoformat(), []).append({
                        'inicio': ini_dia.strftime('%H:%M'),
                        'fin': '24:00' if fin_dia.time() == time.max else fin_dia.strftime('%H:%M'),
                    })
                dia += timedelta(days=1)
        return JsonResponse({
            'espacio': espacio.nombre,
            'disponible': espacio.estado == Espacio.ESTADO_DISPONIBLE,
            'dias': dias,
        })


class SolicitarReservacionView(LoginRequiredMixin, CreateView):
    """
    Permite al cliente autenticado solicitar una reservación para sí mismo
    desde su portal de autoservicio.

    * Pago con tarjeta: la reservación se crea PENDIENTE (reteniendo el
      horario) y el cliente es enviado a la pasarela de pago; se confirma
      sola cuando el cobro se aprueba (apps.pagos.services).
    * Efectivo: queda PENDIENTE hasta que el personal la confirme.
    """
    model = Reservacion
    form_class = SolicitudReservacionForm
    template_name = 'reservaciones/solicitar.html'
    success_url = reverse_lazy('clientes:mi_cuenta')

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, 'cliente'):
            messages.error(request, 'Esta sección está disponible únicamente para clientes.')
            return redirect('dashboard:inicio')
        _liberar_pagos_vencidos()
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        inicial = super().get_initial()
        espacio = self.request.GET.get('espacio')
        if espacio and espacio.isdigit():
            inicial['espacio'] = int(espacio)
        return inicial

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['espacios'] = Espacio.objects.filter(
            activo=True, estado=Espacio.ESTADO_DISPONIBLE).order_by('nombre')
        contexto['pasarela_simulada'] = settings.PASARELA_PAGO == 'simulada'
        return contexto

    def form_valid(self, form):
        form.instance.cliente = self.request.user.cliente
        form.instance.usuario_registro = self.request.user
        try:
            with transaction.atomic():
                respuesta = super().form_valid(form)
        except ValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)

        reservacion = self.object
        Bitacora.objects.create(
            usuario=self.request.user, accion=Bitacora.ACCION_CREAR, modulo='Reservaciones',
            descripcion=f'Solicitud de reservación por el propio cliente: {reservacion}',
            ip=getattr(self.request, 'ip_cliente', None),
        )

        if form.cleaned_data['metodo_pago'] == form.METODO_TARJETA:
            from apps.pagos.pasarelas import ErrorPasarela
            from apps.pagos.services import iniciar_pago_tarjeta
            try:
                _, url_pago = iniciar_pago_tarjeta(reservacion, self.request.user)
            except ErrorPasarela:
                logger.exception('No se pudo iniciar el pago de la reservación %s', reservacion.pk)
                services.cancelar_reservacion(
                    reservacion, self.request.user, 'No se pudo iniciar el pago', notificar=False)
                form.add_error(None, 'No pudimos iniciar el pago con tarjeta. Intenta de nuevo en unos '
                                     'minutos o elige pagar en efectivo.')
                return self.form_invalid(form)
            messages.info(self.request, 'Te estamos llevando a la página segura de pago. '
                                        'Tu horario queda apartado mientras pagas.')
            return redirect(url_pago)

        notificaciones.reservacion_creada(reservacion)
        messages.success(
            self.request,
            'Tu solicitud fue registrada y te enviamos un correo. Quedará pendiente hasta que '
            'un empleado confirme la reservación al recibir el pago en efectivo.')
        return respuesta


class MiCancelarReservacionView(LoginRequiredMixin, View):
    """Permite al cliente cancelar únicamente sus propias reservaciones."""

    def post(self, request, pk):
        reservacion = get_object_or_404(Reservacion, pk=pk)
        if not hasattr(request.user, 'cliente') or reservacion.cliente_id != request.user.cliente.id:
            messages.error(request, 'No tienes permiso para realizar esta acción.')
            return redirect('clientes:mi_cuenta')
        try:
            services.cancelar_reservacion(reservacion, request.user, 'Cancelada por el cliente',
                                          por_cliente=True)
            messages.success(request, 'Tu reservación fue cancelada.')
        except ValidationError as error:
            messages.error(request, error.message)
        return redirect('clientes:mi_cuenta')
