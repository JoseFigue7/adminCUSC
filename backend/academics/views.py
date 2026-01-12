from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import (
    Career, Cuatrimestre, Course, CourseEnrollment, CuatrimestreEnrollment, Thesis,
    CourseSchedule, get_academic_period, get_cuatrimestres_by_period
)
from .serializers import (
    CareerSerializer, CuatrimestreSerializer, CourseSerializer,
    CourseEnrollmentSerializer, CuatrimestreEnrollmentSerializer, ThesisSerializer,
    BulkGradeUploadSerializer
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
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        return [permissions.IsAuthenticated(), HasPermission('manage_academics')]
    
    def get_queryset(self):
        """Permitir filtrar por carrera"""
        queryset = super().get_queryset()
        career_id = self.request.query_params.get('career')
        if career_id:
            queryset = queryset.filter(career_id=career_id)
        return queryset


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


class CuatrimestreEnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet para inscripciones a cuatrimestres"""
    queryset = CuatrimestreEnrollment.objects.select_related('student', 'cuatrimestre', 'cuatrimestre__career').all()
    serializer_class = CuatrimestreEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        return [permissions.IsAuthenticated(), HasPermission('manage_academics')]
    
    def get_queryset(self):
        """Permitir filtrar por estudiante, año académico o cuatrimestre"""
        queryset = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        academic_year = self.request.query_params.get('academic_year')
        cuatrimestre_id = self.request.query_params.get('cuatrimestre_id')
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        if cuatrimestre_id:
            queryset = queryset.filter(cuatrimestre_id=cuatrimestre_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def enroll_courses(self, request, pk=None):
        """Inscribir cursos en un cuatrimestre"""
        cuatrimestre_enrollment = self.get_object()
        course_ids = request.data.get('course_ids', [])
        
        if not course_ids:
            return Response(
                {'error': 'course_ids es requerido (lista de IDs de cursos)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar máximo 7 cursos
        if len(course_ids) > 7:
            return Response(
                {'error': 'No se pueden inscribir más de 7 cursos por cuatrimestre'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener el período académico del cuatrimestre de la inscripción
        enrollment_period = get_academic_period(cuatrimestre_enrollment.cuatrimestre.number)
        if not enrollment_period:
            return Response(
                {'error': 'No se pudo determinar el período académico del cuatrimestre'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener números de cuatrimestres del mismo período
        period_cuatrimestres = get_cuatrimestres_by_period(enrollment_period)
        
        # Validar que los cursos pertenezcan al mismo período académico (no solo al mismo cuatrimestre)
        courses = Course.objects.filter(
            id__in=course_ids,
            cuatrimestre__number__in=period_cuatrimestres,
            cuatrimestre__career=cuatrimestre_enrollment.cuatrimestre.career
        ).select_related('cuatrimestre').prefetch_related('schedules')
        
        if courses.count() != len(course_ids):
            return Response(
                {'error': 'Algunos cursos no pertenecen al período académico del cuatrimestre seleccionado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar traslapes de horarios entre todos los cursos a inscribir
        courses_list = list(courses)
        overlap_errors = []
        for i, course1 in enumerate(courses_list):
            schedules1 = list(course1.schedules.all())
            if not schedules1:
                overlap_errors.append(f"El curso {course1.code} - {course1.name} no tiene horarios asignados.")
                continue
            
            for j, course2 in enumerate(courses_list[i+1:], start=i+1):
                schedules2 = list(course2.schedules.all())
                if not schedules2:
                    overlap_errors.append(f"El curso {course2.code} - {course2.name} no tiene horarios asignados.")
                    continue
                
                # Verificar traslapes entre horarios de course1 y course2
                for schedule1 in schedules1:
                    for schedule2 in schedules2:
                        if schedule1.overlaps_with(schedule2):
                            overlap_errors.append(
                                f"Los cursos {course1.code} y {course2.code} tienen horarios que se traslapan "
                                f"({schedule1.day} {schedule1.start_time.strftime('%H:%M')}-{schedule1.end_time.strftime('%H:%M')} "
                                f"y {schedule2.day} {schedule2.start_time.strftime('%H:%M')}-{schedule2.end_time.strftime('%H:%M')})"
                            )
                            break
                    if overlap_errors and overlap_errors[-1].startswith(f"Los cursos {course1.code} y {course2.code}"):
                        break
                if overlap_errors and overlap_errors[-1].startswith(f"Los cursos {course1.code} y {course2.code}"):
                    break
        
        # Si hay errores de traslape, retornar
        if overlap_errors:
            return Response({
                'error': 'Hay traslapes de horarios entre los cursos seleccionados',
                'errors': overlap_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear inscripciones a cursos
        created = []
        errors = []
        student = cuatrimestre_enrollment.student
        
        # Validar cursos ya inscritos en este cuatrimestre y cursos aprobados
        # PERO permitir reasignar cursos reprobados
        for course in courses_list:
            try:
                # Validar que el curso no haya sido aprobado previamente
                approved_enrollment = CourseEnrollment.objects.filter(
                    student=student,
                    course=course,
                    status='APROBADO'
                ).first()
                
                if approved_enrollment:
                    errors.append(f"El curso {course.code} - {course.name} ya fue aprobado. No se puede volver a inscribir.")
                    continue
                
                # Validar que no esté ya inscrito en este cuatrimestre
                # PERO permitir si el anterior fue reprobado
                existing = CourseEnrollment.objects.filter(
                    student=student,
                    course=course,
                    cuatrimestre_enrollment=cuatrimestre_enrollment
                ).first()
                
                if existing and existing.status != 'REPROBADO':
                    errors.append(f"El estudiante ya está inscrito en {course.code} - {course.name} para este cuatrimestre.")
                    continue
                
                enrollment = CourseEnrollment.objects.create(
                    student=student,
                    course=course,
                    cuatrimestre_enrollment=cuatrimestre_enrollment,
                    status='MATRICULADO'
                )
                created.append(str(enrollment.id))
            except Exception as e:
                errors.append(f"Error al inscribir curso {course.code}: {str(e)}")
        
        return Response({
            'created': created,
            'errors': errors,
            'message': f'Se inscribieron {len(created)} curso(s) exitosamente' + (f'. {len(errors)} error(es).' if errors else '')
        })
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Obtener cursos inscritos en este cuatrimestre"""
        cuatrimestre_enrollment = self.get_object()
        course_enrollments = cuatrimestre_enrollment.course_enrollments.select_related('course').all()
        serializer = CourseEnrollmentSerializer(course_enrollments, many=True)
        return Response(serializer.data)


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    queryset = CourseEnrollment.objects.select_related('student', 'course', 'cuatrimestre_enrollment').all()
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        return [permissions.IsAuthenticated(), HasPermission('manage_academics')]
    
    def get_queryset(self):
        """Permitir filtrar por estudiante o cuatrimestre"""
        queryset = super().get_queryset()
        student_id = self.request.query_params.get('student_id')
        cuatrimestre_enrollment_id = self.request.query_params.get('cuatrimestre_enrollment_id')
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if cuatrimestre_enrollment_id:
            queryset = queryset.filter(cuatrimestre_enrollment_id=cuatrimestre_enrollment_id)
        
        return queryset
    
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
    
    @action(detail=False, methods=['post'])
    def bulk_upload_grades(self, request):
        """
        Subir notas masivamente.
        
        Formato del request:
        {
            "grades": [
                {
                    "student_id": "uuid",
                    "course_id": "uuid",
                    "final_grade": 85.5
                },
                ...
            ]
        }
        """
        serializer = BulkGradeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        grades_data = serializer.validated_data['grades']
        results = {
            'success': [],
            'errors': [],
            'updated': 0,
            'created': 0
        }
        
        with transaction.atomic():
            for grade_item in grades_data:
                student_id = grade_item['student_id']
                course_id = grade_item['course_id']
                final_grade = grade_item['final_grade']
                
                try:
                    # Verificar que el estudiante existe
                    student = Student.objects.get(id=student_id)
                    
                    # Verificar que el curso existe
                    course = Course.objects.get(id=course_id)
                    
                    # Buscar la inscripción existente
                    # Primero buscar por cuatrimestre_enrollment si existe
                    enrollment = CourseEnrollment.objects.filter(
                        student_id=student_id,
                        course_id=course_id
                    ).order_by('-enrollment_date').first()
                    
                    if not enrollment:
                        # Si no existe inscripción, buscar si hay una inscripción al cuatrimestre activa
                        cuatrimestre_enrollment = CuatrimestreEnrollment.objects.filter(
                            student_id=student_id,
                            cuatrimestre=course.cuatrimestre,
                            status__in=['INSCRITO', 'EN_CURSO']
                        ).order_by('-academic_year').first()
                        
                        if cuatrimestre_enrollment:
                            # Crear nueva inscripción
                            enrollment = CourseEnrollment.objects.create(
                                student=student,
                                course=course,
                                cuatrimestre_enrollment=cuatrimestre_enrollment,
                                final_grade=final_grade,
                                status='MATRICULADO'
                            )
                            results['created'] += 1
                            results['success'].append({
                                'student': student.get_full_name(),
                                'course': course.name,
                                'grade': float(final_grade),
                                'action': 'created'
                            })
                        else:
                            results['errors'].append({
                                'student_id': str(student_id),
                                'course_id': str(course_id),
                                'error': f'No se encontró inscripción al cuatrimestre para {student.get_full_name()} en {course.name}'
                            })
                            continue
                    else:
                        # Verificar que no esté aprobado (no se puede modificar notas de cursos aprobados)
                        if enrollment.status == 'APROBADO':
                            results['errors'].append({
                                'student_id': str(student_id),
                                'course_id': str(course_id),
                                'error': f'El curso {course.name} ya fue aprobado por {student.get_full_name()}. No se puede modificar la nota.'
                            })
                            continue
                        
                        # Actualizar la nota
                        enrollment.final_grade = final_grade
                        enrollment.save()
                        results['updated'] += 1
                        results['success'].append({
                            'student': student.get_full_name(),
                            'course': course.name,
                            'grade': float(final_grade),
                            'action': 'updated'
                        })
                    
                    # Verificar si el estudiante completó el pensum
                    total_courses = student.career.courses.count()
                    approved_courses = CourseEnrollment.objects.filter(
                        student=student,
                        status='APROBADO'
                    ).count()
                    
                    if approved_courses >= total_courses and not student.pensum_closed:
                        student.pensum_closed = True
                        student.save()
                        
                except Student.DoesNotExist:
                    results['errors'].append({
                        'student_id': str(student_id),
                        'course_id': str(course_id),
                        'error': f'Estudiante con ID {student_id} no encontrado'
                    })
                except Course.DoesNotExist:
                    results['errors'].append({
                        'student_id': str(student_id),
                        'course_id': str(course_id),
                        'error': f'Curso con ID {course_id} no encontrado'
                    })
                except Exception as e:
                    results['errors'].append({
                        'student_id': str(student_id),
                        'course_id': str(course_id),
                        'error': str(e)
                    })
        
        return Response({
            'message': f'Proceso completado: {results["updated"]} actualizadas, {results["created"]} creadas, {len(results["errors"])} errores',
            'results': results
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def by_cuatrimestre(self, request):
        """
        Obtener todas las matrículas de un cuatrimestre específico.
        Útil para ver qué estudiantes tienen cursos asignados en un cuatrimestre.
        """
        cuatrimestre_enrollment_id = request.query_params.get('cuatrimestre_enrollment_id')
        academic_year = request.query_params.get('academic_year')
        cuatrimestre_id = request.query_params.get('cuatrimestre_id')
        
        queryset = CourseEnrollment.objects.select_related(
            'student', 'course', 'cuatrimestre_enrollment', 'cuatrimestre_enrollment__cuatrimestre'
        ).all()
        
        if cuatrimestre_enrollment_id:
            queryset = queryset.filter(cuatrimestre_enrollment_id=cuatrimestre_enrollment_id)
        elif academic_year and cuatrimestre_id:
            queryset = queryset.filter(
                cuatrimestre_enrollment__academic_year=academic_year,
                cuatrimestre_enrollment__cuatrimestre_id=cuatrimestre_id
            )
        else:
            return Response(
                {'error': 'Se requiere cuatrimestre_enrollment_id o (academic_year y cuatrimestre_id)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(queryset, many=True)
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

