"""
Comando de management para generar credenciales de Moodle para estudiantes que no las tengan
"""
from django.core.management.base import BaseCommand
from django.db import models
from students.models import Student, generate_moodle_username, generate_moodle_password
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Genera credenciales de Moodle para estudiantes que no las tengan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué estudiantes se actualizarían sin hacer cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Buscar estudiantes sin credenciales de Moodle
        students_without_credentials = Student.objects.filter(
            models.Q(moodle_username__isnull=True) | 
            models.Q(moodle_username='') |
            models.Q(moodle_password__isnull=True) | 
            models.Q(moodle_password='')
        )
        
        total = students_without_credentials.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✓ Todos los estudiantes ya tienen credenciales de Moodle'))
            return
        
        self.stdout.write(f'Encontrados {total} estudiantes sin credenciales de Moodle')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Modo dry-run: no se harán cambios'))
            for student in students_without_credentials[:10]:  # Mostrar solo los primeros 10
                self.stdout.write(f'  - {student.get_full_name()} ({student.carnet or "Sin carnet"})')
            if total > 10:
                self.stdout.write(f'  ... y {total - 10} más')
            return
        
        updated = 0
        errors = 0
        
        for student in students_without_credentials:
            try:
                if not student.first_name or not student.first_last_name:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Saltando estudiante {student.id}: faltan datos (first_name o first_last_name)'
                        )
                    )
                    continue
                
                # Generar usuario de Moodle
                username = generate_moodle_username(
                    student.first_name,
                    student.first_last_name,
                    student.second_last_name
                )
                
                # Generar contraseña de Moodle
                password = generate_moodle_password()
                
                # Actualizar estudiante
                student.moodle_username = username
                student.moodle_password = password
                student.save(update_fields=['moodle_username', 'moodle_password'])
                
                updated += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Credenciales generadas para {student.get_full_name()} ({student.carnet or "Sin carnet"}): {username}'
                    )
                )
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ Error al generar credenciales para {student.get_full_name()} ({student.id}): {str(e)}'
                    )
                )
                logger.error(f'Error al generar credenciales para estudiante {student.id}: {str(e)}', exc_info=True)
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'✓ {updated} estudiantes actualizados exitosamente'))
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'✗ {errors} errores'))