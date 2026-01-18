"""
Middleware para capturar información del request y registrar acciones HTTP.
"""
from django.utils.deprecation import MiddlewareMixin
from audit.signals import set_current_request
from audit.utils import is_audit_enabled


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware para establecer el request actual en thread-local storage.
    Esto permite que las señales accedan al request y usuario actual.
    """
    
    def process_request(self, request):
        """Establece el request actual antes de procesar la petición"""
        if is_audit_enabled():
            set_current_request(request)
        return None
    
    def process_response(self, request, response):
        """Limpia el request del thread-local storage después de la respuesta"""
        if is_audit_enabled():
            # Limpiar el request
            set_current_request(None)
        return response
    
    def process_exception(self, request, exception):
        """Limpia el request en caso de excepción"""
        if is_audit_enabled():
            set_current_request(None)
        return None
