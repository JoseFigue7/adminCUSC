"""
Comando para poblar la base de datos con datos de prueba
Incluye estudiantes, documentos, pagos, inscripciones en cursos, becas y tesis
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import datetime, timedelta
import random
import uuid
from io import BytesIO
from PIL import Image
import os

from students.models import Student, Enrollment, StudentDocument
from academics.models import Career, Course, CourseEnrollment, Thesis
from payments.models import Payment, Scholarship, PaymentConfiguration
from students.utils import generate_carnet_number


class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de prueba completos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--students',
            type=int,
            default=20,
            help='Número de estudiantes a crear (default: 20)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Eliminar datos existentes antes de crear nuevos'
        )

    def handle(self, *args, **options):
        num_students = options['students']
        clear = options['clear']

        if clear:
            self.stdout.write(self.style.WARNING('Eliminando datos existentes...'))
            Student.objects.all().delete()
            Payment.objects.all().delete()
            Scholarship.objects.all().delete()
            CourseEnrollment.objects.all().delete()
            Thesis.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Datos eliminados'))

        # Verificar que existan carreras
        careers = Career.objects.all()
        if not careers.exists():
            self.stdout.write(self.style.ERROR('No hay carreras en la base de datos. Ejecuta primero: python manage.py seed_careers'))
            return

        # Crear configuraciones de pago si no existen
        self.create_payment_configs(careers)

        # Nombres y apellidos de prueba
        first_names = [
            'Juan', 'María', 'Carlos', 'Ana', 'Luis', 'Laura', 'Pedro', 'Carmen',
            'José', 'Patricia', 'Miguel', 'Sofía', 'Roberto', 'Elena', 'Fernando', 'Isabel',
            'Ricardo', 'Andrea', 'Daniel', 'Mónica', 'Alejandro', 'Gabriela', 'Francisco', 'Valeria',
            'Andrés', 'Natalia', 'Diego', 'Paola', 'Sergio', 'Diana'
        ]
        
        last_names = [
            'García', 'Rodríguez', 'López', 'Martínez', 'González', 'Pérez', 'Sánchez', 'Ramírez',
            'Torres', 'Flores', 'Rivera', 'Gómez', 'Díaz', 'Cruz', 'Morales', 'Ortiz',
            'Gutiérrez', 'Chávez', 'Ramos', 'Reyes', 'Herrera', 'Jiménez', 'Mendoza', 'Vargas',
            'Castro', 'Romero', 'Álvarez', 'Méndez', 'Guerrero', 'Ruiz'
        ]

        # Crear estudiantes
        self.stdout.write(self.style.SUCCESS(f'Creando {num_students} estudiantes...'))
        
        students_created = []
        current_year = datetime.now().year
        
        for i in range(num_students):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            career = random.choice(careers)
            
            # Generar email único
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            
            # Generar fecha de nacimiento (entre 18 y 30 años)
            birth_year = current_year - random.randint(18, 30)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            date_of_birth = datetime(birth_year, birth_month, birth_day).date()
            
            # Generar CURP (formato simplificado)
            curp = f"{last_name[:2]}{first_name[:2]}{birth_year}{birth_month:02d}{birth_day:02d}H{random.randint(100, 999)}"
            
            # Crear estudiante
            student = Student.objects.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=f"+52{random.randint(1000000000, 9999999999)}",
                date_of_birth=date_of_birth,
                gender=random.choice(['M', 'F', 'O']),
                curp=curp,
                address=f"Calle {random.randint(1, 999)} # {random.randint(1, 999)}, Col. {random.choice(['Centro', 'Norte', 'Sur', 'Oriente', 'Poniente'])}",
                career=career,
                is_active=random.choice([True, True, True, False]),  # 75% activos
                has_scholarship=random.choice([True, False, False, False]),  # 25% con beca
                scholarship_type=random.choice(['NINGUNA', 'MEDIA', 'COMPLETA']) if random.random() < 0.25 else 'NINGUNA',
                pensum_closed=random.choice([True, False, False, False, False]),  # 20% con pensum cerrado
                thesis_started=random.choice([True, False, False, False, False, False])  # 16% con tesis iniciada
            )
            
            # Generar carnet
            student.carnet = generate_carnet_number(career.code, current_year)
            student.save()
            
            # Crear inscripción
            enrollment_status = random.choice(['PENDIENTE', 'EN_REVISION', 'APROBADA', 'APROBADA', 'APROBADA'])
            Enrollment.objects.create(
                student=student,
                status=enrollment_status,
                contract_generated=random.choice([True, False]) if enrollment_status == 'APROBADA' else False
            )
            
            students_created.append(student)
            
            # Crear documentos con archivos de prueba
            self.create_student_documents(student)
            
            # Crear pagos
            self.create_payments(student)
            
            # Crear inscripciones en cursos
            self.create_course_enrollments(student, career)
            
            # Crear beca si corresponde
            if student.has_scholarship:
                self.create_scholarship(student)
            
            # Crear tesis si corresponde
            if student.thesis_started:
                self.create_thesis(student)

        self.stdout.write(self.style.SUCCESS(f'✓ {len(students_created)} estudiantes creados exitosamente'))
        self.stdout.write(self.style.SUCCESS('✓ Documentos creados con archivos de prueba'))
        self.stdout.write(self.style.SUCCESS('✓ Pagos creados con comprobantes de prueba'))
        self.stdout.write(self.style.SUCCESS('✓ Inscripciones en cursos creadas'))
        self.stdout.write(self.style.SUCCESS('✓ Becas y tesis creadas'))

    def create_payment_configs(self, careers):
        """Crear configuraciones de pago para cada carrera"""
        for career in careers:
            PaymentConfiguration.objects.get_or_create(
                career=career,
                defaults={
                    'monthly_amount': random.choice([1500.00, 2000.00, 2500.00, 3000.00]),
                    'enrollment_fee': random.choice([500.00, 750.00, 1000.00]),
                    'is_active': True
                }
            )

    def create_student_documents(self, student):
        """Crear documentos del estudiante con archivos de prueba"""
        document_types = [
            'BACHILLERATO_ORIGINAL',
            'BACHILLERATO_COPIA1',
            'BACHILLERATO_COPIA2',
            'NACIMIENTO_ORIGINAL',
            'NACIMIENTO_COPIA1',
            'NACIMIENTO_COPIA2',
            'CURP',
            'MEDICO',
            'FOTO_DIGITAL',
            'FOTO_FISICA1',
            'FOTO_FISICA2',
            'DOMICILIO',
        ]
        
        for doc_type in document_types:
            # 80% de probabilidad de tener cada documento
            if random.random() < 0.8:
                status = random.choice(['PENDIENTE', 'RECIBIDO', 'APROBADO', 'APROBADO', 'APROBADO'])
                
                # Crear archivo de prueba según el tipo
                file_content = self.create_test_file(doc_type)
                
                if file_content:
                    doc = StudentDocument.objects.create(
                        student=student,
                        document_type=doc_type,
                        status=status,
                        notes='Documento de prueba generado automáticamente' if status == 'APROBADO' else ''
                    )
                    
                    # Asignar archivo
                    filename = self.get_filename_for_document_type(doc_type)
                    doc.file.save(filename, file_content, save=True)

    def create_test_file(self, doc_type):
        """Crear archivo de prueba según el tipo de documento"""
        if 'FOTO' in doc_type:
            # Crear imagen de prueba
            img = Image.new('RGB', (800, 1000), color=(73, 109, 137))
            buffer = BytesIO()
            img.save(buffer, format='JPEG')
            buffer.seek(0)
            return ContentFile(buffer.read(), name=f'test_{doc_type.lower()}.jpg')
        else:
            # Crear PDF de prueba (simulado como texto)
            pdf_content = f"""
            Documento de Prueba: {doc_type}
            Generado automáticamente para pruebas del sistema
            Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Estudiante: {doc_type}
            """
            return ContentFile(pdf_content.encode(), name=f'test_{doc_type.lower()}.pdf')

    def get_filename_for_document_type(self, doc_type):
        """Obtener nombre de archivo apropiado según el tipo"""
        if 'FOTO' in doc_type:
            return f'test_{doc_type.lower()}.jpg'
        else:
            return f'test_{doc_type.lower()}.pdf'

    def create_payments(self, student):
        """Crear pagos para el estudiante"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Crear pagos para los últimos 6 meses
        for month_offset in range(6):
            month = current_month - month_offset
            year = current_year
            
            if month <= 0:
                month += 12
                year -= 1
            
            # 70% de probabilidad de tener pago para cada mes
            if random.random() < 0.7:
                payment_method = random.choice(['TRANSFERENCIA', 'TARJETA', 'EFECTIVO'])
                status = random.choice(['PENDIENTE', 'EN_REVISION', 'APROBADO', 'APROBADO', 'APROBADO'])
                
                # Obtener monto de la configuración o usar default
                try:
                    config = PaymentConfiguration.objects.get(career=student.career, is_active=True)
                    amount = config.monthly_amount
                except PaymentConfiguration.DoesNotExist:
                    amount = random.choice([1500.00, 2000.00, 2500.00])
                
                payment = Payment.objects.create(
                    student=student,
                    payment_method=payment_method,
                    amount=amount,
                    month=month,
                    year=year,
                    status=status,
                    receipt_number=f'REC-{random.randint(1000, 9999)}' if payment_method == 'EFECTIVO' else '',
                    card_last_four=f'{random.randint(1000, 9999)}' if payment_method == 'TARJETA' else '',
                    transaction_id=f'TXN-{uuid.uuid4().hex[:8].upper()}' if payment_method == 'TARJETA' else '',
                    notes='Pago de prueba generado automáticamente'
                )
                
                # Agregar comprobante si es transferencia
                if payment_method == 'TRANSFERENCIA' and status in ['EN_REVISION', 'APROBADO']:
                    receipt_content = self.create_payment_receipt()
                    payment.transfer_receipt.save(
                        f'comprobante_{student.carnet}_{year}_{month:02d}.pdf',
                        receipt_content,
                        save=True
                    )

    def create_payment_receipt(self):
        """Crear comprobante de pago de prueba"""
        receipt_content = f"""
        COMPROBANTE DE TRANSFERENCIA
        ============================
        Fecha: {datetime.now().strftime('%d/%m/%Y')}
        Monto: ${random.choice([1500.00, 2000.00, 2500.00])}
        Banco: Banco de Prueba
        Número de referencia: REF-{random.randint(100000, 999999)}
        Comprobante generado automáticamente para pruebas
        """
        return ContentFile(receipt_content.encode(), name='comprobante_transferencia.pdf')

    def create_course_enrollments(self, student, career):
        """Crear inscripciones en cursos para el estudiante"""
        courses = career.courses.all()
        
        if not courses.exists():
            return
        
        # Inscribir en 30-80% de los cursos
        num_courses = int(len(courses) * random.uniform(0.3, 0.8))
        selected_courses = random.sample(list(courses), min(num_courses, len(courses)))
        
        for course in selected_courses:
            status = random.choice(['MATRICULADO', 'EN_CURSO', 'APROBADO', 'REPROBADO', 'APROBADO', 'APROBADO'])
            
            enrollment = CourseEnrollment.objects.create(
                student=student,
                course=course,
                status=status,
                enrollment_date=datetime.now().date() - timedelta(days=random.randint(0, 365))
            )
            
            # Agregar nota final si está aprobado o reprobado
            if status in ['APROBADO', 'REPROBADO']:
                if status == 'APROBADO':
                    enrollment.final_grade = random.randint(70, 100)
                else:
                    enrollment.final_grade = random.randint(0, 69)
                enrollment.save()

    def create_scholarship(self, student):
        """Crear beca para el estudiante"""
        scholarship_type = student.scholarship_type if student.scholarship_type != 'NINGUNA' else random.choice(['COMPLETA', 'MEDIA'])
        percentage = 100.00 if scholarship_type == 'COMPLETA' else 50.00
        
        start_date = datetime.now().date() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=365) if random.random() < 0.5 else None
        
        Scholarship.objects.create(
            student=student,
            scholarship_type=scholarship_type,
            percentage=percentage,
            start_date=start_date,
            end_date=end_date,
            status=random.choice(['ACTIVA', 'ACTIVA', 'ACTIVA', 'SUSPENDIDA', 'FINALIZADA']),
            notes='Beca de prueba generada automáticamente'
        )

    def create_thesis(self, student):
        """Crear tesis para el estudiante"""
        statuses = [
            'REVISION_TEMA',
            'APROBACION_TEMA',
            'PRIMERA_REVISION',
            'SEGUNDA_REVISION',
            'TERCERA_REVISION',
            'APROBADA',
        ]
        
        # Progreso más realista: la mayoría en etapas iniciales
        status_weights = [0.3, 0.25, 0.2, 0.1, 0.08, 0.07]
        status = random.choices(statuses, weights=status_weights)[0]
        
        Thesis.objects.create(
            student=student,
            title=f'Tesis de Prueba: {random.choice(["Análisis", "Estudio", "Investigación", "Propuesta"])} sobre {random.choice(["Educación", "Derecho", "Administración", "Criminología"])}',
            advisor=f'Dr. {random.choice(["García", "Rodríguez", "López", "Martínez"])}',
            status=status,
            start_date=datetime.now().date() - timedelta(days=random.randint(60, 365)),
            notes='Tesis de prueba generada automáticamente'
        )

