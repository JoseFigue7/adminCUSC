from django.core.management.base import BaseCommand
from certificates.models import RegistrationStatus, DocumentType


class Command(BaseCommand):
    help = 'Seed catálogos SEP para certificados y títulos'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando seed de catálogos SEP...')
        
        # Crear Estatus de Registro
        registration_statuses = [
            {'codigo': 'CERT', 'nombre': 'Certificado'},
            {'codigo': 'TITL', 'nombre': 'Título'},
        ]
        
        for status_data in registration_statuses:
            status, created = RegistrationStatus.objects.get_or_create(
                codigo=status_data['codigo'],
                defaults={'nombre': status_data['nombre'], 'is_active': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creado estatus: {status.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Estatus ya existe: {status.nombre}'))
        
        # Crear Tipos de Documento
        document_types = [
            {'codigo': 'CERT_TOT', 'nombre': 'CERTIFICADO_TOTAL'},
            {'codigo': 'CERT_PAR', 'nombre': 'CERTIFICADO_PARCIAL'},
            {'codigo': 'TITULO', 'nombre': 'TITULO'},
            {'codigo': 'DIPLOMA', 'nombre': 'DIPLOMA'},
            {'codigo': 'GRADO', 'nombre': 'GRADO'},
        ]
        
        for doc_type_data in document_types:
            doc_type, created = DocumentType.objects.get_or_create(
                codigo=doc_type_data['codigo'],
                defaults={'nombre': doc_type_data['nombre'], 'is_active': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Creado tipo de documento: {doc_type.nombre}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Tipo de documento ya existe: {doc_type.nombre}'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ Seed de catálogos SEP completado exitosamente!'))






