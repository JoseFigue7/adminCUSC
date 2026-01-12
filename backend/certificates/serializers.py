from rest_framework import serializers
from .models import (
    RegistrationStatus, DocumentType, AcademicCertificate,
    CourseCertificate, UniversityTitle
)


class RegistrationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistrationStatus
        fields = '__all__'


class DocumentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentType
        fields = '__all__'


class AcademicCertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    student_id = serializers.UUIDField(source='student.id', read_only=True)
    student_curp = serializers.CharField(source='student.curp', read_only=True)
    registration_status_name = serializers.CharField(source='registration_status.nombre', read_only=True)
    document_type_name = serializers.CharField(source='document_type.nombre', read_only=True)
    issuance_date_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = AcademicCertificate
        fields = '__all__'
    
    def get_issuance_date_formatted(self, obj):
        """Formatear fecha de expedición a formato legible"""
        if obj.issuance_date and len(obj.issuance_date) == 8:
            try:
                year = obj.issuance_date[:4]
                month = obj.issuance_date[4:6]
                day = obj.issuance_date[6:8]
                return f"{day}/{month}/{year}"
            except:
                return obj.issuance_date
        return obj.issuance_date
    
    def validate_curp(self, value):
        """Validar formato de CURP"""
        if len(value) != 18:
            raise serializers.ValidationError("El CURP debe tener exactamente 18 caracteres")
        return value.upper()
    
    def validate_issuance_date(self, value):
        """Validar formato de fecha de expedición"""
        if len(value) != 8:
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
    
    def validate(self, data):
        """Validaciones adicionales"""
        # Validar que el promedio general sea obligatorio para certificados
        registration_status = data.get('registration_status')
        if registration_status:
            registration_status_name = registration_status.nombre.upper() if hasattr(registration_status, 'nombre') else ''
            if 'CERTIFICADO' in registration_status_name:
                general_average = data.get('general_average')
                if not general_average:
                    raise serializers.ValidationError({
                        'general_average': 'El promedio general es obligatorio para certificados.'
                    })
        
        # Validar que la CURP del estudiante coincida si se proporciona
        student = data.get('student')
        curp = data.get('curp')
        if student and curp and student.curp != curp:
            # Permitir que se pueda actualizar, pero mostrar advertencia
            pass
        
        return data


class CourseCertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    student_id = serializers.UUIDField(source='student.id', read_only=True)
    course_enrollments_count = serializers.IntegerField(source='course_enrollments.count', read_only=True)
    course_details = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseCertificate
        fields = '__all__'
        extra_kwargs = {
            'course_enrollments': {'required': False}
        }
    
    def get_course_details(self, obj):
        """Obtener detalles de los cursos incluidos"""
        from academics.serializers import CourseEnrollmentSerializer
        enrollments = obj.course_enrollments.filter(status='APROBADO') if obj.pk else []
        return CourseEnrollmentSerializer(enrollments, many=True).data if enrollments else []
    
    def validate_course_enrollments(self, value):
        """Validar que los cursos estén aprobados"""
        if value:
            not_approved = [e for e in value if e.status != 'APROBADO']
            if not_approved:
                raise serializers.ValidationError(
                    "Todos los cursos deben estar aprobados para incluirse en el certificado."
                )
        return value


class UniversityTitleSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    student_id = serializers.UUIDField(source='student.id', read_only=True)
    student_curp = serializers.CharField(source='student.curp', read_only=True)
    career_name = serializers.CharField(source='student.career.name', read_only=True)
    requirements_status = serializers.SerializerMethodField()
    
    class Meta:
        model = UniversityTitle
        fields = '__all__'
    
    def get_requirements_status(self, obj):
        """Obtener estado de los requisitos"""
        return {
            'pensum_completed': obj.pensum_completed,
            'all_courses_approved': obj.all_courses_approved,
            'thesis_approved': obj.thesis_approved,
            'requirements_met': obj.requirements_met,
            'can_print': obj.requirements_met and obj.student.pensum_closed
        }
    
    def validate(self, data):
        """Validar requisitos antes de crear o actualizar"""
        student = data.get('student') or (self.instance.student if self.instance else None)
        
        if student:
            # Verificar que el pensum esté cerrado
            if not student.pensum_closed:
                raise serializers.ValidationError({
                    'student': 'El estudiante debe tener el pensum cerrado para obtener un título universitario.'
                })
            
            # Verificar que no exista ya un título para este estudiante
            if not self.instance:
                if UniversityTitle.objects.filter(student=student).exists():
                    raise serializers.ValidationError({
                        'student': 'El estudiante ya tiene un título universitario registrado.'
                    })
        
        return data






