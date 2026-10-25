from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),

    path('cuenta/', include('apps.autenticacion.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('clientes/', include('apps.clientes.urls')),
    path('espacios/', include('apps.espacios.urls')),
    path('reservaciones/', include('apps.reservaciones.urls')),
    path('pagos/', include('apps.pagos.urls')),
    path('fidelizacion/', include('apps.fidelizacion.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
