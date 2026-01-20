from django.db import models, transaction
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import uuid
import json


class Career(models.Model):
    """Modelo para carreras con campos requeridos por la SEP"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.IntegerField(unique=True, verbose_name='Código de carrera')
    name = models.CharField(max_length=200, unique=True, verbose_name='Nombre de la carrera')
    description = models.TextField(blank=True, verbose_name='Descripción')
    total_credits = models.IntegerField(default=0, verbose_name='Total de créditos')
    max_scholarships_full = models.IntegerField(default=0, verbose_name='Máximo de becas completas')
    max_scholarships_half = models.IntegerField(default=0, verbose_name='Máximo de medias becas')
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    
    # Campos SEP requeridos (temporalmente opcionales para migración)
    institution_key = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Clave de la institución',
        help_text='Texto, 10 caracteres, proporcionada por la Dirección General de Profesiones de la SEP',
        validators=[RegexValidator(regex=r'^.{10}$', message="Debe tener exactamente 10 caracteres")]
    )
    career_key = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Clave de la carrera',
        help_text='Texto, 10 caracteres, proporcionada por la Dirección General de Profesiones de la SEP',
        validators=[RegexValidator(regex=r'^.{10}$', message="Debe tener exactamente 10 caracteres")]
    )
    cct = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Clave del Centro de Trabajo (CCT)',
        help_text='Texto, 10 caracteres, de la institución particular titular del RVOE',
        validators=[RegexValidator(regex=r'^.{10}$', message="Debe tener exactamente 10 caracteres")]
    )
    rvoe_agreement_number = models.CharField(
        max_length=70,
        blank=True,
        null=True,
        verbose_name='Número de Acuerdo de RVOE',
        help_text='Texto, máximo 70 caracteres'
    )
    rvoe_agreement_date = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        verbose_name='Fecha del Acuerdo de RVOE',
        help_text='Numérico, 8 caracteres, formato aaaammdd',
        validators=[RegexValidator(regex=r'^\d{8}$', message="Debe ser formato aaaammdd (8 dígitos)")]
    )
    rvoe = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='RVOE',
        help_text='Código RVOE de la carrera (ej: 20260159)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """Validar restricciones de negocio antes de guardar"""
        from django.core.exceptions import ValidationError
        
        # Validar que los campos SEP requeridos tengan el formato correcto
        if self.institution_key and len(self.institution_key) != 10:
            raise ValidationError({
                'institution_key': 'La clave de institución debe tener exactamente 10 caracteres.'
            })
        
        if self.career_key and len(self.career_key) != 10:
            raise ValidationError({
                'career_key': 'La clave de carrera debe tener exactamente 10 caracteres.'
            })
        
        if self.cct and len(self.cct) != 10:
            raise ValidationError({
                'cct': 'El CCT debe tener exactamente 10 caracteres.'
            })
        
        if self.rvoe_agreement_date and len(self.rvoe_agreement_date) != 8:
            raise ValidationError({
                'rvoe_agreement_date': 'La fecha del acuerdo RVOE debe tener 8 dígitos en formato aaaammdd.'
            })
    
    def save(self, *args, **kwargs):
        """Guardar con validación"""
        self.full_clean()
        super().save(*args, **kwargs)


class Cuatrimestre(models.Model):
    """Modelo para cuatrimestres"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    career = models.ForeignKey(Career, on_delete=models.CASCADE, related_name='cuatrimestres', verbose_name='Carrera')
    number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)], verbose_name='Número de cuatrimestre')
    name = models.CharField(max_length=100, verbose_name='Nombre del cuatrimestre')
    
    class Meta:
        verbose_name = 'Cuatrimestre'
        verbose_name_plural = 'Cuatrimestres'
        unique_together = ['career', 'number']
        ordering = ['career', 'number']
    
    def __str__(self):
        return f"{self.career.name} - {self.name}"


