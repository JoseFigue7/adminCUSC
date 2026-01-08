from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import DocumentTemplate


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name_display', 'document_type_badge', 'template_file_link',
        'status_badge', 'updated_at'
    ]
    list_filter = ['document_type', 'is_active', 'created_at']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'template_preview']
    
    fieldsets = (
        ('Información de la Plantilla', {
            'fields': (
                'name',
                'document_type',
                'template_file',
                'is_active',
            ),
            'classes': ('wide',),
        }),
        ('Vista Previa', {
            'fields': ('template_preview',),
            'classes': ('collapse',),
        }),
        ('Información del Sistema', {
            'fields': (
                'id',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['activate_templates', 'deactivate_templates']
    
    def name_display(self, obj):
        """Nombre con link"""
        url = reverse('admin:documents_documenttemplate_change', args=[obj.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            url,
            obj.name
        )
    name_display.short_description = 'Nombre'
    name_display.admin_order_field = 'name'
    
    def document_type_badge(self, obj):
        """Badge para tipo de documento"""
        colors = {
            'CONTRACT': '#007bff',
            'CERTIFICATE': '#28a745',
            'TRANSCRIPT': '#17a2b8'
        }
        icons = {
            'CONTRACT': '📄',
            'CERTIFICATE': '📜',
            'TRANSCRIPT': '📋'
        }
        color = colors.get(obj.document_type, '#6c757d')
        icon = icons.get(obj.document_type, '📑')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_document_type_display()
        )
    document_type_badge.short_description = 'Tipo de Documento'
    document_type_badge.admin_order_field = 'document_type'
    
    def template_file_link(self, obj):
        """Link al archivo de plantilla"""
        if obj.template_file:
            return format_html(
                '<a href="{}" target="_blank">📄 Descargar plantilla</a>',
                obj.template_file.url
            )
        return format_html('<span style="color: #dc3545;">⚠ Sin archivo</span>')
    template_file_link.short_description = 'Archivo'
    
    def status_badge(self, obj):
        """Badge para estado"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✓ Activa</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✗ Inactiva</span>'
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'is_active'
    
    def template_preview(self, obj):
        """Vista previa del archivo"""
        if obj.template_file:
            file_size = obj.template_file.size
            size_kb = file_size / 1024
            return format_html(
                '<div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">'
                '<strong>Archivo:</strong> {}<br>'
                '<strong>Tamaño:</strong> {:.2f} KB<br>'
                '<a href="{}" target="_blank" style="margin-top: 10px; display: inline-block; padding: 5px 15px; background-color: #007bff; color: white; text-decoration: none; border-radius: 3px;">📥 Descargar</a>'
                '</div>',
                obj.template_file.name.split('/')[-1],
                size_kb,
                obj.template_file.url
            )
        return format_html('<span style="color: #999;">No hay archivo disponible</span>')
    template_preview.short_description = 'Vista Previa'
    
    # Actions
    def activate_templates(self, request, queryset):
        """Activar plantillas"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} plantilla(s) activada(s).')
    activate_templates.short_description = "Activar plantillas seleccionadas"
    
    def deactivate_templates(self, request, queryset):
        """Desactivar plantillas"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} plantilla(s) desactivada(s).')
    deactivate_templates.short_description = "Desactivar plantillas seleccionadas"
