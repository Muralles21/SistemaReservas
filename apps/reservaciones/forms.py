from django import forms
from apps.clientes.models import Cliente
from apps.espacios.models import Espacio
from .models import Reservacion


class ReservacionForm(forms.ModelForm):
    class Meta:
        model = Reservacion
        fields = ['cliente', 'espacio', 'fecha_inicio', 'fecha_fin', 'observaciones']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'espacio': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'fecha_fin': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
        self.fields['espacio'].queryset = Espacio.objects.filter(activo=True)

    def clean(self):
        datos = super().clean()
        espacio = datos.get('espacio')
        if espacio:
            datos['precio_total'] = espacio.precio_por_evento
        return datos

    def save(self, commit=True):
        reservacion = super().save(commit=False)
        if reservacion.espacio_id:
            reservacion.precio_total = reservacion.espacio.precio_por_evento
        if commit:
            reservacion.full_clean()
            reservacion.save()
        return reservacion


class ReprogramarForm(forms.Form):
    fecha_inicio = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))
    fecha_fin = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}))


class CancelarForm(forms.Form):
    motivo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                      'placeholder': 'Motivo de la cancelación (opcional)'}))


class SolicitudReservacionForm(forms.ModelForm):
    """
    Formulario reducido para que el propio cliente solicite una reservacion
    desde su portal de autoservicio: no incluye el campo `cliente` (se
    asigna automaticamente al perfil del usuario autenticado en la vista).

    Metodo de pago:
      * Tarjeta: el cliente es enviado a la pagina segura de la pasarela de
        pago. El sistema NUNCA recibe numero de tarjeta ni CVV. La reservacion
        se confirma automaticamente cuando la pasarela aprueba el cobro.
      * Efectivo: queda PENDIENTE hasta que un empleado la confirme al
        recibir el pago en el local.
    """
    METODO_EFECTIVO = 'EFECTIVO'
    METODO_TARJETA = 'TARJETA'

    metodo_pago = forms.ChoiceField(
        choices=[
            (METODO_TARJETA, 'Tarjeta — pago seguro en línea (tu reserva se confirma al instante)'),
            (METODO_EFECTIVO, 'Efectivo — pago en el local (un empleado debe confirmar tu reserva)'),
        ],
        initial=METODO_TARJETA,
        widget=forms.RadioSelect,
        label='Método de pago',
    )

    class Meta:
        model = Reservacion
        fields = ['espacio', 'fecha_inicio', 'fecha_fin', 'observaciones']
        widgets = {
            'espacio': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'fecha_fin': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                                     'placeholder': 'Detalles adicionales (opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['espacio'].queryset = Espacio.objects.filter(
            activo=True, estado=Espacio.ESTADO_DISPONIBLE)
        self.fields['espacio'].empty_label = 'Selecciona una cancha o salón'

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get('fecha_inicio'), datos.get('fecha_fin')
        if inicio and fin:
            from django.utils import timezone
            if inicio < timezone.now():
                self.add_error('fecha_inicio', 'No puedes reservar en una fecha y hora que ya pasó.')
        return datos

    def save(self, commit=True):
        reservacion = super().save(commit=False)
        if reservacion.espacio_id:
            reservacion.precio_total = reservacion.espacio.precio_por_evento
        if commit:
            reservacion.full_clean()
            reservacion.save()
        return reservacion