class Course(models.Model):
    """Modelo para cursos"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    career = models.ForeignKey(Career, on_delete=models.CASCADE, related_name='courses', verbose_name='Carrera')
    cuatrimestre = models.ForeignKey(Cuatrimestre, on_delete=models.CASCADE, related_name='courses', verbose_name='Cuatrimestre')
    code = models.CharField(max_length=20, verbose_name='Código del curso')
    name = models.CharField(max_length=200, verbose_name='Nombre del curso')
    credits = models.IntegerField(default=0, verbose_name='Créditos')
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Costo del curso',
        help_text='Costo de la colegiatura para este curso'
    )
    is_required = models.BooleanField(default=True, verbose_name='Obligatorio')
    prerequisite = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Prerequisito')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        unique_together = ['career', 'code']
        ordering = ['cuatrimestre', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_academic_period(self):
        """
        Determina el período académico (1, 2 o 3) basado en el número de cuatrimestre.
        Período 1 (Febrero-Mayo): Cuatrimestres 1, 4, 7
        Período 2 (Junio-Agosto): Cuatrimestres 2, 5, 8
        Período 3 (Septiembre-Diciembre): Cuatrimestres 3, 6, 9
        """
        if self.cuatrimestre:
            number = self.cuatrimestre.number
            # Determinar período: 1,4,7 -> 1; 2,5,8 -> 2; 3,6,9 -> 3
            period_map = {
                1: 1, 4: 1, 7: 1,
                2: 2, 5: 2, 8: 2,
                3: 3, 6: 3, 9: 3
            }
            return period_map.get(number, None)
        return None


class CourseSchedule(models.Model):
    """Modelo para horarios de cursos"""
    
    DAY_CHOICES = [
        ('Lunes', 'Lunes'),
        ('Martes', 'Martes'),
        ('Miércoles', 'Miércoles'),
        ('Jueves', 'Jueves'),
        ('Viernes', 'Viernes'),
        ('Sábado', 'Sábado'),
        ('Domingo', 'Domingo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Curso'
    )
    day = models.CharField(
        max_length=20,
        choices=DAY_CHOICES,
        verbose_name='Día'
    )
    start_time = models.TimeField(verbose_name='Hora de inicio')
    end_time = models.TimeField(verbose_name='Hora de fin')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Horario de Curso'
        verbose_name_plural = 'Horarios de Cursos'
        ordering = ['course', 'day', 'start_time']
        indexes = [
            models.Index(fields=['course', 'day']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.day} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
    
    def clean(self):
        """Validar que la hora de fin sea mayor que la hora de inicio"""
        from django.core.exceptions import ValidationError
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                raise ValidationError({
                    'end_time': 'La hora de fin debe ser mayor que la hora de inicio.'
                })
    
    def save(self, *args, **kwargs):
        """Validar antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def overlaps_with(self, other_schedule):
        """Verificar si este horario se traslapa con otro"""
        if self.day != other_schedule.day:
            return False
        
        # Verificar traslape: (start1 < end2) and (start2 < end1)
        return (self.start_time < other_schedule.end_time and 
                other_schedule.start_time < self.end_time)


def get_academic_period(cuatrimestre_number):
    """
    Función helper para determinar el período académico basado en el número de cuatrimestre.
    
    Período 1 (Febrero-Mayo): Cuatrimestres 1, 4, 7
    Período 2 (Junio-Agosto): Cuatrimestres 2, 5, 8
    Período 3 (Septiembre-Diciembre): Cuatrimestres 3, 6, 9
    
    Args:
        cuatrimestre_number: Número del cuatrimestre (1-9)
    
    Returns:
        int: Período académico (1, 2 o 3), o None si no es válido
    """
    period_map = {
        1: 1, 4: 1, 7: 1,
        2: 2, 5: 2, 8: 2,
        3: 3, 6: 3, 9: 3
    }
    return period_map.get(cuatrimestre_number, None)


def get_cuatrimestres_by_period(period):
    """
    Obtiene los números de cuatrimestres que pertenecen a un período académico.
    
    Args:
        period: Período académico (1, 2 o 3)
    
    Returns:
        list: Lista de números de cuatrimestres
    """
    period_map = {
        1: [1, 4, 7],
        2: [2, 5, 8],
        3: [3, 6, 9]
    }
    return period_map.get(period, [])


