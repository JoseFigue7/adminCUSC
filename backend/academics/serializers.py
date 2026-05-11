from rest_framework import serializers
from .models import Career, Cuatrimestre, Course, CourseEnrollment, CuatrimestreEnrollment, GraduationMethod, CourseSchedule


class CourseScheduleSerializer(serializers.ModelSerializer):
    """Serializer para horarios de cursos"""
    
    class Meta:
        model = CourseSchedule
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    prerequisite_name = serializers.CharField(source='prerequisite.name', read_only=True)
    cuatrimestre_name = serializers.CharField(source='cuatrimestre.name', read_only=True)
    cuatrimestre_number = serializers.IntegerField(source='cuatrimestre.number', read_only=True)
    career_name = serializers.CharField(source='career.name', read_only=True)
    schedules = CourseScheduleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'


class CuatrimestreSerializer(serializers.ModelSerializer):
    courses = CourseSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cuatrimestre
        fields = '__all__'


class CareerSerializer(serializers.ModelSerializer):
    cuatrimestres = CuatrimestreSerializer(many=True, read_only=True)
    total_courses = serializers.IntegerField(source='courses.count', read_only=True)
    
    class Meta:
        model = Career
        fields = '__all__'
    
    def validate_institution_key(self, value):
        """Validar que la clave de institución tenga exactamente 10 caracteres"""
        if value and len(value) != 10:
            raise serializers.ValidationError("La clave de institución debe tener exactamente 10 caracteres")
        return value
    
    def validate_career_key(self, value):
        """Validar que la clave de carrera tenga exactamente 10 caracteres"""
        if value and len(value) != 10:
            raise serializers.ValidationError("La clave de carrera debe tener exactamente 10 caracteres")
        return value
    
    def validate_cct(self, value):
        """Validar que el CCT tenga exactamente 10 caracteres"""
        if value and len(value) != 10:
            raise serializers.ValidationError("El CCT debe tener exactamente 10 caracteres")
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
        except ValueError:
            raise serializers.ValidationError("La fecha debe contener solo dígitos")
        return value


class CuatrimestreEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    cuatrimestre_name = serializers.CharField(source='cuatrimestre.name', read_only=True)
    cuatrimestre_number = serializers.IntegerField(source='cuatrimestre.number', read_only=True)
    career_name = serializers.CharField(source='cuatrimestre.career.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    courses_count = serializers.SerializerMethodField()
    can_assign_courses = serializers.SerializerMethodField()
    can_confirm_assignment = serializers.SerializerMethodField()
    can_preview_boleta = serializers.SerializerMethodField()
    
    class Meta:
        model = CuatrimestreEnrollment
        fields = '__all__'
    
    def get_student_name(self, obj):
        """Obtener nombre completo del estudiante"""
        if obj.student:
            return obj.student.get_full_name()
        return ''
    
    def get_courses_count(self, obj):
        """Contar cursos inscritos en este cuatrimestre"""
        return obj.course_enrollments.count()
    
    def get_can_assign_courses(self, obj):
        """Verificar si se pueden asignar cursos"""
        return obj.can_assign_courses()
    
    def get_can_confirm_assignment(self, obj):
        """Verificar si se puede confirmar la asignación"""
        return obj.can_confirm_assignment()
    
    def get_can_preview_boleta(self, obj):
        """Verificar si se puede generar boleta de asignación"""
        return obj.can_preview_boleta()


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    student_carnet = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_id = serializers.CharField(source='course.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cuatrimestre = serializers.CharField(source='course.cuatrimestre.name', read_only=True)
    cuatrimestre_enrollment_academic_year = serializers.SerializerMethodField()
    cuatrimestre_enrollment_cuatrimestre = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseEnrollment
        fields = '__all__'
    
    def get_student_name(self, obj):
        """Obtener nombre completo del estudiante"""
        if obj.student:
            return obj.student.get_full_name()
        return ''
    
    def get_student_carnet(self, obj):
        """Obtener carnet del estudiante"""
        if obj.student:
            return obj.student.carnet or ''
        return ''
    
    def get_cuatrimestre_enrollment_academic_year(self, obj):
        """Obtener año académico de la inscripción al cuatrimestre"""
        if obj.cuatrimestre_enrollment:
            return obj.cuatrimestre_enrollment.academic_year
        return None
    
    def get_cuatrimestre_enrollment_cuatrimestre(self, obj):
        """Obtener nombre del cuatrimestre de la inscripción"""
        if obj.cuatrimestre_enrollment and obj.cuatrimestre_enrollment.cuatrimestre:
            return obj.cuatrimestre_enrollment.cuatrimestre.name
        return None


class GraduationMethodSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    student_id = serializers.CharField(source='student.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    method_type_display = serializers.CharField(source='get_method_type_display', read_only=True)
    
    class Meta:
        model = GraduationMethod
        fields = '__all__'


class GradeUploadItemSerializer(serializers.Serializer):
    """Serializer para un item individual de carga de notas
    
    Acepta dos formatos:
    1. Con IDs: student_id, course_id, final_grade
    2. Con carnet y código: student_carnet, course_code, final_grade (opcionalmente con career_code, cuatrimestre_number, academic_year)
    """
    # Formato con IDs (formato original)
    student_id = serializers.UUIDField(required=False, allow_null=True)
    course_id = serializers.UUIDField(required=False, allow_null=True)
    
    # Formato con carnet y código (más fácil de usar)
    student_carnet = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    course_code = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    # Campos opcionales para formato completo
    career_code = serializers.IntegerField(required=False, allow_null=True)
    cuatrimestre_number = serializers.IntegerField(required=False, allow_null=True)
    academic_year = serializers.IntegerField(required=False, allow_null=True)
    
    final_grade = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=True,
        min_value=0,
        max_value=100
    )
    
    def validate(self, data):
        """Validar que se proporcione uno de los dos formatos"""
        # Verificar formato con IDs
        student_id = data.get('student_id')
        course_id = data.get('course_id')
        has_id_format = student_id is not None and course_id is not None
        
        # Verificar formato con carnet y código
        student_carnet = data.get('student_carnet')
        course_code = data.get('course_code')
        has_carnet_format = student_carnet and student_carnet.strip() and course_code and course_code.strip()
        
        if not has_id_format and not has_carnet_format:
            raise serializers.ValidationError(
                "Debe proporcionar (student_id y course_id) o (student_carnet y course_code)"
            )
        
        if has_id_format and has_carnet_format:
            raise serializers.ValidationError(
                "No puede proporcionar ambos formatos a la vez. Use (student_id y course_id) o (student_carnet y course_code)"
            )
        
        return data


class BulkGradeUploadSerializer(serializers.Serializer):
    """Serializer para carga masiva de notas"""
    grades = GradeUploadItemSerializer(many=True, required=True)
    
    def validate_grades(self, value):
        """Validar que haya al menos una nota"""
        if not value:
            raise serializers.ValidationError("Debe proporcionar al menos una nota")
        return value
