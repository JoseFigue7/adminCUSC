from rest_framework import serializers
from django.core.exceptions import ValidationError
import re
from .models import (
    Student, Enrollment, StudentDocument,
    Pais, EntidadFederativa, Idioma, NecesidadEducativaEspecial,
    AntecedenteAcademico, NivelEducativo, ModalidadEducativa, Turno
)


# ==================== SERIALIZERS DE CATÁLOGOS ====================

class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = '__all__'


class EntidadFederativaSerializer(serializers.ModelSerializer):
    pais_nombre = serializers.CharField(source='pais.nombre', read_only=True)
    pais_codigo = serializers.CharField(source='pais.codigo', read_only=True)
    
    class Meta:
        model = EntidadFederativa
        fields = '__all__'


class IdiomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Idioma
        fields = '__all__'


class NecesidadEducativaEspecialSerializer(serializers.ModelSerializer):
    class Meta:
        model = NecesidadEducativaEspecial
        fields = '__all__'


class AntecedenteAcademicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AntecedenteAcademico
        fields = '__all__'


class NivelEducativoSerializer(serializers.ModelSerializer):
    class Meta:
        model = NivelEducativo
        fields = '__all__'


class ModalidadEducativaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModalidadEducativa
        fields = '__all__'


class TurnoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Turno
        fields = '__all__'


# ==================== SERIALIZERS DE ESTUDIANTES ====================

class StudentDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = StudentDocument
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    career_name = serializers.CharField(source='career.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    last_name = serializers.CharField(source='first_last_name', read_only=True)  # Compatibilidad
    documents = StudentDocumentSerializer(many=True, read_only=True)
    
    # Campos de catálogos (read-only para display)
    birth_country_name = serializers.CharField(source='birth_country.nombre', read_only=True)
    birth_state_name = serializers.CharField(source='birth_state.nombre', read_only=True)
    origin_country_name = serializers.CharField(source='origin_country.nombre', read_only=True)
    native_language_name = serializers.CharField(source='native_language.nombre', read_only=True)
    special_educational_need_name = serializers.CharField(source='special_educational_need.nombre', read_only=True)
    academic_background_name = serializers.CharField(source='academic_background.nombre', read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'
        extra_kwargs = {
            'curp': {'validators': []},  # Remover validación única en actualización, se maneja en clean()
            'email': {'validators': []},  # Remover validación única, se maneja en clean()
        }
    
    def validate_curp(self, value):
        """
        Validar formato CURP según el estándar mexicano.
        Formato esperado: 4 letras + 6 dígitos + H/M + 5 letras + 1 alfanumérico + 1 dígito
        Ejemplo: ABCD123456HHIJKLM01
        """
        import re
        if not value:
            return value
        
        value = value.strip().upper()
        
        # Verificar longitud
        if len(value) != 18:
            raise serializers.ValidationError(
                f"El CURP debe tener exactamente 18 caracteres. Se encontraron {len(value)} caracteres."
            )
        
        # Verificar formato completo
        if not re.match(r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d$', value):
            raise serializers.ValidationError(
                "Formato de CURP inválido. El formato correcto es: "
                "4 letras + 6 dígitos + H o M + 5 letras + 1 alfanumérico + 1 dígito. "
                "Ejemplo: ABCD123456HHIJKLM01"
            )
        
        return value
    
    def validate(self, attrs):
        """Validación a nivel de objeto completo"""
        # La validación de unicidad de CURP y email se hace en el modelo clean()
        # Aquí solo validamos relaciones y lógica de negocio adicional
        return attrs


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    student_id = serializers.UUIDField(source='student.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    enrollment_status_display = serializers.CharField(source='get_enrollment_status_display', read_only=True)
    career_name = serializers.CharField(source='career.name', read_only=True)
    contract_file_url = serializers.SerializerMethodField(read_only=True)
    contract_scanned_url = serializers.SerializerMethodField(read_only=True)
    
    # Campos de catálogos (read-only para display)
    educational_level_name = serializers.CharField(source='educational_level.nombre', read_only=True)
    shift_name = serializers.CharField(source='shift.nombre', read_only=True)
    educational_modality_name = serializers.CharField(source='educational_modality.nombre', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ['contract_generated', 'contract_uploaded_at', 'is_officially_enrolled']
    
    def get_contract_file_url(self, obj):
        """Obtener URL del contrato generado"""
        if obj.contract_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.contract_file.url)
            return obj.contract_file.url
        return None
    
    def get_contract_scanned_url(self, obj):
        """Obtener URL del contrato escaneado"""
        if obj.contract_scanned:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.contract_scanned.url)
            return obj.contract_scanned.url
        return None
    
    def validate_school_year(self, value):
        """Validar que el año sea razonable"""
        if value < 1900 or value > 9999:
            raise serializers.ValidationError("El año debe estar entre 1900 y 9999")
        return value
    
    def validate_rvoe_agreement_date(self, value):
        """Validar formato de fecha RVOE (aaaammdd)"""
        if value and len(value) != 8:
            raise serializers.ValidationError("La fecha debe tener 8 dígitos en formato aaaammdd")
        try:
            year = int(value[:4])
            month = int(value[4:6])
            day = int(value[6:8])
            if month < 1 or month > 12:
                raise serializers.ValidationError("El mes debe estar entre 01 y 12")
            if day < 1 or day > 31:
                raise serializers.ValidationError("El día debe estar entre 01 y 31")
        except (ValueError, IndexError):
            raise serializers.ValidationError("Formato de fecha inválido. Use formato aaaammdd")
        return value
    
    def validate(self, attrs):
        """Validación a nivel de objeto completo"""
        # Validar que la carrera del enrollment coincida con la del estudiante si ambas existen
        student = attrs.get('student') or (self.instance.student if self.instance else None)
        career = attrs.get('career') or (self.instance.career if self.instance else None)
        
        if student and career:
            if student.career != career:
                raise serializers.ValidationError({
                    'career': 'La carrera de la inscripción debe coincidir con la carrera del estudiante.'
                })
        
        return attrs

