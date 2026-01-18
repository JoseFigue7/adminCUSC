from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import AuditLog, AuditAction
import json


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Administración para el modelo AuditLog"""
    
    list_display = [
        'timestamp',
        'user_link',
        'action_badge',
        'model_name',
        'object_link',
        'ip_address'
    ]
    
    list_filter = [
        'action',
        'timestamp',
        'model_name',
        ('user', admin.RelatedOnlyFieldListFilter),
    ]
    
    search_fields = [
        'username',
        'model_name',
        'object_id',
        'ip_address',
        'user__username',
        'user__email'
    ]
    
    readonly_fields = [
        'id',
        'user',
        'username',
        'action',
        'content_type',
        'object_id',
        'model_name',
        'data_snapshot_formatted',
        'previous_data_formatted',
        'changes_formatted',
        'ip_address',
        'user_agent',
        'metadata_formatted',
        'timestamp',
        'object_repr'
    ]
    
    fieldsets = (
        ('Información General', {
            'fields': ('id', 'timestamp', 'user', 'username', 'action')
        }),
        ('Objeto Afectado', {
            'fields': ('content_type', 'model_name', 'object_id', 'object_repr')
        }),
        ('Datos', {
            'fields': (
                'data_snapshot_formatted',
                'previous_data_formatted',
                'changes_formatted'
            ),
            'classes': ('collapse',)
        }),
        ('Contexto', {
            'fields': ('ip_address', 'user_agent', 'metadata_formatted'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'timestamp'
    
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        """No permitir crear registros manualmente"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Permitir eliminar solo a super admins"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """No permitir editar registros de auditoría"""
        return False
    
    def user_link(self, obj):
        """Muestra un enlace al usuario"""
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.username or obj.user.username)
        return obj.username or 'Sistema'
    user_link.short_description = 'Usuario'
    
    def action_badge(self, obj):
        """Muestra la acción con un badge de color"""
        colors = {
            AuditAction.CREATE: 'green',
            AuditAction.UPDATE: 'blue',
            AuditAction.DELETE: 'red',
            AuditAction.APPROVE: 'green',
            AuditAction.REJECT: 'orange',
            AuditAction.VIEW: 'gray',
            AuditAction.EXPORT: 'purple',
        }
        color = colors.get(obj.action, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Acción'
    
    def object_link(self, obj):
        """Muestra un enlace al objeto si aún existe"""
        try:
            obj_instance = obj.content_object
            admin_url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', admin_url, str(obj_instance)[:50])
        except Exception:
            return f"{obj.model_name} (ID: {obj.object_id})"
    object_link.short_description = 'Objeto'
    
    def object_repr(self, obj):
        """Representación del objeto"""
        return obj.get_object_repr()
    object_repr.short_description = 'Representación del objeto'
    
    def data_snapshot_formatted(self, obj):
        """Muestra el snapshot de datos formateado"""
        if not obj.data_snapshot:
            return 'Sin datos'
        return format_html(
            '<pre style="max-height: 400px; overflow-y: auto;">{}</pre>',
            json.dumps(obj.data_snapshot, indent=2, ensure_ascii=False)
        )
    data_snapshot_formatted.short_description = 'Snapshot de Datos'
    
    def previous_data_formatted(self, obj):
        """Muestra los datos anteriores formateados"""
        if not obj.previous_data:
            return 'Sin datos anteriores'
        return format_html(
            '<pre style="max-height: 400px; overflow-y: auto;">{}</pre>',
            json.dumps(obj.previous_data, indent=2, ensure_ascii=False)
        )
    previous_data_formatted.short_description = 'Datos Anteriores'
    
    def changes_formatted(self, obj):
        """Muestra los cambios formateados"""
        if not obj.changes:
            return 'Sin cambios'
        return format_html(
            '<pre style="max-height: 400px; overflow-y: auto;">{}</pre>',
            json.dumps(obj.changes, indent=2, ensure_ascii=False)
        )
    changes_formatted.short_description = 'Cambios Realizados'
    
    def metadata_formatted(self, obj):
        """Muestra los metadatos formateados"""
        if not obj.metadata:
            return 'Sin metadatos'
        return format_html(
            '<pre style="max-height: 200px; overflow-y: auto;">{}</pre>',
            json.dumps(obj.metadata, indent=2, ensure_ascii=False)
        )
    metadata_formatted.short_description = 'Metadatos'
