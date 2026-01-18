from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer para el modelo AuditLog"""
    
    user_username = serializers.CharField(source='username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True, allow_null=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    object_repr = serializers.CharField(source='get_object_repr', read_only=True)
    formatted_changes = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'user_username',
            'user_email',
            'action',
            'action_display',
            'model_name',
            'object_id',
            'object_repr',
            'data_snapshot',
            'previous_data',
            'changes',
            'formatted_changes',
            'ip_address',
            'user_agent',
            'metadata',
            'timestamp'
        ]
        read_only_fields = fields
    
    def get_formatted_changes(self, obj):
        """Retorna los cambios en formato legible"""
        return obj.get_formatted_changes()


class AuditLogListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de AuditLog"""
    
    user_username = serializers.CharField(source='username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    object_repr = serializers.CharField(source='get_object_repr', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user_username',
            'action',
            'action_display',
            'model_name',
            'object_id',
            'object_repr',
            'timestamp'
        ]
