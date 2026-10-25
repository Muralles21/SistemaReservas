from django import forms
from .models import Premio, ConfiguracionFidelizacion


class PremioForm(forms.ModelForm):
    class Meta:
        model = Premio
        fields = ['nombre', 'descripcion', 'costo_puntos', 'stock', 'foto']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'costo_puntos': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class ConfiguracionFidelizacionForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionFidelizacion
        fields = ['puntos_por_reservacion', 'monto_por_punto_extra', 'dias_expiracion_puntos']
        widgets = {
            'puntos_por_reservacion': forms.NumberInput(attrs={'class': 'form-control'}),
            'monto_por_punto_extra': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'dias_expiracion_puntos': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class CanjeForm(forms.Form):
    premio = forms.ModelChoiceField(
        queryset=Premio.objects.filter(activo=True, stock__gt=0),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
