"""
Servicios de negocio para el flujo presencial y guiado de inscripción
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    CuatrimestreEnrollment, CourseEnrollment, Course, CourseSchedule,
    get_academic_period, get_cuatrimestres_by_period,
    AcademicPeriodConfig, MonthlyPaymentDueDate
)


class PreAssignCoursesService:
    """
    Servicio para pre-asignar cursos a un CuatrimestreEnrollment.
    Los cursos se pre-asignan pero NO se crean CourseEnrollment definitivos.
    Se valida prerequisitos y horarios.
    """
    
    def __init__(self, cuatrimestre_enrollment):
        self.cuatrimestre_enrollment = cuatrimestre_enrollment
        self.student = cuatrimestre_enrollment.student
    
    def validate_prerequisites(self, course):
        """
        Validar que el estudiante cumpla con los prerequisitos del curso.
        
        Args:
            course: Curso a validar
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not course.prerequisite:
            return True, None
        
        # Verificar que el estudiante haya aprobado el prerequisito
        prerequisite_enrollment = CourseEnrollment.objects.filter(
            student=self.student,
            course=course.prerequisite,
            status='APROBADO'
        ).first()
        
        if not prerequisite_enrollment:
            return False, f"El curso {course.code} requiere haber aprobado {course.prerequisite.code} - {course.prerequisite.name}"
        
        return True, None
    
    def validate_schedule_overlaps(self, courses_to_assign):
        """
        Validar que no haya traslapes de horarios entre los cursos a asignar.
        
        Args:
            courses_to_assign: Lista de cursos a validar
            
        Returns:
            tuple: (is_valid, list_of_errors)
        """
        errors = []
        courses_list = list(courses_to_assign)
        
        for i, course1 in enumerate(courses_list):
            schedules1 = list(course1.schedules.all())
            if not schedules1:
                errors.append(f"El curso {course1.code} - {course1.name} no tiene horarios asignados.")
                continue
            
            for j, course2 in enumerate(courses_list[i+1:], start=i+1):
                schedules2 = list(course2.schedules.all())
                if not schedules2:
                    errors.append(f"El curso {course2.code} - {course2.name} no tiene horarios asignados.")
                    continue
                
                # Verificar traslapes entre horarios de course1 y course2
                for schedule1 in schedules1:
                    for schedule2 in schedules2:
                        if schedule1.overlaps_with(schedule2):
                            errors.append(
                                f"Los cursos {course1.code} y {course2.code} tienen horarios que se traslapan "
                                f"({schedule1.day} {schedule1.start_time.strftime('%H:%M')}-{schedule1.end_time.strftime('%H:%M')} "
                                f"y {schedule2.day} {schedule2.start_time.strftime('%H:%M')}-{schedule2.end_time.strftime('%H:%M')})"
                            )
                            break
                    if errors and errors[-1].startswith(f"Los cursos {course1.code} y {course2.code}"):
                        break
                if errors and errors[-1].startswith(f"Los cursos {course1.code} y {course2.code}"):
                    break
        
        return len(errors) == 0, errors
    
    def validate_courses_belong_to_period(self, course_ids):
        """
        Validar que los cursos pertenezcan al período académico del cuatrimestre.
        
        Args:
            course_ids: Lista de IDs de cursos
            
        Returns:
            tuple: (is_valid, courses, error_message)
        """
        enrollment_period = get_academic_period(self.cuatrimestre_enrollment.cuatrimestre.number)
        if not enrollment_period:
            return False, [], 'No se pudo determinar el período académico del cuatrimestre'
        
        period_cuatrimestres = get_cuatrimestres_by_period(enrollment_period)
        
        courses = Course.objects.filter(
            id__in=course_ids,
            cuatrimestre__number__in=period_cuatrimestres,
            cuatrimestre__career=self.cuatrimestre_enrollment.cuatrimestre.career
        ).select_related('cuatrimestre').prefetch_related('schedules', 'prerequisite')
        
        if courses.count() != len(course_ids):
            found_course_ids = set(courses.values_list('id', flat=True))
            missing_course_ids = [cid for cid in course_ids if cid not in found_course_ids]
            
            all_courses = Course.objects.filter(id__in=missing_course_ids).select_related('cuatrimestre')
            errors_detail = []
            for course in all_courses:
                if course.cuatrimestre.number not in period_cuatrimestres:
                    errors_detail.append(
                        f"El curso {course.code} pertenece al cuatrimestre {course.cuatrimestre.number} "
                        f"(período {get_academic_period(course.cuatrimestre.number)}), "
                        f"pero la inscripción es para el período {enrollment_period} "
                        f"(cuatrimestres {period_cuatrimestres})"
                    )
                elif course.cuatrimestre.career_id != self.cuatrimestre_enrollment.cuatrimestre.career_id:
                    errors_detail.append(
                        f"El curso {course.code} pertenece a la carrera {course.cuatrimestre.career.name}, "
                        f"pero la inscripción es para la carrera {self.cuatrimestre_enrollment.cuatrimestre.career.name}"
                    )
            
            return False, [], f"Algunos cursos no pertenecen al período académico: {', '.join(errors_detail)}"
        
        return True, list(courses), None
    
    @transaction.atomic
    def pre_assign_courses(self, course_ids):
        """
        Pre-asignar cursos al cuatrimestre enrollment.
        Crea CourseEnrollment temporales que pueden ser modificados antes de confirmar.
        
        Args:
            course_ids: Lista de IDs de cursos a pre-asignar
            
        Returns:
            dict: {
                'success': bool,
                'created': list of course enrollment IDs,
                'errors': list of error messages
            }
        """
        # Validar estado
        if not self.cuatrimestre_enrollment.can_assign_courses():
            return {
                'success': False,
                'created': [],
                'errors': [f'El estado actual ({self.cuatrimestre_enrollment.get_status_display()}) no permite asignar cursos. Debe estar en PRE_INSCRIPCION o CURSOS_PREASIGNADOS.']
            }
        
        # Validar máximo 7 cursos
        if len(course_ids) > 7:
            return {
                'success': False,
                'created': [],
                'errors': ['No se pueden pre-asignar más de 7 cursos por cuatrimestre.']
            }
        
        # Validar que los cursos pertenezcan al período
        is_valid, courses, error_msg = self.validate_courses_belong_to_period(course_ids)
        if not is_valid:
            return {
                'success': False,
                'created': [],
                'errors': [error_msg]
            }
        
        # Validar prerequisitos
        prerequisite_errors = []
        for course in courses:
            is_valid, error = self.validate_prerequisites(course)
            if not is_valid:
                prerequisite_errors.append(error)
        
        if prerequisite_errors:
            return {
                'success': False,
                'created': [],
                'errors': prerequisite_errors
            }
        
        # Validar traslapes de horarios
        is_valid, schedule_errors = self.validate_schedule_overlaps(courses)
        if not is_valid:
            return {
                'success': False,
                'created': [],
                'errors': schedule_errors
            }
        
        # Validar cursos y guardar IDs temporalmente (NO crear CourseEnrollment todavía)
        validated_course_ids = []
        errors = []
        
        for course in courses:
            try:
                # Validar que no esté ya aprobado
                approved_enrollment = CourseEnrollment.objects.filter(
                    student=self.student,
                    course=course,
                    status='APROBADO'
                ).first()
                
                if approved_enrollment:
                    errors.append(f"El curso {course.code} - {course.name} ya fue aprobado. No se puede volver a inscribir.")
                    continue
                
                # Solo guardar el ID, NO crear CourseEnrollment
                validated_course_ids.append(str(course.id))
            except Exception as e:
                errors.append(f"Error al validar curso {course.code}: {str(e)}")
        
        # Si hay errores, no actualizar nada
        if errors:
            return {
                'success': False,
                'created': [],
                'errors': errors
            }
        
        # Guardar los IDs de cursos pre-asignados en el campo JSONField (NO crear CourseEnrollment)
        self.cuatrimestre_enrollment.pre_assign_course_ids = validated_course_ids
        self.cuatrimestre_enrollment.status = 'CURSOS_PREASIGNADOS'
        self.cuatrimestre_enrollment.save()
        
        return {
            'success': True,
            'created': validated_course_ids,  # Retornar IDs en lugar de IDs de CourseEnrollment
            'errors': []
        }


