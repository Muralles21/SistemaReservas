from django.urls import path
from . import views

app_name = 'autenticacion'

urlpatterns = [
    path('login/', views.LoginPersonalizadoView.as_view(), name='login'),
    path('logout/', views.LogoutPersonalizadoView.as_view(), name='logout'),
    path('registro/', views.RegistroClienteView.as_view(), name='registro'),

    path('recuperar/', views.SolicitudRecuperacionView.as_view(), name='recuperar'),
    path('recuperar/enviado/', views.RecuperacionEnviadaView.as_view(), name='recuperar_enviado'),
    path('recuperar/<uidb64>/<token>/', views.RestablecerContrasenaView.as_view(), name='restablecer'),
    path('recuperar/completo/', views.RestablecimientoCompletoView.as_view(), name='restablecer_completo'),

    path('cambiar-password/', views.CambiarContrasenaView.as_view(), name='cambiar_password'),
    path('cambiar-password/completo/', views.CambioCompletoView.as_view(), name='cambiar_completo'),
]
