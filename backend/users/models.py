from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid


class Role(models.Model):
    """Modelo para roles de usuario"""
    
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Administrador'),
        ('ADMIN', 'Administrador'),
        ('SECRETARY', 'Secretario'),
        ('ACADEMIC_COORDINATOR', 'Coordinador Académico'),
        ('FINANCIAL', 'Financiero'),
        ('VIEWER', 'Consulta'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True, verbose_name='Nombre del rol')
    description = models.TextField(blank=True, verbose_name='Descripción')
    
    # Permisos
    can_manage_students = models.BooleanField(default=False, verbose_name='Puede gestionar estudiantes')
    can_manage_payments = models.BooleanField(default=False, verbose_name='Puede gestionar pagos')
    can_manage_academics = models.BooleanField(default=False, verbose_name='Puede gestionar académico')
    can_manage_scholarships = models.BooleanField(default=False, verbose_name='Puede gestionar becas')
    can_manage_thesis = models.BooleanField(default=False, verbose_name='Puede gestionar tesis')
    can_view_reports = models.BooleanField(default=False, verbose_name='Puede ver reportes')
    can_manage_users = models.BooleanField(default=False, verbose_name='Puede gestionar usuarios')
    can_manage_settings = models.BooleanField(default=False, verbose_name='Puede gestionar configuraciones')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        ordering = ['name']
    
    def __str__(self):
        return self.get_name_display()


class User(AbstractUser):
    """Modelo de usuario personalizado"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.PROTECT, null=True, blank=True, related_name='users', verbose_name='Rol')
    phone = models.CharField(max_length=15, blank=True, verbose_name='Teléfono')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='Último acceso')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} - {self.get_full_name() or self.email}"
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, permission_name):
        """Verificar si el usuario tiene un permiso específico"""
        if not self.role:
            return False
        
        permission_map = {
            'manage_students': self.role.can_manage_students,
            'manage_payments': self.role.can_manage_payments,
            'manage_academics': self.role.can_manage_academics,
            'manage_scholarships': self.role.can_manage_scholarships,
            'manage_thesis': self.role.can_manage_thesis,
            'view_reports': self.role.can_view_reports,
            'manage_users': self.role.can_manage_users,
            'manage_settings': self.role.can_manage_settings,
        }
        
        # Super admin tiene todos los permisos
        if self.role.name == 'SUPER_ADMIN':
            return True
        
        return permission_map.get(permission_name, False)




