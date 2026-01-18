from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog, AuditAction
from .serializers import AuditLogSerializer, AuditLogListSerializer


class AuditLogFilter(django_filters.FilterSet):
    """Filtros para AuditLog"""
    
    action = django_filters.ChoiceFilter(choices=AuditAction.choices)
    model_name = django_filters.CharFilter(lookup_expr='icontains')
    username = django_filters.CharFilter(field_name='username', lookup_expr='icontains')
    date_from = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    date_to = django_filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    
    class Meta:
        model = AuditLog
        fields = ['action', 'model_name', 'username', 'user', 'ip_address']


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar registros de auditoría.
    Solo lectura - los registros no pueden ser creados, editados o eliminados via API.
    """
    
    queryset = AuditLog.objects.all().select_related('user', 'content_type')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AuditLogFilter
    search_fields = ['username', 'model_name', 'object_id', 'ip_address']
    ordering_fields = ['timestamp', 'action', 'model_name']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        """Usar serializer completo para detalle, simplificado para lista"""
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer
    
    def get_queryset(self):
        """Filtrar queryset según permisos del usuario"""
        queryset = super().get_queryset()
        
        # Solo usuarios con permisos de administrador pueden ver todos los registros
        if not (self.request.user.is_superuser or 
                hasattr(self.request.user, 'role') and 
                self.request.user.role and 
                self.request.user.role.name in ['SUPER_ADMIN', 'ADMIN']):
            # Otros usuarios solo ven sus propios registros
            queryset = queryset.filter(user=self.request.user)
        
        # Filtro opcional por modelo
        model_name = self.request.query_params.get('model_name', None)
        if model_name:
            queryset = queryset.filter(model_name__icontains=model_name)
        
        # Filtro opcional por rango de fechas (últimos 30 días por defecto)
        date_from = self.request.query_params.get('date_from', None)
        if not date_from:
            date_from = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(timestamp__gte=date_from)
        
        return queryset
