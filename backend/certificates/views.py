from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.template.loader import render_to_string
from config.weasyprint_lazy import get_html
import io
from datetime import datetime

from .models import (
    RegistrationStatus, DocumentType, AcademicCertificate,
    CourseCertificate, UniversityTitle
)
from .serializers import (
    RegistrationStatusSerializer, DocumentTypeSerializer,
    AcademicCertificateSerializer, CourseCertificateSerializer,
    UniversityTitleSerializer
)
from students.models import Student
from academics.models import CourseEnrollment
from users.permissions import HasPermission


class RegistrationStatusViewSet(viewsets.ModelViewSet):
    """ViewSet para catálogo de estatus de registro SEP"""
    queryset = RegistrationStatus.objects.filter(is_active=True)
    serializer_class = RegistrationStatusSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_certificates')]


class DocumentTypeViewSet(viewsets.ModelViewSet):
    """ViewSet para catálogo de tipos de documento SEP"""
    queryset = DocumentType.objects.filter(is_active=True)
    serializer_class = DocumentTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_certificates')]


class AcademicCertificateViewSet(viewsets.ModelViewSet):
    """ViewSet para certificados académicos SEP"""
    queryset = AcademicCertificate.objects.all()
    serializer_class = AcademicCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'print']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_certificates')]
    
    def get_queryset(self):
        """Permitir filtrar por estudiante"""
        queryset = AcademicCertificate.objects.select_related(
            'student', 'registration_status', 'document_type'
        ).all()
        
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def print(self, request, pk=None):
        """Generar PDF del certificado académico"""
        certificate = self.get_object()
        
        try:
            # Formatear fecha de expedición
            issuance_date = certificate.issuance_date
            if issuance_date and len(issuance_date) == 8:
                year = issuance_date[:4]
                month = issuance_date[4:6]
                day = issuance_date[6:8]
                months_es = {
                    '01': 'enero', '02': 'febrero', '03': 'marzo', '04': 'abril',
                    '05': 'mayo', '06': 'junio', '07': 'julio', '08': 'agosto',
                    '09': 'septiembre', '10': 'octubre', '11': 'noviembre', '12': 'diciembre'
                }
                issuance_date_formatted = f"{day} de {months_es.get(month, month)} de {year}"
            else:
                issuance_date_formatted = issuance_date
            
            context = {
                'certificate': certificate,
                'student': certificate.student,
                'issuance_date_formatted': issuance_date_formatted,
                'current_date': datetime.now().strftime('%d de %B de %Y')
            }
            
            html_string = render_to_string('certificates/academic_certificate.html', context)
            HTML = get_html()
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf_file = html.write_pdf()
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="certificado_academico_{certificate.student.carnet}_{certificate.school_year}.pdf"'
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Error al generar el PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Obtener certificados académicos de un estudiante"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificates = AcademicCertificate.objects.filter(student_id=student_id)
        serializer = self.get_serializer(certificates, many=True)
        return Response(serializer.data)


