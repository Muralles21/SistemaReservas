def _fondo_modulo(match):
    """
    Devuelve la clave del fondo fotografico segun el modulo (app) y la vista
    actuales. Cada clave corresponde a static/img/fondos/<clave>.jpg y a una
    clase body.fondo-<clave> definida en static/css/estilos.css.
    """
    if not match:
        return 'portal'
    app, nombre = match.app_name, match.url_name
    if app == 'autenticacion':
        return 'registro' if nombre == 'registro' else 'auth'
    if app == 'clientes' and nombre == 'mi_cuenta':
        return 'portal'
    if app == 'pagos' and nombre in ('retorno', 'cancelado', 'simulada'):
        return 'portal'
    if app == 'reservaciones':
        if nombre == 'calendario':
            return 'calendario'
        return 'portal' if nombre == 'solicitar' else 'reservaciones'
    return {
        'dashboard': 'dashboard', 'clientes': 'clientes', 'espacios': 'espacios',
        'pagos': 'pagos', 'fidelizacion': 'fidelizacion', 'reportes': 'reportes',
        'usuarios': 'usuarios', 'core': 'portal',
    }.get(app, 'dashboard')


def datos_globales(request):
    """
    Expone datos comunes a todos los templates (nombre del sistema,
    modulo activo por URL y fondo del modulo) sin tener que pasarlos
    manualmente en cada vista (DRY).
    """
    match = request.resolver_match
    return {
        'NOMBRE_SISTEMA': 'EventSpace',
        'ruta_actual': match.url_name if match else '',
        'app_actual': match.app_name if match else '',
        'fondo_modulo': _fondo_modulo(match),
    }
