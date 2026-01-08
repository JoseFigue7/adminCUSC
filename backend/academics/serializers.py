from rest_framework import serializers
from .models import Career, Cuatrimestre, Course, CourseEnrollment, Thesis


class CourseSerializer(serializers.ModelSerializer):
    prerequisite_name = serializers.CharField(source='prerequisite.name', read_only=True)
    cuatrimestre_name = serializers.CharField(source='cuatrimestre.name', read_only=True)
    career_name = serializers.CharField(source='career.name', read_only=True)
    
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


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    course_name = serializers.CharField(source='course.name', read_only=True)
    course_code = serializers.CharField(source='course.code', read_only=True)
    course_id = serializers.CharField(source='course.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cuatrimestre = serializers.CharField(source='course.cuatrimestre.name', read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = '__all__'


class ThesisSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    student_id = serializers.CharField(source='student.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Thesis
        fields = '__all__'

