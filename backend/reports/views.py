from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Count, Sum, Avg, Q, F, DecimalField
from django.db.models.functions import TruncMonth, ExtractYear, ExtractMonth
from django.utils import timezone
from django.http import HttpResponse
from django.conf import settings
import csv
from datetime import datetime, timedelta
from decimal import Decimal

from students.models import Student
from payments.models import Payment, Scholarship
from academics.models import CourseEnrollment, Course, Career
from .serializers import (
    StudentReportSerializer, PaymentReportSerializer,
    AcademicReportSerializer, ScholarshipReportSerializer,
    OverviewReportSerializer
)
from users.permissions import HasPermission


class ReportsViewSet(viewsets.ViewSet):
    """ViewSet para generar reportes consolidados"""
    
    def get_permissions(self):
        """Permisos específicos por acción - más permisivo durante desarrollo"""
        # Temporalmente más permisivo - solo requiere autenticación
        # TODO: Restaurar permiso específico en producción
        # return [permissions.IsAuthenticated(), HasPermission('view_reports')]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['get'], url_path='overview')
    def overview(self, request):
        """
        Reporte general consolidado con todas las estadísticas
        Permite filtrar por rango de fechas
        """
        # Obtener parámetros de filtro
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parsear fechas o usar valores por defecto
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        else:
            # Por defecto, año actual
            start_date = datetime.now().replace(month=1, day=1).date()
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        else:
            end_date = timezone.now().date()
        
        # Obtener reportes individuales
        student_data = self._get_student_report(start_date, end_date)
        payment_data = self._get_payment_report(start_date, end_date)
        academic_data = self._get_academic_report(start_date, end_date)
        scholarship_data = self._get_scholarship_report(start_date, end_date)
        
        # Consolidar respuesta
        report_data = {
            'students': student_data,
            'payments': payment_data,
            'academics': academic_data,
            'scholarships': scholarship_data,
            'date_range': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None,
            }
        }
        
        # Devolver datos directamente (el serializador es opcional para validación)
        # En este caso, los datos ya están estructurados correctamente
        return Response(report_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='students')
    def students_report(self, request):
        """Reporte detallado de estudiantes"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        else:
            start_date = datetime.now().replace(month=1, day=1).date()
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        else:
            end_date = timezone.now().date()
        
        data = self._get_student_report(start_date, end_date)
        serializer = StudentReportSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='payments')
    def payments_report(self, request):
        """Reporte detallado de pagos"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        else:
            start_date = datetime.now().replace(month=1, day=1).date()
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        else:
            end_date = timezone.now().date()
        
        data = self._get_payment_report(start_date, end_date)
        serializer = PaymentReportSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='academics')
    def academics_report(self, request):
        """Reporte detallado académico"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        else:
            start_date = datetime.now().replace(month=1, day=1).date()
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        else:
            end_date = timezone.now().date()
        
        data = self._get_academic_report(start_date, end_date)
        serializer = AcademicReportSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='scholarships')
    def scholarships_report(self, request):
        """Reporte detallado de becas"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        else:
            start_date = datetime.now().replace(month=1, day=1).date()
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        else:
            end_date = timezone.now().date()
        
        data = self._get_scholarship_report(start_date, end_date)
        serializer = ScholarshipReportSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='export/students')
    def export_students_csv(self, request):
        """Exportar reporte de estudiantes a CSV"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        else:
            start_date = datetime.now().replace(month=1, day=1).date()
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        else:
            end_date = timezone.now().date()
        
        students_qs = Student.objects.all()
        if start_date and end_date:
            students_qs = students_qs.filter(enrollment_date__gte=start_date, enrollment_date__lte=end_date)
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="estudiantes_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Carnet', 'Nombre Completo', 'Email', 'Carrera', 'Fecha Inscripción', 'Activo', 'Tipo Beca'])
        
        for student in students_qs:
            writer.writerow([
                student.carnet or '',
                student.get_full_name(),
                student.email,
                student.career.name if student.career else '',
                student.enrollment_date.strftime('%Y-%m-%d'),
                'Sí' if student.is_active else 'No',
                student.get_scholarship_type_display(),
            ])
        
        return response

    @action(detail=False, methods=['get'], url_path='export/payments')
    def export_payments_csv(self, request):
        """Exportar reporte de pagos a CSV"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = None
        else:
            start_date = datetime.now().replace(month=1, day=1).date()
        
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = None
        else:
            end_date = timezone.now().date()
        
        payments_qs = Payment.objects.select_related('student', 'payment_type').all()
        if start_date and end_date:
            payments_qs = payments_qs.filter(payment_date__gte=start_date, payment_date__lte=end_date)
        
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="pagos_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Estudiante', 'Tipo Pago', 'Monto', 'Mes', 'Año', 'Estado', 'Fecha Pago', 'Método Pago'])
        
        for payment in payments_qs:
            writer.writerow([
                payment.student.get_full_name(),
                payment.payment_type.name if payment.payment_type else '',
                str(payment.amount),
                payment.get_month_display() if payment.month else '',
                str(payment.year) if payment.year else '',
                payment.get_status_display(),
                payment.payment_date.strftime('%Y-%m-%d'),
                payment.get_payment_method_display(),
            ])
        
        return response

    def _get_student_report(self, start_date, end_date):
        """Generar datos de reporte de estudiantes"""
        # Base queryset de estudiantes
        students_qs = Student.objects.all()
        
        # Filtrar por fecha de inscripción si se especifica (más relevante que created_at)
        if start_date and end_date:
            students_qs = students_qs.filter(enrollment_date__gte=start_date, enrollment_date__lte=end_date)
        
        total = students_qs.count()
        active = students_qs.filter(is_active=True).count()
        
        # Estudiantes por carrera
        students_by_career = {}
        career_data = students_qs.values('career__name').annotate(count=Count('id'))
        for item in career_data:
            career_name = item['career__name'] or 'Sin carrera'
            students_by_career[career_name] = item['count']
        
        # Estudiantes por tipo de beca
        students_by_scholarship = {}
        scholarship_data = students_qs.values('scholarship_type').annotate(count=Count('id'))
        for item in scholarship_data:
            scholarship_type = item['scholarship_type'] or 'NINGUNA'
            students_by_scholarship[scholarship_type] = item['count']
        
        return {
            'total': total,
            'active': active,
            'by_career': students_by_career,
            'by_scholarship': students_by_scholarship,
        }

    def _get_payment_report(self, start_date, end_date):
        """Generar datos de reporte de pagos"""
        payments_qs = Payment.objects.all()
        
        # Filtrar por rango de fechas
        if start_date and end_date:
            payments_qs = payments_qs.filter(
                Q(payment_date__gte=start_date) & Q(payment_date__lte=end_date)
            )
        
        total = payments_qs.count()
        approved = payments_qs.filter(status='APROBADO').count()
        pending = payments_qs.filter(status__in=['PENDIENTE', 'EN_REVISION']).count()
        rejected = payments_qs.filter(status='RECHAZADO').count()
        
        # Monto total de pagos aprobados
        total_amount = payments_qs.filter(status='APROBADO').aggregate(
            total=Sum('amount', output_field=DecimalField(max_digits=12, decimal_places=2))
        )['total'] or Decimal('0.00')
        
        # Pagos por mes
        payments_by_month = {}
        approved_payments = payments_qs.filter(status='APROBADO')
        
        if start_date and end_date:
            # Agrupar por año-mes usando payment_date
            monthly_data = approved_payments.filter(
                Q(payment_date__gte=start_date) & Q(payment_date__lte=end_date)
            ).annotate(
                year_extracted=ExtractYear('payment_date'),
                month_extracted=ExtractMonth('payment_date')
            ).values('year_extracted', 'month_extracted').annotate(
                total_amount=Sum('amount', output_field=DecimalField(max_digits=12, decimal_places=2))
            ).order_by('year_extracted', 'month_extracted')
            
            for item in monthly_data:
                month_key = f"{item['year_extracted']}-{str(item['month_extracted']).zfill(2)}"
                payments_by_month[month_key] = float(item['total_amount'] or Decimal('0.00'))
        else:
            # Usar mes y año del modelo si están disponibles
            monthly_data = approved_payments.exclude(year__isnull=True, month__isnull=True).values(
                'year', 'month'
            ).annotate(
                total_amount=Sum('amount', output_field=DecimalField(max_digits=12, decimal_places=2))
            ).order_by('year', 'month')
            
            for item in monthly_data:
                month_key = f"{item['year']}-{str(item['month']).zfill(2)}"
                payments_by_month[month_key] = float(item['total_amount'] or Decimal('0.00'))
        
        return {
            'total': total,
            'approved': approved,
            'pending': pending,
            'rejected': rejected,
            'total_amount': float(total_amount),
            'by_month': payments_by_month,
        }

    def _get_academic_report(self, start_date, end_date):
        """Generar datos de reporte académico"""
        enrollments_qs = CourseEnrollment.objects.all()
        
        # Filtrar por rango de fechas
        if start_date and end_date:
            enrollments_qs = enrollments_qs.filter(
                Q(enrollment_date__gte=start_date) & Q(enrollment_date__lte=end_date)
            )
        
        total_enrollments = enrollments_qs.count()
        approved_courses = enrollments_qs.filter(status='APROBADO').count()
        
        # Promedio de calificaciones
        avg_data = enrollments_qs.filter(
            status='APROBADO',
            final_grade__isnull=False
        ).aggregate(avg_grade=Avg('final_grade'))
        
        average_grade = float(avg_data['avg_grade'] or Decimal('0.00'))
        
        # Completitud del pensum (cursos aprobados / total de cursos por carrera)
        # Calcular el total de cursos por carrera
        total_students = Student.objects.filter(is_active=True).count()
        total_courses_by_career = {}
        
        careers = Career.objects.all()
        for career in careers:
            total_courses = Course.objects.filter(career=career).count()
            if total_courses > 0:
                total_courses_by_career[career.id] = total_courses
        
        # Calcular completitud
        if total_students > 0 and total_courses_by_career:
            total_possible_courses = sum(total_courses_by_career.values()) * total_students
            if total_possible_courses > 0:
                pensum_completion = (approved_courses / total_possible_courses) * 100
            else:
                pensum_completion = Decimal('0.00')
        else:
            pensum_completion = Decimal('0.00')
        
        pensum_completion = min(float(pensum_completion), 100.0)
        
        return {
            'total_enrollments': total_enrollments,
            'approved_courses': approved_courses,
            'average_grade': average_grade,
            'pensum_completion': pensum_completion,
        }

    def _get_scholarship_report(self, start_date, end_date):
        """Generar datos de reporte de becas"""
        scholarships_qs = Scholarship.objects.all()
        
        # Filtrar por fecha de inicio si se especifica
        if start_date and end_date:
            scholarships_qs = scholarships_qs.filter(
                Q(start_date__gte=start_date) & Q(start_date__lte=end_date)
            )
        
        total = scholarships_qs.count()
        active = scholarships_qs.filter(status='ACTIVA').count()
        completa = scholarships_qs.filter(
            status='ACTIVA',
            scholarship_type='COMPLETA'
        ).count()
        media = scholarships_qs.filter(
            status='ACTIVA',
            scholarship_type='MEDIA'
        ).count()
        
        return {
            'total': total,
            'active': active,
            'completa': completa,
            'media': media,
        }
