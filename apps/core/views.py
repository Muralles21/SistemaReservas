from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView

from apps.espacios.models import Espacio
from apps.fidelizacion.models import Premio


def destino_inicio(usuario):
    """Pagina de inicio segun el rol: portal para clientes, dashboard para personal."""
    rol = getattr(usuario, 'rol', None)
    if rol and rol.clave == 'CLIENTE':
        return 'clientes:mi_cuenta'
    return 'dashboard:inicio'


class LandingView(TemplateView):
    """
    Pagina publica de presentacion del sistema. Muestra canchas y salones
    disponibles y el catalogo de premios (datos de solo lectura, sin
    informacion sensible). Si el usuario ya inicio sesion, se le redirige
    directamente a su panel.
    """
    template_name = 'landing.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(destino_inicio(request.user))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        disponibles = Espacio.objects.filter(activo=True, estado=Espacio.ESTADO_DISPONIBLE)
        contexto['espacios'] = disponibles.order_by('nombre')[:6]
        contexto['total_canchas'] = disponibles.filter(tipo=Espacio.TIPO_RECREATIVO).count()
        contexto['total_salones'] = disponibles.filter(tipo=Espacio.TIPO_SALON).count()
        contexto['premios'] = Premio.objects.filter(activo=True, stock__gt=0).order_by('costo_puntos')[:4]
        return contexto


class CatalogoView(LoginRequiredMixin, ListView):
    """
    Catalogo visual de canchas y salones para el cliente autenticado (solo
    lectura). Usa LoginRequiredMixin y no RolRequeridoMixin porque este ultimo
    excluye por defecto al rol Cliente.
    """
    model = Espacio
    template_name = 'core/catalogo.html'
    context_object_name = 'espacios'
    paginate_by = 12

    def get_queryset(self):
        qs = Espacio.objects.filter(activo=True, estado=Espacio.ESTADO_DISPONIBLE).order_by('nombre')
        tipo = self.request.GET.get('tipo')
        if tipo in (Espacio.TIPO_RECREATIVO, Espacio.TIPO_SALON):
            qs = qs.filter(tipo=tipo)
        return qs
