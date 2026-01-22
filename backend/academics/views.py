from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal
from .models import (
    Career, Cuatrimestre, Course, CourseEnrollment, CuatrimestreEnrollment, GraduationMethod,
    CourseSchedule, get_academic_period, get_cuatrimestres_by_period,
    AcademicPeriodConfig, MonthlyPaymentDueDate
)
from .services import PreAssignCoursesService, ConfirmCourseAssignmentService
from .pdf_utils import generate_assignment_boleta, generate_payment_voucher
from .serializers import (
    CareerSerializer, CuatrimestreSerializer, CourseSerializer,
    CourseEnrollmentSerializer, CuatrimestreEnrollmentSerializer, GraduationMethodSerializer,
    BulkGradeUploadSerializer
)
from students.models import Student
from users.permissions import HasPermission
from payments.models import Payment, PaymentType, PaymentConfiguration


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
    
    def perform_create(self, serializer):
        """Capturar usuario que crea la inscripción y validar pago 100 o 101"""
        user = self.request.user if self.request.user.is_authenticated else None
        validated_data = serializer.validated_data
        student = validated_data.get('student')
        
        # Validar que el estudiante tenga un pago 100 o 101 aprobado
        # Esto aplica tanto para primera inscripción como para siguientes
        # Obtener los tipos de pago 100 y 101
        payment_type_100 = PaymentType.objects.filter(code='100', is_active=True).first()
        payment_type_101 = PaymentType.objects.filter(code='101', is_active=True).first()
        
        if not payment_type_100 and not payment_type_101:
            raise serializers.ValidationError(
                'Los tipos de pago 100 o 101 (Inscripción al Cuatrimestre) no están configurados. '
                'Contacte al administrador.'
            )
        
        # Verificar si hay un pago 100 o 101 aprobado para este estudiante
        # El pago debe estar aprobado y NO debe estar vinculado a otro cuatrimestre enrollment
        # (cada cuatrimestre requiere su propio pago)
        approved_payment = None
        payment_types_to_check = []
        if payment_type_100:
            payment_types_to_check.append(payment_type_100)
        if payment_type_101:
            payment_types_to_check.append(payment_type_101)
        
        approved_payment = Payment.objects.filter(
            student=student,
            payment_type__in=payment_types_to_check,
            status='APROBADO',
            cuatrimestre_enrollment__isnull=True  # Pago no vinculado a ningún cuatrimestre aún
        ).first()
        
        if not approved_payment:
            available_codes = []
            if payment_type_100:
                available_codes.append('100 (Gratis)')
            if payment_type_101:
                available_codes.append('101')
            raise serializers.ValidationError(
                f'El estudiante debe tener un pago de inscripción ({", ".join(available_codes)}) aprobado '
                'antes de crear una nueva inscripción. Realice el pago primero.'
            )
        
        # Estado por defecto: PRE_INSCRIPCION para el flujo presencial guiado
        status = validated_data.get('status', 'PRE_INSCRIPCION')
        
        # Si el pago es 100 (gratis), marcar como exonerado
        if approved_payment.payment_type.code == '100':
            validated_data['is_enrollment_fee_exempt'] = True
        # Si es primera inscripción y el pago es 101, también marcar como exonerado (compatibilidad)
        elif validated_data.get('is_first_enrollment', False):
            validated_data['is_enrollment_fee_exempt'] = True
        
        # Si el estado es EN_CURSO, usar el manager para validación thread-safe
        if status == 'EN_CURSO':
            instance = CuatrimestreEnrollment.objects.create_with_en_curso_validation(
                **validated_data
            )
        else:
            instance = serializer.save()
        
        # Vincular el pago aprobado (100 o 101) a este cuatrimestre enrollment
        if approved_payment:
            approved_payment.cuatrimestre_enrollment = instance
            approved_payment.save()
        
        instance._changed_by_user = user
        instance._status_change_notes = 'Inscripción al cuatrimestre creada'
        return instance
    
    def perform_update(self, serializer):
        """Capturar usuario que realiza el cambio"""
        user = self.request.user if self.request.user.is_authenticated else None
        instance = serializer.instance
        
        # No permitir modificar asignaciones confirmadas (EN_CURSO o FINALIZADO)
        if instance.status in ['EN_CURSO', 'FINALIZADO']:
            raise serializers.ValidationError(
                f'No se puede modificar una asignación que está en estado {instance.get_status_display()}. '
                'La asignación ya fue confirmada y no puede ser modificada.'
            )
        
        new_status = serializer.validated_data.get('status', instance.status)
        old_status = instance.status
        
        # Si estamos cambiando a EN_CURSO, usar el manager para validación thread-safe
        if new_status == 'EN_CURSO' and old_status != 'EN_CURSO':
            # Actualizar otros campos primero si existen
            update_fields = {k: v for k, v in serializer.validated_data.items() if k != 'status'}
            instance = CuatrimestreEnrollment.objects.update_to_en_curso(
                instance, **update_fields
            )
            # Actualizar campos adicionales que no sean status
            for field, value in serializer.validated_data.items():
                if field != 'status':
                    setattr(instance, field, value)
            instance.save()
        else:
            instance = serializer.save()
        
        instance._changed_by_user = user
        instance._status_change_notes = self.request.data.get('notes', '') or ''
        return instance
    
    def perform_destroy(self, instance):
        """No permitir eliminar asignaciones confirmadas"""
        if instance.status in ['EN_CURSO', 'FINALIZADO']:
            raise serializers.ValidationError(
                f'No se puede eliminar una asignación que está en estado {instance.get_status_display()}. '
                'La asignación ya fue confirmada y no puede ser eliminada.'
            )
        super().perform_destroy(instance)
    
    @action(detail=True, methods=['post'])
    def enroll_courses(self, request, pk=None):
        """Inscribir cursos en un cuatrimestre"""
        cuatrimestre_enrollment = self.get_object()
        course_ids = request.data.get('course_ids', [])
        
        # Validar que el estado permita asignar cursos
        if not cuatrimestre_enrollment.can_assign_courses():
            return Response(
                {
                    'error': f'No se pueden matricular cursos. El estado actual es: {cuatrimestre_enrollment.get_status_display()}. '
                             f'Debe estar en PRE_INSCRIPCION o CURSOS_PREASIGNADOS para matricular cursos.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
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
        
        # Convertir course_ids a UUIDs si son strings
        try:
            from uuid import UUID
            course_ids_uuids = []
            for cid in course_ids:
                if isinstance(cid, str):
                    course_ids_uuids.append(UUID(cid))
                else:
                    course_ids_uuids.append(cid)
        except (ValueError, TypeError) as e:
            return Response({
                'error': 'Formato de IDs de cursos inválido',
                'details': str(e),
                'course_ids_received': course_ids
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar que los cursos pertenezcan al mismo período académico (no solo al mismo cuatrimestre)
        courses = Course.objects.filter(
            id__in=course_ids_uuids,
            cuatrimestre__number__in=period_cuatrimestres,
            cuatrimestre__career=cuatrimestre_enrollment.cuatrimestre.career
        ).select_related('cuatrimestre', 'cuatrimestre__career').prefetch_related('schedules')
        
        if courses.count() != len(course_ids):
            # Obtener los cursos que no se encontraron para dar un mensaje más específico
            found_course_ids = set(courses.values_list('id', flat=True))
            missing_course_ids = [cid for cid in course_ids if cid not in found_course_ids]
            
            # Intentar encontrar los cursos faltantes para ver por qué no calificaron
            all_courses = Course.objects.filter(id__in=missing_course_ids).select_related('cuatrimestre', 'cuatrimestre__career')
            errors_detail = []
            for course in all_courses:
                course_period = get_academic_period(course.cuatrimestre.number)
                if course.cuatrimestre.number not in period_cuatrimestres:
                    errors_detail.append(
                        f"El curso {course.code} - {course.name} pertenece al cuatrimestre {course.cuatrimestre.number} "
                        f"(período {course_period}), pero la inscripción es para el período {enrollment_period} "
                        f"(cuatrimestres válidos: {period_cuatrimestres})"
                    )
                elif course.cuatrimestre.career_id != cuatrimestre_enrollment.cuatrimestre.career_id:
                    errors_detail.append(
                        f"El curso {course.code} - {course.name} pertenece a la carrera {course.cuatrimestre.career.name}, "
                        f"pero la inscripción es para la carrera {cuatrimestre_enrollment.cuatrimestre.career.name}"
                    )
                else:
                    # Si llegamos aquí, el curso no existe o hay otro problema
                    errors_detail.append(
                        f"El curso {course.code if course else 'N/A'} no pudo ser validado correctamente"
                    )
            
            # Si no encontramos algunos cursos, agregar información adicional
            if len(all_courses) < len(missing_course_ids):
                not_found_ids = [cid for cid in missing_course_ids if cid not in [str(c.id) for c in all_courses]]
                errors_detail.append(
                    f"Los siguientes IDs de cursos no fueron encontrados: {', '.join(not_found_ids)}"
                )
            
            return Response({
                'error': 'Algunos cursos no pertenecen al período académico del cuatrimestre seleccionado',
                'errors': errors_detail,
                'enrollment_period': enrollment_period,
                'period_cuatrimestres': period_cuatrimestres,
                'enrollment_cuatrimestre_number': cuatrimestre_enrollment.cuatrimestre.number,
                'enrollment_cuatrimestre_name': cuatrimestre_enrollment.cuatrimestre.name,
                'total_courses_requested': len(course_ids),
                'valid_courses_found': courses.count(),
                'invalid_courses_count': len(missing_course_ids)
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
        
        # Actualizar estado a CURSOS_PREASIGNADOS si se crearon asignaciones
        if created:
            cuatrimestre_enrollment.status = 'CURSOS_PREASIGNADOS'
            cuatrimestre_enrollment.save()
        
        return Response({
            'created': created,
            'errors': errors,
            'message': f'Se inscribieron {len(created)} curso(s) exitosamente' + (f'. {len(errors)} error(es).' if errors else ''),
            'status': cuatrimestre_enrollment.status,
            'status_display': cuatrimestre_enrollment.get_status_display()
        })
    
    @action(detail=False, methods=['get'])
    def can_create_enrollment(self, request):
        """
        Verificar si un estudiante puede crear una nueva inscripción.
        Retorna True si tiene un pago 100 o 101 aprobado sin vincular a ningún cuatrimestre.
        """
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Estudiante no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener los tipos de pago 100 y 101
        payment_type_100 = PaymentType.objects.filter(code='100', is_active=True).first()
        payment_type_101 = PaymentType.objects.filter(code='101', is_active=True).first()
        
        if not payment_type_100 and not payment_type_101:
            return Response({
                'can_create': False,
                'reason': 'Los tipos de pago 100 o 101 no están configurados',
                'has_approved_payment': False
            })
        
        # Verificar si hay un pago 100 o 101 aprobado sin vincular a ningún cuatrimestre
        payment_types_to_check = []
        if payment_type_100:
            payment_types_to_check.append(payment_type_100)
        if payment_type_101:
            payment_types_to_check.append(payment_type_101)
        
        approved_payment = Payment.objects.filter(
            student=student,
            payment_type__in=payment_types_to_check,
            status='APROBADO',
            cuatrimestre_enrollment__isnull=True
        ).first()
        
        available_codes = []
        if payment_type_100:
            available_codes.append('100 (Gratis)')
        if payment_type_101:
            available_codes.append('101')
        
        return Response({
            'can_create': approved_payment is not None,
            'has_approved_payment': approved_payment is not None,
            'payment_id': str(approved_payment.id) if approved_payment else None,
            'payment_code': approved_payment.payment_type.code if approved_payment else None,
            'available_payment_codes': available_codes,
            'message': 'Puede crear una nueva inscripción' if approved_payment else 
                      f'Debe realizar y aprobar el pago de inscripción ({", ".join(available_codes)}) antes de crear una nueva inscripción'
        })
    
    @action(detail=True, methods=['get'])
    def courses(self, request, pk=None):
        """Obtener cursos inscritos en este cuatrimestre"""
        cuatrimestre_enrollment = self.get_object()
        course_enrollments = cuatrimestre_enrollment.course_enrollments.select_related('course').all()
        serializer = CourseEnrollmentSerializer(course_enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def available_courses(self, request, pk=None):
        """
        Obtener cursos disponibles para matricular en este cuatrimestre.
        Solo devuelve cursos del mismo período académico.
        """
        cuatrimestre_enrollment = self.get_object()
        
        # Obtener el período académico del cuatrimestre de la inscripción
        enrollment_period = get_academic_period(cuatrimestre_enrollment.cuatrimestre.number)
        if not enrollment_period:
            return Response(
                {'error': 'No se pudo determinar el período académico del cuatrimestre'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener números de cuatrimestres del mismo período
        period_cuatrimestres = get_cuatrimestres_by_period(enrollment_period)
        
        # Obtener cursos del mismo período académico y carrera
        available_courses = Course.objects.filter(
            cuatrimestre__number__in=period_cuatrimestres,
            cuatrimestre__career=cuatrimestre_enrollment.cuatrimestre.career
        ).select_related('cuatrimestre', 'career', 'prerequisite').prefetch_related('schedules')
        
        # Excluir cursos ya aprobados por el estudiante
        approved_course_ids = CourseEnrollment.objects.filter(
            student=cuatrimestre_enrollment.student,
            status='APROBADO'
        ).values_list('course_id', flat=True)
        
        available_courses = available_courses.exclude(id__in=approved_course_ids)
        
        serializer = CourseSerializer(available_courses, many=True)
        return Response({
            'courses': serializer.data,
            'enrollment_period': enrollment_period,
            'period_cuatrimestres': period_cuatrimestres,
            'total_available': available_courses.count()
        })
    
    @action(detail=True, methods=['post'])
    def process_enrollment_payment(self, request, pk=None):
        """Procesar pago de inscripción al cuatrimestre"""
        cuatrimestre_enrollment = self.get_object()
        
        # Validar que esté en estado PENDIENTE_PAGO
        if cuatrimestre_enrollment.status != 'PENDIENTE_PAGO':
            return Response(
                {'error': f'La inscripción no está en estado PENDIENTE_PAGO (estado actual: {cuatrimestre_enrollment.get_status_display()})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si está exonerado, no necesita crear pago de inscripción
        if cuatrimestre_enrollment.is_enrollment_fee_exempt:
            return Response(
                {'error': 'El estudiante está exonerado de la cuota de inscripción. No se requiere pago.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_method = request.data.get('payment_method')
        payment_reference = request.data.get('payment_reference', '')
        transfer_receipt = request.FILES.get('transfer_receipt')
        
        if not payment_method:
            return Response(
                {'error': 'payment_method es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener el monto de inscripción desde PaymentConfiguration
        try:
            payment_config = PaymentConfiguration.objects.get(
                career=cuatrimestre_enrollment.cuatrimestre.career,
                is_active=True
            )
            enrollment_fee = payment_config.enrollment_fee
        except PaymentConfiguration.DoesNotExist:
            return Response(
                {'error': 'No se encontró configuración de pago para esta carrera'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener o crear tipo de pago de inscripción (código 101)
        # El pago 100 solo se puede crear desde el formulario de pagos, no desde aquí
        payment_type, _ = PaymentType.objects.get_or_create(
            code='101',
            defaults={
                'name': 'Inscripción al Cuatrimestre',
                'description': 'Pago de inscripción al cuatrimestre (requerido para asignar cursos)',
                'is_active': True
            }
        )
        
        # Verificar si ya existe un pago 100 o 101 aprobado para este estudiante sin cuatrimestre enrollment
        # Si existe, vincularlo a este cuatrimestre enrollment
        payment_type_100 = PaymentType.objects.filter(code='100', is_active=True).first()
        payment_types_to_check = [payment_type]
        if payment_type_100:
            payment_types_to_check.append(payment_type_100)
        
        existing_payment = Payment.objects.filter(
            student=cuatrimestre_enrollment.student,
            payment_type__in=payment_types_to_check,
            status='APROBADO',
            cuatrimestre_enrollment__isnull=True
        ).first()
        
        if existing_payment:
            # Vincular el pago existente a este cuatrimestre enrollment
            existing_payment.cuatrimestre_enrollment = cuatrimestre_enrollment
            existing_payment.save()
            payment = existing_payment
        else:
            # Crear el pago nuevo (solo 101, el 100 se crea desde el formulario de pagos)
            payment = Payment.objects.create(
                student=cuatrimestre_enrollment.student,
                payment_type=payment_type,
                payment_method=payment_method,
                original_amount=enrollment_fee,
                payment_reference=payment_reference,
                transfer_receipt=transfer_receipt,
                status='PENDIENTE',
                cuatrimestre_enrollment=cuatrimestre_enrollment,
                year=cuatrimestre_enrollment.academic_year
            )
        
        return Response({
            'payment_id': str(payment.id),
            'amount': str(enrollment_fee),
            'status': payment.status,
            'message': 'Pago de inscripción creado. Debe ser aprobado para completar la inscripción.'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def approve_enrollment_payment(self, request, pk=None):
        """Aprobar pago de inscripción y cambiar estado a PENDIENTE_CONFIRMACION o PRE_INSCRIPCION"""
        cuatrimestre_enrollment = self.get_object()
        
        # Si está exonerado, no necesita aprobar pago, pasar directamente a PRE_INSCRIPCION
        if cuatrimestre_enrollment.is_enrollment_fee_exempt:
            if cuatrimestre_enrollment.status == 'PRE_INSCRIPCION':
                return Response({
                    'message': 'El estudiante está exonerado. Ya puede seleccionar cursos.',
                    'status': cuatrimestre_enrollment.status
                })
            else:
                # Cambiar a PRE_INSCRIPCION si no lo está
                cuatrimestre_enrollment.status = 'PRE_INSCRIPCION'
                cuatrimestre_enrollment.save()
                return Response({
                    'message': 'El estudiante está exonerado. Ya puede seleccionar cursos.',
                    'status': cuatrimestre_enrollment.status
                })
        
        if cuatrimestre_enrollment.status != 'PENDIENTE_PAGO':
            return Response(
                {'error': f'La inscripción no está en estado PENDIENTE_PAGO'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar el pago de inscripción pendiente
        payment = Payment.objects.filter(
            cuatrimestre_enrollment=cuatrimestre_enrollment,
            status__in=['PENDIENTE', 'EN_REVISION']
        ).first()
        
        if not payment:
            return Response(
                {'error': 'No se encontró un pago pendiente para esta inscripción'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with transaction.atomic():
            # Aprobar el pago
            payment.status = 'APROBADO'
            payment.save()
            
            # Cambiar estado de la inscripción
            # En el nuevo flujo, cambiar a PRE_INSCRIPCION para permitir selección de cursos
            # Si ya hay cursos asignados, cambiar directamente a CURSOS_PREASIGNADOS
            courses_count = cuatrimestre_enrollment.course_enrollments.count()
            if courses_count > 0:
                cuatrimestre_enrollment.status = 'CURSOS_PREASIGNADOS'
                cuatrimestre_enrollment.save()
            else:
                cuatrimestre_enrollment.status = 'PRE_INSCRIPCION'
                cuatrimestre_enrollment.save()
        
        return Response({
            'message': 'Pago aprobado. Ahora puede seleccionar los cursos.',
            'status': cuatrimestre_enrollment.status
        })
    
    @action(detail=True, methods=['post'])
    def reject_enrollment_payment(self, request, pk=None):
        """Rechazar pago de inscripción"""
        cuatrimestre_enrollment = self.get_object()
        
        # Buscar el pago pendiente
        payment = Payment.objects.filter(
            cuatrimestre_enrollment=cuatrimestre_enrollment,
            status__in=['PENDIENTE', 'EN_REVISION']
        ).first()
        
        if not payment:
            return Response(
                {'error': 'No se encontró un pago pendiente para esta inscripción'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with transaction.atomic():
            # Rechazar el pago
            payment.status = 'RECHAZADO'
            payment.save()
            
            # La inscripción permanece en PENDIENTE_PAGO para reintentar
        
        return Response({
            'message': 'Pago rechazado. Puede crear un nuevo pago para reintentar.',
            'status': cuatrimestre_enrollment.status
        })
    
    @action(detail=True, methods=['get'])
    def calculate_tuition(self, request, pk=None):
        """Calcular el costo total de la colegiatura: base (tipo 102) + adicionales de cursos"""
        from payments.models import PaymentType
        
        cuatrimestre_enrollment = self.get_object()
        career = cuatrimestre_enrollment.cuatrimestre.career
        
        # Obtener monto base mensual del tipo de pago 102 (Colegiatura de Cursos)
        try:
            tuition_payment_type = PaymentType.objects.get(code='102', is_active=True)
            base_monthly_amount = tuition_payment_type.amount or Decimal('0.00')
            if base_monthly_amount == 0:
                return Response(
                    {'error': 'Tipo de pago 102 (Colegiatura de Cursos) no tiene monto configurado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except PaymentType.DoesNotExist:
            return Response(
                {'error': 'Tipo de pago 102 (Colegiatura de Cursos) no encontrado. Ejecute el comando seed_payment_types.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular adicionales de cursos (course.cost ahora son adicionales)
        course_additionals = Decimal('0.00')
        course_enrollments = cuatrimestre_enrollment.course_enrollments.select_related('course').all()
        courses_detail = []
        
        for enrollment in course_enrollments:
            course_additional = enrollment.course.cost or Decimal('0.00')
            course_additionals += course_additional
            courses_detail.append({
                'course_id': str(enrollment.course.id),
                'course_code': enrollment.course.code,
                'course_name': enrollment.course.name,
                'additional_cost': str(course_additional)  # Ahora es adicional, no costo total
            })
        
        # Pago mensual total = base + adicionales
        monthly_payment = base_monthly_amount + course_additionals
        
        # Obtener período académico para calcular total del cuatrimestre
        period = get_academic_period(cuatrimestre_enrollment.cuatrimestre.number)
        try:
            period_config = AcademicPeriodConfig.objects.get(period=period, is_active=True)
            months = period_config.get_months()
        except AcademicPeriodConfig.DoesNotExist:
            period_months = {
                1: [2, 3, 4, 5],  # Febrero-Mayo
                2: [6, 7, 8],  # Junio-Agosto
                3: [9, 10, 11, 12]  # Septiembre-Diciembre
            }
            months = period_months.get(period, [2, 3, 4, 5])
        
        # Total del cuatrimestre = pago_mensual * número_de_meses
        total_cuatrimestre = monthly_payment * len(months)
        
        return Response({
            'base_monthly_amount': str(base_monthly_amount),  # Monto base del tipo 102
            'course_additionals': str(course_additionals),  # Adicionales de cursos
            'monthly_payment': str(monthly_payment),  # Pago mensual total
            'total_cuatrimestre': str(total_cuatrimestre),  # Total del cuatrimestre
            'courses_count': len(courses_detail),
            'courses': courses_detail,
            'payment_plan': {
                'monthly_payment': str(monthly_payment),
                'full_payment_discount': str(total_cuatrimestre * Decimal('0.10')),
                'full_payment_total': str(total_cuatrimestre * Decimal('0.90'))
            }
        })
    
    @action(detail=True, methods=['post'])
    def confirm_assignment(self, request, pk=None):
        """Confirmar asignación de cursos y generar plan de pagos mensuales"""
        cuatrimestre_enrollment = self.get_object()
        
        if cuatrimestre_enrollment.status != 'PENDIENTE_CONFIRMACION':
            return Response(
                {'error': f'La inscripción debe estar en estado PENDIENTE_CONFIRMACION (estado actual: {cuatrimestre_enrollment.get_status_display()})'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que tenga cursos asignados
        courses_count = cuatrimestre_enrollment.course_enrollments.count()
        if courses_count == 0:
            return Response(
                {'error': 'No hay cursos asignados. Debe asignar cursos antes de confirmar.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment_option = request.data.get('payment_option', 'monthly')  # 'monthly' o 'full'
        
        with transaction.atomic():
            # Obtener monto base mensual del tipo de pago 102 (Colegiatura de Cursos)
            try:
                tuition_payment_type = PaymentType.objects.get(code='102', is_active=True)
                base_monthly_amount = tuition_payment_type.amount or Decimal('0.00')
                if base_monthly_amount == 0:
                    return Response(
                        {'error': 'Tipo de pago 102 (Colegiatura de Cursos) no tiene monto configurado'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except PaymentType.DoesNotExist:
                return Response(
                    {'error': 'Tipo de pago 102 (Colegiatura de Cursos) no encontrado. Ejecute el comando seed_payment_types.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calcular adicionales de cursos (course.cost ahora son adicionales)
            course_additionals = Decimal('0.00')
            for enrollment in cuatrimestre_enrollment.course_enrollments.select_related('course').all():
                course_additionals += enrollment.course.cost or Decimal('0.00')
            
            # Pago mensual total = base + adicionales
            monthly_amount = base_monthly_amount + course_additionals
            
            # Obtener período académico y configuración
            period = get_academic_period(cuatrimestre_enrollment.cuatrimestre.number)
            try:
                period_config = AcademicPeriodConfig.objects.get(period=period, is_active=True)
            except AcademicPeriodConfig.DoesNotExist:
                period_config = None
            
            # Obtener meses del período
            if period_config:
                months = period_config.get_months()
            else:
                # Fallback a meses por defecto según período
                period_months = {
                    1: [2, 3, 4, 5],  # Febrero-Mayo
                    2: [6, 7, 8],  # Junio-Agosto
                    3: [9, 10, 11, 12]  # Septiembre-Diciembre
                }
                months = period_months.get(period, [2, 3, 4, 5])
            
            payments_created = []
            
            if payment_option == 'full':
                # Pago completo con 10% de descuento
                # El pago mensual ya incluye base + adicionales, entonces el total del cuatrimestre es: pago_mensual * número_de_meses
                total_cuatrimestre = monthly_amount * len(months)
                discounted_amount = total_cuatrimestre * Decimal('0.90')
                current_year = cuatrimestre_enrollment.academic_year
                first_month = months[0] if months else 1
                
                # Establecer fecha programada de pago al día 1 del primer mes del período
                payment_date = datetime(current_year, first_month, 1).date()
                
                # Obtener fecha límite de pago
                try:
                    due_date_config = MonthlyPaymentDueDate.objects.get(month=first_month, is_active=True)
                    due_day = due_date_config.due_day
                except MonthlyPaymentDueDate.DoesNotExist:
                    due_day = 10  # Valor por defecto
                
                # Calcular fecha límite
                try:
                    due_date = datetime(current_year, first_month, due_day).date()
                except ValueError:
                    if first_month == 2:
                        due_date = datetime(current_year, first_month, 28).date()
                    else:
                        due_date = datetime(current_year, first_month, due_day).date()
                
                payment = Payment.objects.create(
                    student=cuatrimestre_enrollment.student,
                    payment_type=tuition_payment_type,
                    payment_method='TRANSFERENCIA',  # Por defecto, se puede cambiar
                    original_amount=discounted_amount,
                    month=first_month,
                    year=current_year,
                    payment_date=payment_date,  # Fecha programada: día 1 del primer mes
                    due_date=due_date,
                    status='NO_PAGADO',  # Estado inicial: NO_PAGADO
                    cuatrimestre_enrollment=cuatrimestre_enrollment,
                    notes=f'Pago completo de colegiatura con 10% descuento. Monto original: {total_cuatrimestre}, Descuento: {total_cuatrimestre * Decimal("0.10")}, Pago mensual base: {base_monthly_amount}, Adicionales cursos: {course_additionals}'
                )
                payments_created.append(str(payment.id))
            else:
                # Pagos mensuales (uno por cada mes del período)
                # monthly_amount ya incluye base + adicionales
                current_year = cuatrimestre_enrollment.academic_year
                
                for month in months:  # Generar un pago por cada mes del período
                    # Establecer fecha programada de pago al día 1 del mes correspondiente
                    payment_date = datetime(current_year, month, 1).date()
                    
                    # Obtener fecha límite de pago para este mes
                    try:
                        due_date_config = MonthlyPaymentDueDate.objects.get(month=month, is_active=True)
                        due_day = due_date_config.due_day
                    except MonthlyPaymentDueDate.DoesNotExist:
                        due_day = 10  # Valor por defecto
                    
                    # Calcular fecha límite (día 10 del mes correspondiente)
                    try:
                        due_date = datetime(current_year, month, due_day).date()
                    except ValueError:
                        # Si el día no es válido para ese mes (ej: 31 en febrero), usar el último día del mes
                        if month == 2:
                            due_date = datetime(current_year, month, 28).date()
                        else:
                            due_date = datetime(current_year, month, due_day).date()
                    
                    payment = Payment.objects.create(
                        student=cuatrimestre_enrollment.student,
                        payment_type=tuition_payment_type,
                        payment_method='TRANSFERENCIA',  # Por defecto, se puede cambiar
                        original_amount=monthly_amount,
                        month=month,
                        year=current_year,
                        payment_date=payment_date,  # Fecha programada: día 1 del mes
                        due_date=due_date,
                        status='NO_PAGADO',  # Estado inicial: NO_PAGADO
                        cuatrimestre_enrollment=cuatrimestre_enrollment,
                        notes=f'Colegiatura mensual - {dict(Payment.MONTHS)[month]} {current_year}'
                    )
                    payments_created.append(str(payment.id))
            
            # NO cambiar el estado aquí - se mantiene en PENDIENTE_PAGO hasta que se apruebe el pago de inscripción
            # El estado cambiará a EN_CURSO cuando se apruebe el pago de inscripción
            # cuatrimestre_enrollment.status permanece en 'PENDIENTE_PAGO'
        
        return Response({
            'message': 'Asignación confirmada. Plan de pagos generado.',
            'status': cuatrimestre_enrollment.status,
            'total_tuition': str(total_tuition),
            'payment_option': payment_option,
            'payments_created': payments_created
        })
    
    @action(detail=True, methods=['get'])
    def assignment_sheet(self, request, pk=None):
        """Generar hoja de asignación con información del estudiante, cursos, horarios y colegiatura"""
        cuatrimestre_enrollment = self.get_object()
        
        # Validar que tenga cursos asignados o pre-asignados
        courses_count = cuatrimestre_enrollment.course_enrollments.count()
        pre_assigned_ids = cuatrimestre_enrollment.pre_assign_course_ids or []
        
        if courses_count == 0 and len(pre_assigned_ids) == 0:
            return Response(
                {'error': 'No hay cursos asignados o pre-asignados.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener información del estudiante
        student = cuatrimestre_enrollment.student
        
        # Obtener cursos con horarios (solo para mostrar, no para calcular costo)
        # Puede venir de dos flujos:
        # 1. Cursos pre-asignados (pre_assign_course_ids) - antes de confirmar
        # 2. CourseEnrollment existentes - después de confirmar
        courses_data = []
        
        pre_assigned_ids = cuatrimestre_enrollment.pre_assign_course_ids or []
        
        if pre_assigned_ids:
            # Obtener cursos desde los IDs pre-asignados (antes de confirmar)
            from uuid import UUID
            from .models import Course
            course_uuids = [UUID(cid) for cid in pre_assigned_ids]
            courses = Course.objects.filter(id__in=course_uuids).prefetch_related('schedules')
        else:
            # Obtener cursos desde CourseEnrollment (después de confirmar)
            course_enrollments = cuatrimestre_enrollment.course_enrollments.select_related('course').prefetch_related('course__schedules').all()
            courses = [enrollment.course for enrollment in course_enrollments]
        
        for course in courses:
            schedules = [
                {
                    'day': schedule.day,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M')
                }
                for schedule in course.schedules.all()
            ]
            
            courses_data.append({
                'code': course.code,
                'name': course.name,
                'credits': course.credits,
                'schedules': schedules
            })
        
        # Obtener monto base mensual del tipo de pago 102 (Colegiatura de Cursos)
        career = cuatrimestre_enrollment.cuatrimestre.career
        try:
            tuition_payment_type = PaymentType.objects.get(code='102', is_active=True)
            base_monthly_amount = tuition_payment_type.amount or Decimal('0.00')
            if base_monthly_amount == 0:
                return Response(
                    {'error': 'Tipo de pago 102 (Colegiatura de Cursos) no tiene monto configurado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except PaymentType.DoesNotExist:
            return Response(
                {'error': 'Tipo de pago 102 (Colegiatura de Cursos) no encontrado. Ejecute el comando seed_payment_types.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calcular adicionales de cursos (course.cost ahora son adicionales)
        course_additionals = Decimal('0.00')
        for course in courses:
            course_additional = course.cost or Decimal('0.00')
            course_additionals += course_additional
        
        # Pago mensual total = base + adicionales
        monthly_amount = base_monthly_amount + course_additionals
        
        # Obtener período académico y configuración
        period = get_academic_period(cuatrimestre_enrollment.cuatrimestre.number)
        period_config = None
        try:
            period_config = AcademicPeriodConfig.objects.get(period=period, is_active=True)
            penalty_percentage = period_config.penalty_percentage
        except AcademicPeriodConfig.DoesNotExist:
            penalty_percentage = Decimal('5.00')  # Por defecto
        
        # Obtener meses del período y fechas límite
        if period_config:
            months = period_config.get_months()
        else:
            period_months = {
                1: [2, 3, 4, 5],  # Febrero-Mayo
                2: [6, 7, 8],  # Junio-Agosto
                3: [9, 10, 11, 12]  # Septiembre-Diciembre
            }
            months = period_months.get(period, [2, 3, 4, 5])
        
        # Calcular plan de pagos mensuales
        payment_plan = []
        current_year = cuatrimestre_enrollment.academic_year
        
        for month in months:
            try:
                due_date_config = MonthlyPaymentDueDate.objects.get(month=month, is_active=True)
                due_day = due_date_config.due_day
            except MonthlyPaymentDueDate.DoesNotExist:
                due_day = 10
            
            month_name = dict(Payment.MONTHS)[month]
            payment_plan.append({
                'month': month,
                'month_name': month_name,
                'year': current_year,
                'amount': str(monthly_amount),
                'due_day': due_day,
                'penalty_percentage': str(penalty_percentage)
            })
        
        # Información del período académico
        period_names = {
            1: 'Febrero - Mayo',
            2: 'Junio - Agosto',
            3: 'Septiembre - Diciembre'
        }
        period_name = period_names.get(period, '')
        
        # Formatear respuesta para hoja de asignación
        assignment_sheet = {
            'student': {
                'full_name': student.get_full_name(),
                'carnet': student.carnet or 'N/A',
                'career': cuatrimestre_enrollment.cuatrimestre.career.name
            },
            'enrollment': {
                'cuatrimestre': cuatrimestre_enrollment.cuatrimestre.name,
                'academic_year': cuatrimestre_enrollment.academic_year,
                'period': period,
                'period_name': period_name
            },
            'courses': courses_data,
            'tuition': {
                'base_monthly_amount': str(base_monthly_amount),  # Monto base del tipo 102
                'course_additionals': str(course_additionals),  # Adicionales de cursos
                'monthly_payment': str(monthly_amount),  # Pago mensual total
                'total_cuatrimestre': str(monthly_amount * len(months)),  # Total del cuatrimestre
                'payment_plan': payment_plan,
                'full_payment_discount': str((monthly_amount * len(months)) * Decimal('0.10')),
                'full_payment_total': str((monthly_amount * len(months)) * Decimal('0.90'))
            },
            'generated_at': timezone.now().isoformat()
        }
        
        return Response(assignment_sheet)
    
    @action(detail=True, methods=['post'])
    def pre_assign_courses(self, request, pk=None):
        """
        Pre-asignar cursos al cuatrimestre (flujo presencial guiado).
        Los cursos se pre-asignan pero NO se confirman hasta que se llame a confirm_course_assignment.
        """
        cuatrimestre_enrollment = self.get_object()
        
        # No permitir pre-asignar cursos si ya está confirmado
        if cuatrimestre_enrollment.status in ['EN_CURSO', 'FINALIZADO']:
            return Response(
                {
                    'error': f'No se pueden pre-asignar cursos. La asignación ya está confirmada (estado: {cuatrimestre_enrollment.get_status_display()}).'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        course_ids = request.data.get('course_ids', [])
        
        if not course_ids:
            return Response(
                {'error': 'course_ids es requerido (lista de IDs de cursos)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Usar el servicio de pre-asignación
        service = PreAssignCoursesService(cuatrimestre_enrollment)
        result = service.pre_assign_courses(course_ids)
        
        if not result['success']:
            return Response(
                {
                    'error': 'Error al pre-asignar cursos',
                    'errors': result['errors']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Refrescar desde la BD
        cuatrimestre_enrollment.refresh_from_db()
        
        return Response({
            'message': f'Se pre-asignaron {len(result["created"])} curso(s) exitosamente.',
            'created': result['created'],
            'errors': result['errors'],
            'status': cuatrimestre_enrollment.status,
            'status_display': cuatrimestre_enrollment.get_status_display()
        })
    
    @action(detail=True, methods=['get'])
    def preview_boleta(self, request, pk=None):
        """
        Generar boleta académica en PDF (PREVIEW).
        Esta boleta es SOLO INFORMATIVA antes de confirmar la asignación.
        """
        cuatrimestre_enrollment = self.get_object()
        
        # Validar que se pueda generar boleta
        if not cuatrimestre_enrollment.can_preview_boleta():
            return Response(
                {
                    'error': f'No se puede generar boleta. Estado actual: {cuatrimestre_enrollment.get_status_display()}. '
                             f'Debe tener cursos pre-asignados (estado: CURSOS_PREASIGNADOS).'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Generar PDF
            pdf_file = generate_assignment_boleta(cuatrimestre_enrollment)
            
            # Retornar como respuesta HTTP
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="boleta_asignacion_{cuatrimestre_enrollment.id}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Error al generar boleta: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def confirm_course_assignment(self, request, pk=None):
        """
        Confirmar asignación de cursos (PASO CRÍTICO).
        Una vez confirmada, los CourseEnrollment se vuelven definitivos y se generan los pagos.
        La asignación queda en estado EN_CURSO y no puede ser modificada ni eliminada.
        
        Body params:
            payment_option: 'monthly' para pagos mensuales o 'full' para pago completo (default: 'monthly')
        """
        cuatrimestre_enrollment = self.get_object()
        
        # No permitir confirmar si ya está confirmado
        if cuatrimestre_enrollment.status in ['EN_CURSO', 'FINALIZADO']:
            return Response(
                {
                    'error': f'La asignación ya está confirmada (estado: {cuatrimestre_enrollment.get_status_display()}). No se puede confirmar nuevamente.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener opción de pago del request
        payment_option = request.data.get('payment_option', 'monthly')
        
        # Usar el servicio de confirmación
        service = ConfirmCourseAssignmentService(cuatrimestre_enrollment)
        result = service.confirm_assignment(payment_option=payment_option)
        
        if not result['success']:
            return Response(
                {
                    'error': result['message'],
                    'errors': result['errors']
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Refrescar desde la BD
        cuatrimestre_enrollment.refresh_from_db()
        
        return Response({
            'message': result['message'],
            'status': cuatrimestre_enrollment.status,
            'status_display': cuatrimestre_enrollment.get_status_display(),
            'payments_created': result['payments_created'],
            'is_enrollment_fee_exempt': cuatrimestre_enrollment.is_enrollment_fee_exempt
        })
    
    @action(detail=True, methods=['get'])
    def payment_voucher(self, request, pk=None):
        """
        Generar talonario de pagos en PDF con los pagos mensuales del cuatrimestre.
        """
        cuatrimestre_enrollment = self.get_object()
        
        # Refrescar desde la BD para asegurar que tenemos los datos más recientes
        cuatrimestre_enrollment.refresh_from_db()
        
        # Validar que tenga pagos generados (pagos de colegiatura: códigos 102, 103 o 105)
        from payments.models import Payment, PaymentType
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Buscar todos los tipos de pago de colegiatura (102: sin beca, 103: media beca, 105: beca completa)
        tuition_payment_codes = ['102', '103', '105']
        tuition_payment_types = PaymentType.objects.filter(code__in=tuition_payment_codes, is_active=True)
        
        if not tuition_payment_types.exists():
            logger.error(f'No se encontraron tipos de pago de colegiatura (códigos 102, 103, 105) para cuatrimestre_enrollment {cuatrimestre_enrollment.id}')
            return Response(
                {'error': 'No se encontraron tipos de pago de colegiatura. Contacte al administrador.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Debug: Verificar todos los pagos relacionados
        all_payments = Payment.objects.filter(cuatrimestre_enrollment=cuatrimestre_enrollment)
        logger.info(f'Total pagos para cuatrimestre_enrollment {cuatrimestre_enrollment.id}: {all_payments.count()}')
        for p in all_payments:
            logger.info(f'  - Pago {p.id}: tipo={p.payment_type.code if p.payment_type else None}, monto={p.original_amount}')
        
        # Buscar pagos de colegiatura (cualquiera de los códigos: 102, 103, 105)
        payments = Payment.objects.filter(
            cuatrimestre_enrollment=cuatrimestre_enrollment,
            payment_type__in=tuition_payment_types
        )
        
        payments_count = payments.count()
        logger.info(f'Pagos de colegiatura (códigos 102, 103, 105) para cuatrimestre_enrollment {cuatrimestre_enrollment.id}: {payments_count}')
        
        if payments_count == 0:
            # Si está exonerado, no debería haber pagos de colegiatura
            if cuatrimestre_enrollment.is_enrollment_fee_exempt:
                return Response(
                    {'error': 'El estudiante está exonerado de pagos de colegiatura. No se requiere talonario de pagos.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar si los cursos tienen costo asignado
            course_enrollments = cuatrimestre_enrollment.course_enrollments.select_related('course').all()
            total_tuition = Decimal('0.00')
            for enrollment in course_enrollments:
                total_tuition += enrollment.course.cost or Decimal('0.00')
            
            if total_tuition == 0:
                return Response(
                    {
                        'error': 'Los cursos asignados no tienen costo asignado. No se requiere talonario de pagos.',
                        'status': cuatrimestre_enrollment.status,
                        'status_display': cuatrimestre_enrollment.get_status_display(),
                        'courses_count': course_enrollments.count(),
                        'hint': 'Asigne costos a los cursos para generar pagos de colegiatura.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar si hay otros tipos de pagos
            all_payments_count = Payment.objects.filter(
                cuatrimestre_enrollment=cuatrimestre_enrollment
            ).count()
            
            if all_payments_count == 0:
                return Response(
                    {
                        'error': 'No hay pagos generados para este cuatrimestre. Debe confirmar la asignación primero.',
                        'status': cuatrimestre_enrollment.status,
                        'status_display': cuatrimestre_enrollment.get_status_display(),
                        'hint': 'Si acaba de confirmar la asignación, espere unos segundos e intente nuevamente.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {
                        'error': 'No hay pagos de colegiatura generados. Solo se encontraron otros tipos de pagos.',
                        'tuition_payments_count': 0,
                        'other_payments_count': all_payments_count
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            # Generar PDF
            pdf_file = generate_payment_voucher(cuatrimestre_enrollment)
            
            # Retornar como respuesta HTTP
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="talonario_pagos_{cuatrimestre_enrollment.id}.pdf"'
            return response
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error al generar talonario de pagos: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Error al generar talonario: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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


class GraduationMethodViewSet(viewsets.ModelViewSet):
    queryset = GraduationMethod.objects.all()
    serializer_class = GraduationMethodSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'by_student']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_thesis')]
    
    def perform_create(self, serializer):
        """Capturar usuario que crea el método de graduación y validar que el estudiante haya completado el pensum"""
        student = serializer.validated_data.get('student')
        if not student or not student.pensum_closed:
            raise serializers.ValidationError(
                {'student': 'El estudiante debe haber completado todos los cursos del pensum para iniciar un método de graduación.'}
            )
        
        user = self.request.user if self.request.user.is_authenticated else None
        instance = serializer.save()
        instance._changed_by_user = user
        instance._status_change_notes = 'Método de graduación creado'
        return instance
    
    def perform_update(self, serializer):
        """Capturar usuario que realiza el cambio"""
        user = self.request.user if self.request.user.is_authenticated else None
        instance = serializer.save()
        instance._changed_by_user = user
        instance._status_change_notes = self.request.data.get('notes', '') or ''
        return instance
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Actualizar estado del método de graduación"""
        graduation_method = self.get_object()
        new_status = request.data.get('status')
        
        if new_status:
            # Pasar usuario para el historial de cambios
            user = request.user if request.user.is_authenticated else None
            graduation_method._changed_by_user = user
            graduation_method._status_change_notes = request.data.get('notes', '') or f'Estado cambiado a {new_status}'
            
            graduation_method.status = new_status
            if new_status == 'SOLICITUD_ASESOR' and not graduation_method.student.graduation_method_started:
                graduation_method.student.graduation_method_started = True
                graduation_method.student.save()
            graduation_method.save()
        
        serializer = self.get_serializer(graduation_method)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Obtener método de graduación de un estudiante"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            graduation_method = GraduationMethod.objects.get(student_id=student_id)
            serializer = self.get_serializer(graduation_method)
            return Response(serializer.data)
        except GraduationMethod.DoesNotExist:
            return Response(
                {'error': 'El estudiante no tiene método de graduación registrado'},
                status=status.HTTP_404_NOT_FOUND
            )

