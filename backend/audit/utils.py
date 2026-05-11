"""
Utilidades para el sistema de auditoría
"""
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
import json


def get_model_fields_snapshot(instance, exclude_fields=None):
    """
    Obtiene un snapshot de los campos de un modelo como diccionario JSON.
    
    Args:
        instance: Instancia del modelo
        exclude_fields: Lista de campos a excluir (por defecto: id, created_at, updated_at)
    
    Returns:
        dict: Diccionario con los campos y valores del modelo
    """
    if exclude_fields is None:
        exclude_fields = ['id', 'created_at', 'updated_at', 'password']
    
    snapshot = {}
    
    # Obtener campos del modelo
    for field in instance._meta.get_fields():
        field_name = field.name
        
        # Excluir campos especificados
        if field_name in exclude_fields:
            continue
        
        # Excluir relaciones inversas
        if field.one_to_many or field.many_to_many:
            continue
        
        try:
            value = getattr(instance, field_name, None)
            
            # Manejar ForeignKey
            if isinstance(field, models.ForeignKey):
                if value is not None:
                    snapshot[field_name] = str(value.id)
                    snapshot[f'{field_name}_str'] = str(value)
                else:
                    snapshot[field_name] = None
            # Manejar campos ManyToMany (solo IDs)
            elif isinstance(field, models.ManyToManyField):
                if hasattr(value, 'all'):
                    snapshot[field_name] = [str(v.id) for v in value.all()]
                else:
                    snapshot[field_name] = []
            # Manejar campos DateTime, Date, Time
            elif isinstance(field, (models.DateTimeField, models.DateField, models.TimeField)):
                snapshot[field_name] = value.isoformat() if value else None
            # Manejar campos Boolean
            elif isinstance(field, models.BooleanField):
                snapshot[field_name] = bool(value)
            # Manejar campos UUID
            elif isinstance(field, models.UUIDField):
                snapshot[field_name] = str(value) if value else None
            # Otros campos
            else:
                # Intentar serializar a JSON
                try:
                    json.dumps(value)
                    snapshot[field_name] = value
                except (TypeError, ValueError):
                    snapshot[field_name] = str(value)
        except Exception:
            # Si hay error al obtener el valor, omitir el campo
            pass
    
    return snapshot


def get_field_changes(old_instance, new_instance, exclude_fields=None):
    """
    Compara dos instancias y retorna los campos que cambiaron.
    
    Args:
        old_instance: Instancia anterior
        new_instance: Instancia nueva
        exclude_fields: Lista de campos a excluir
    
    Returns:
        dict: Diccionario con los cambios {campo: {'old': valor_anterior, 'new': valor_nuevo}}
    """
    if exclude_fields is None:
        exclude_fields = ['updated_at', 'last_login']
    
    changes = {}
    
    # Obtener snapshots de ambas instancias
    old_snapshot = get_model_fields_snapshot(old_instance, exclude_fields)
    new_snapshot = get_model_fields_snapshot(new_instance, exclude_fields)
    
    # Comparar campos
    all_fields = set(old_snapshot.keys()) | set(new_snapshot.keys())
    
    for field in all_fields:
        old_value = old_snapshot.get(field)
        new_value = new_snapshot.get(field)
        
        if old_value != new_value:
            changes[field] = {
                'old': old_value,
                'new': new_value
            }
    
    return changes


def get_request_info(request):
    """
    Extrae información del request para auditoría.
    
    Args:
        request: Objeto HttpRequest de Django
    
    Returns:
        dict: Diccionario con ip_address y user_agent
    """
    info = {}
    
    # IP Address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    info['ip_address'] = ip
    
    # User Agent
    info['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    return info


def is_audit_enabled():
    """
    Verifica si la auditoría está habilitada en la configuración.
    También verifica si la tabla de auditoría existe (para evitar errores durante migraciones).
    
    Returns:
        bool: True si la auditoría está habilitada y la tabla existe
    """
    if not getattr(settings, 'AUDIT_ENABLED', True):
        return False
    
    # Verificar si la tabla existe para evitar errores durante migraciones
    try:
        from django.db import connection
        table_name = 'audit_auditlog'
        # Usar introspection de Django para verificar si la tabla existe
        # Esto funciona con todos los backends
        with connection.cursor() as cursor:
            tables = connection.introspection.table_names(cursor)
            return table_name in tables
    except Exception:
        # Si hay algún error al verificar, deshabilitar la auditoría para ser seguro
        return False


def get_auditable_models():
    """
    Obtiene la lista de modelos auditables desde la configuración.
    
    Returns:
        list: Lista de nombres de modelos en formato 'app_label.ModelName'
    """
    auditable = getattr(settings, 'AUDIT_MODELS', None)
    
    if auditable is None:
        # Por defecto, auditar todos los modelos excepto el AuditLog mismo
        return None
    
    return auditable


def should_audit_model(model):
    """
    Determina si un modelo debe ser auditado.
    
    Args:
        model: Clase del modelo
    
    Returns:
        bool: True si el modelo debe ser auditado
    """
    if not is_audit_enabled():
        return False
    
    # No auditar el modelo AuditLog mismo
    if model.__name__ == 'AuditLog':
        return False
    
    # Sesiones: payload grande y sensible; además evita ruido y posibles fallos en logout
    if model._meta.label_lower == 'sessions.session':
        return False
    
    auditable_models = get_auditable_models()
    
    # Si no hay lista específica, auditar todos
    if auditable_models is None:
        return True
    
    # Verificar si el modelo está en la lista
    model_name = f"{model._meta.app_label}.{model.__name__}"
    return model_name in auditable_models