class CuatrimestreEnrollmentManager(models.Manager):
    """Manager personalizado para CuatrimestreEnrollment con validación thread-safe"""
    
    def create_with_en_curso_validation(self, **kwargs):
        """
        Crear una inscripción validando que el estudiante no tenga otra EN_CURSO.
        Usa select_for_update() para prevenir condiciones de carrera.
        """
        student = kwargs.get('student')
        status = kwargs.get('status', 'PENDIENTE_PAGO')
        
        if not student:
            raise ValueError("El campo 'student' es requerido")
        
        # Solo validar si el estado es EN_CURSO
        if status == 'EN_CURSO':
            with transaction.atomic():
                # Bloquear filas existentes con EN_CURSO para este estudiante
                existing = self.select_for_update().filter(
                    student=student,
                    status='EN_CURSO'
                ).first()
                
                if existing:
                    raise ValidationError({
                        'status': (
                            f'El estudiante ya tiene una inscripción EN_CURSO en '
                            f'{existing.cuatrimestre.name} ({existing.academic_year}). '
                            f'Debe finalizar ese período académico antes de inscribirse a otro cuatrimestre.'
                        )
                    })
                
                # Crear la nueva inscripción
                return self.create(**kwargs)
        else:
            # Para otros estados, crear normalmente
            return self.create(**kwargs)
    
    def update_to_en_curso(self, enrollment, **update_fields):
        """
        Actualizar una inscripción a EN_CURSO validando que no haya otra EN_CURSO.
        Usa select_for_update() para prevenir condiciones de carrera.
        """
        student = enrollment.student
        
        with transaction.atomic():
            # Bloquear filas existentes con EN_CURSO para este estudiante
            existing = self.select_for_update().filter(
                student=student,
                status='EN_CURSO'
            ).exclude(pk=enrollment.pk).first()
            
            if existing:
                raise ValidationError({
                    'status': (
                        f'El estudiante ya tiene una inscripción EN_CURSO en '
                        f'{existing.cuatrimestre.name} ({existing.academic_year}). '
                        f'Debe finalizar ese período académico antes de inscribirse a otro cuatrimestre.'
                    )
                })
            
            # Actualizar campos en el objeto
            enrollment.status = 'EN_CURSO'
            for field, value in update_fields.items():
                setattr(enrollment, field, value)
            
            # Validar antes de guardar
            enrollment.full_clean()
            
            # Usar update() del QuerySet para evitar recursión en save()
            update_data = {'status': 'EN_CURSO'}
            update_data.update(update_fields)
            self.filter(pk=enrollment.pk).update(**update_data)
            
            # Refrescar el objeto desde la BD
            enrollment.refresh_from_db()
            return enrollment


class AcademicPeriodConfig(models.Model):
    """Modelo para configuración de períodos académicos (fechas límite de pago, mora, etc.)"""
    
    PERIOD_CHOICES = [
        (1, 'Período 1 (Febrero-Mayo)'),
        (2, 'Período 2 (Junio-Agosto)'),
        (3, 'Período 3 (Septiembre-Diciembre)'),
    ]
    
    MONTH_CHOICES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    period = models.IntegerField(choices=PERIOD_CHOICES, unique=True, verbose_name='Período Académico')
    penalty_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        verbose_name='Porcentaje de Mora (%)',
        help_text='Porcentaje de mora aplicado sobre el monto del pago cuando se excede la fecha límite'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Período Académico'
        verbose_name_plural = 'Configuraciones de Períodos Académicos'
        ordering = ['period']
    
    def __str__(self):
        return f"Período {self.period} - Mora: {self.penalty_percentage}%"
    
    def get_months(self):
        """Retorna los meses que corresponden a este período"""
        period_months = {
            1: [2, 3, 4, 5],  # Febrero-Mayo
            2: [6, 7, 8],  # Junio-Agosto
            3: [9, 10, 11, 12],  # Septiembre-Diciembre
        }
        return period_months.get(self.period, [])


class MonthlyPaymentDueDate(models.Model):
    """Modelo para fechas límite de pago por mes"""
    
    MONTH_CHOICES = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    month = models.IntegerField(choices=MONTH_CHOICES, unique=True, verbose_name='Mes')
    due_day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        default=10,
        verbose_name='Día límite de pago',
        help_text='Día del mes en que vence el pago (ej: 10 = día 10 de cada mes)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fecha Límite de Pago Mensual'
        verbose_name_plural = 'Fechas Límite de Pago Mensuales'
        ordering = ['month']
    
    def __str__(self):
        month_name = dict(self.MONTH_CHOICES)[self.month]
        return f"{month_name} - Día {self.due_day}"


