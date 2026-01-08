from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from .models import Student, Enrollment, StudentDocument
from .serializers import StudentSerializer, EnrollmentSerializer, StudentDocumentSerializer
from .filters import StudentFilter
from academics.models import Career
from django.db import transaction
from datetime import datetime
from .utils import generate_carnet_number, generate_contract
from users.permissions import HasPermission


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission('manage_students')]
    filterset_class = StudentFilter
    search_fields = ['carnet', 'first_name', 'last_name', 'email', 'career__name']
    ordering_fields = ['enrollment_date', 'first_name', 'last_name', 'carnet']
    ordering = ['-enrollment_date']
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            # Permitir ver a usuarios autenticados
            return [permissions.IsAuthenticated()]
        # Para crear/editar/eliminar requiere permiso específico
        return [permissions.IsAuthenticated(), HasPermission('manage_students')]
    
    def create(self, request, *args, **kwargs):
        """Crear estudiante y generar carnet automáticamente"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        career_id = request.data.get('career')
        if not career_id:
            return Response(
                {'error': 'career es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            career = Career.objects.get(id=career_id)
        except Career.DoesNotExist:
            return Response(
                {'error': 'Carrera no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with transaction.atomic():
            student = serializer.save()
            
            # Generar carnet usando función utilitaria
            year = datetime.now().year
            student.carnet = generate_carnet_number(career.code, year)
            student.save()
            
            # Crear inscripción automáticamente si no existe
            if not hasattr(student, 'enrollment'):
                Enrollment.objects.create(student=student, status='PENDIENTE')
        
        return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Obtener progreso académico del estudiante"""
        student = self.get_object()
        from academics.models import CourseEnrollment
        
        total_courses = student.career.courses.count()
        approved_courses = CourseEnrollment.objects.filter(
            student=student,
            status='APROBADO'
        ).count()
        
        return Response({
            'total_courses': total_courses,
            'approved_courses': approved_courses,
            'progress_percentage': (approved_courses / total_courses * 100) if total_courses > 0 else 0,
            'pensum_closed': student.pensum_closed,
            'thesis_started': student.thesis_started,
        })


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'generate_contract']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_students')]
    
    def get_queryset(self):
        """Permitir filtrar por estudiante"""
        queryset = Enrollment.objects.all()
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        return queryset
    
    @action(detail=True, methods=['get'])
    def generate_contract(self, request, pk=None):
        """Generar contrato PDF para la inscripción"""
        enrollment = self.get_object()
        
        if not enrollment.contract_generated:
            try:
                pdf_file = generate_contract(enrollment.student, enrollment)
                
                # Guardar el archivo
                filename = f"contrato_{enrollment.student.carnet}.pdf"
                enrollment.contract_file.save(filename, pdf_file, save=True)
                enrollment.contract_generated = True
                enrollment.save()
                
                # Retornar el PDF
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
            except Exception as e:
                return Response(
                    {'error': f'Error al generar contrato: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # Retornar contrato existente
            if enrollment.contract_file:
                enrollment.contract_file.seek(0)
                response = HttpResponse(
                    enrollment.contract_file.read(),
                    content_type='application/pdf'
                )
                response['Content-Disposition'] = f'attachment; filename="{enrollment.contract_file.name.split('/')[-1]}"'
                return response
        
        return Response(
            {'error': 'No se pudo generar el contrato'},
            status=status.HTTP_400_BAD_REQUEST
        )


class StudentDocumentViewSet(viewsets.ModelViewSet):
    queryset = StudentDocument.objects.all()
    serializer_class = StudentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_students')]
    
    @action(detail=True, methods=['post'])
    def upload_file(self, request, pk=None):
        """Subir archivo para un documento"""
        document = self.get_object()
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        document.file = file
        document.status = 'RECIBIDO'
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Actualizar estado de un documento"""
        document = self.get_object()
        
        new_status = request.data.get('status')
        if new_status not in dict(StudentDocument.STATUS_CHOICES):
            return Response(
                {'error': 'Estado inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        document.status = new_status
        if 'notes' in request.data:
            document.notes = request.data['notes']
        document.save()
        
        serializer = self.get_serializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)

