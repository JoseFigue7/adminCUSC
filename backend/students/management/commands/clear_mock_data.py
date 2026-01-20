"""
Comando para eliminar todos los datos mock generados para pruebas
Elimina estudiantes de prueba, usuarios de prueba y todos sus datos relacionados
Mantiene datos de configuración (carreras, cursos, tipos de pago, catálogos SEP, roles)
"""
from django.core.management.base import BaseCommand
from django.db import transaction
import os
import shutil

from students.models import (
    Student, Enrollment, StudentDocument,
    EnrollmentStatusHistory, StudentDocumentStatusHistory
)
from academics.models import (
    CourseEnrollment, GraduationMethod, CuatrimestreEnrollment,
    CuatrimestreEnrollmentStatusHistory, GraduationMethodStatusHistory
)
from payments.models import Payment, Scholarship, PaymentStatusHistory
from users.models import User


class Command(BaseCommand):
    help = 'Elimina todos los datos mock generados para pruebas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirmar eliminación (requerido para ejecutar)'
        )
        parser.add_argument(
            '--keep-users',
            action='store_true',
            help='Mantener usuarios de prueba (solo eliminar estudiantes)'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.ERROR(
                '⚠️  ADVERTENCIA: Este comando eliminará TODOS los datos mock.\n'
                'Para ejecutar, usa: python manage.py clear_mock_data --confirm'
            ))
            return

        self.stdout.write(self.style.WARNING('Iniciando eliminación de datos mock...'))

        with transaction.atomic():
            # Contadores
            counts = {}

            # 1. Eliminar historiales relacionados con estudiantes
            self.stdout.write('Eliminando historiales de estado...')
            counts['enrollment_status_history'] = EnrollmentStatusHistory.objects.all().delete()[0]
            counts['student_document_status_history'] = StudentDocumentStatusHistory.objects.all().delete()[0]
            counts['payment_status_history'] = PaymentStatusHistory.objects.all().delete()[0]
            counts['cuatrimestre_enrollment_status_history'] = CuatrimestreEnrollmentStatusHistory.objects.all().delete()[0]
            counts['graduation_method_status_history'] = GraduationMethodStatusHistory.objects.all().delete()[0]

            # 2. Eliminar documentos de estudiantes (y sus archivos)
            self.stdout.write('Eliminando documentos de estudiantes...')
            documents = StudentDocument.objects.all()
            for doc in documents:
                if doc.file:
                    try:
                        if os.path.isfile(doc.file.path):
                            os.remove(doc.file.path)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'No se pudo eliminar archivo: {doc.file.path} - {e}'))
            counts['student_documents'] = documents.delete()[0]

            # 3. Eliminar pagos (y sus comprobantes)
            self.stdout.write('Eliminando pagos...')
            payments = Payment.objects.all()
            for payment in payments:
                if payment.transfer_receipt:
                    try:
                        if os.path.isfile(payment.transfer_receipt.path):
                            os.remove(payment.transfer_receipt.path)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'No se pudo eliminar archivo: {payment.transfer_receipt.path} - {e}'))
            counts['payments'] = payments.delete()[0]

            # 4. Eliminar becas
            self.stdout.write('Eliminando becas...')
            counts['scholarships'] = Scholarship.objects.all().delete()[0]

            # 5. Eliminar inscripciones en cursos
            self.stdout.write('Eliminando inscripciones en cursos...')
            counts['course_enrollments'] = CourseEnrollment.objects.all().delete()[0]

            # 6. Eliminar inscripciones a cuatrimestres
            self.stdout.write('Eliminando inscripciones a cuatrimestres...')
            counts['cuatrimestre_enrollments'] = CuatrimestreEnrollment.objects.all().delete()[0]

            # 7. Eliminar métodos de graduación
            self.stdout.write('Eliminando métodos de graduación...')
            counts['graduation_methods'] = GraduationMethod.objects.all().delete()[0]

            # 8. Eliminar inscripciones (enrollments) y sus contratos
            self.stdout.write('Eliminando inscripciones...')
            enrollments = Enrollment.objects.all()
            for enrollment in enrollments:
                if enrollment.contract_file:
                    try:
                        if os.path.isfile(enrollment.contract_file.path):
                            os.remove(enrollment.contract_file.path)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'No se pudo eliminar archivo: {enrollment.contract_file.path} - {e}'))
                if enrollment.contract_scanned:
                    try:
                        if os.path.isfile(enrollment.contract_scanned.path):
                            os.remove(enrollment.contract_scanned.path)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'No se pudo eliminar archivo: {enrollment.contract_scanned.path} - {e}'))
            counts['enrollments'] = enrollments.delete()[0]

            # 8. Eliminar estudiantes
            self.stdout.write('Eliminando estudiantes...')
            counts['students'] = Student.objects.all().delete()[0]

            # 9. Eliminar usuarios de prueba (si no se especifica --keep-users)
            if not options['keep_users']:
                self.stdout.write('Eliminando usuarios de prueba...')
                test_usernames = ['admin', 'secretario', 'academico', 'financiero', 'consulta']
                test_users = User.objects.filter(username__in=test_usernames)
                counts['test_users'] = test_users.delete()[0]
            else:
                self.stdout.write('Manteniendo usuarios de prueba (--keep-users)')
                counts['test_users'] = 0

        # Resumen
        self.stdout.write(self.style.SUCCESS('\n✅ Eliminación completada!\n'))
        self.stdout.write(self.style.SUCCESS('Resumen:'))
        self.stdout.write(f"  - Estudiantes eliminados: {counts.get('students', 0)}")
        self.stdout.write(f"  - Inscripciones eliminadas: {counts.get('enrollments', 0)}")
        self.stdout.write(f"  - Documentos eliminados: {counts.get('student_documents', 0)}")
        self.stdout.write(f"  - Pagos eliminados: {counts.get('payments', 0)}")
        self.stdout.write(f"  - Becas eliminadas: {counts.get('scholarships', 0)}")
        self.stdout.write(f"  - Inscripciones en cursos eliminadas: {counts.get('course_enrollments', 0)}")
        self.stdout.write(f"  - Inscripciones a cuatrimestres eliminadas: {counts.get('cuatrimestre_enrollments', 0)}")
        self.stdout.write(f"  - Métodos de graduación eliminados: {counts.get('graduation_methods', 0)}")
        total_history = (
            counts.get('enrollment_status_history', 0) +
            counts.get('student_document_status_history', 0) +
            counts.get('payment_status_history', 0) +
            counts.get('cuatrimestre_enrollment_status_history', 0) +
            counts.get('graduation_method_status_history', 0)
        )
        self.stdout.write(f"  - Historiales eliminados: {total_history}")
        self.stdout.write(f"  - Usuarios de prueba eliminados: {counts.get('test_users', 0)}")

        self.stdout.write(self.style.SUCCESS('\n✓ Los datos de configuración (carreras, cursos, tipos de pago, catálogos SEP, roles) se mantienen intactos.'))
