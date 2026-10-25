from django.db.models import Sum, Count
from django.views import View
from django.views.generic import TemplateView

from apps.clientes.models import Cliente
from apps.core.mixins import RolRequeridoMixin
from apps.espacios.models import Espacio
from apps.fidelizacion.models import MovimientoPuntos
from apps.pagos.models import Pago
from apps.reservaciones.models import Reservacion
from .utilidades import generar_pdf_tabular


class ReportesMenuView(RolRequeridoMixin, TemplateView):
    template_name = 'reportes/menu.html'
    roles_permitidos = []


class ReporteClientesView(RolRequeridoMixin, View):
    roles_permitidos = []

    def get(self, request):
        clientes = Cliente.objects.filter(activo=True).order_by('nombres')
        filas = [[c.nombre_completo, c.dpi, c.telefono, c.correo, str(c.puntos_disponibles)]
                  for c in clientes]
        return generar_pdf_tabular(
            'Reporte de clientes',
            ['Nombre', 'DPI', 'Teléfono', 'Correo', 'Puntos'],
            filas, 'reporte_clientes.pdf'
        )


class ReporteReservacionesView(RolRequeridoMixin, View):
    roles_permitidos = []

    def get(self, request):
        reservaciones = Reservacion.objects.select_related('cliente', 'espacio').order_by('-fecha_inicio')
        filas = [[
            r.espacio.nombre, r.cliente.nombre_completo,
            r.fecha_inicio.strftime('%d/%m/%Y %H:%M'), r.get_estado_display(),
            f'Q{r.precio_total}'
        ] for r in reservaciones]
        return generar_pdf_tabular(
            'Reporte de reservaciones',
            ['Espacio', 'Cliente', 'Fecha', 'Estado', 'Precio'],
            filas, 'reporte_reservaciones.pdf'
        )


class ReportePagosView(RolRequeridoMixin, View):
    roles_permitidos = []

    def get(self, request):
        pagos = Pago.objects.select_related('reservacion__cliente').order_by('-fecha')
        filas = [[
            p.reservacion.cliente.nombre_completo, p.get_tipo_display(),
            f'Q{p.monto}', p.get_metodo_pago_display(), p.get_estado_display(),
            p.fecha.strftime('%d/%m/%Y')
        ] for p in pagos]
        return generar_pdf_tabular(
            'Reporte de pagos',
            ['Cliente', 'Tipo', 'Monto', 'Método', 'Estado', 'Fecha'],
            filas, 'reporte_pagos.pdf'
        )


class ReporteEspaciosView(RolRequeridoMixin, View):
    roles_permitidos = []

    def get(self, request):
        espacios = Espacio.objects.filter(activo=True).annotate(
            total_reservaciones=Count('reservaciones')).order_by('-total_reservaciones')
        filas = [[
            e.nombre, e.get_tipo_display(), str(e.capacidad),
            f'Q{e.precio_por_evento}', e.get_estado_display(), str(e.total_reservaciones)
        ] for e in espacios]
        return generar_pdf_tabular(
            'Reporte de espacios y salones',
            ['Nombre', 'Tipo', 'Capacidad', 'Precio', 'Estado', 'Reservaciones'],
            filas, 'reporte_espacios.pdf'
        )


class ReportePuntosView(RolRequeridoMixin, View):
    roles_permitidos = []

    def get(self, request):
        movimientos = MovimientoPuntos.objects.select_related('cliente').order_by('-fecha')
        filas = [[
            m.cliente.nombre_completo, m.get_tipo_display(), str(m.puntos),
            m.fecha.strftime('%d/%m/%Y'), m.descripcion
        ] for m in movimientos]
        return generar_pdf_tabular(
            'Reporte de puntos de fidelización',
            ['Cliente', 'Tipo', 'Puntos', 'Fecha', 'Descripción'],
            filas, 'reporte_puntos.pdf'
        )


class ReporteIngresosView(RolRequeridoMixin, View):
    roles_permitidos = []

    def get(self, request):
        ingresos_por_espacio = (
            Pago.objects.filter(estado=Pago.ESTADO_APROBADO)
            .values('reservacion__espacio__nombre')
            .annotate(total=Sum('monto'))
            .order_by('-total')
        )
        filas = [[i['reservacion__espacio__nombre'], f"Q{i['total']}"] for i in ingresos_por_espacio]
        return generar_pdf_tabular(
            'Reporte de ingresos por espacio',
            ['Espacio', 'Ingresos totales'],
            filas, 'reporte_ingresos.pdf'
        )
