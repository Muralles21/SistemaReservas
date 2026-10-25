from .base import *  # noqa

DEBUG = True
# El backend de correo se toma del .env (EMAIL_BACKEND). Si no lo defines, los
# correos se imprimen en la terminal (modo consola). Para enviarlos de verdad:
#   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
