from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView, PasswordChangeView,
    PasswordChangeDoneView,
)
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from apps.clientes.models import Cliente
from apps.core import notificaciones
from apps.core.models import Bitacora
from apps.usuarios.models import Rol
from .forms import (
    LoginForm, SolicitudRecuperacionForm, NuevaContrasenaForm, CambioContrasenaForm,
    RegistroClienteForm,
)

Usuario = get_user_model()


class LoginPersonalizadoView(LoginView):
    """
    Login con control de intentos fallidos y bloqueo temporal de cuenta,
    requisito explicito del sistema.
    """
    template_name = 'autenticacion/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        usuario = form.get_user()
        if usuario.esta_bloqueado:
            messages.error(
                self.request,
                'Tu cuenta está bloqueada temporalmente por múltiples intentos '
                'fallidos. Intenta de nuevo más tarde o recupera tu contraseña.'
            )
            return self.form_invalid(form)
        usuario.reiniciar_intentos()
        return super().form_valid(form)

    def get_success_url(self):
        usuario = self.request.user
        if usuario.rol and usuario.rol.clave == 'CLIENTE':
            return reverse_lazy('clientes:mi_cuenta')
        return super().get_success_url()

    def form_invalid(self, form):
        username = self.request.POST.get('username')
        usuario = Usuario.objects.filter(username=username).first()
        if usuario and not usuario.esta_bloqueado:
            usuario.registrar_intento_fallido(
                settings.LOGIN_MAX_INTENTOS, settings.LOGIN_MINUTOS_BLOQUEO
            )
            Bitacora.objects.create(
                usuario=usuario,
                accion=Bitacora.ACCION_LOGIN_FALLIDO,
                modulo='Autenticación',
                descripcion=f'Intento fallido de inicio de sesión ({usuario.intentos_fallidos})',
                ip=getattr(self.request, 'ip_cliente', None),
            )
            if usuario.esta_bloqueado:
                messages.error(
                    self.request,
                    'Se superó el número máximo de intentos. Tu cuenta fue '
                    f'bloqueada por {settings.LOGIN_MINUTOS_BLOQUEO} minutos.'
                )
        return super().form_invalid(form)


class LogoutPersonalizadoView(LogoutView):
    next_page = reverse_lazy('autenticacion:login')


class SolicitudRecuperacionView(PasswordResetView):
    template_name = 'autenticacion/recuperar_password.html'
    email_template_name = 'autenticacion/correo_recuperar_password.html'
    subject_template_name = 'autenticacion/correo_recuperar_asunto.txt'
    form_class = SolicitudRecuperacionForm
    success_url = reverse_lazy('autenticacion:recuperar_enviado')


class RecuperacionEnviadaView(PasswordResetDoneView):
    template_name = 'autenticacion/recuperar_enviado.html'


class RestablecerContrasenaView(PasswordResetConfirmView):
    template_name = 'autenticacion/restablecer_password.html'
    form_class = NuevaContrasenaForm
    success_url = reverse_lazy('autenticacion:restablecer_completo')


class RestablecimientoCompletoView(PasswordResetCompleteView):
    template_name = 'autenticacion/restablecer_completo.html'


class CambiarContrasenaView(PasswordChangeView):
    template_name = 'autenticacion/cambiar_password.html'
    form_class = CambioContrasenaForm
    success_url = reverse_lazy('autenticacion:cambiar_completo')


class CambioCompletoView(PasswordChangeDoneView):
    template_name = 'autenticacion/cambiar_completo.html'


class RegistroClienteView(View):
    """
    Registro público de autoservicio, exclusivo para clientes. El registro
    de personal interno (Recepción, Cajero, otro Administrador) NO se hace
    aquí: únicamente el Administrador puede crear esas cuentas desde el
    módulo Usuarios, otorgando el rol correspondiente.
    """
    template_name = 'autenticacion/registro.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:inicio')
        return render(request, self.template_name, {'form': RegistroClienteForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:inicio')
        form = RegistroClienteForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        datos = form.cleaned_data
        with transaction.atomic():
            rol_cliente, _ = Rol.objects.get_or_create(
                clave=Rol.CLAVE_CLIENTE,
                defaults={'nombre': 'Cliente'},
            )
            usuario = Usuario.objects.create_user(
                username=datos['username'],
                email=datos['correo'],
                password=datos['password2'],
                first_name=datos['nombres'],
                last_name=datos['apellidos'],
                telefono=datos['telefono'],
            )
            usuario.rol = rol_cliente
            usuario.save(update_fields=['rol'])

            cliente = Cliente.objects.create(
                usuario=usuario,
                nombres=datos['nombres'],
                apellidos=datos['apellidos'],
                dpi=datos['dpi'],
                telefono=datos['telefono'],
                direccion=datos['direccion'],
                correo=datos['correo'],
                foto=datos.get('foto'),
            )

        notificaciones.bienvenida_cliente(usuario, cliente)

        Bitacora.objects.create(
            usuario=usuario, accion=Bitacora.ACCION_CREAR, modulo='Registro de clientes',
            descripcion=f'Autorregistro de cliente: {usuario}',
            ip=getattr(request, 'ip_cliente', None),
        )

        login(request, usuario)
        messages.success(request, '¡Cuenta creada correctamente! Te enviamos un correo de confirmación.')
        return redirect('clientes:mi_cuenta')
