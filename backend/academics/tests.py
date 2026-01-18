"""
Tests para validar la restricción de solo una inscripción EN_CURSO por estudiante.
Incluye tests de concurrencia para verificar que select_for_update() previene condiciones de carrera.
"""
from django.test import TestCase, TransactionTestCase
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import threading
import time
from academics.models import (
    Career, Cuatrimestre, CuatrimestreEnrollment
)
from students.models import Student

User = get_user_model()


class CuatrimestreEnrollmentConcurrencyTest(TransactionTestCase):
    """
    Tests de concurrencia para validar que solo puede haber una inscripción EN_CURSO
    por estudiante, incluso en condiciones de alta concurrencia.
    """
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear carrera
        self.career = Career.objects.create(
            code=1,
            name='Ingeniería en Sistemas',
            description='Carrera de prueba'
        )
        
        # Crear cuatrimestres
        self.cuatrimestre1 = Cuatrimestre.objects.create(
            career=self.career,
            number=1,
            name='Primer Cuatrimestre'
        )
        
        self.cuatrimestre2 = Cuatrimestre.objects.create(
            career=self.career,
            number=2,
            name='Segundo Cuatrimestre'
        )
        
        # Crear estudiante
        self.student = Student.objects.create(
            first_name='Juan',
            first_last_name='Pérez',
            email='juan@example.com',
            career=self.career
        )
    
    def test_single_en_curso_enrollment(self):
        """Test básico: un estudiante solo puede tener una inscripción EN_CURSO"""
        # Crear primera inscripción EN_CURSO
        enrollment1 = CuatrimestreEnrollment.objects.create_with_en_curso_validation(
            student=self.student,
            cuatrimestre=self.cuatrimestre1,
            academic_year=2024,
            status='EN_CURSO'
        )
        
        # Intentar crear segunda inscripción EN_CURSO debería fallar
        with self.assertRaises(ValidationError):
            CuatrimestreEnrollment.objects.create_with_en_curso_validation(
                student=self.student,
                cuatrimestre=self.cuatrimestre2,
                academic_year=2024,
                status='EN_CURSO'
            )
        
        # Verificar que solo hay una inscripción EN_CURSO
        en_curso_count = CuatrimestreEnrollment.objects.filter(
            student=self.student,
            status='EN_CURSO'
        ).count()
        self.assertEqual(en_curso_count, 1)
    
    def test_multiple_non_en_curso_enrollments(self):
        """Test: un estudiante puede tener múltiples inscripciones en otros estados"""
        # Crear múltiples inscripciones en diferentes estados
        enrollment1 = CuatrimestreEnrollment.objects.create(
            student=self.student,
            cuatrimestre=self.cuatrimestre1,
            academic_year=2024,
            status='PENDIENTE_PAGO'
        )
        
        enrollment2 = CuatrimestreEnrollment.objects.create(
            student=self.student,
            cuatrimestre=self.cuatrimestre2,
            academic_year=2024,
            status='PENDIENTE_CONFIRMACION'
        )
        
        enrollment3 = CuatrimestreEnrollment.objects.create(
            student=self.student,
            cuatrimestre=self.cuatrimestre1,
            academic_year=2023,
            status='FINALIZADO'
        )
        
        # Todas deberían crearse exitosamente
        self.assertEqual(
            CuatrimestreEnrollment.objects.filter(student=self.student).count(),
            3
        )
    
    def test_update_to_en_curso_validation(self):
        """Test: actualizar a EN_CURSO valida que no haya otra EN_CURSO"""
        # Crear primera inscripción EN_CURSO
        enrollment1 = CuatrimestreEnrollment.objects.create_with_en_curso_validation(
            student=self.student,
            cuatrimestre=self.cuatrimestre1,
            academic_year=2024,
            status='EN_CURSO'
        )
        
        # Crear segunda inscripción en otro estado
        enrollment2 = CuatrimestreEnrollment.objects.create(
            student=self.student,
            cuatrimestre=self.cuatrimestre2,
            academic_year=2024,
            status='PENDIENTE_PAGO'
        )
        
        # Intentar actualizar la segunda a EN_CURSO debería fallar
        with self.assertRaises(ValidationError):
            CuatrimestreEnrollment.objects.update_to_en_curso(enrollment2)
        
        # Verificar que solo hay una EN_CURSO
        en_curso_count = CuatrimestreEnrollment.objects.filter(
            student=self.student,
            status='EN_CURSO'
        ).count()
        self.assertEqual(en_curso_count, 1)
    
    def test_update_to_en_curso_success(self):
        """Test: actualizar a EN_CURSO funciona cuando no hay otra EN_CURSO"""
        # Crear inscripción en otro estado
        enrollment = CuatrimestreEnrollment.objects.create(
            student=self.student,
            cuatrimestre=self.cuatrimestre1,
            academic_year=2024,
            status='PENDIENTE_CONFIRMACION'
        )
        
        # Actualizar a EN_CURSO debería funcionar
        updated = CuatrimestreEnrollment.objects.update_to_en_curso(enrollment)
        self.assertEqual(updated.status, 'EN_CURSO')
        
        # Verificar que hay una EN_CURSO
        en_curso_count = CuatrimestreEnrollment.objects.filter(
            student=self.student,
            status='EN_CURSO'
        ).count()
        self.assertEqual(en_curso_count, 1)
    
    def test_concurrent_en_curso_creation(self):
        """
        Test de concurrencia: múltiples threads intentando crear inscripciones EN_CURSO
        simultáneamente. Solo una debería tener éxito.
        """
        results = []
        errors = []
        lock = threading.Lock()
        
        def create_enrollment(cuatrimestre, year):
            """Función para crear inscripción en un thread"""
            try:
                enrollment = CuatrimestreEnrollment.objects.create_with_en_curso_validation(
                    student=self.student,
                    cuatrimestre=cuatrimestre,
                    academic_year=year,
                    status='EN_CURSO'
                )
                with lock:
                    results.append(enrollment.id)
            except ValidationError as e:
                with lock:
                    errors.append(str(e))
            except Exception as e:
                with lock:
                    errors.append(f"Unexpected error: {str(e)}")
        
        # Crear múltiples threads intentando crear inscripciones EN_CURSO simultáneamente
        threads = []
        for i in range(5):
            cuatrimestre = self.cuatrimestre1 if i % 2 == 0 else self.cuatrimestre2
            year = 2024 + (i % 2)
            thread = threading.Thread(
                target=create_enrollment,
                args=(cuatrimestre, year)
            )
            threads.append(thread)
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que todos terminen
        for thread in threads:
            thread.join()
        
        # Solo una inscripción EN_CURSO debería haberse creado
        en_curso_count = CuatrimestreEnrollment.objects.filter(
            student=self.student,
            status='EN_CURSO'
        ).count()
        self.assertEqual(en_curso_count, 1, 
                        f"Expected 1 EN_CURSO enrollment, got {en_curso_count}. "
                        f"Results: {results}, Errors: {errors}")
    
    def test_concurrent_update_to_en_curso(self):
        """
        Test de concurrencia: múltiples threads intentando actualizar diferentes
        inscripciones a EN_CURSO simultáneamente. Solo una debería tener éxito.
        """
        # Crear múltiples inscripciones en otros estados
        enrollments = []
        for i in range(3):
            enrollment = CuatrimestreEnrollment.objects.create(
                student=self.student,
                cuatrimestre=self.cuatrimestre1 if i == 0 else self.cuatrimestre2,
                academic_year=2024 + i,
                status='PENDIENTE_CONFIRMACION'
            )
            enrollments.append(enrollment)
        
        results = []
        errors = []
        lock = threading.Lock()
        
        def update_enrollment(enrollment):
            """Función para actualizar inscripción en un thread"""
            try:
                updated = CuatrimestreEnrollment.objects.update_to_en_curso(enrollment)
                with lock:
                    results.append(updated.id)
            except ValidationError as e:
                with lock:
                    errors.append(str(e))
            except Exception as e:
                with lock:
                    errors.append(f"Unexpected error: {str(e)}")
        
        # Crear múltiples threads intentando actualizar a EN_CURSO simultáneamente
        threads = []
        for enrollment in enrollments:
            thread = threading.Thread(
                target=update_enrollment,
                args=(enrollment,)
            )
            threads.append(thread)
        
        # Iniciar todos los threads
        for thread in threads:
            thread.start()
        
        # Esperar a que todos terminen
        for thread in threads:
            thread.join()
        
        # Solo una inscripción EN_CURSO debería existir
        en_curso_count = CuatrimestreEnrollment.objects.filter(
            student=self.student,
            status='EN_CURSO'
        ).count()
        self.assertEqual(en_curso_count, 1,
                        f"Expected 1 EN_CURSO enrollment, got {en_curso_count}. "
                        f"Results: {results}, Errors: {errors}")
    
    def test_finalize_en_curso_allows_new_enrollment(self):
        """Test: finalizar una inscripción EN_CURSO permite crear una nueva EN_CURSO"""
        # Crear inscripción EN_CURSO
        enrollment1 = CuatrimestreEnrollment.objects.create_with_en_curso_validation(
            student=self.student,
            cuatrimestre=self.cuatrimestre1,
            academic_year=2024,
            status='EN_CURSO'
        )
        
        # Finalizar la inscripción
        enrollment1.status = 'FINALIZADO'
        enrollment1.save()
        
        # Ahora debería poder crear una nueva inscripción EN_CURSO
        enrollment2 = CuatrimestreEnrollment.objects.create_with_en_curso_validation(
            student=self.student,
            cuatrimestre=self.cuatrimestre2,
            academic_year=2025,
            status='EN_CURSO'
        )
        
        # Verificar que la nueva inscripción existe
        self.assertEqual(enrollment2.status, 'EN_CURSO')
        
        # Verificar que solo hay una EN_CURSO (la nueva)
        en_curso_count = CuatrimestreEnrollment.objects.filter(
            student=self.student,
            status='EN_CURSO'
        ).count()
        self.assertEqual(en_curso_count, 1)
        self.assertEqual(
            CuatrimestreEnrollment.objects.get(
                student=self.student,
                status='EN_CURSO'
            ).id,
            enrollment2.id
        )


