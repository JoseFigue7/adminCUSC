from rest_framework import permissions


class IsSuperAdmin(permissions.BasePermission):
    """Permiso para super administradores"""
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role and
            request.user.role.name == 'SUPER_ADMIN'
        )


class IsAdminOrSelf(permissions.BasePermission):
    """Permiso para administradores o el mismo usuario"""
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin y admin pueden editar cualquier usuario
        if request.user.role and request.user.role.name in ['SUPER_ADMIN', 'ADMIN']:
            return True
        
        # Usuario puede editar su propio perfil
        return True
    
    def has_object_permission(self, request, view, obj):
        # Super admin y admin pueden editar cualquier usuario
        if request.user.role and request.user.role.name in ['SUPER_ADMIN', 'ADMIN']:
            return True
        
        # Usuario solo puede editar su propio perfil
        return obj == request.user


class HasPermission(permissions.BasePermission):
    """Permiso basado en permisos del rol"""
    
    def __init__(self, permission_name):
        self.permission_name = permission_name
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Super admin tiene todos los permisos
        if request.user.role and request.user.role.name == 'SUPER_ADMIN':
            return True
        
        return request.user.has_permission(self.permission_name)



