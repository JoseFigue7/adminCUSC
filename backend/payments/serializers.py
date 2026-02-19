import uuid as uuid_module
from rest_framework import serializers
from .models import Payment, Scholarship, PaymentConfiguration, PaymentType


class PaymentTypePrimaryKeyField(serializers.Field):
    """
    Acepta UUID del tipo de pago, o código (ej. "100"), o formato "code - name"
    para evitar ValidationError cuando el frontend envía el nombre en lugar del ID.
    """
    def to_internal_value(self, data):
        if data is None or data == '':
            return None
        s = str(data).strip()
        # Intentar como UUID
        try:
            uuid_module.UUID(s)
            pt = PaymentType.objects.filter(id=s).first()
            if pt:
                return pt.id
        except (ValueError, TypeError):
            pass
        # Intentar como código o "code - name" (ej. "100 - Inscripción al Cuatrimestre - Gratis")
        code = s.split(' - ')[0].strip() if ' - ' in s else s
        pt = PaymentType.objects.filter(code=code, is_active=True).first()
        if pt:
            return pt.id
        raise serializers.ValidationError(
            f'Tipo de pago no encontrado para "{data}". Use el ID (UUID) o el código del tipo de pago.'
        )

    def to_representation(self, value):
        if value is None:
            return None
        return str(value.id) if hasattr(value, 'id') else str(value)


class PaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    month_display = serializers.CharField(source='get_month_display', read_only=True)
    payment_type_name = serializers.CharField(source='payment_type.name', read_only=True)
    payment_type_code = serializers.CharField(source='payment_type.code', read_only=True)
    total_amount = serializers.SerializerMethodField()
    
    # Información de trazabilidad
    career_name = serializers.CharField(source='career.name', read_only=True)
    career_code = serializers.CharField(source='career.code', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    payment_type = PaymentTypePrimaryKeyField(allow_null=True, required=False)

    class Meta:
        model = Payment
        fields = '__all__'
    
    def update(self, instance, validated_data):
        # Remover status de validated_data si está presente
        # El modelo se encargará de establecer el status correcto automáticamente en save()
        # según las reglas de negocio (aprobación automática para pagos sin cuatrimestre_enrollment)
        validated_data.pop('status', None)
        return super().update(instance, validated_data)
    
    def get_total_amount(self, obj):
        """Retorna el monto total (base + mora)"""
        if obj.base_amount:
            return str(obj.base_amount + obj.penalty_amount)
        return str(obj.amount)


class ScholarshipSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    student_id = serializers.CharField(source='student.id', read_only=True)
    career_name = serializers.CharField(source='student.career.name', read_only=True)
    scholarship_type_display = serializers.CharField(source='get_scholarship_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Scholarship
        fields = '__all__'


class PaymentConfigurationSerializer(serializers.ModelSerializer):
    career_name = serializers.CharField(source='career.name', read_only=True)
    
    class Meta:
        model = PaymentConfiguration
        fields = '__all__'


class PaymentTypeSerializer(serializers.ModelSerializer):
    penalty_type_display = serializers.CharField(source='get_penalty_type_display', read_only=True)
    
    class Meta:
        model = PaymentType
        fields = '__all__'


class PublicPaymentSerializer(serializers.Serializer):
    """Serializer para pagos públicos (sin autenticación)"""
    carnet = serializers.CharField(max_length=9)
    payment_type = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    month = serializers.IntegerField(required=False, allow_null=True)
    year = serializers.IntegerField(required=False, allow_null=True)
    semester = serializers.IntegerField(required=False, allow_null=True)
    quantity = serializers.IntegerField(required=False, allow_null=True)
    card_token = serializers.CharField(required=False)  # Token de tarjeta para procesamiento

