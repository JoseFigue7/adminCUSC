from rest_framework import serializers
from .models import Payment, Scholarship, PaymentConfiguration, PaymentType


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
    
    class Meta:
        model = Payment
        fields = '__all__'
    
    def get_total_amount(self, obj):
        """
        Retorna el monto total del pago.
        
        Prioriza final_amount (nuevo campo), pero mantiene compatibilidad
        con registros antiguos usando amount o base_amount + penalty_amount.
        """
        # Usar final_amount si está disponible (nuevo campo calculado)
        if obj.final_amount:
            return str(obj.final_amount)
        
        # Compatibilidad con registros antiguos
        if obj.base_amount:
            return str(obj.base_amount + obj.penalty_amount)
        
        # Fallback al campo amount (deprecated pero mantenido para compatibilidad)
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

