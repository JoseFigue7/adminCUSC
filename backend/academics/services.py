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
    def confirm_assignment(self, payment_option='monthly'):
        """
        Confirmar la asignación de cursos y generar pagos.
        
        Args:
            payment_option: 'monthly' para pagos mensuales o 'full' para pago completo
        
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'payments_created': list of payment IDs,
                'errors': list of error messages
            }
        """
        # Validar que se pueda confirmar
        # Permitir confirmar si:
        # 1. Estado es CURSOS_PREASIGNADOS (flujo normal)
        # 2. Estado es PENDIENTE_PAGO pero no hay pagos generados (confirmación incompleta anterior)
        from payments.models import Payment, PaymentType
        
        can_confirm = False
        if self.cuatrimestre_enrollment.status == 'CURSOS_PREASIGNADOS':
            can_confirm = True
        elif self.cuatrimestre_enrollment.status == 'PENDIENTE_PAGO':
            # Verificar si ya hay pagos de colegiatura generados
            try:
                tuition_payment_type = PaymentType.objects.get(code='201')
                existing_payments = Payment.objects.filter(
                    cuatrimestre_enrollment=self.cuatrimestre_enrollment,
                    payment_type=tuition_payment_type
                )
                # Si no hay pagos, permitir confirmar (confirmación incompleta)
                if not existing_payments.exists():
                    can_confirm = True
            except PaymentType.DoesNotExist:
                # Si no existe el tipo de pago, permitir confirmar
                can_confirm = True
        
        if not can_confirm:
            return {
                'success': False,
                'message': f'No se puede confirmar la asignación. Estado actual: {self.cuatrimestre_enrollment.get_status_display()}',
                'payments_created': [],
                'errors': ['El estado debe ser CURSOS_PREASIGNADOS para confirmar, o PENDIENTE_PAGO sin pagos generados.']
            }
        
        # Validar que tenga cursos para confirmar
        # Puede venir de dos flujos:
        # 1. Nuevo flujo: cursos en pre_assign_course_ids (aún no creados como CourseEnrollment)
        # 2. Flujo antiguo: CourseEnrollment ya creados pero estado aún en CURSOS_PREASIGNADOS
        pre_assigned_ids = self.cuatrimestre_enrollment.pre_assign_course_ids or []
        existing_enrollments = self.cuatrimestre_enrollment.course_enrollments.filter(
            status__in=['MATRICULADO', 'CURSOS_PREASIGNADOS']
        )
        
        # Si no hay cursos pre-asignados NI enrollments existentes, error
        if len(pre_assigned_ids) == 0 and existing_enrollments.count() == 0:
            return {
                'success': False,
                'message': 'No hay cursos asignados para confirmar.',
                'payments_created': [],
                'errors': ['Debe haber al menos un curso asignado antes de confirmar.']
            }
        
        # AHORA SÍ: Crear los CourseEnrollment definitivos desde los IDs pre-asignados (si existen)
        from uuid import UUID
        created_enrollments = []
        
        try:
            # Si hay cursos en pre_assign_course_ids, crear CourseEnrollment desde esos IDs
            if len(pre_assigned_ids) > 0:
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
                    
                    # Verificar si ya existe un CourseEnrollment para este curso en este cuatrimestre
                    existing = CourseEnrollment.objects.filter(
                        student=self.student,
                        course=course,
                        cuatrimestre_enrollment=self.cuatrimestre_enrollment
                    ).first()
                    
                    if existing:
                        # Si ya existe, solo asegurarse de que esté en estado MATRICULADO
                        if existing.status != 'MATRICULADO':
                            existing.status = 'MATRICULADO'
                            existing.save()
                        created_enrollments.append(str(existing.id))
                    else:
                        # Crear nuevo CourseEnrollment definitivo
                        enrollment = CourseEnrollment.objects.create(
                            student=self.student,
                            course=course,
                            cuatrimestre_enrollment=self.cuatrimestre_enrollment,
                            status='MATRICULADO'
                        )
                        created_enrollments.append(str(enrollment.id))
                
                # Limpiar los IDs pre-asignados ahora que se crearon los CourseEnrollment
                self.cuatrimestre_enrollment.pre_assign_course_ids = []
            else:
                # Flujo antiguo: los CourseEnrollment ya existen, solo asegurarse de que estén en MATRICULADO
                for enrollment in existing_enrollments:
                    if enrollment.status != 'MATRICULADO':
                        enrollment.status = 'MATRICULADO'
                        enrollment.save()
                    created_enrollments.append(str(enrollment.id))
        except Exception as e:
            return {
                'success': False,
                'message': f'Error al crear CourseEnrollment: {str(e)}',
                'payments_created': [],
                'errors': [str(e)]
            }
        
        # Determinar el estado final - siempre pasar a EN_CURSO después de confirmar
        # La asignación queda finalizada y no se puede modificar
        new_status = 'EN_CURSO'
        
        # Cambiar estado usando el manager (valida que no haya otra inscripción EN_CURSO)
        CuatrimestreEnrollment.objects.update_to_en_curso(self.cuatrimestre_enrollment)
        
        # Generar pagos según la opción seleccionada
        if payment_option == 'full':
            payments_created = self._generate_full_payment()
        else:
            payments_created = self._generate_monthly_payments()
        
        # Refrescar el objeto desde la BD para asegurar que los cambios estén disponibles
        self.cuatrimestre_enrollment.refresh_from_db()
        
        # Verificar si se crearon pagos
        if len(payments_created) == 0:
            # Calcular si los cursos tienen costo
            total_tuition = Decimal('0.00')
            for enrollment in self.cuatrimestre_enrollment.course_enrollments.select_related('course').all():
                total_tuition += enrollment.course.cost or Decimal('0.00')
            
            if total_tuition == 0:
                payment_message = 'Los cursos asignados no tienen costo asignado. No se generaron pagos.'
            else:
                payment_message = 'No se pudieron generar los pagos. Contacte al administrador.'
        else:
            payment_message = 'Pagos mensuales generados.' if payment_option == 'monthly' else 'Pago completo con descuento generado.'
        
        return {
            'success': True,
            'message': f'Asignación confirmada exitosamente. {payment_message}',
            'payments_created': payments_created,
            'errors': [],
            'no_payments_reason': 'no_cost' if len(payments_created) == 0 else None
        }
    
    def _generate_monthly_payments(self):
        """
        Generar pagos mensuales del cuatrimestre.
        El pago mensual = Monto base del tipo 102 (PaymentType) + adicionales de cursos (course.cost)
        
        Returns:
            list: Lista de IDs de pagos creados
        """
        from payments.models import Payment, PaymentType
        from datetime import datetime
        
        # Obtener carrera del estudiante
        career = self.cuatrimestre_enrollment.cuatrimestre.career
        
        # Obtener monto base mensual del tipo de pago 102 (Colegiatura de Cursos)
        try:
            tuition_payment_type = PaymentType.objects.get(code='102', is_active=True)
            base_monthly_amount = tuition_payment_type.amount or Decimal('0.00')
            if base_monthly_amount == 0:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning('Tipo de pago 102 (Colegiatura de Cursos) no tiene monto configurado. No se generan pagos.')
                return []
        except PaymentType.DoesNotExist:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('Tipo de pago 102 (Colegiatura de Cursos) no encontrado. Ejecute el comando seed_payment_types.')
            return []
        
        # Calcular adicionales de cursos (course.cost ahora son adicionales, no el costo total)
        course_additionals = Decimal('0.00')
        course_enrollments = self.cuatrimestre_enrollment.course_enrollments.select_related('course').all()
        
        for enrollment in course_enrollments:
            course_additional = enrollment.course.cost or Decimal('0.00')
            course_additionals += course_additional
        
        # Pago mensual total = base + adicionales
        monthly_amount = base_monthly_amount + course_additionals
        
        if monthly_amount == 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'No se generan pagos para cuatrimestre_enrollment {self.cuatrimestre_enrollment.id}: el monto mensual es cero')
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
                1: [2, 3, 4, 5],  # Febrero-Mayo
                2: [6, 7, 8],  # Junio-Agosto
                3: [9, 10, 11, 12]  # Septiembre-Diciembre
            }
            months = period_months.get(period, [2, 3, 4, 5])
        
        # Obtener tipo de pago de colegiatura (código 102)
        try:
            tuition_payment_type = PaymentType.objects.get(code='102')
        except PaymentType.DoesNotExist:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('Tipo de pago 102 (Colegiatura de Cursos) no encontrado. Ejecute el comando seed_payment_types.')
            return []
        
        # Verificar si ya existen pagos para este cuatrimestre enrollment
        existing_payments = Payment.objects.filter(
            cuatrimestre_enrollment=self.cuatrimestre_enrollment,
            payment_type=tuition_payment_type
        )
        
        # Si ya existen pagos, no crear duplicados
        if existing_payments.exists():
            return [str(p.id) for p in existing_payments]
        
        # Generar pagos mensuales (uno por cada mes del período)
        current_year = self.cuatrimestre_enrollment.academic_year
        payments_created = []
        
        for month in months:  # Generar un pago por cada mes del período
            # Establecer fecha programada de pago al día 1 del mes correspondiente
            payment_date = datetime(current_year, month, 1).date()
            
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
            
            # Crear pago con estado inicial NO_PAGADO y fecha programada al día 1
            payment = Payment.objects.create(
                student=self.student,
                payment_type=tuition_payment_type,
                payment_method='TRANSFERENCIA',  # Por defecto, se puede cambiar
                original_amount=monthly_amount,
                month=month,
                year=current_year,
                payment_date=payment_date,  # Fecha programada: día 1 del mes
                due_date=due_date,
                status='NO_PAGADO',  # Estado inicial: NO_PAGADO
                cuatrimestre_enrollment=self.cuatrimestre_enrollment,
                notes=f'Colegiatura mensual - {dict(Payment.MONTHS)[month]} {current_year}'
            )
            payments_created.append(str(payment.id))
        
        return payments_created
    
    def _generate_full_payment(self):
        """
        Generar un solo pago completo con 10% de descuento.
        
        Returns:
            list: Lista con un solo ID de pago creado
        """
        from payments.models import Payment, PaymentType
        from datetime import datetime
        
        # Obtener carrera del estudiante
        career = self.cuatrimestre_enrollment.cuatrimestre.career
        
        # Obtener monto base mensual del tipo de pago 102 (Colegiatura de Cursos)
        try:
            tuition_payment_type = PaymentType.objects.get(code='102', is_active=True)
            base_monthly_amount = tuition_payment_type.amount or Decimal('0.00')
            if base_monthly_amount == 0:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning('Tipo de pago 102 (Colegiatura de Cursos) no tiene monto configurado. No se genera pago.')
                return None
        except PaymentType.DoesNotExist:
            import logging
            logger = logging.getLogger(__name__)
            logger.error('Tipo de pago 102 (Colegiatura de Cursos) no encontrado. Ejecute el comando seed_payment_types.')
            return None
        
        # Calcular adicionales de cursos (course.cost ahora son adicionales, no el costo total)
        course_additionals = Decimal('0.00')
        course_enrollments = self.cuatrimestre_enrollment.course_enrollments.select_related('course').all()
        
        for enrollment in course_enrollments:
            course_additional = enrollment.course.cost or Decimal('0.00')
            course_additionals += course_additional
        
        # Pago mensual total = base + adicionales
        monthly_amount = base_monthly_amount + course_additionals
        
        if monthly_amount == 0:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'No se generan pagos para cuatrimestre_enrollment {self.cuatrimestre_enrollment.id}: el monto mensual es cero')
            return []
        
        # Obtener período académico para determinar fecha límite
        period = get_academic_period(self.cuatrimestre_enrollment.cuatrimestre.number)
        if not period:
            return []
        
        # Obtener meses del período para determinar fecha límite (usar el primer mes)
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
        
        # Verificar si ya existen pagos para este cuatrimestre enrollment
        existing_payments = Payment.objects.filter(
            cuatrimestre_enrollment=self.cuatrimestre_enrollment,
            payment_type=tuition_payment_type
        )
        
        # Si ya existen pagos, no crear duplicados
        if existing_payments.exists():
            return [str(p.id) for p in existing_payments]
        
        # Calcular monto con descuento (10% de descuento)
        # Total del cuatrimestre = pago_mensual * número_de_meses
        total_cuatrimestre = monthly_amount * len(months)
        discounted_amount = total_cuatrimestre * Decimal('0.90')
        current_year = self.cuatrimestre_enrollment.academic_year
        first_month = months[0] if months else 1
        
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
        
        # Establecer fecha programada de pago al día 1 del primer mes del período
        payment_date = datetime(current_year, first_month, 1).date()
        
        # Crear pago completo
        payment = Payment.objects.create(
            student=self.student,
            payment_type=tuition_payment_type,
            payment_method='TRANSFERENCIA',  # Por defecto, se puede cambiar
            original_amount=discounted_amount,
            month=first_month,
            year=current_year,
            payment_date=payment_date,  # Fecha programada: día 1 del primer mes
            due_date=due_date,
            status='NO_PAGADO',  # Estado inicial: NO_PAGADO
            cuatrimestre_enrollment=self.cuatrimestre_enrollment,
            notes=f'Pago completo de colegiatura con 10% descuento. Monto original: {total_cuatrimestre}, Descuento: {total_cuatrimestre * Decimal("0.10")}, Pago mensual base: {base_monthly_amount}, Adicionales cursos: {course_additionals}'
        )
        
        return [str(payment.id)]
    