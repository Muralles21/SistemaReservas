from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.clientes.models import Cliente
from apps.core.mixins import RolRequeridoMixin
from apps.espacios.models import Espacio
from apps.pagos.models import Pago
from apps.reservaciones.models import Reservacion


class DashboardView(RolRequeridoMixin, TemplateView):
    template_name = 'dashboard/inicio.html'
    roles_permitidos = []

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        hoy = timezone.now()
        inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        contexto['total_clientes'] = Cliente.objects.filter(activo=True).count()
        contexto['total_espacios'] = Espacio.objects.filter(activo=True).count()
        contexto['reservaciones_mes'] = Reservacion.objects.filter(
            fecha_inicio__gte=inicio_mes).count()
        contexto['ingresos_mes'] = Pago.objects.filter(
            estado=Pago.ESTADO_APROBADO, fecha__gte=inicio_mes
        ).aggregate(total=Sum('monto'))['total'] or 0
        contexto['reservaciones_pendientes'] = Reservacion.objects.filter(
            estado=Reservacion.ESTADO_PENDIENTE).count()
        contexto['proximas_reservaciones'] = Reservacion.objects.select_related(
            'cliente', 'espacio'
        ).filter(fecha_inicio__gte=hoy, estado__in=['PENDIENTE', 'CONFIRMADA']).order_by(
            'fecha_inicio')[:6]
        return contexto


class DatosGraficasView(RolRequeridoMixin, View):
    roles_permitidos = []

    def get(self, request):
        hoy = timezone.now()
        hace_seis_meses = hoy - timedelta(days=180)

        espacios_top = list(
            Reservacion.objects.exclude(estado=Reservacion.ESTADO_CANCELADA)
            .values('espacio__nombre').annotate(total=Count('id'))
            .order_by('-total')[:6]
        )
        clientes_frecuentes = list(
            Reservacion.objects.exclude(estado=Reservacion.ESTADO_CANCELADA)
            .values('cliente__nombres', 'cliente__apellidos')
            .annotate(total=Count('id')).order_by('-total')[:6]
        )
        # TruncMonth es agnostico de motor (funciona igual en SQL Server, MySQL,
        # PostgreSQL o SQLite), a diferencia de usar funciones SQL crudas por motor.
        ventas_mensuales = list(
            Pago.objects.filter(estado=Pago.ESTADO_APROBADO, fecha__gte=hace_seis_meses)
            .annotate(mes=TruncMonth('fecha'))
            .values('mes').annotate(total=Sum('monto')).order_by('mes')
        )

        return JsonResponse({
            'espacios_top': {
                'labels': [e['espacio__nombre'] for e in espacios_top],
                'valores': [e['total'] for e in espacios_top],
            },
            'clientes_frecuentes': {
                'labels': [f"{c['cliente__nombres']} {c['cliente__apellidos']}" for c in clientes_frecuentes],
                'valores': [c['total'] for c in clientes_frecuentes],
            },
            'ventas_mensuales': {
                'labels': [v['mes'].strftime('%Y-%m') for v in ventas_mensuales],
                'valores': [float(v['total']) for v in ventas_mensuales],
            },
        })
