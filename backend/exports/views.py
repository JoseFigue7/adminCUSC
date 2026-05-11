"""
Vistas para el módulo de exportación de estudiantes a Moodle
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db.models import Q
import csv
import io
from students.models import Student
from academics.models import CourseEnrollment
from users.permissions import HasPermission


class ExportViewSet(viewsets.ViewSet):
    """
    ViewSet para exportar estudiantes a formato CSV para Moodle
    """
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action == 'students_list':
            # Para listar estudiantes, solo requiere autenticación
            return [IsAuthenticated()]
        # Para exportar, requiere permiso manage_students
        return [IsAuthenticated(), HasPermission('manage_students')]
    
    @action(detail=False, methods=['post'])
    def export_students(self, request):
        """
        Exporta estudiantes seleccionados a CSV en formato Moodle
        
        Body:
        {
            "student_ids": ["uuid1", "uuid2", ...]
        }
        
        Formato CSV:
        username,firstname,lastname,email,course1,course2,course3,course4,course5
        """
        student_ids = request.data.get('student_ids', [])
        
        if not student_ids:
            return Response(
                {'error': 'Debe seleccionar al menos un estudiante'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener estudiantes con sus cursos
        students = Student.objects.filter(
            id__in=student_ids
        ).prefetch_related(
            'course_enrollments__course'
        ).select_related('career')
        
        if not students.exists():
            return Response(
                {'error': 'No se encontraron estudiantes con los IDs proporcionados'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="moodle_export.csv"'
        
        # Escribir BOM para UTF-8 (ayuda con Excel)
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Escribir encabezados
        # Máximo 5 cursos por estudiante según el ejemplo
        # Agregar columna password para la contraseña de Moodle
        headers = ['username', 'firstname', 'lastname', 'email', 'password', 'course1', 'course2', 'course3', 'course4', 'course5']
        writer.writerow(headers)
        
        # Escribir datos de cada estudiante
        for student in students:
            # Verificar que tenga credenciales de Moodle
            if not student.moodle_username or not student.moodle_password:
                continue
            
            # Obtener cursos activos del estudiante (solo cursos con status EN_CURSO o MATRICULADO)
            course_enrollments = student.course_enrollments.filter(
                status__in=['EN_CURSO', 'MATRICULADO']
            ).select_related('course')
            
            # Obtener nombres de cursos (máximo 5)
            course_names = [enrollment.course.name for enrollment in course_enrollments[:5]]
            
            # Completar hasta 5 cursos con strings vacíos si es necesario
            while len(course_names) < 5:
                course_names.append('')
            
            # Preparar datos del estudiante
            row = [
                student.moodle_username or '',
                student.first_name or '',
                student.first_last_name or '',  # Solo primer apellido según el ejemplo
                student.email or '',
                student.moodle_password or '',  # Contraseña de Moodle
            ] + course_names
            
            writer.writerow(row)
        
        return response
    
    @action(detail=False, methods=['get'], url_path='students-list', permission_classes=[IsAuthenticated])
    def students_list(self, request):
        """
        Lista estudiantes con filtros para la tabla de selección
        """
        from students.serializers import StudentSerializer
        import logging
        
        logger = logging.getLogger(__name__)
        
        logger.info(f'students_list called with params: {dict(request.query_params)}')
        logger.info(f'User: {request.user}, Authenticated: {request.user.is_authenticated}')
        
        try:
            # Aplicar filtros
            queryset = Student.objects.select_related('career').all()
            logger.info(f'Initial queryset count: {queryset.count()}')
            
            # Filtros básicos
            career_id = request.query_params.get('career')
            is_active = request.query_params.get('is_active')
            search = request.query_params.get('search')
            has_moodle_credentials = request.query_params.get('has_moodle_credentials')
            
            if career_id:
                queryset = queryset.filter(career_id=career_id)
            
            if is_active is not None and is_active != '':
                queryset = queryset.filter(is_active=is_active.lower() == 'true')
            
            if search:
                queryset = queryset.filter(
                    Q(first_name__icontains=search) |
                    Q(first_last_name__icontains=search) |
                    Q(second_last_name__icontains=search) |
                    Q(email__icontains=search) |
                    Q(carnet__icontains=search)
                )
            
            if has_moodle_credentials is not None and has_moodle_credentials != '':
                if has_moodle_credentials.lower() == 'true':
                    queryset = queryset.filter(
                        moodle_username__isnull=False,
                        moodle_username__gt='',
                        moodle_password__isnull=False,
                        moodle_password__gt=''
                    )
                elif has_moodle_credentials.lower() == 'false':
                    queryset = queryset.filter(
                        Q(moodle_username__isnull=True) |
                        Q(moodle_username='') |
                        Q(moodle_password__isnull=True) |
                        Q(moodle_password='')
                    )
            
            # Paginación
            try:
                page_size = int(request.query_params.get('page_size', 50))
            except (ValueError, TypeError):
                page_size = 50
            
            try:
                page = int(request.query_params.get('page', 1))
            except (ValueError, TypeError):
                page = 1
            
            # Contar total antes de paginar
            total = queryset.count()
            
            # Aplicar paginación
            start = (page - 1) * page_size
            end = start + page_size
            students = queryset[start:end]
            
            # Pasar el request en el contexto para que el serializer pueda generar URLs absolutas si es necesario
            serializer = StudentSerializer(students, many=True, context={'request': request})
            
            logger.info(f'Export students list: total={total}, page={page}, page_size={page_size}, returned={len(serializer.data)}')
            
            return Response({
                'count': total,
                'results': serializer.data,
                'page': page,
                'page_size': page_size
            })
        except Exception as e:
            logger.error(f'Error in students_list: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Error al obtener estudiantes: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
