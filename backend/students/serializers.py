from rest_framework import serializers
from .models import Student, Enrollment, StudentDocument


class StudentDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = StudentDocument
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    career_name = serializers.CharField(source='career.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    documents = StudentDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Student
        fields = '__all__'


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_carnet = serializers.CharField(source='student.carnet', read_only=True)
    student_id = serializers.UUIDField(source='student.id', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = '__all__'

