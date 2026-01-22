"""
Señales para rastrear cambios de estado en modelos de estudiantes
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import logging
from .models import (
    Student, Enrollment, StudentDocument, 
    EnrollmentStatusHistory, StudentDocumentStatusHistory,
    generate_moodle_username, generate_moodle_password
)

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Enrollment)
def track_enrollment_status_change(sender, instance, **kwargs):
    """
    Rastrea cambios de estado en Enrollment antes de guardar
    """
    if instance.pk:
        try:
            old_instance = Enrollment.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status
            
            # Solo registrar si el estado cambió
            if old_status != new_status:
                instance._old_status = old_status
        except Enrollment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=Enrollment)
def save_enrollment_status_history(sender, instance, created, **kwargs):
    """
    Guarda el historial de cambio de estado después de guardar Enrollment
    """
    if created:
        EnrollmentStatusHistory.objects.create(
            enrollment=instance,
            previous_status=None,
            new_status=instance.status,
            changed_by=getattr(instance, '_changed_by_user', None),
            comment='Estado inicial al crear la inscripción'
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        
        # Solo crear registro si el estado cambió
        if old_status is not None and old_status != instance.status:
            EnrollmentStatusHistory.objects.create(
                enrollment=instance,
                previous_status=old_status,
                new_status=instance.status,
                changed_by=getattr(instance, '_changed_by_user', None),
                comment=getattr(instance, '_status_change_notes', '')
            )


@receiver(pre_save, sender=StudentDocument)
def track_student_document_status_change(sender, instance, **kwargs):
    """
    Rastrea cambios de estado en StudentDocument antes de guardar
    """
    if instance.pk:
        try:
            old_instance = StudentDocument.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status
            
            if old_status != new_status:
                instance._old_status = old_status
        except StudentDocument.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=StudentDocument)
def save_student_document_status_history(sender, instance, created, **kwargs):
    """
    Guarda el historial de cambio de estado después de guardar StudentDocument
    """
    if created:
        StudentDocumentStatusHistory.objects.create(
            student_document=instance,
            previous_status=None,
            new_status=instance.status,
            changed_by=getattr(instance, '_changed_by_user', None),
            comment='Estado inicial al crear el documento'
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        
        # Solo crear registro si el estado cambió
        if old_status is not None and old_status != instance.status:
            StudentDocumentStatusHistory.objects.create(
                student_document=instance,
                previous_status=old_status,
                new_status=instance.status,
                changed_by=getattr(instance, '_changed_by_user', None),
                comment=getattr(instance, '_status_change_notes', '')
            )


@receiver(post_save, sender=Student)
def generate_moodle_credentials(sender, instance, created, **kwargs):
    """
    Genera automáticamente el usuario y contraseña de Moodle cuando se crea un estudiante.
    Solo se genera si no existen ya (para no sobrescribir si se crean manualmente).
    """
    # Verificar si las credenciales no existen (tanto en creación como en actualización)
    if not instance.moodle_username or not instance.moodle_password:
        # Solo generar si tenemos los datos necesarios
        if instance.first_name and instance.first_last_name:
            try:
                # Generar usuario de Moodle
                username = generate_moodle_username(
                    instance.first_name,
                    instance.first_last_name,
                    instance.second_last_name
                )
                
                # Generar contraseña de Moodle
                password = generate_moodle_password()
                
                logger.info(f'Generando credenciales de Moodle para estudiante {instance.id}: usuario={username}')
                
                # Actualizar el estudiante con las credenciales
                # Usar update para evitar recursión en el signal
                Student.objects.filter(pk=instance.pk).update(
                    moodle_username=username,
                    moodle_password=password
                )
                
                # Actualizar la instancia en memoria para que esté sincronizada
                instance.moodle_username = username
                instance.moodle_password = password
                
                logger.info(f'Credenciales de Moodle generadas exitosamente para estudiante {instance.id}')
            except Exception as e:
                logger.error(f'Error al generar credenciales de Moodle para estudiante {instance.id}: {str(e)}', exc_info=True)
        else:
            logger.warning(f'No se pueden generar credenciales de Moodle para estudiante {instance.id}: faltan datos (first_name o first_last_name)')
