from django.db import models
from django.core.validators import RegexValidator, MaxLengthValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import uuid
import re


# ==================== VALIDADORES PERSONALIZADOS ====================

def validate_mexican_phone(value):
    """
    Valida que el número telefónico sea mexicano válido.
    El formato debe ser: +52 seguido de exactamente 10 dígitos (solo números).
    Ejemplo: +525512345678
    """
    if not value:
        raise ValidationError('El número de teléfono es requerido.')
    
    phone = str(value).strip()
    
    # Debe empezar con +52
    if not phone.startswith('+52'):
        raise ValidationError('El número telefónico debe comenzar con +52 (código de país de México).')
    
    # Obtener solo los dígitos después de +52
    digits_after_country = phone[3:]  # Remover +52
    
    # Eliminar espacios, guiones y paréntesis si los hay
    digits_after_country = re.sub(r'[\s\-\(\)]', '', digits_after_country)
    
    # Debe contener exactamente 10 dígitos
    if len(digits_after_country) != 10:
        raise ValidationError(
            'El número telefónico debe tener exactamente 10 dígitos después de +52. '
            f'Se encontraron {len(digits_after_country)} dígitos.'
        )
    
    # Debe contener solo números
    if not digits_after_country.isdigit():
        raise ValidationError('El número telefónico solo debe contener números después de +52.')
    
    # Validar que el código de área (LADA) sea válido (primer dígito debe ser 2-9)
    lada_first_digit = int(digits_after_country[0])
    if lada_first_digit < 2 or lada_first_digit > 9:
        raise ValidationError('El código de área (LADA) no es válido para México. El primer dígito debe ser entre 2 y 9.')
    
    return value


# ==================== MODELOS DE CATÁLOGOS SEP ====================

class Pais(models.Model):
    """Catálogo de países"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código del país')
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre del país')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class EntidadFederativa(models.Model):
    """Catálogo de entidades federativas, estados o ciudades según el país"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pais = models.ForeignKey(
        Pais,
        on_delete=models.CASCADE,
        related_name='entidades',
        null=True,
        blank=True,
        verbose_name='País',
        help_text='País al que pertenece esta entidad federativa, estado o ciudad'
    )
    codigo = models.CharField(max_length=10, verbose_name='Código de la entidad')
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la entidad')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Entidad Federativa / Estado / Ciudad'
        verbose_name_plural = 'Entidades Federativas / Estados / Ciudades'
        ordering = ['pais', 'nombre']
        unique_together = ['pais', 'codigo']  # El código debe ser único por país
        indexes = [
            models.Index(fields=['pais', 'is_active']),
        ]
    
    def __str__(self):
        if self.pais:
            return f"{self.pais.nombre} - {self.nombre}"
        return self.nombre


class Idioma(models.Model):
    """Catálogo de idiomas o lenguas naturales"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código del idioma')
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre del idioma')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Idioma'
        verbose_name_plural = 'Idiomas'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class NecesidadEducativaEspecial(models.Model):
    """Catálogo de necesidades educativas especiales (discapacidades o aptitudes sobresalientes)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, unique=True, verbose_name='Nombre')
    tipo = models.CharField(
        max_length=25,
        choices=[('DISCAPACIDAD', 'Discapacidad'), ('APTITUD_SOBRESALIENTE', 'Aptitud Sobresaliente'), ('NINGUNA', 'Ninguna')],
        default='NINGUNA',
        verbose_name='Tipo'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Necesidad Educativa Especial'
        verbose_name_plural = 'Necesidades Educativas Especiales'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class AntecedenteAcademico(models.Model):
    """Catálogo de antecedentes académicos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, unique=True, verbose_name='Nombre')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Antecedente Académico'
        verbose_name_plural = 'Antecedentes Académicos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class NivelEducativo(models.Model):
    """Catálogo de niveles educativos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, unique=True, verbose_name='Nombre')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Nivel Educativo'
        verbose_name_plural = 'Niveles Educativos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class ModalidadEducativa(models.Model):
    """Catálogo de modalidades educativas"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Modalidad Educativa'
        verbose_name_plural = 'Modalidades Educativas'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


class Turno(models.Model):
    """Catálogo de turnos"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=100, unique=True, verbose_name='Nombre')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    class Meta:
        verbose_name = 'Turno'
        verbose_name_plural = 'Turnos'
        ordering = ['nombre']
    
    def __str__(self):
        return self.nombre


# ==================== MODELO DE ESTUDIANTE ====================

