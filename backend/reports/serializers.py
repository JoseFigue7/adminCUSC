from rest_framework import serializers
from django.db.models import Count, Sum, Avg, Q
from django.db.models.functions import TruncMonth
from students.models import Student
from payments.models import Payment, Scholarship
from academics.models import CourseEnrollment, Course, Career
from datetime import datetime


class StudentReportSerializer(serializers.Serializer):
    """Serializer para reporte de estudiantes"""
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    by_career = serializers.DictField(child=serializers.IntegerField())
    by_scholarship = serializers.DictField(child=serializers.IntegerField())


class PaymentReportSerializer(serializers.Serializer):
    """Serializer para reporte de pagos"""
    total = serializers.IntegerField()
    approved = serializers.IntegerField()
    pending = serializers.IntegerField()
    rejected = serializers.IntegerField()
    total_amount = serializers.FloatField()  # Cambiar a FloatField ya que se convierte a float en views
    by_month = serializers.DictField(child=serializers.FloatField())  # Cambiar a FloatField


class AcademicReportSerializer(serializers.Serializer):
    """Serializer para reporte académico"""
    total_enrollments = serializers.IntegerField()
    approved_courses = serializers.IntegerField()
    average_grade = serializers.FloatField()  # Cambiar a FloatField
    pensum_completion = serializers.FloatField()  # Cambiar a FloatField


class ScholarshipReportSerializer(serializers.Serializer):
    """Serializer para reporte de becas"""
    total = serializers.IntegerField()
    active = serializers.IntegerField()
    completa = serializers.IntegerField()
    media = serializers.IntegerField()


class OverviewReportSerializer(serializers.Serializer):
    """Serializer para reporte general consolidado"""
    students = StudentReportSerializer()
    payments = PaymentReportSerializer()
    academics = AcademicReportSerializer()
    scholarships = ScholarshipReportSerializer()
    date_range = serializers.DictField()