class CuatrimestreEnrollmentBasicTest(TestCase):
    """
    Tests básicos de funcionalidad (sin concurrencia)
    """
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear carrera
        self.career = Career.objects.create(
            code=1,
            name='Ingeniería en Sistemas',
            description='Carrera de prueba'
        )
        
        # Crear cuatrimestre
        self.cuatrimestre = Cuatrimestre.objects.create(
            career=self.career,
            number=1,
            name='Primer Cuatrimestre'
        )
        
        # Crear estudiante
        self.student = Student.objects.create(
            first_name='María',
            first_last_name='García',
            email='maria@example.com',
            career=self.career
        )
    
    def test_clean_validation(self):
        """Test que el método clean() valida correctamente"""
        # Crear primera inscripción EN_CURSO
        enrollment1 = CuatrimestreEnrollment.objects.create(
            student=self.student,
            cuatrimestre=self.cuatrimestre,
            academic_year=2024,
            status='EN_CURSO'
        )
        
        # Intentar crear segunda inscripción EN_CURSO debería fallar en clean()
        enrollment2 = CuatrimestreEnrollment(
            student=self.student,
            cuatrimestre=self.cuatrimestre,
            academic_year=2025,
            status='EN_CURSO'
        )
        
        with self.assertRaises(ValidationError):
            enrollment2.full_clean()
    
    def test_save_method_uses_manager(self):
        """Test que el método save() usa el manager cuando cambia a EN_CURSO"""
        # Crear inscripción en otro estado
        enrollment1 = CuatrimestreEnrollment.objects.create(
            student=self.student,
            cuatrimestre=self.cuatrimestre,
            academic_year=2024,
            status='PENDIENTE_CONFIRMACION'
        )
        
        # Cambiar a EN_CURSO usando save() debería funcionar
        enrollment1.status = 'EN_CURSO'
        enrollment1.save()
        
        # Verificar que se actualizó correctamente
        enrollment1.refresh_from_db()
        self.assertEqual(enrollment1.status, 'EN_CURSO')
        
        # Intentar crear otra EN_CURSO debería fallar
        enrollment2 = CuatrimestreEnrollment(
            student=self.student,
            cuatrimestre=self.cuatrimestre,
            academic_year=2025,
            status='EN_CURSO'
        )
        
        with self.assertRaises(ValidationError):
            enrollment2.save()
