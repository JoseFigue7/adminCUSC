"""
Decoradores para registrar acciones personalizadas de auditoría (APPROVE, REJECT, etc.)
"""
from functools import wraps
from django.contrib.contenttypes.models import ContentType
from audit.models import AuditLog, AuditAction
from audit.signals import get_current_user, get_current_request
from audit.utils import get_model_fields_snapshot, is_audit_enabled
import threading


def audit_action(action, model_class=None, object_id_param='pk'):
    """
    Decorador para registrar acciones personalizadas de auditoría (APPROVE, REJECT, etc.)
    
    Uso:
        @audit_action(AuditAction.APPROVE)
        def approve_payment(request, pk):
            payment = Payment.objects.get(pk=pk)
            payment.status = 'APPROVED'
            payment.save()
            return Response(...)
    
    Args:
        action: AuditAction (APPROVE, REJECT, etc.)
        model_class: Clase del modelo (opcional, se infiere del objeto)
        object_id_param: Nombre del parámetro que contiene el ID del objeto
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Ejecutar la función original
            result = func(*args, **kwargs)
            
            if not is_audit_enabled():
                return result
            
            # Obtener el ID del objeto desde kwargs
            object_id = kwargs.get(object_id_param)
            
            if not object_id and args:
                # Intentar obtener del primer argumento si es un objeto
                first_arg = args[0]
                if hasattr(first_arg, 'pk'):
                    object_id = first_arg.pk
                elif isinstance(first_arg, dict) and object_id_param in first_arg:
                    object_id = first_arg[object_id_param]
            
            # Si no hay object_id, intentar inferirlo del resultado
            if not object_id and hasattr(result, 'data'):
                # Si es una respuesta de DRF, intentar obtener el objeto
                try:
                    data = result.data
                    if isinstance(data, dict) and 'id' in data:
                        object_id = data['id']
                except:
                    pass
            
            # Obtener usuario y request
            user = get_current_user()
            request = get_current_request()
            
            ip_address = None
            user_agent = None
            
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(',')[0]
                else:
                    ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Intentar obtener el modelo si no se proporcionó
            model = model_class
            instance = None
            
            if model and object_id:
                try:
                    instance = model.objects.get(pk=object_id)
                except:
                    pass
            
            # Si hay instancia, registrar auditoría
            if instance:
                content_type = ContentType.objects.get_for_model(instance.__class__)
                model_name = f"{content_type.app_label}.{content_type.model}"
                data_snapshot = get_model_fields_snapshot(instance)
                
                try:
                    AuditLog.objects.create(
                        user=user,
                        username=user.username if user else None,
                        action=action,
                        content_type=content_type,
                        object_id=str(object_id),
                        model_name=model_name,
                        data_snapshot=data_snapshot,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata={
                            'function': func.__name__,
                            'decorator': 'audit_action'
                        }
                    )
                except Exception:
                    # No afectar el flujo principal si falla la auditoría
                    pass
            
            return result
        
        return wrapper
    return decorator