class CuatrimestreEnrollment(models.Model):
    """Modelo para inscripción de estudiantes en un cuatrimestre específico de un año académico"""
    
    STATUS_CHOICES = [
        ('PRE_INSCRIPCION', 'Pre-inscripción'),
        ('CURSOS_PREASIGNADOS', 'Cursos Pre-asignados'),
        ('PENDIENTE_PAGO', 'Pendiente de Pago'),
        ('PENDIENTE_CONFIRMACION', 'Pendiente de Confirmación'),
        ('EN_CURSO', 'En Curso'),
        ('FINALIZADO', 'Finalizado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        'students.Student', 
        on_delete=models.CASCADE, 
        related_name='cuatrimestre_enrollments', 
        verbose_name='Estudiante'
    )
    cuatrimestre = models.ForeignKey(
        Cuatrimestre, 
        on_delete=models.PROTECT, 
        related_name='enrollments', 
        verbose_name='Cuatrimestre'
    )
    academic_year = models.IntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(9999)],
        verbose_name='Año académico',
        help_text='Año en que se realiza la inscripción al cuatrimestre'
    )
    enrollment_date = models.DateField(auto_now_add=True, verbose_name='Fecha de inscripción')
    status = models.CharField(
        max_length=25, 
        choices=STATUS_CHOICES, 
        default='PRE_INSCRIPCION', 
        verbose_name='Estado'
    )
    # Campos para el flujo presencial guiado
    is_first_enrollment = models.BooleanField(
        default=False,
        verbose_name='Primera inscripción',
        help_text='Indica si esta es la primera inscripción del estudiante (exoneración de cuota de inscripción)'
    )
    is_enrollment_fee_exempt = models.BooleanField(
        default=False,
        verbose_name='Exonerado de cuota de inscripción',
        help_text='Si es primera inscripción, se omite el pago de inscripción'
    )
    # Campo temporal para almacenar IDs de cursos pre-asignados (antes de confirmar)
    pre_assign_course_ids = models.JSONField(
        default=list,
        blank=True,
        verbose_name='IDs de cursos pre-asignados',
        help_text='Lista temporal de IDs de cursos pre-asignados (se limpia al confirmar)'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manager personalizado
    objects = CuatrimestreEnrollmentManager()
    
    class Meta:
        verbose_name = 'Inscripción a Cuatrimestre'
        verbose_name_plural = 'Inscripciones a Cuatrimestres'
        unique_together = ['student', 'cuatrimestre', 'academic_year']
        ordering = ['-academic_year', 'cuatrimestre__number']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['academic_year', 'cuatrimestre']),
            models.Index(fields=['student', 'status'], condition=models.Q(status='EN_CURSO'), name='idx_student_en_curso'),
        ]
        constraints = [
            # Nota: Un constraint único condicional (UNIQUE WHERE status='EN_CURSO') 
            # no es directamente soportado por Django para SQLite/MySQL de forma estándar.
            # La validación se realiza a nivel de aplicación usando el manager con select_for_update().
            # Para MySQL, se podría crear un índice único parcial mediante migración personalizada,
            # pero para mantener compatibilidad con SQLite, usamos validación a nivel de aplicación.
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.cuatrimestre.name} {self.academic_year}"
    
    def clean(self):
        """Validar restricciones de negocio académicas"""
        if self.student and self.cuatrimestre:
            if not self.student.career:
                raise ValidationError({
                    'student': 'El estudiante debe tener una carrera asignada.'
                })
            
            if self.student.career != self.cuatrimestre.career:
                raise ValidationError({
                    'cuatrimestre': 'El cuatrimestre debe pertenecer a la carrera del estudiante.'
                })
        
        # Validar que el año académico sea razonable
        if self.academic_year:
            if self.academic_year < 1900 or self.academic_year > 9999:
                raise ValidationError({
                    'academic_year': 'El año académico debe estar entre 1900 y 9999.'
                })
        
        # NOTA: La validación de solo una EN_CURSO se hace en el manager
        # con select_for_update() para prevenir condiciones de carrera.
        # Esta validación en clean() es una capa adicional de seguridad.
        if self.student and self.status == 'EN_CURSO':
            # Solo validar si no estamos en una transacción con select_for_update
            # (el manager ya lo hace de forma thread-safe)
            existing_enrollment = self.__class__.objects.filter(
                student=self.student,
                status='EN_CURSO'
            ).exclude(pk=self.pk if self.pk else None).first()
            
            if existing_enrollment:
                raise ValidationError({
                    'status': (
                        f'El estudiante ya tiene una inscripción EN_CURSO en '
                        f'{existing_enrollment.cuatrimestre.name} ({existing_enrollment.academic_year}). '
                        f'Debe finalizar ese período académico antes de inscribirse a otro cuatrimestre.'
                    )
                })
    
    def save(self, *args, **kwargs):
        """
        Guardar con validación.
        Si el estado es EN_CURSO y es una actualización, usar el manager para validación thread-safe.
        Aplicar regla: si is_first_enrollment == True, entonces is_enrollment_fee_exempt = True
        """
        # Regla de negocio: Si es primera inscripción, exonerar automáticamente
        if self.is_first_enrollment:
            self.is_enrollment_fee_exempt = True
        
        # Si estamos cambiando a EN_CURSO y ya existe el objeto, usar el manager
        if self.pk and self.status == 'EN_CURSO':
            # Obtener el estado anterior
            try:
                old_instance = self.__class__.objects.get(pk=self.pk)
                if old_instance.status != 'EN_CURSO':
                    # Estamos cambiando a EN_CURSO, usar el manager
                    self.__class__.objects.update_to_en_curso(self)
                    return
            except self.__class__.DoesNotExist:
                pass
        
        # Validar antes de guardar
        self.full_clean()
        super().save(*args, **kwargs)
    
    def calculate_total_tuition(self):
        """Calcular el costo total de la colegiatura basado en los cursos asignados"""
        from decimal import Decimal
        total = Decimal('0.00')
        for enrollment in self.course_enrollments.select_related('course').all():
            total += enrollment.course.cost or Decimal('0.00')
        return total
    
    def get_academic_period(self):
        """Obtener el período académico de este cuatrimestre"""
        if self.cuatrimestre:
            return get_academic_period(self.cuatrimestre.number)
        return None
    
    def can_assign_courses(self):
        """Verificar si se pueden asignar cursos (debe estar en PRE_INSCRIPCION o CURSOS_PREASIGNADOS)"""
        return self.status in ['PRE_INSCRIPCION', 'CURSOS_PREASIGNADOS']
    
    def can_confirm_assignment(self):
        """Verificar si se puede confirmar la asignación (debe estar en CURSOS_PREASIGNADOS con cursos pre-asignados)"""
        pre_assigned_ids = self.pre_assign_course_ids or []
        return (
            self.status == 'CURSOS_PREASIGNADOS' and
            len(pre_assigned_ids) > 0
        )
    
    def can_preview_boleta(self):
        """Verificar si se puede generar boleta de asignación (debe tener cursos pre-asignados)"""
        pre_assigned_ids = self.pre_assign_course_ids or []
        return (
            self.status == 'CURSOS_PREASIGNADOS' and
            len(pre_assigned_ids) > 0
        )


