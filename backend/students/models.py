from django.db import models
from django.core.validators import RegexValidator
import uuid


class Student(models.Model):
    """Modelo para estudiantes"""
    
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    
    # Información personal
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    carnet = models.CharField(max_length=9, unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100, verbose_name='Nombres')
    last_name = models.CharField(max_length=100, verbose_name='Apellidos')
    email = models.EmailField(unique=True, verbose_name='Correo electrónico')
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Formato de teléfono inválido")],
        verbose_name='Teléfono'
    )
    date_of_birth = models.DateField(verbose_name='Fecha de nacimiento')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Género')
    curp = models.CharField(max_length=18, unique=True, verbose_name='CURP')
    address = models.TextField(verbose_name='Dirección')
    
    # Información académica
    career = models.ForeignKey('academics.Career', on_delete=models.PROTECT, related_name='students', verbose_name='Carrera')
    enrollment_date = models.DateField(auto_now_add=True, verbose_name='Fecha de inscripción')
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
        return f"{self.carnet} - {self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Enrollment(models.Model):
    """Modelo para inscripciones de estudiantes"""
    
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En Revisión'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='enrollment', verbose_name='Estudiante')
    enrollment_date = models.DateField(auto_now_add=True, verbose_name='Fecha de inscripción')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE', verbose_name='Estado')
    contract_generated = models.BooleanField(default=False, verbose_name='Contrato generado')
    contract_file = models.FileField(upload_to='contracts/', null=True, blank=True, verbose_name='Archivo de contrato')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        ordering = ['-enrollment_date']
    
    def __str__(self):
        return f"Inscripción de {self.student.get_full_name()}"


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

