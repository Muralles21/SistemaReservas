from django import forms
from django.forms import inlineformset_factory

from .models import Espacio, EspacioFoto


class EspacioForm(forms.ModelForm):
    class Meta:
        model = Espacio
        fields = ['nombre', 'tipo', 'descripcion', 'precio_por_evento', 'capacidad',
                  'estado', 'foto_principal']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio_por_evento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'foto_principal': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


EspacioFotoFormSet = inlineformset_factory(
    Espacio, EspacioFoto, fields=['imagen'], extra=3, can_delete=True,
    widgets={'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'})}
)
