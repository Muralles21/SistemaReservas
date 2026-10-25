from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='inicio'),
    path('datos-graficas.json', views.DatosGraficasView.as_view(), name='datos_graficas'),
]