class CourseCertificateViewSet(viewsets.ModelViewSet):
    """ViewSet para certificados de cursos"""
    queryset = CourseCertificate.objects.all()
    serializer_class = CourseCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'print', 'by_student']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_certificates')]
    
    def get_queryset(self):
        """Permitir filtrar por estudiante"""
        queryset = CourseCertificate.objects.select_related('student').prefetch_related('course_enrollments').all()
        
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Crear certificado de cursos con validaciones"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        student_id = request.data.get('student')
        course_enrollment_ids = request.data.get('course_enrollments', [])
        
        if not student_id or not course_enrollment_ids:
            return Response(
                {'error': 'student y course_enrollments son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(id=student_id)
            enrollments = CourseEnrollment.objects.filter(
                id__in=course_enrollment_ids,
                student=student,
                status='APROBADO'
            )
            
            if enrollments.count() != len(course_enrollment_ids):
                return Response(
                    {'error': 'Algunos cursos no están aprobados o no pertenecen al estudiante'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            certificate = serializer.save(student=student)
            certificate.course_enrollments.set(enrollments)
            certificate.save()  # Para recalcular total_courses y average_grade
            
            serializer = self.get_serializer(certificate)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Student.DoesNotExist:
            return Response(
                {'error': 'Estudiante no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get'])
    def print(self, request, pk=None):
        """Generar PDF del certificado de cursos"""
        certificate = self.get_object()
        
        try:
            # Obtener detalles de los cursos
            enrollments = certificate.course_enrollments.filter(status='APROBADO').select_related('course')
            
            months_es = {
                1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
            }
            
            issuance_date = certificate.issuance_date
            issuance_date_formatted = f"{issuance_date.day} de {months_es.get(issuance_date.month, '')} de {issuance_date.year}"
            
            context = {
                'certificate': certificate,
                'student': certificate.student,
                'enrollments': enrollments,
                'issuance_date_formatted': issuance_date_formatted,
                'current_date': datetime.now().strftime('%d de %B de %Y')
            }
            
            html_string = render_to_string('certificates/course_certificate.html', context)
            HTML = get_html()
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf_file = html.write_pdf()
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="certificado_cursos_{certificate.student.carnet}_{certificate.id}.pdf"'
            
            # Marcar como impreso
            certificate.is_printed = True
            certificate.save()
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Error al generar el PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Obtener certificados de cursos de un estudiante"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        certificates = CourseCertificate.objects.filter(student_id=student_id)
        serializer = self.get_serializer(certificates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_from_approved_courses(self, request):
        """Crear certificado de cursos automáticamente con todos los cursos aprobados de un estudiante"""
        student_id = request.data.get('student_id')
        certificate_name = request.data.get('certificate_name', 'Certificado de Cursos Aprobados')
        
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(id=student_id)
            approved_enrollments = CourseEnrollment.objects.filter(
                student=student,
                status='APROBADO'
            ).select_related('course')
            
            if not approved_enrollments.exists():
                return Response(
                    {'error': 'El estudiante no tiene cursos aprobados'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calcular promedio
            grades = [e.final_grade for e in approved_enrollments if e.final_grade is not None]
            average = sum(grades) / len(grades) if grades else None
            
            certificate = CourseCertificate.objects.create(
                student=student,
                certificate_name=certificate_name,
                total_courses=approved_enrollments.count(),
                average_grade=average
            )
            certificate.course_enrollments.set(approved_enrollments)
            
            serializer = self.get_serializer(certificate)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Student.DoesNotExist:
            return Response(
                {'error': 'Estudiante no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )


class UniversityTitleViewSet(viewsets.ModelViewSet):
    """ViewSet para títulos universitarios"""
    queryset = UniversityTitle.objects.all()
    serializer_class = UniversityTitleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'validate_requirements', 'print']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_certificates')]
    
    def get_queryset(self):
        """Permitir filtrar por estudiante"""
        queryset = UniversityTitle.objects.select_related('student', 'academic_certificate').all()
        
        student_id = self.request.query_params.get('student_id')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def create_for_student(self, request):
        """Crear título universitario para un estudiante si cumple requisitos"""
        student_id = request.data.get('student_id')
        title_name = request.data.get('title_name')
        
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.select_related('career').get(id=student_id)
            
            # Verificar que el estudiante tenga el pensum cerrado
            if not student.pensum_closed:
                return Response(
                    {'error': 'El estudiante debe tener el pensum cerrado para obtener un título universitario'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar si ya existe un título
            if UniversityTitle.objects.filter(student=student).exists():
                return Response(
                    {'error': 'El estudiante ya tiene un título universitario registrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear título y validar requisitos
            title_name = title_name or f"Título de {student.career.name if student.career else 'Carrera'}"
            title = UniversityTitle.objects.create(
                student=student,
                title_name=title_name
            )
            
            # Validar requisitos
            requirements_met = title.validate_requirements()
            
            if not requirements_met:
                return Response(
                    {
                        'error': 'El estudiante no cumple con todos los requisitos para obtener el título',
                        'title': UniversityTitleSerializer(title).data
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = self.get_serializer(title)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Student.DoesNotExist:
            return Response(
                {'error': 'Estudiante no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def validate_requirements(self, request, pk=None):
        """Validar requisitos de un título universitario"""
        title = self.get_object()
        requirements_met = title.validate_requirements()
        
        serializer = self.get_serializer(title)
        return Response({
            'requirements_met': requirements_met,
            'title': serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def print(self, request, pk=None):
        """Generar PDF del título universitario"""
        title = self.get_object()
        
        # Verificar que los requisitos estén cumplidos
        if not title.requirements_met:
            return Response(
                {'error': 'Los requisitos no están cumplidos para imprimir el título'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Obtener información del estudiante y carrera
            student = title.student
            career = student.career
            
            # Obtener todos los cursos aprobados
            enrollments = CourseEnrollment.objects.filter(
                student=student,
                status='APROBADO'
            ).select_related('course').order_by('course__cuatrimestre__number', 'course__code')
            
            months_es = {
                1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
                5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
                9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
            }
            
            issuance_date = title.issuance_date or datetime.now().date()
            issuance_date_formatted = f"{issuance_date.day} de {months_es.get(issuance_date.month, '')} de {issuance_date.year}"
            
            context = {
                'title': title,
                'student': student,
                'career': career,
                'enrollments': enrollments,
                'issuance_date_formatted': issuance_date_formatted,
                'current_date': datetime.now().strftime('%d de %B de %Y')
            }
            
            html_string = render_to_string('certificates/university_title.html', context)
            HTML = get_html()
            html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
            pdf_file = html.write_pdf()
            
            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="titulo_universitario_{student.carnet}.pdf"'
            
            # Marcar como impreso y establecer fecha de expedición si no está establecida
            title.is_printed = True
            if not title.issuance_date:
                title.issuance_date = datetime.now().date()
            title.save()
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Error al generar el PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Obtener título universitario de un estudiante"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            title = UniversityTitle.objects.get(student_id=student_id)
            serializer = self.get_serializer(title)
            return Response(serializer.data)
        except UniversityTitle.DoesNotExist:
            return Response(
                {'error': 'El estudiante no tiene un título universitario registrado'},
                status=status.HTTP_404_NOT_FOUND
            )