class CourseEnrollment(models.Model):
    """Modelo para matrícula de estudiantes en cursos"""
    
    STATUS_CHOICES = [
        ('MATRICULADO', 'Matriculado'),
        ('EN_CURSO', 'En Curso'),
        ('APROBADO', 'Aprobado'),
        ('REPROBADO', 'Reprobado'),
        ('RETIRADO', 'Retirado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='course_enrollments', verbose_name='Estudiante')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Curso')
    cuatrimestre_enrollment = models.ForeignKey(
        CuatrimestreEnrollment,
        on_delete=models.CASCADE,
        related_name='course_enrollments',
        null=True,
        blank=True,
        verbose_name='Inscripción al Cuatrimestre',
        help_text='Inscripción al cuatrimestre específico (opcional para mantener compatibilidad)'
    )
    enrollment_date = models.DateField(auto_now_add=True, verbose_name='Fecha de matrícula')
    final_grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Nota final'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='MATRICULADO', verbose_name='Estado')
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Matrícula de Curso'
        verbose_name_plural = 'Matrículas de Cursos'
        # Mantener compatibilidad: si no hay cuatrimestre_enrollment, mantener único por estudiante y curso
        # Si hay cuatrimestre_enrollment, permitir múltiples inscripciones en diferentes cuatrimestres
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'course'],
                condition=models.Q(cuatrimestre_enrollment__isnull=True),
                name='unique_student_course_without_cuatrimestre'
            ),
            models.UniqueConstraint(
                fields=['student', 'course', 'cuatrimestre_enrollment'],
                condition=models.Q(cuatrimestre_enrollment__isnull=False),
                name='unique_student_course_per_cuatrimestre'
            ),
        ]
        ordering = ['-enrollment_date']
        indexes = [
            models.Index(fields=['student', 'cuatrimestre_enrollment']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.name}"
    
    def clean(self):
        """Validar restricciones de negocio"""
        from django.core.exceptions import ValidationError
        
        if self.student and self.course:
            # Validar que el estudiante tenga carrera
            if not self.student.career:
                raise ValidationError({
                    'student': 'El estudiante debe tener una carrera asignada.'
                })
            
            # Validar que el curso pertenezca a la carrera del estudiante
            if self.student.career != self.course.career:
                raise ValidationError({
                    'course': 'El curso debe pertenecer a la carrera del estudiante.'
                })
            
            # Validar que el curso pertenezca al cuatrimestre de la inscripción si existe
            if self.cuatrimestre_enrollment and self.course:
                if self.cuatrimestre_enrollment.cuatrimestre != self.course.cuatrimestre:
                    raise ValidationError({
                        'course': 'El curso debe pertenecer al cuatrimestre de la inscripción.'
                    })
                
                # Validar que el cuatrimestre enrollment pertenezca al estudiante
                if self.cuatrimestre_enrollment.student != self.student:
                    raise ValidationError({
                        'cuatrimestre_enrollment': 'La inscripción al cuatrimestre debe pertenecer al mismo estudiante.'
                    })
            
            # REGLA DE NEGOCIO: No se puede inscribir a un curso que ya fue aprobado
            # PERO sí se puede reasignar cursos que fueron reprobados
            if not self.pk:  # Solo validar en creación
                approved_enrollment = CourseEnrollment.objects.filter(
                    student=self.student,
                    course=self.course,
                    status='APROBADO'
                ).first()
                
                if approved_enrollment:
                    raise ValidationError({
                        'course': f'El estudiante ya aprobó este curso ({self.course.code} - {self.course.name}). No se puede volver a inscribir.'
                    })
            
            # Validar restricción única: si no hay cuatrimestre_enrollment, solo puede haber una inscripción
            # Si hay cuatrimestre_enrollment, solo puede haber una inscripción por cuatrimestre
            # EXCEPTO si el curso anterior fue reprobado (se puede reasignar)
            if not self.pk:  # Solo validar en creación, no en actualización
                if self.cuatrimestre_enrollment is None:
                    # Sin cuatrimestre_enrollment: solo una inscripción por estudiante y curso
                    # Pero permitir si el anterior fue reprobado
                    existing = CourseEnrollment.objects.filter(
                        student=self.student,
                        course=self.course,
                        cuatrimestre_enrollment__isnull=True
                    ).first()
                    
                    if existing and existing.status != 'REPROBADO':
                        raise ValidationError({
                            'course': 'El estudiante ya está inscrito en este curso.'
                        })
                else:
                    # Con cuatrimestre_enrollment: solo una inscripción por cuatrimestre
                    # Pero permitir si el anterior fue reprobado
                    existing = CourseEnrollment.objects.filter(
                        student=self.student,
                        course=self.course,
                        cuatrimestre_enrollment=self.cuatrimestre_enrollment
                    ).first()
                    
                    if existing and existing.status != 'REPROBADO':
                        raise ValidationError({
                            'course': 'El estudiante ya está inscrito en este curso para este cuatrimestre.'
                        })
        
        # Validar que la nota final esté en el rango correcto
        if self.final_grade is not None:
            if self.final_grade < 0 or self.final_grade > 100:
                raise ValidationError({
                    'final_grade': 'La nota final debe estar entre 0 y 100.'
                })
    
    def save(self, *args, **kwargs):
        """Actualizar estado basado en nota final y validar"""
        self.full_clean()
        if self.final_grade is not None:
            if self.final_grade >= 70:
                self.status = 'APROBADO'
            else:
                self.status = 'REPROBADO'
        super().save(*args, **kwargs)


class GraduationMethod(models.Model):
    """Modelo para métodos de graduación de estudiantes"""
    
    METHOD_TYPE_CHOICES = [
        ('EXAMEN_PROFESIONAL', 'Examen Profesional'),
        ('TESINA', 'Tesina'),
        ('TESIS', 'Tesis'),
        ('DIPLOMADO', 'Diplomado'),
    ]
    
    STATUS_CHOICES = [
        ('NO_INICIADA', 'No Iniciada'),
        ('SOLICITUD_ASESOR', 'Solicitud de Asesor'),
        ('REVISION_TEMA', 'Revisión de Tema'),
        ('APROBACION_TEMA', 'Aprobación de Tema'),
        ('PRIMERA_REVISION', 'Primera Revisión'),
        ('SEGUNDA_REVISION', 'Segunda Revisión'),
        ('TERCERA_REVISION', 'Tercera Revisión'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='graduation_method', verbose_name='Estudiante')
    method_type = models.CharField(max_length=30, choices=METHOD_TYPE_CHOICES, verbose_name='Método de Graduación')
    title = models.CharField(max_length=500, blank=True, verbose_name='Título')
    advisor = models.CharField(max_length=200, blank=True, verbose_name='Asesor')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='NO_INICIADA', verbose_name='Estado')
    start_date = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio')
    defense_date = models.DateField(null=True, blank=True, verbose_name='Fecha de defensa/examen')
    notes = models.TextField(blank=True, verbose_name='Notas')
    document = models.FileField(upload_to='graduation_methods/', null=True, blank=True, verbose_name='Documento')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Método de Graduación'
        verbose_name_plural = 'Métodos de Graduación'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_method_type_display()} de {self.student.get_full_name()} - {self.get_status_display()}"


