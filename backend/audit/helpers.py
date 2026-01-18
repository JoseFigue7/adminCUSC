"""
Funciones helper para registrar acciones personalizadas de auditoría (APPROVE, REJECT, etc.)
"""
from django.contrib.contenttypes.models import ContentType
from audit.models import AuditLog, AuditAction
from audit.signals import get_current_user, get_current_request
from audit.utils import get_model_fields_snapshot, is_audit_enabled


def log_audit_action(instance, action, metadata=None):
    """
    Función helper para registrar acciones personalizadas de auditoría.
    
    Uso:
        from audit.helpers import log_audit_action
        from audit.models import AuditAction
        
        payment = Payment.objects.get(pk=pk)
        payment.status = 'APPROVED'
        payment.save()
        
        log_audit_action(
            instance=payment,
            action=AuditAction.APPROVE,
            metadata={'comment': 'Pago aprobado por coordinador financiero'}
        )
    
    Args:
        instance: Instancia del modelo a auditar
        action: AuditAction (APPROVE, REJECT, etc.)
        metadata: Diccionario con información adicional (opcional)
    
    Returns:
        AuditLog: Instancia creada o None si falló
    """
    if not is_audit_enabled():
        return None
    
    # Obtener usuario actual
    user = get_current_user()
    
    # Obtener información del request
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
    
    # Obtener ContentType
    content_type = ContentType.objects.get_for_model(instance.__class__)
    model_name = f"{content_type.app_label}.{content_type.model}"
    
    # Obtener snapshot de datos
    data_snapshot = get_model_fields_snapshot(instance)
    
    # Crear registro de auditoría
    try:
        audit_log = AuditLog.objects.create(
            user=user,
            username=user.username if user else None,
            action=action,
            content_type=content_type,
            object_id=str(instance.pk),
            model_name=model_name,
            data_snapshot=data_snapshot,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        return audit_log
    except Exception as e:
        # En producción, podrías querer registrar este error en logs
        # Por ahora, solo retornamos None para no afectar el flujo principal
        return None
