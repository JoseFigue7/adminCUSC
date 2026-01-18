from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings
import json
import uuid


class AuditAction(models.TextChoices):
    """Acciones auditables en el sistema"""
    CREATE = 'CREATE', 'Crear'
    UPDATE = 'UPDATE', 'Actualizar'
    DELETE = 'DELETE', 'Eliminar'
    APPROVE = 'APPROVE', 'Aprobar'
    REJECT = 'REJECT', 'Rechazar'
    VIEW = 'VIEW', 'Consultar'
    EXPORT = 'EXPORT', 'Exportar'


class AuditLog(models.Model):
    """
    Modelo para registro de auditoría completo del sistema.
    
    Registra todas las acciones realizadas en el sistema incluyendo:
    - Usuario que realizó la acción
    - Tipo de acción (CREATE, UPDATE, DELETE, APPROVE, REJECT)
    - Modelo y registro afectado
    - Fecha y hora
    - Snapshot de los datos (JSON)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Usuario que realizó la acción
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuario',
        help_text='Usuario que realizó la acción'
    )
    
    # Información del usuario (para casos donde se elimina el usuario)
    username = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name='Nombre de usuario',
        help_text='Nombre de usuario al momento de la acción'
    )
    
    # Acción realizada
    action = models.CharField(
        max_length=20,
        choices=AuditAction.choices,
        verbose_name='Acción',
        help_text='Tipo de acción realizada'
    )
    
    # Modelo afectado usando ContentType para ser genérico
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name='Tipo de contenido',
        help_text='Modelo afectado'
    )
    
    # ID del registro afectado
    object_id = models.TextField(
        verbose_name='ID del objeto',
        help_text='ID del registro afectado'
    )
    
    # Relación genérica al objeto
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Nombre del modelo (cached para búsquedas más rápidas)
    model_name = models.CharField(
        max_length=255,
        verbose_name='Nombre del modelo',
        help_text='Nombre del modelo afectado (app_label.ModelName)'
    )
    
    # Snapshot de datos (JSON)
    data_snapshot = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Snapshot de datos',
        help_text='Datos del registro al momento de la acción (JSON)'
    )
    
    # Datos anteriores (para UPDATE)
    previous_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Datos anteriores',
        help_text='Datos anteriores del registro (para acciones UPDATE)'
    )
    
    # Cambios realizados (para UPDATE)
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Cambios',
        help_text='Campos modificados y sus valores anteriores/nuevos'
    )
    
    # Información adicional de contexto
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Dirección IP',
        help_text='IP desde donde se realizó la acción'
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent',
        help_text='Navegador o cliente utilizado'
    )
    
    # Información adicional (metadatos)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Metadatos',
        help_text='Información adicional de contexto (comentarios, razones, etc.)'
    )
    
    # Fecha y hora
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha y hora',
        help_text='Fecha y hora de la acción'
    )
    
    class Meta:
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['model_name', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        user_str = self.username or self.user.username if self.user else 'Sistema'
        return f"{user_str} - {self.get_action_display()} - {self.model_name} ({self.object_id})"
    
    def get_object_repr(self):
        """Obtiene la representación del objeto si aún existe"""
        try:
            obj = self.content_object
            return str(obj)
        except Exception:
            return f"{self.model_name} (ID: {self.object_id})"
    
    def get_formatted_changes(self):
        """Retorna los cambios en formato legible"""
        if not self.changes:
            return {}
        
        formatted = {}
        for field, values in self.changes.items():
            formatted[field] = {
                'anterior': values.get('old'),
                'nuevo': values.get('new')
            }
        return formatted
