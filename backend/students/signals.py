"""
Señales para rastrear cambios de estado en modelos de estudiantes
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Enrollment, StudentDocument, EnrollmentStatusHistory, StudentDocumentStatusHistory


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
