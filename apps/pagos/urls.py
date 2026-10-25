from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    path('', views.PagoListView.as_view(), name='lista'),
    path('reservacion/<int:reservacion_id>/nuevo/', views.PagoCreateView.as_view(), name='crear'),
    # Pago con tarjeta en linea
    path('retorno/<int:pk>/', views.RetornoPagoView.as_view(), name='retorno'),
    path('cancelado/<int:pk>/', views.CancelarPagoView.as_view(), name='cancelado'),
    path('simulada/<int:pk>/', views.PagoSimuladoView.as_view(), name='simulada'),
]
