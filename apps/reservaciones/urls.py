from django.urls import path
from . import views

app_name = 'reservaciones'

urlpatterns = [
    path('', views.ReservacionListView.as_view(), name='lista'),
    path('nueva/', views.ReservacionCreateView.as_view(), name='crear'),
    path('calendario/', views.CalendarioView.as_view(), name='calendario'),
    path('calendario/eventos.json', views.EventosCalendarioView.as_view(), name='eventos_json'),
    path('<int:pk>/', views.ReservacionDetailView.as_view(), name='detalle'),
    path('<int:pk>/editar/', views.ReservacionUpdateView.as_view(), name='editar'),
    path('<int:pk>/confirmar/', views.ConfirmarReservacionView.as_view(), name='confirmar'),
    path('<int:pk>/cancelar/', views.CancelarReservacionView.as_view(), name='cancelar'),
    path('<int:pk>/reprogramar/', views.ReprogramarReservacionView.as_view(), name='reprogramar'),
    path('<int:pk>/finalizar/', views.FinalizarReservacionView.as_view(), name='finalizar'),
    path('disponibilidad.json', views.DisponibilidadView.as_view(), name='disponibilidad_json'),
    path('solicitar/', views.SolicitarReservacionView.as_view(), name='solicitar'),
    path('<int:pk>/mi-cancelar/', views.MiCancelarReservacionView.as_view(), name='mi_cancelar'),
]