class Student(models.Model):
    """Modelo para estudiantes con campos requeridos por la SEP"""
    
    GENDER_CHOICES = [
        ('M', 'Mujer'),
        ('H', 'Hombre'),
    ]
    
    # Información personal básica (campos SEP)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carnet = models.CharField(max_length=9, unique=True, null=True, blank=True, verbose_name='Carnet')
    
    # Campos SEP requeridos
    first_name = models.CharField(
        max_length=70, 
        verbose_name='Nombre(s) del alumno',
        help_text='Máximo 70 caracteres, tal como aparece en el acta de nacimiento'
    )
    first_last_name = models.CharField(
        max_length=70, 
        blank=True,
        null=True,
        verbose_name='Primer apellido del alumno',
        help_text='Máximo 70 caracteres, conforme al acta de nacimiento'
    )
    second_last_name = models.CharField(
        max_length=70, 
        blank=True, 
        null=True,
        verbose_name='Segundo apellido del alumno',
        help_text='Máximo 70 caracteres; dejar en blanco si no cuenta con segundo apellido'
    )
    
    # Información de contacto (no requerida por SEP pero necesaria para el sistema)
    email = models.EmailField(unique=True, blank=False, null=False, verbose_name='Correo electrónico')
    phone = models.CharField(
        max_length=13,
        validators=[validate_mexican_phone],
        verbose_name='Teléfono',
        help_text='Número telefónico mexicano: debe comenzar con +52 seguido de 10 dígitos. Ejemplo: +525512345678'
    )
    address = models.TextField(verbose_name='Dirección')
    
    # Campos SEP requeridos - Identificación
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES, 
        verbose_name='Género',
        help_text='M = Mujer, H = Hombre'
    )
    curp = models.CharField(
        max_length=18, 
        unique=True, 
        verbose_name='CURP del alumno',
        help_text='18 caracteres: 4 letras + 6 dígitos + H/M + 5 letras + 1 alfanumérico + 1 dígito. Ejemplo: ABCD123456HHIJKLM01',
        validators=[RegexValidator(
            regex=r'^[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d$', 
            message="Formato de CURP inválido. Debe tener: 4 letras + 6 dígitos + H/M + 5 letras + 1 alfanumérico + 1 dígito"
        )]
    )
    date_of_birth = models.DateField(
        verbose_name='Fecha de nacimiento',
        help_text='Conforme al acta de nacimiento'
    )
    
    # Campos SEP requeridos - Lugar de nacimiento
    birth_country = models.ForeignKey(
        Pais, 
        on_delete=models.PROTECT, 
        related_name='born_students',
        null=True,
        blank=True,
        verbose_name='País de nacimiento',
        help_text='Conforme al acta de nacimiento o documento equivalente'
    )
    birth_state = models.ForeignKey(
        EntidadFederativa, 
        on_delete=models.PROTECT, 
        related_name='born_students',
        null=True,
        blank=True,
        verbose_name='Entidad federativa o ciudad de nacimiento',
        help_text='Conforme al acta de nacimiento o documento equivalente'
    )
    
    # Campos SEP opcionales
    origin_country = models.ForeignKey(
        Pais,
        on_delete=models.PROTECT,
        related_name='origin_students',
        null=True,
        blank=True,
        verbose_name='País de procedencia',
        help_text='Únicamente si realizó estudios previos en dicho país'
    )
    native_language = models.ForeignKey(
        Idioma,
        on_delete=models.PROTECT,
        related_name='native_speakers',
        null=True,
        blank=True,
        verbose_name='Idioma o lengua natural del alumno'
    )
    special_educational_need = models.ForeignKey(
        NecesidadEducativaEspecial,
        on_delete=models.PROTECT,
        related_name='students_with_need',
        null=True,
        blank=True,
        verbose_name='Necesidad educativa especial',
        help_text='En caso de discapacidad o aptitudes sobresalientes'
    )
    academic_background = models.ForeignKey(
        AntecedenteAcademico,
        on_delete=models.PROTECT,
        related_name='students',
        null=True,
        blank=True,
        verbose_name='Presenta antecedente académico'
    )
    
    # Información académica
    career = models.ForeignKey(
        'academics.Career', 
        on_delete=models.PROTECT, 
        related_name='students', 
        verbose_name='Carrera'
    )
    enrollment_date = models.DateField(auto_now_add=True, verbose_name='Fecha de primera inscripción')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    
    # Información de beca
    has_scholarship = models.BooleanField(default=False, verbose_name='Tiene beca')
    scholarship_type = models.CharField(
        max_length=20,
        choices=[('COMPLETA', 'Beca Completa'), ('MEDIA', 'Media Beca'), ('NINGUNA', 'Sin Beca')],
        default='NINGUNA',
        verbose_name='Tipo de beca'
    )
    
    # Estados
    pensum_closed = models.BooleanField(default=False, verbose_name='Pensum cerrado')
    thesis_started = models.BooleanField(default=False, verbose_name='Tesis iniciada')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'
        ordering = ['-enrollment_date']
    
    def __str__(self):
        return f"{self.carnet} - {self.get_full_name()}"
    
    def clean(self):
        """Validar restricciones de negocio antes de guardar"""
        from django.core.exceptions import ValidationError
        
        # Validar que si se proporciona email, sea único (validación adicional)
        if self.email:
            existing = Student.objects.filter(email=self.email).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'email': 'Ya existe un estudiante con este correo electrónico.'})
        
        # Validar que si se proporciona CURP, sea único (validación adicional)
        if self.curp:
            existing = Student.objects.filter(curp=self.curp).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'curp': 'Ya existe un estudiante con este CURP.'})
        
        # Validar que el estudiante tenga una carrera asignada
        if not self.career:
            raise ValidationError({'career': 'El estudiante debe tener una carrera asignada.'})
    
    def save(self, *args, **kwargs):
        """Guardar con validación"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_full_name(self):
        """Retorna el nombre completo con ambos apellidos"""
        if self.second_last_name:
            return f"{self.first_name} {self.first_last_name} {self.second_last_name}"
        return f"{self.first_name} {self.first_last_name}"
    
    @property
    def last_name(self):
        """Compatibilidad con código existente que usa last_name"""
        return self.first_last_name


class Enrollment(models.Model):
    """Modelo para inscripciones de estudiantes - permite múltiples inscripciones por ciclo/trimestre"""
    
    ENROLLMENT_STATUS_CHOICES = [
        ('INSCRIPCION', 'Inscripción'),
        ('REINSCRIPCION', 'Reinscripción'),
    ]
    
    ADMIN_STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En Revisión'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relación con estudiante - ahora ForeignKey para permitir múltiples inscripciones
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        related_name='enrollments', 
        verbose_name='Estudiante'
    )
    
    # Campos SEP requeridos para cada inscripción
    enrollment_status = models.CharField(
        max_length=20, 
        choices=ENROLLMENT_STATUS_CHOICES, 
        default='INSCRIPCION',
        verbose_name='Estatus del alumno',
        help_text='Inscripción o Reinscripción'
    )
    school_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Año del ciclo escolar',
        help_text='Numérico, 4 caracteres, por ejemplo: 2017. Si no se especifica, se usa el año actual',
        validators=[MinValueValidator(1900), MaxValueValidator(9999)]
    )
    
    # Campos SEP - Información institucional
    institutional_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Matrícula institucional del alumno',
        help_text='Texto, máximo 20 caracteres. Si no se especifica, se usa el carnet del estudiante'
    )
    cct = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        verbose_name='Clave del Centro de Trabajo (CCT)',
        help_text='Texto, 10 caracteres, de la institución particular titular del RVOE. Si no se especifica, se toma de la carrera'
    )
    
    # Campos SEP - Información académica
    career = models.ForeignKey(
        'academics.Career',
        on_delete=models.PROTECT,
        related_name='student_enrollments',
        null=True,
        blank=True,
        verbose_name='Carrera',
        help_text='Si no se especifica, se toma del estudiante'
    )
    educational_level = models.ForeignKey(
        NivelEducativo,
        on_delete=models.PROTECT,
        related_name='enrollments',
        null=True,
        blank=True,
        verbose_name='Nivel educativo'
    )
    shift = models.ForeignKey(
        Turno,
        on_delete=models.PROTECT,
        related_name='enrollments',
        null=True,
        blank=True,
        verbose_name='Turno',
        help_text='Conforme al CCT'
    )
    educational_modality = models.ForeignKey(
        ModalidadEducativa,
        on_delete=models.PROTECT,
        related_name='enrollments',
        null=True,
        blank=True,
        verbose_name='Modalidad educativa',
        help_text='Escolar, no escolarizada o mixta'
    )
    
    # Campos SEP - RVOE
    rvoe_agreement_number = models.CharField(
        max_length=70,
        blank=True,
        null=True,
        verbose_name='Número de Acuerdo de RVOE',
        help_text='Texto, máximo 70 caracteres. Si no se especifica, se toma de la carrera'
    )
    rvoe_agreement_date = models.CharField(
        max_length=8,
        blank=True,
        null=True,
        verbose_name='Fecha del Acuerdo de RVOE',
        help_text='Numérico, 8 caracteres, formato aaaammdd. Si no se especifica, se toma de la carrera',
        validators=[RegexValidator(regex=r'^\d{8}$', message="Debe ser formato aaaammdd (8 dígitos)")]
    )
    
    # Campos administrativos del sistema
    enrollment_date = models.DateField(auto_now_add=True, verbose_name='Fecha de inscripción')
    status = models.CharField(
        max_length=20, 
        choices=ADMIN_STATUS_CHOICES, 
        default='PENDIENTE', 
        verbose_name='Estado administrativo'
    )
    contract_generated = models.BooleanField(default=False, verbose_name='Contrato generado')
    contract_file = models.FileField(upload_to='contracts/', null=True, blank=True, verbose_name='Archivo de contrato generado')
    contract_scanned = models.FileField(upload_to='contracts/scanned/', null=True, blank=True, verbose_name='Contrato escaneado')
    contract_uploaded_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de subida del contrato escaneado')
    is_officially_enrolled = models.BooleanField(default=False, verbose_name='Oficialmente inscrito', help_text='True cuando el contrato escaneado ha sido subido y aprobado')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        ordering = ['-school_year', '-enrollment_date']
        # Un estudiante solo puede inscribirse una vez por año y carrera
        # Usar UniqueConstraint para manejar campos opcionales correctamente
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'school_year', 'career'],
                condition=models.Q(career__isnull=False),
                name='unique_enrollment_per_student_year_career'
            ),
        ]
    
    def clean(self):
        """Validar restricciones de negocio antes de guardar"""
        from django.core.exceptions import ValidationError
        
        # Validar que la carrera del enrollment coincida con la del estudiante si ambas existen
        if self.student and self.career:
            if self.student.career != self.career:
                raise ValidationError({
                    'career': 'La carrera de la inscripción debe coincidir con la carrera del estudiante.'
                })
        
        # Validar que el estudiante tenga carrera asignada
        if self.student and not self.student.career and not self.career:
            raise ValidationError({
                'career': 'El estudiante debe tener una carrera asignada o se debe especificar una carrera en la inscripción.'
            })
    
    def save(self, *args, **kwargs):
        """Completar campos automáticamente si no se especifican"""
        # Validar antes de guardar
        self.full_clean()
        
        # Si no se especifica career, usar la del estudiante
        if not self.career and self.student and self.student.career:
            self.career = self.student.career
        
        # Si no se especifica institutional_id, usar el carnet del estudiante
        if not self.institutional_id and self.student and self.student.carnet:
            self.institutional_id = self.student.carnet
        
        # Si no se especifica school_year, usar el año actual
        if not self.school_year:
            from datetime import datetime
            self.school_year = datetime.now().year
        
        # Completar campos desde Career si no se especifican
        if self.career:
            if not self.cct and self.career.cct:
                self.cct = self.career.cct
            if not self.rvoe_agreement_number and self.career.rvoe_agreement_number:
                self.rvoe_agreement_number = self.career.rvoe_agreement_number
            if not self.rvoe_agreement_date and self.career.rvoe_agreement_date:
                self.rvoe_agreement_date = self.career.rvoe_agreement_date
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_enrollment_status_display()} - {self.student.get_full_name()} - {self.school_year}"


class StudentDocument(models.Model):
    """Modelo para documentos de estudiantes"""
    
    DOCUMENT_TYPES = [
        ('BACHILLERATO_ORIGINAL', 'Certificado de Bachillerato (Original)'),
        ('BACHILLERATO_COPIA1', 'Certificado de Bachillerato (Copia 1)'),
        ('BACHILLERATO_COPIA2', 'Certificado de Bachillerato (Copia 2)'),
        ('NACIMIENTO_ORIGINAL', 'Acta de Nacimiento (Original)'),
        ('NACIMIENTO_COPIA1', 'Acta de Nacimiento (Copia 1)'),
        ('NACIMIENTO_COPIA2', 'Acta de Nacimiento (Copia 2)'),
        ('CURP', 'CURP'),
        ('MEDICO', 'Certificado Médico'),
        ('FOTO_DIGITAL', 'Fotografía Digital para Carnet'),
        ('FOTO_FISICA1', 'Fotografía Física 1'),
        ('FOTO_FISICA2', 'Fotografía Física 2'),
        ('DOMICILIO', 'Comprobante de Domicilio'),
    ]
    
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('RECIBIDO', 'Recibido'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='documents', verbose_name='Estudiante')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name='Tipo de documento')
    file = models.FileField(upload_to='student_documents/', null=True, blank=True, verbose_name='Archivo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE', verbose_name='Estado')
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Documento de Estudiante'
        verbose_name_plural = 'Documentos de Estudiantes'
        unique_together = ['student', 'document_type']
    
    def __str__(self):
        return f"{self.get_document_type_display()} - {self.student.get_full_name()}"

