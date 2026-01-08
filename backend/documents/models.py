from django.db import models
import uuid


class DocumentTemplate(models.Model):
    """Modelo para plantillas de documentos"""
    
    DOCUMENT_TYPES = [
        ('CONTRACT', 'Contrato'),
        ('CERTIFICATE', 'Certificado'),
        ('TRANSCRIPT', 'Acta de Calificaciones'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='Nombre de la plantilla')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name='Tipo de documento')
    template_file = models.FileField(upload_to='document_templates/', verbose_name='Archivo de plantilla')
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Plantilla de Documento'
        verbose_name_plural = 'Plantillas de Documentos'
    
    def __str__(self):
        return f"{self.name} - {self.get_document_type_display()}"

