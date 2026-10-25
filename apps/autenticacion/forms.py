from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from django.core.exceptions import ValidationError

from apps.clientes.models import Cliente, validador_dpi, validador_telefono

Usuario = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Usuario', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Contraseña'}))


class SolicitudRecuperacionForm(PasswordResetForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'form-control', 'placeholder': 'Correo electrónico'}))


class NuevaContrasenaForm(SetPasswordForm):
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class CambioContrasenaForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class RegistroClienteForm(forms.Form):
    """
    Registro público de autoservicio: crea, en una sola operación, la cuenta
    de acceso (Usuario con rol Cliente) y el perfil de Cliente asociado.
    Los roles de personal (Administrador, Recepción, Cajero) NO se otorgan
    aquí: solo el administrador puede asignarlos desde el módulo Usuarios.
    """
    nombres = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    apellidos = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    dpi = forms.CharField(max_length=13, validators=[validador_dpi],
                           widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '13 dígitos'}))
    telefono = forms.CharField(max_length=8, validators=[validador_telefono],
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '8 dígitos'}))
    direccion = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    correo = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    foto = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))

    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean_username(self):
        username = self.cleaned_data['username']
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError('Ese nombre de usuario ya está en uso.')
        return username

    def clean_dpi(self):
        dpi = self.cleaned_data['dpi']
        if Cliente.objects.filter(dpi=dpi).exists():
            raise ValidationError('Ya existe un cliente registrado con ese DPI.')
        return dpi

    def clean_correo(self):
        correo = self.cleaned_data['correo']
        if Cliente.objects.filter(correo=correo).exists() or Usuario.objects.filter(email=correo).exists():
            raise ValidationError('Ya existe una cuenta registrada con ese correo.')
        return correo

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('Las contraseñas no coinciden.')
        if p2:
            password_validation.validate_password(p2)
        return p2
