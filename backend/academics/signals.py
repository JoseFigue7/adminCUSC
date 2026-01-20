"""
Señales para rastrear cambios de estado en modelos académicos
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import (
    CuatrimestreEnrollment, GraduationMethod,
    CuatrimestreEnrollmentStatusHistory, GraduationMethodStatusHistory
)


@receiver(pre_save, sender=CuatrimestreEnrollment)
def track_cuatrimestre_enrollment_status_change(sender, instance, **kwargs):
    """
    Rastrea cambios de estado en CuatrimestreEnrollment antes de guardar
    """
    if instance.pk:
        try:
            old_instance = CuatrimestreEnrollment.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status
            
            if old_status != new_status:
                instance._old_status = old_status
        except CuatrimestreEnrollment.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=CuatrimestreEnrollment)
def save_cuatrimestre_enrollment_status_history(sender, instance, created, **kwargs):
    """
    Guarda el historial de cambio de estado después de guardar CuatrimestreEnrollment
    """
    if created:
        CuatrimestreEnrollmentStatusHistory.objects.create(
            cuatrimestre_enrollment=instance,
            previous_status=None,
            new_status=instance.status,
            changed_by=getattr(instance, '_changed_by_user', None),
            comment='Estado inicial al crear la inscripción al cuatrimestre'
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        
        # Solo crear registro si el estado cambió
        if old_status is not None and old_status != instance.status:
            CuatrimestreEnrollmentStatusHistory.objects.create(
                cuatrimestre_enrollment=instance,
                previous_status=old_status,
                new_status=instance.status,
                changed_by=getattr(instance, '_changed_by_user', None),
                comment=getattr(instance, '_status_change_notes', '')
            )


@receiver(pre_save, sender=GraduationMethod)
def track_graduation_method_status_change(sender, instance, **kwargs):
    """
    Rastrea cambios de estado en GraduationMethod antes de guardar
    """
    if instance.pk:
        try:
            old_instance = GraduationMethod.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status
            
            if old_status != new_status:
                instance._old_status = old_status
        except GraduationMethod.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=GraduationMethod)
def save_graduation_method_status_history(sender, instance, created, **kwargs):
    """
    Guarda el historial de cambio de estado después de guardar GraduationMethod
    """
    if created:
        GraduationMethodStatusHistory.objects.create(
            graduation_method=instance,
            previous_status=None,
            new_status=instance.status,
            changed_by=getattr(instance, '_changed_by_user', None),
            comment='Estado inicial al crear el método de graduación'
        )
    else:
        old_status = getattr(instance, '_old_status', None)
        
        # Solo crear registro si el estado cambió
        if old_status is not None and old_status != instance.status:
            GraduationMethodStatusHistory.objects.create(
                graduation_method=instance,
                previous_status=old_status,
                new_status=instance.status,
                changed_by=getattr(instance, '_changed_by_user', None),
                comment=getattr(instance, '_status_change_notes', '')
            )
