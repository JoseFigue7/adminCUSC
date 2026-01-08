from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Career, Cuatrimestre, Course, CourseEnrollment, Thesis
from .serializers import (
    CareerSerializer, CuatrimestreSerializer, CourseSerializer,
    CourseEnrollmentSerializer, ThesisSerializer
)
from students.models import Student
from users.permissions import HasPermission


class CareerViewSet(viewsets.ModelViewSet):
    queryset = Career.objects.filter(is_active=True)
    serializer_class = CareerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'pensum']:
            # Permitir ver a usuarios autenticados
            return [permissions.IsAuthenticated()]
        # Para crear/editar/eliminar requiere permiso específico
        return [permissions.IsAuthenticated(), HasPermission('manage_academics')]
    
    @action(detail=True, methods=['get'])
    def pensum(self, request, pk=None):
        """Obtener pensum completo de una carrera"""
        career = self.get_object()
        courses = Course.objects.filter(career=career).select_related('cuatrimestre', 'prerequisite')
        serializer = CourseSerializer(courses, many=True)
        return Response({
            'career': {
                'id': str(career.id),
                'name': career.name,
                'code': career.code
            },
            'courses': serializer.data
        })


class CuatrimestreViewSet(viewsets.ModelViewSet):
    queryset = Cuatrimestre.objects.all()
    serializer_class = CuatrimestreSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission('manage_academics')]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_academics')]
    
    def get_queryset(self):
        """Permitir filtrar por carrera"""
        queryset = Course.objects.select_related('career', 'cuatrimestre', 'prerequisite').all()
        career_id = self.request.query_params.get('career')
        if career_id:
            queryset = queryset.filter(career_id=career_id)
        return queryset


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = CourseEnrollment.objects.all()
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission('manage_academics')]
    
    @action(detail=True, methods=['patch'])
    def update_grade(self, request, pk=None):
        """Actualizar nota final de un curso"""
        enrollment = self.get_object()
        final_grade = request.data.get('final_grade')
        
        if final_grade is None:
            return Response(
                {'error': 'final_grade es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment.final_grade = final_grade
        enrollment.save()
        
        # Verificar si el estudiante completó el pensum
        student = enrollment.student
        total_courses = student.career.courses.count()
        approved_courses = CourseEnrollment.objects.filter(
            student=student,
            status='APROBADO'
        ).count()
        
        if approved_courses >= total_courses and not student.pensum_closed:
            student.pensum_closed = True
            student.save()
        
        serializer = self.get_serializer(enrollment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Obtener matrículas de un estudiante"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollments = CourseEnrollment.objects.filter(student_id=student_id)
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)


class ThesisViewSet(viewsets.ModelViewSet):
    queryset = Thesis.objects.all()
    serializer_class = ThesisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'by_student']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_thesis')]
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Actualizar estado de la tesis"""
        thesis = self.get_object()
        new_status = request.data.get('status')
        
        if new_status:
            thesis.status = new_status
            if new_status == 'SOLICITUD_ASESOR' and not thesis.student.thesis_started:
                thesis.student.thesis_started = True
                thesis.student.save()
            thesis.save()
        
        serializer = self.get_serializer(thesis)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Obtener tesis de un estudiante"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            thesis = Thesis.objects.get(student_id=student_id)
            serializer = self.get_serializer(thesis)
            return Response(serializer.data)
        except Thesis.DoesNotExist:
            return Response(
                {'error': 'El estudiante no tiene tesis registrada'},
                status=status.HTTP_404_NOT_FOUND
            )

