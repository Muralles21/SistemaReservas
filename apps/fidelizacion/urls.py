from django.urls import path
from . import views

app_name = 'fidelizacion'

urlpatterns = [
    path('premios/', views.PremioListView.as_view(), name='premios'),
    path('premios/nuevo/', views.PremioCreateView.as_view(), name='premio_crear'),
    path('premios/<int:pk>/editar/', views.PremioUpdateView.as_view(), name='premio_editar'),
    path('premios/<int:pk>/eliminar/', views.PremioDeleteView.as_view(), name='premio_eliminar'),

    path('historial/', views.HistorialPuntosListView.as_view(), name='historial'),
    path('canjes/', views.CanjeListView.as_view(), name='canjes'),
    path('canjear/<int:cliente_id>/', views.RealizarCanjeView.as_view(), name='canjear'),

    path('configuracion/', views.ConfiguracionFidelizacionView.as_view(), name='configuracion'),
]
