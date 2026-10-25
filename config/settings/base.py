"""
Configuracion base del proyecto.
Sistema Automatizado de Gestion y Reservacion de Espacios Recreativos
y Salones de Eventos.
"""
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='inseguro-cambiar-en-produccion')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())
# URL del sistema (se usa en los enlaces de los correos y en el retorno del pago).
SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000').rstrip('/')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    # Apps del sistema
    'apps.core',
    'apps.autenticacion',
    'apps.usuarios',
    'apps.clientes',
    'apps.espacios',
    'apps.reservaciones',
    'apps.pagos',
    'apps.fidelizacion',
    'apps.reportes',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.BitacoraMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.datos_globales',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': config('DB_NAME', default='sistema_reservaciones'),
        'USER': config('DB_USER', default=''),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default=''),
        'OPTIONS': {
            'driver': config('DB_DRIVER', default='ODBC Driver 17 for SQL Server'),
            # Autenticacion de Windows (usuario/contraseña de Windows en vez de SQL Login).
            # Se activa automaticamente cuando DB_USER queda vacío en el .env.
            'trusted_connection': config('DB_TRUSTED_CONNECTION', default='yes' if not config('DB_USER', default='') else 'no'),
            'extra_params': 'TrustServerCertificate=yes;',
        },
    }
}

AUTH_USER_MODEL = 'usuarios.Usuario'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Guatemala'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Autenticacion
LOGIN_URL = 'autenticacion:login'
LOGIN_REDIRECT_URL = 'dashboard:inicio'
LOGOUT_REDIRECT_URL = 'autenticacion:login'

LOGIN_MAX_INTENTOS = config('LOGIN_MAX_INTENTOS', default=5, cast=int)
LOGIN_MINUTOS_BLOQUEO = config('LOGIN_MINUTOS_BLOQUEO', default=15, cast=int)

# Correo (recuperacion de contrasena)
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or 'no-reply@reservaciones.local'
EMAIL_TIMEOUT = 10
# Correos internos: aviso al personal cuando un cliente solicita una reservacion.
NOTIFICAR_PERSONAL = config('NOTIFICAR_PERSONAL', default=True, cast=bool)

# Seguridad
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600 * 8
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Fidelizacion (valores por defecto configurables desde la app Configuracion)
PUNTOS_POR_RESERVACION_CONFIRMADA = 10

# Pasarela de pago con tarjeta: pantalla de pago simulada (demostracion, no cobra dinero).
# El sistema no recibe ni guarda numeros de tarjeta.
PASARELA_PAGO = 'simulada'
# Minutos que se retiene el horario mientras el cliente completa el pago con tarjeta.
PAGO_MINUTOS_RETENCION = config('PAGO_MINUTOS_RETENCION', default=30, cast=int)