# ==================== MODELOS DE HISTORIAL DE CAMBIOS DE ESTADO ====================

class CuatrimestreEnrollmentStatusHistory(models.Model):
    """Modelo para rastrear cambios de estado en CuatrimestreEnrollment"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key al modelo principal
    cuatrimestre_enrollment = models.ForeignKey(
        CuatrimestreEnrollment,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Inscripción al Cuatrimestre'
    )
    
    # Estados
    previous_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Estado anterior'
    )
    new_status = models.CharField(
        max_length=50,
        verbose_name='Estado nuevo'
    )
    
    # Usuario que realizó el cambio
    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuatrimestre_enrollment_status_changes',
        verbose_name='Cambiado por'
    )
    
    # Timestamp
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de cambio')
    
    # Comentario opcional
    comment = models.TextField(blank=True, verbose_name='Comentario')
    
    class Meta:
        verbose_name = 'Historial de Estado de Inscripción a Cuatrimestre'
        verbose_name_plural = 'Historial de Estados de Inscripciones a Cuatrimestres'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['cuatrimestre_enrollment', 'changed_at']),
            models.Index(fields=['changed_at']),
            models.Index(fields=['cuatrimestre_enrollment']),
        ]
    
    def __str__(self):
        return f"Inscripción Cuatrimestre {self.cuatrimestre_enrollment.id} - {self.previous_status or 'N/A'} → {self.new_status} ({self.changed_at})"


class GraduationMethodStatusHistory(models.Model):
    """Modelo para rastrear cambios de estado en GraduationMethod"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key al modelo principal
    graduation_method = models.ForeignKey(
        GraduationMethod,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Método de Graduación'
    )
    
    # Estados
    previous_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Estado anterior'
    )
    new_status = models.CharField(
        max_length=50,
        verbose_name='Estado nuevo'
    )
    
    # Usuario que realizó el cambio
    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='thesis_status_changes',
        verbose_name='Cambiado por'
    )
    
    # Timestamp
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de cambio')
    
    # Comentario opcional
    comment = models.TextField(blank=True, verbose_name='Comentario')
    
    class Meta:
        verbose_name = 'Historial de Estado de Método de Graduación'
        verbose_name_plural = 'Historial de Estados de Métodos de Graduación'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['graduation_method', 'changed_at']),
            models.Index(fields=['changed_at']),
            models.Index(fields=['graduation_method']),
        ]
    
    def __str__(self):
        return f"Método de Graduación {self.graduation_method.id} - {self.previous_status or 'N/A'} → {self.new_status} ({self.changed_at})"

