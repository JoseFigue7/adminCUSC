from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class Career(models.Model):
    """Modelo para carreras"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.IntegerField(unique=True, verbose_name='Código de carrera')
    name = models.CharField(max_length=200, unique=True, verbose_name='Nombre de la carrera')
    description = models.TextField(blank=True, verbose_name='Descripción')
    total_credits = models.IntegerField(default=0, verbose_name='Total de créditos')
    max_scholarships_full = models.IntegerField(default=0, verbose_name='Máximo de becas completas')
    max_scholarships_half = models.IntegerField(default=0, verbose_name='Máximo de medias becas')
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def courses(self):
        """Retorna todos los cursos de la carrera"""
        return Course.objects.filter(career=self)


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
        unique_together = ['student', 'course']
        ordering = ['-enrollment_date']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.name}"
    
    def save(self, *args, **kwargs):
        """Actualizar estado basado en nota final"""
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

