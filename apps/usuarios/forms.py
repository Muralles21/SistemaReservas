from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Rol, Usuario

CLASE_INPUT = 'form-control'
CLASE_SELECT = 'form-select'


class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['nombre', 'clave', 'descripcion', 'permisos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': CLASE_INPUT}),
            'clave': forms.Select(attrs={'class': CLASE_SELECT}),
            'descripcion': forms.Textarea(attrs={'class': CLASE_INPUT, 'rows': 3}),
            'permisos': forms.SelectMultiple(attrs={'class': CLASE_SELECT, 'size': 10}),
        }


class UsuarioCreacionForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono',
                  'rol', 'foto', 'is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre in ('is_active',):
                campo.widget.attrs['class'] = 'form-check-input'
            elif nombre == 'rol':
                campo.widget.attrs['class'] = CLASE_SELECT
            elif nombre == 'foto':
                campo.widget.attrs['class'] = 'form-control'
            else:
                campo.widget.attrs['class'] = CLASE_INPUT


class UsuarioEdicionForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'telefono',
                  'rol', 'foto', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': CLASE_INPUT}),
            'first_name': forms.TextInput(attrs={'class': CLASE_INPUT}),
            'last_name': forms.TextInput(attrs={'class': CLASE_INPUT}),
            'email': forms.EmailInput(attrs={'class': CLASE_INPUT}),
            'telefono': forms.TextInput(attrs={'class': CLASE_INPUT}),
            'rol': forms.Select(attrs={'class': CLASE_SELECT}),
            'foto': forms.ClearableFileInput(attrs={'class': CLASE_INPUT}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
