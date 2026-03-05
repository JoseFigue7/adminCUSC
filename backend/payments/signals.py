"""
Señales para rastrear cambios de estado en modelos de pagos
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import Payment
# TODO: Descomentar cuando se cree el modelo PaymentStatusHistory
# from .models import PaymentStatusHistory


@receiver(pre_save, sender=Payment)
def track_payment_status_change(sender, instance, **kwargs):
    """
    Rastrea cambios de estado en Payment antes de guardar
    """
    if instance.pk:
        try:
            old_instance = Payment.objects.get(pk=instance.pk)
            old_status = old_instance.status
            new_status = instance.status
            
            # Solo registrar si el estado cambió
            if old_status != new_status:
                # Guardar el estado anterior en el modelo para usarlo en post_save
                instance._old_status = old_status
        except Payment.DoesNotExist:
            # Es un nuevo objeto, no hay estado anterior
            instance._old_status = None
    else:
        # Es un nuevo objeto
        instance._old_status = None


# TODO: Descomentar cuando se cree el modelo PaymentStatusHistory
# @receiver(post_save, sender=Payment)
# def save_payment_status_history(sender, instance, created, **kwargs):
#     """
#     Guarda el historial de cambio de estado después de guardar Payment
#     """
#     # Si es creación, registrar el estado inicial
#     if created:
#         PaymentStatusHistory.objects.create(
#             payment=instance,
#             previous_status=None,
#             new_status=instance.status,
#             changed_by=getattr(instance, '_changed_by_user', None),
#             comment='Estado inicial al crear el pago'
#         )
#     else:
#         # Si hay cambio de estado, registrar el historial
#         old_status = getattr(instance, '_old_status', None)
#         
#         # Solo crear registro si el estado cambió
#         if old_status is not None and old_status != instance.status:
#             PaymentStatusHistory.objects.create(
#                 payment=instance,
#                 previous_status=old_status,
#                 new_status=instance.status,
#                 changed_by=getattr(instance, '_changed_by_user', None),
#                 comment=getattr(instance, '_status_change_notes', '')
#             )
