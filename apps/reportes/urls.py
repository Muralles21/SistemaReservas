from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('', views.ReportesMenuView.as_view(), name='menu'),
    path('clientes.pdf', views.ReporteClientesView.as_view(), name='clientes'),
    path('reservaciones.pdf', views.ReporteReservacionesView.as_view(), name='reservaciones'),
    path('pagos.pdf', views.ReportePagosView.as_view(), name='pagos'),
    path('espacios.pdf', views.ReporteEspaciosView.as_view(), name='espacios'),
    path('puntos.pdf', views.ReportePuntosView.as_view(), name='puntos'),
    path('ingresos.pdf', views.ReporteIngresosView.as_view(), name='ingresos'),
]
