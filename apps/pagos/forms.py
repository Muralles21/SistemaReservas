from django import forms
from .models import Pago


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['tipo', 'monto', 'metodo_pago', 'estado', 'referencia']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'referencia': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, reservacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.reservacion = reservacion

    def clean_monto(self):
        monto = self.cleaned_data['monto']
        if self.reservacion and monto > self.reservacion.saldo_pendiente:
            raise forms.ValidationError(
                f'El monto excede el saldo pendiente (Q{self.reservacion.saldo_pendiente}).')
        return monto
