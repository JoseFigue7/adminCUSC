from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
import uuid


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
        Período 1 (Enero-Abril): Cuatrimestres 1, 4, 7
        Período 2 (Mayo-Agosto): Cuatrimestres 2, 5, 8
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
    
    Período 1 (Enero-Abril): Cuatrimestres 1, 4, 7
    Período 2 (Mayo-Agosto): Cuatrimestres 2, 5, 8
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


class CuatrimestreEnrollment(models.Model):
    """Modelo para inscripción de estudiantes en un cuatrimestre específico de un año académico"""
    
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('INSCRITO', 'Inscrito'),
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
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='INSCRITO', 
        verbose_name='Estado'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Inscripción a Cuatrimestre'
        verbose_name_plural = 'Inscripciones a Cuatrimestres'
        unique_together = ['student', 'cuatrimestre', 'academic_year']
        ordering = ['-academic_year', 'cuatrimestre__number']
        indexes = [
            models.Index(fields=['student', 'academic_year']),
            models.Index(fields=['academic_year', 'cuatrimestre']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.cuatrimestre.name} {self.academic_year}"
    
    def clean(self):
        """Validar restricciones de negocio académicas"""
        from django.core.exceptions import ValidationError
        
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
        
        # REGLA DE NEGOCIO: Un estudiante solo puede tener UNA inscripción EN_CURSO a la vez
        # Solo se aplica cuando se está creando una nueva inscripción o cambiando a EN_CURSO
        if self.student and (not self.pk or self.status == 'EN_CURSO'):
            existing_enrollment = CuatrimestreEnrollment.objects.filter(
                student=self.student,
                status='EN_CURSO'
            ).exclude(pk=self.pk if self.pk else None).first()
            
            if existing_enrollment:
                raise ValidationError({
                    'status': f'El estudiante ya tiene una inscripción EN_CURSO en {existing_enrollment.cuatrimestre.name} ({existing_enrollment.academic_year}). Debe finalizar ese período académico antes de inscribirse a otro cuatrimestre.'
                })
    
    def save(self, *args, **kwargs):
        """Validar antes de guardar"""
        self.full_clean()
        super().save(*args, **kwargs)


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


class Thesis(models.Model):
    """Modelo para tesis de estudiantes"""
    
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
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='thesis', verbose_name='Estudiante')
    title = models.CharField(max_length=500, blank=True, verbose_name='Título de la tesis')
    advisor = models.CharField(max_length=200, blank=True, verbose_name='Asesor')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='NO_INICIADA', verbose_name='Estado')
    start_date = models.DateField(null=True, blank=True, verbose_name='Fecha de inicio')
    defense_date = models.DateField(null=True, blank=True, verbose_name='Fecha de defensa')
    notes = models.TextField(blank=True, verbose_name='Notas')
    document = models.FileField(upload_to='thesis/', null=True, blank=True, verbose_name='Documento de tesis')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tesis'
        verbose_name_plural = 'Tesis'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Tesis de {self.student.get_full_name()} - {self.get_status_display()}"

