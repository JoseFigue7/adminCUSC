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
    
    def validate(self, data):
        """
        Validación personalizada para asegurar que amount tenga un valor
        si original_amount o final_amount están presentes
        """
        from decimal import Decimal
        
        # Asegurar que los campos Decimal sean Decimal, no float o string
        for field in ['amount', 'original_amount', 'final_amount', 'scholarship_discount_amount', 'penalty_amount']:
            if field in data and data[field] is not None:
                if not isinstance(data[field], Decimal):
                    try:
                        data[field] = Decimal(str(data[field]))
                    except (ValueError, TypeError):
                        pass
        
        # Si amount no está presente o es None/vacío, establecer basado en otros campos
        if 'amount' not in data or data.get('amount') is None or data.get('amount') == '':
            if 'final_amount' in data and data.get('final_amount') is not None:
                data['amount'] = data['final_amount']
            elif 'original_amount' in data and data.get('original_amount') is not None:
                data['amount'] = data['original_amount']
            else:
                # Si no hay ningún monto, establecer en 0
                data['amount'] = Decimal('0.00')
        
        # Asegurar que amount siempre tenga un valor válido (no None, no vacío)
        if 'amount' in data:
            if data['amount'] is None or data['amount'] == '':
                if 'final_amount' in data and data.get('final_amount') is not None:
                    data['amount'] = data['final_amount']
                elif 'original_amount' in data and data.get('original_amount') is not None:
                    data['amount'] = data['original_amount']
                else:
                    data['amount'] = Decimal('0.00')
        
        return data
    
    def create(self, validated_data):
        """
        Crear un pago asegurándonos de que amount tenga un valor
        """
        from decimal import Decimal
        
        # Asegurar que amount tenga un valor antes de crear
        if 'amount' not in validated_data or validated_data.get('amount') is None:
            if 'final_amount' in validated_data and validated_data.get('final_amount') is not None:
                validated_data['amount'] = validated_data['final_amount']
            elif 'original_amount' in validated_data and validated_data.get('original_amount') is not None:
                validated_data['amount'] = validated_data['original_amount']
            else:
                validated_data['amount'] = Decimal('0.00')
        
        # Convertir a Decimal si es necesario
        if 'amount' in validated_data and not isinstance(validated_data['amount'], Decimal):
            validated_data['amount'] = Decimal(str(validated_data['amount']))
        
        return super().create(validated_data)
    
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

