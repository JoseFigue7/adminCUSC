from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = [
        'name_display', 'description_short', 'permissions_summary', 
        'users_count', 'created_at'
    ]
    list_filter = ['name']
    search_fields = ['name', 'description']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description'),
            'classes': ('wide',),
        }),
        ('Permisos de Gestión', {
            'fields': (
                ('can_manage_students', 'can_manage_payments'),
                ('can_manage_academics', 'can_manage_scholarships'),
                ('can_manage_thesis', 'can_view_reports'),
                ('can_manage_users', 'can_manage_settings'),
            ),
            'classes': ('wide',),
        }),
        ('Información del Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def name_display(self, obj):
        """Muestra el nombre del rol con estilo"""
        icons = {
            'SUPER_ADMIN': '👑',
            'ADMIN': '🔑',
            'SECRETARY': '📋',
            'ACADEMIC_COORDINATOR': '🎓',
            'FINANCIAL': '💰',
            'VIEWER': '👁️',
        }
        icon = icons.get(obj.name, '👤')
        return format_html(
            '<strong style="font-size: 14px;">{} {}</strong>',
            icon,
            obj.get_name_display()
        )
    name_display.short_description = 'Rol'
    name_display.admin_order_field = 'name'
    
    def description_short(self, obj):
        """Descripción corta"""
        if obj.description:
            return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
        return '-'
    description_short.short_description = 'Descripción'
    
    def permissions_summary(self, obj):
        """Resumen de permisos"""
        permissions = []
        if obj.can_manage_students:
            permissions.append('Estudiantes')
        if obj.can_manage_payments:
            permissions.append('Pagos')
        if obj.can_manage_academics:
            permissions.append('Académico')
        if obj.can_manage_scholarships:
            permissions.append('Becas')
        if obj.can_manage_thesis:
            permissions.append('Tesis')
        if obj.can_view_reports:
            permissions.append('Reportes')
        if obj.can_manage_users:
            permissions.append('Usuarios')
        if obj.can_manage_settings:
            permissions.append('Configuración')
        
        if permissions:
            return format_html(
                '<span style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
                ', '.join(permissions[:3]) + ('...' if len(permissions) > 3 else '')
            )
        return format_html('<span style="color: #999;">Sin permisos</span>')
    permissions_summary.short_description = 'Permisos'
    
    def users_count(self, obj):
        """Cuenta de usuarios con este rol"""
        count = obj.users.count()
        url = f"{reverse('admin:users_user_changelist')}?role__id__exact={obj.id}"
        return format_html(
            '<a href="{}">{} usuario(s)</a>',
            url,
            count
        )
    users_count.short_description = 'Usuarios'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'email', 'full_name_display', 'role_badge', 
        'status_badge', 'last_login_display', 'date_joined'
    ]
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'phone'),
            'classes': ('wide',),
        }),
        ('Información del Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Información Adicional', {
            'fields': ('role', 'phone', 'email', 'first_name', 'last_name'),
            'classes': ('wide',),
        }),
    )
    
    actions = ['make_staff', 'remove_staff', 'activate_users', 'deactivate_users']
    
    def full_name_display(self, obj):
        """Muestra nombre completo"""
        full_name = obj.get_full_name()
        if full_name and full_name != obj.username:
            return format_html(
                '<strong>{}</strong>',
                full_name
            )
        return '-'
    full_name_display.short_description = 'Nombre Completo'
    full_name_display.admin_order_field = 'first_name'
    
    def role_badge(self, obj):
        """Badge para el rol"""
        if obj.role:
            colors = {
                'SUPER_ADMIN': '#6f42c1',
                'ADMIN': '#007bff',
                'SECRETARY': '#28a745',
                'ACADEMIC_COORDINATOR': '#17a2b8',
                'FINANCIAL': '#ffc107',
                'VIEWER': '#6c757d'
            }
            color = colors.get(obj.role.name, '#6c757d')
            url = reverse('admin:users_role_change', args=[obj.role.pk])
            return format_html(
                '<a href="{}"><span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; text-decoration: none;">{}</span></a>',
                url,
                color,
                obj.role.get_name_display()
            )
        return format_html('<span style="color: #999;">Sin rol</span>')
    role_badge.short_description = 'Rol'
    role_badge.admin_order_field = 'role__name'
    
    def status_badge(self, obj):
        """Badge para estado del usuario"""
        badges = []
        
        if obj.is_active:
            badges.append(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; margin-right: 4px;">✓ Activo</span>'
            )
        else:
            badges.append(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; margin-right: 4px;">✗ Inactivo</span>'
            )
        
        if obj.is_staff:
            badges.append(
                '<span style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px; margin-right: 4px;">👤 Staff</span>'
            )
        
        if obj.is_superuser:
            badges.append(
                '<span style="background-color: #6f42c1; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">👑 Super</span>'
            )
        
        return format_html(''.join(badges))
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'is_active'
    
    def last_login_display(self, obj):
        """Muestra último acceso"""
        if obj.last_login:
            return format_html(
                '<span style="color: #28a745;">{}</span>',
                obj.last_login.strftime('%d/%m/%Y %H:%M')
            )
        return format_html('<span style="color: #999;">Nunca</span>')
    last_login_display.short_description = 'Último Acceso'
    last_login_display.admin_order_field = 'last_login'
    
    # Actions
    def make_staff(self, request, queryset):
        """Dar permisos de staff"""
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'{updated} usuario(s) ahora tienen permisos de staff.')
    make_staff.short_description = "Dar permisos de staff"
    
    def remove_staff(self, request, queryset):
        """Quitar permisos de staff"""
        updated = queryset.update(is_staff=False)
        # No quitar superuser automáticamente
        self.message_user(request, f'{updated} usuario(s) ya no tienen permisos de staff.')
    remove_staff.short_description = "Quitar permisos de staff"
    
    def activate_users(self, request, queryset):
        """Activar usuarios"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} usuario(s) activado(s).')
    activate_users.short_description = "Activar usuarios"
    
    def deactivate_users(self, request, queryset):
        """Desactivar usuarios"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} usuario(s) desactivado(s).')
    deactivate_users.short_description = "Desactivar usuarios"
