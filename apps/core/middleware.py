class BitacoraMiddleware:
    """
    Middleware ligero: unicamente resuelve y adjunta la IP real del cliente
    a cada request (considerando proxies/balanceadores), para que las
    vistas y señales que registran bitacora no dupliquen esa logica (DRY).
    No escribe en la base de datos en cada peticion para no saturar la
    tabla de auditoria; el registro puntual de acciones se hace mediante
    AuditoriaMixin y las señales de autenticacion.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.ip_cliente = self._obtener_ip(request)
        response = self.get_response(request)
        return response

    @staticmethod
    def _obtener_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
