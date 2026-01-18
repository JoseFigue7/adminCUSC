"""
Señales para capturar cambios en modelos y registrar en auditoría.
"""
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.utils.functional import SimpleLazyObject
from audit.models import AuditLog, AuditAction
from audit.utils import (
    get_model_fields_snapshot,
    get_field_changes,
    should_audit_model,
    is_audit_enabled
)
import threading

# Thread-local storage para mantener el request actual
_thread_locals = threading.local()


def set_current_request(request):
    """Establece el request actual en el thread-local storage"""
    _thread_locals.request = request


def get_current_request():
    """Obtiene el request actual del thread-local storage"""
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    """Obtiene el usuario actual del request"""
    request = get_current_request()
    if request and hasattr(request, 'user'):
        user = request.user
        if isinstance(user, SimpleLazyObject):
            user = user._wrapped
        if hasattr(user, 'is_authenticated') and user.is_authenticated:
            return user
    return None


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """
    Captura el estado anterior antes de guardar.
    Guarda los datos anteriores en _audit_old_data para uso en post_save.
    """
    if not is_audit_enabled():
        return
    
    if not should_audit_model(sender):
        return
    
    # Si la instancia ya existe, obtener los datos anteriores
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._audit_old_data = get_model_fields_snapshot(old_instance)
            instance._audit_old_instance = old_instance
        except ObjectDoesNotExist:
            instance._audit_old_data = None
            instance._audit_old_instance = None
    else:
        instance._audit_old_data = None
        instance._audit_old_instance = None


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """
    Registra acciones CREATE y UPDATE en el log de auditoría.
    """
    if not is_audit_enabled():
        return
    
    if not should_audit_model(sender):
        return
    
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
    
    # Determinar acción
    action = AuditAction.CREATE if created else AuditAction.UPDATE
    
    # Obtener ContentType
    content_type = ContentType.objects.get_for_model(sender)
    model_name = f"{content_type.app_label}.{content_type.model}"
    
    # Obtener snapshot de datos actuales
    data_snapshot = get_model_fields_snapshot(instance)
    
    # Para UPDATE, calcular cambios
    previous_data = {}
    changes = {}
    
    if not created and hasattr(instance, '_audit_old_instance'):
        old_instance = getattr(instance, '_audit_old_instance', None)
        if old_instance:
            previous_data = get_model_fields_snapshot(old_instance)
            changes = get_field_changes(old_instance, instance)
    
    # Crear registro de auditoría
    try:
        AuditLog.objects.create(
            user=user,
            username=user.username if user else None,
            action=action,
            content_type=content_type,
            object_id=str(instance.pk),
            model_name=model_name,
            data_snapshot=data_snapshot,
            previous_data=previous_data,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=getattr(instance, '_audit_metadata', {})
        )
    except Exception as e:
        # En producción, podrías querer registrar este error en logs
        # Por ahora, solo ignoramos el error para no afectar el flujo principal
        pass


@receiver(pre_delete)
def audit_pre_delete(sender, instance, **kwargs):
    """
    Captura el estado antes de eliminar.
    Guarda los datos en _audit_deleted_data para uso en post_delete.
    """
    if not is_audit_enabled():
        return
    
    if not should_audit_model(sender):
        return
    
    # Guardar snapshot antes de eliminar
    instance._audit_deleted_data = get_model_fields_snapshot(instance)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """
    Registra acciones DELETE en el log de auditoría.
    """
    if not is_audit_enabled():
        return
    
    if not should_audit_model(sender):
        return
    
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
    content_type = ContentType.objects.get_for_model(sender)
    model_name = f"{content_type.app_label}.{content_type.model}"
    
    # Obtener snapshot de datos (guardado en pre_delete)
    data_snapshot = getattr(instance, '_audit_deleted_data', {})
    
    # Crear registro de auditoría
    try:
        AuditLog.objects.create(
            user=user,
            username=user.username if user else None,
            action=AuditAction.DELETE,
            content_type=content_type,
            object_id=str(instance.pk),
            model_name=model_name,
            data_snapshot=data_snapshot,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=getattr(instance, '_audit_metadata', {})
        )
    except Exception as e:
        # En producción, podrías querer registrar este error en logs
        pass
