from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.core.mixins import RolRequeridoMixin, AuditoriaMixin
from apps.core.models import Bitacora
from .forms import EspacioForm, EspacioFotoFormSet
from .models import Espacio


class EspacioListView(RolRequeridoMixin, ListView):
    model = Espacio
    template_name = 'espacios/espacio_lista.html'
    context_object_name = 'espacios'
    paginate_by = 12
    roles_permitidos = []

    def get_queryset(self):
        qs = Espacio.objects.filter(activo=True).order_by('nombre')
        tipo = self.request.GET.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        return qs


class EspacioDetailView(RolRequeridoMixin, DetailView):
    model = Espacio
    template_name = 'espacios/espacio_detalle.html'
    context_object_name = 'espacio'
    roles_permitidos = []


class EspacioCreateView(RolRequeridoMixin, AuditoriaMixin, CreateView):
    model = Espacio
    form_class = EspacioForm
    template_name = 'espacios/espacio_form.html'
    success_url = reverse_lazy('espacios:lista')
    roles_permitidos = []
    modulo_bitacora = 'Espacios'
    accion_bitacora = Bitacora.ACCION_CREAR

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['formset_fotos'] = EspacioFotoFormSet(
            self.request.POST or None, self.request.FILES or None)
        return contexto

    def form_valid(self, form):
        contexto = self.get_context_data()
        formset = contexto['formset_fotos']
        response = super().form_valid(form)
        if formset.is_valid():
            formset.instance = self.object
            formset.save()
        messages.success(self.request, 'Espacio registrado correctamente.')
        return response


class EspacioUpdateView(RolRequeridoMixin, AuditoriaMixin, UpdateView):
    model = Espacio
    form_class = EspacioForm
    template_name = 'espacios/espacio_form.html'
    success_url = reverse_lazy('espacios:lista')
    roles_permitidos = []
    modulo_bitacora = 'Espacios'
    accion_bitacora = Bitacora.ACCION_EDITAR

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['formset_fotos'] = EspacioFotoFormSet(
            self.request.POST or None, self.request.FILES or None, instance=self.object)
        return contexto

    def form_valid(self, form):
        contexto = self.get_context_data()
        formset = contexto['formset_fotos']
        response = super().form_valid(form)
        if formset.is_valid():
            formset.save()
        messages.success(self.request, 'Espacio actualizado correctamente.')
        return response


class EspacioDeleteView(RolRequeridoMixin, AuditoriaMixin, DeleteView):
    model = Espacio
    template_name = 'espacios/espacio_confirmar_eliminar.html'
    success_url = reverse_lazy('espacios:lista')
    roles_permitidos = []
    modulo_bitacora = 'Espacios'
