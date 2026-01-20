from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
import uuid


# ==================== CATÁLOGOS SEP ====================

class RegistrationStatus(models.Model):
    """Catálogo de estatus de registro SEP (Certificado o Título)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Estatus de Registro'
        verbose_name_plural = 'Estatus de Registro'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class DocumentType(models.Model):
    """Catálogo de tipos de documento SEP"""
    
    DOCUMENT_TYPE_CHOICES = [
        ('CERTIFICADO_TOTAL', 'Certificado Total'),
        ('CERTIFICADO_PARCIAL', 'Certificado Parcial'),
        ('TITULO', 'Título'),
        ('DIPLOMA', 'Diploma'),
        ('GRADO', 'Grado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    nombre = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name='Nombre',
        choices=DOCUMENT_TYPE_CHOICES
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Tipo de Documento'
        verbose_name_plural = 'Tipos de Documento'
        ordering = ['nombre']
    
    def __str__(self):
        if self.nombre:
            return self.get_nombre_display()
        return self.codigo


# ==================== MODELOS DE CERTIFICADOS ====================

class AcademicCertificate(models.Model):
    """
    Modelo para certificados académicos con requisitos SEP.
    Se utiliza para el registro de Certificados, Títulos y documentos académicos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relación con estudiante
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='academic_certificates',
        verbose_name='Estudiante'
    )
    
    # Campos SEP requeridos
    registration_status = models.ForeignKey(
        RegistrationStatus,
        on_delete=models.PROTECT,
        related_name='certificates',
        verbose_name='Estatus del registro',
        help_text='Certificado o Título'
    )
    
    school_year = models.IntegerField(
        verbose_name='Año del ciclo escolar',
        help_text='Numérico, 4 caracteres, correspondiente al año en que el alumno fue certificado o titulado',
        validators=[MinValueValidator(1900), MaxValueValidator(9999)]
    )
    
    curp = models.CharField(
        max_length=18,
        verbose_name='CURP del alumno',
        help_text='18 caracteres, clave única de registro de población',
        validators=[RegexValidator(
            regex=r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d$',
            message="Formato de CURP inválido"
        )]
    )
    
    general_average = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Promedio general',
        help_text='Obligatorio únicamente cuando se trate de un Certificado'
    )
    
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name='certificates',
        verbose_name='Tipo de documento',
        help_text='Certificado Total, Certificado Parcial, Título, Diploma o Grado'
    )
    
    issuance_date = models.CharField(
        max_length=8,
        verbose_name='Fecha de expedición del documento',
        help_text='Numérico, 8 caracteres, formato aaaammdd',
        validators=[RegexValidator(regex=r'^\d{8}$', message="Debe ser formato aaaammdd (8 dígitos)")]
    )
    
    document_folio = models.CharField(
        max_length=20,
        verbose_name='Folio del documento',
        help_text='Máximo 20 caracteres; corresponde al folio asignado por la institución educativa'
    )
    
    # Campos adicionales del sistema
    is_sep_registered = models.BooleanField(
        default=False,
        verbose_name='Registrado en SEP',
        help_text='Indica si el documento ha sido registrado en la SEP'
    )
    sep_registration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de registro SEP'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    # Archivo generado
    certificate_file = models.FileField(
        upload_to='certificates/academic/',
        null=True,
        blank=True,
        verbose_name='Archivo del certificado generado'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Certificado Académico'
        verbose_name_plural = 'Certificados Académicos'
        ordering = ['-school_year', '-created_at']
    
    def __str__(self):
        status_name = self.registration_status.nombre if self.registration_status else 'N/A'
        student_name = self.student.get_full_name() if self.student else 'N/A'
        return f"{status_name} - {student_name} - {self.school_year}"


class CourseCertificate(models.Model):
    """
    Modelo para certificados de cursos.
    Se genera validando las calificaciones obtenidas por los estudiantes en los cursos aprobados.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relación con estudiante
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='course_certificates',
        verbose_name='Estudiante'
    )
    
    # Información del certificado
    certificate_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del certificado',
        help_text='Nombre descriptivo del certificado de cursos'
    )
    
    course_enrollments = models.ManyToManyField(
        'academics.CourseEnrollment',
        related_name='course_certificates',
        verbose_name='Matrículas de cursos',
        help_text='Cursos aprobados incluidos en el certificado'
    )
    
    # Calificaciones y promedio
    total_courses = models.IntegerField(
        default=0,
        verbose_name='Total de cursos',
        help_text='Número total de cursos incluidos'
    )
    average_grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Promedio de calificaciones'
    )
    
    # Fechas
    issuance_date = models.DateField(
        auto_now_add=True,
        verbose_name='Fecha de expedición'
    )
    
    # Estado
    is_printed = models.BooleanField(
        default=False,
        verbose_name='Impreso',
        help_text='Indica si el certificado ha sido impreso'
    )
    
    # Archivo generado
    certificate_file = models.FileField(
        upload_to='certificates/courses/',
        null=True,
        blank=True,
        verbose_name='Archivo del certificado generado'
    )
    
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Certificado de Cursos'
        verbose_name_plural = 'Certificados de Cursos'
        ordering = ['-issuance_date', '-created_at']
    
    def __str__(self):
        return f"Certificado de Cursos - {self.student.get_full_name()} - {self.certificate_name}"
    
    def save(self, *args, **kwargs):
        """Calcular total de cursos y promedio antes de guardar"""
        if self.pk:
            # Si ya existe, recalcular
            enrollments = self.course_enrollments.filter(status='APROBADO')
            self.total_courses = enrollments.count()
            
            grades = [e.final_grade for e in enrollments if e.final_grade is not None]
            if grades:
                self.average_grade = sum(grades) / len(grades)
            else:
                self.average_grade = None
        
        super().save(*args, **kwargs)


class UniversityTitle(models.Model):
    """
    Modelo para títulos universitarios.
    Se genera después de cerrar el pensum y cumplir todos los requisitos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relación con estudiante (OneToOne para asegurar un solo título por estudiante)
    student = models.OneToOneField(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='university_title',
        verbose_name='Estudiante'
    )
    
    # Información del título
    title_name = models.CharField(
        max_length=200,
        verbose_name='Nombre del título',
        help_text='Nombre completo del título universitario'
    )
    
    # Requisitos validados
    pensum_completed = models.BooleanField(
        default=False,
        verbose_name='Pensum completado',
        help_text='Indica si el estudiante completó el pensum'
    )
    
    all_courses_approved = models.BooleanField(
        default=False,
        verbose_name='Todos los cursos aprobados',
        help_text='Indica si todos los cursos requeridos fueron aprobados'
    )
    
    thesis_approved = models.BooleanField(
        default=False,
        null=True,
        blank=True,
        verbose_name='Método de graduación aprobado',
        help_text='Indica si el método de graduación fue aprobado (si aplica)'
    )
    
    average_grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Promedio general'
    )
    
    # Información SEP para registro
    academic_certificate = models.OneToOneField(
        AcademicCertificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='university_title',
        verbose_name='Certificado académico asociado',
        help_text='Certificado académico SEP asociado al título'
    )
    
    # Fechas
    issuance_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de expedición'
    )
    
    # Estado
    requirements_met = models.BooleanField(
        default=False,
        verbose_name='Requisitos cumplidos',
        help_text='Indica si todos los requisitos para emitir el título fueron cumplidos'
    )
    
    is_printed = models.BooleanField(
        default=False,
        verbose_name='Impreso',
        help_text='Indica si el título ha sido impreso'
    )
    
    # Archivo generado
    title_file = models.FileField(
        upload_to='certificates/titles/',
        null=True,
        blank=True,
        verbose_name='Archivo del título generado'
    )
    
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Título Universitario'
        verbose_name_plural = 'Títulos Universitarios'
        ordering = ['-issuance_date', '-created_at']
    
    def __str__(self):
        return f"Título - {self.student.get_full_name()} - {self.title_name}"
    
    def validate_requirements(self):
        """
        Valida si el estudiante cumple con todos los requisitos para obtener el título.
        Retorna True si todos los requisitos están cumplidos.
        """
        from academics.models import CourseEnrollment
        
        # Verificar que el pensum esté cerrado
        if not self.student.pensum_closed:
            return False
        
        # Verificar que todos los cursos requeridos estén aprobados
        total_required_courses = self.student.career.courses.filter(is_required=True).count()
        approved_required_courses = CourseEnrollment.objects.filter(
            student=self.student,
            course__is_required=True,
            status='APROBADO'
        ).count()
        
        if approved_required_courses < total_required_courses:
            return False
        
        # Si hay método de graduación, verificar que esté aprobado
        if hasattr(self.student, 'graduation_method') and self.student.graduation_method:
            if self.student.graduation_method.status != 'APROBADA':
                return False
        
        # Actualizar campos
        self.pensum_completed = True
        self.all_courses_approved = True
        self.thesis_approved = (
            hasattr(self.student, 'thesis') and 
            self.student.thesis and 
            self.student.thesis.status == 'APROBADA'
        ) if hasattr(self.student, 'thesis') else None
        
        # Calcular promedio general
        enrollments = CourseEnrollment.objects.filter(
            student=self.student,
            status='APROBADO',
            final_grade__isnull=False
        )
        if enrollments.exists():
            grades = [e.final_grade for e in enrollments]
            self.average_grade = sum(grades) / len(grades)
        
        self.requirements_met = True
        self.save()
        
        return True