class ConfirmCourseAssignmentService:
    """
    Servicio para confirmar la asignación de cursos.
    Una vez confirmada, los CourseEnrollment se vuelven definitivos y no se pueden modificar.
    Se generan los pagos mensuales automáticamente.
    """
    
    def __init__(self, cuatrimestre_enrollment):
        self.cuatrimestre_enrollment = cuatrimestre_enrollment
        self.student = cuatrimestre_enrollment.student
    
    @transaction.atomic
    def confirm_assignment(self):
        """
        Confirmar la asignación de cursos y generar pagos.
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'payments_created': list of payment IDs,
                'errors': list of error messages
            }
        """
        # Validar que se pueda confirmar
        if self.cuatrimestre_enrollment.status != 'CURSOS_PREASIGNADOS':
            return {
                'success': False,
                'message': f'No se puede confirmar la asignación. Estado actual: {self.cuatrimestre_enrollment.get_status_display()}',
                'payments_created': [],
                'errors': ['El estado debe ser CURSOS_PREASIGNADOS para confirmar.']
            }
        
        # Validar que tenga cursos pre-asignados
        pre_assigned_ids = self.cuatrimestre_enrollment.pre_assign_course_ids or []
        if len(pre_assigned_ids) == 0:
            return {
                'success': False,
                'message': 'No hay cursos pre-asignados para confirmar.',
                'payments_created': [],
                'errors': ['Debe haber al menos un curso pre-asignado.']
            }
        
        # AHORA SÍ: Crear los CourseEnrollment definitivos desde los IDs pre-asignados
        from uuid import UUID
        created_enrollments = []
        
        try:
            # Convertir IDs string a UUID
            course_uuids = [UUID(cid) for cid in pre_assigned_ids]
            
            # Obtener los cursos
            courses = Course.objects.filter(id__in=course_uuids)
            
            if courses.count() != len(course_uuids):
                return {
                    'success': False,
                    'message': 'Algunos cursos pre-asignados no fueron encontrados.',
                    'payments_created': [],
                    'errors': ['Error al validar cursos pre-asignados.']
                }
            
            # Crear CourseEnrollment definitivos
            for course in courses:
                # Validar que no esté ya aprobado
                approved_enrollment = CourseEnrollment.objects.filter(
                    student=self.student,
                    course=course,
                    status='APROBADO'
                ).first()
                
                if approved_enrollment:
                    continue  # Saltar cursos ya aprobados
                
                # Crear CourseEnrollment definitivo
                enrollment = CourseEnrollment.objects.create(
                    student=self.student,
                    course=course,
                    cuatrimestre_enrollment=self.cuatrimestre_enrollment,
                    status='MATRICULADO'
                )
                created_enrollments.append(str(enrollment.id))
            
            # Limpiar los IDs pre-asignados ahora que se crearon los CourseEnrollment
            self.cuatrimestre_enrollment.pre_assign_course_ids = []
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al crear CourseEnrollment: {str(e)}',
                'payments_created': [],
                'errors': [str(e)]
            }
        
        # Determinar el estado final según si está exonerado
        if self.cuatrimestre_enrollment.is_enrollment_fee_exempt:
            # Si está exonerado, pasar directamente a EN_CURSO
            new_status = 'EN_CURSO'
        else:
            # Si no está exonerado, pasar a PENDIENTE_PAGO
            new_status = 'PENDIENTE_PAGO'
        
        # Cambiar estado usando el manager si es EN_CURSO
        if new_status == 'EN_CURSO':
            CuatrimestreEnrollment.objects.update_to_en_curso(self.cuatrimestre_enrollment)
        else:
            self.cuatrimestre_enrollment.status = new_status
            self.cuatrimestre_enrollment.save()
        
        # Generar pagos mensuales
        payments_created = self._generate_monthly_payments()
        
        return {
            'success': True,
            'message': 'Asignación confirmada exitosamente. Pagos mensuales generados.',
            'payments_created': payments_created,
            'errors': []
        }
    
    def _generate_monthly_payments(self):
        """
        Generar pagos mensuales del cuatrimestre.
        
        Returns:
            list: Lista de IDs de pagos creados
        """
        from payments.models import Payment, PaymentType, PaymentConfiguration
        from datetime import datetime
        
        # Calcular colegiatura total
        total_tuition = Decimal('0.00')
        for enrollment in self.cuatrimestre_enrollment.course_enrollments.select_related('course').all():
            total_tuition += enrollment.course.cost or Decimal('0.00')
        
        if total_tuition == 0:
            return []
        
        # Obtener período académico
        period = get_academic_period(self.cuatrimestre_enrollment.cuatrimestre.number)
        if not period:
            return []
        
        # Obtener meses del período
        try:
            period_config = AcademicPeriodConfig.objects.get(period=period, is_active=True)
            months = period_config.get_months()
        except AcademicPeriodConfig.DoesNotExist:
            # Fallback a meses por defecto
            period_months = {
                1: [1, 2, 3, 4],
                2: [5, 6, 7, 8],
                3: [9, 10, 11, 12]
            }
            months = period_months.get(period, [1, 2, 3, 4])
        
        # Obtener o crear tipo de pago de colegiatura
        tuition_payment_type, _ = PaymentType.objects.get_or_create(
            code='201',
            defaults={
                'name': 'Colegiatura Cursos',
                'description': 'Pago de colegiatura por cursos',
                'is_active': True
            }
        )
        
        # Generar pagos mensuales (4 pagos)
        monthly_amount = total_tuition / 4
        current_year = self.cuatrimestre_enrollment.academic_year
        payments_created = []
        
        for month in months[:4]:  # Solo los primeros 4 meses del período
            # Obtener fecha límite de pago
            try:
                due_date_config = MonthlyPaymentDueDate.objects.get(month=month, is_active=True)
                due_day = due_date_config.due_day
            except MonthlyPaymentDueDate.DoesNotExist:
                due_day = 10  # Valor por defecto
            
            # Calcular fecha límite
            try:
                due_date = datetime(current_year, month, due_day).date()
            except ValueError:
                # Si el día no es válido para ese mes, usar el último día del mes
                if month == 2:
                    due_date = datetime(current_year, month, 28).date()
                else:
                    due_date = datetime(current_year, month, due_day).date()
            
            # Crear pago
            payment = Payment.objects.create(
                student=self.student,
                payment_type=tuition_payment_type,
                payment_method='TRANSFERENCIA',  # Por defecto, se puede cambiar
                original_amount=monthly_amount,
                month=month,
                year=current_year,
                due_date=due_date,
                status='PENDIENTE',
                cuatrimestre_enrollment=self.cuatrimestre_enrollment,
                notes=f'Colegiatura mensual - {dict(Payment.MONTHS)[month]} {current_year}'
            )
            payments_created.append(str(payment.id))
        
        return payments_created
