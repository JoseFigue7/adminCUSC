# Generated manually for payment amount refactoring
# This migration adds original_amount, scholarship_discount_amount, and final_amount fields
# to support detailed payment breakdown with scholarship discounts

from django.db import migrations, models
import django.core.validators
from decimal import Decimal


def populate_new_amount_fields(apps, schema_editor):
    """
    Migración de datos: Popula los nuevos campos de monto basándose en datos existentes.
    
    Para registros existentes:
    - original_amount: Se establece desde base_amount si existe, o desde amount
    - scholarship_discount_amount: Se calcula si el estudiante tiene beca activa
    - final_amount: Se calcula como original_amount - scholarship_discount_amount + penalty_amount
    """
    Payment = apps.get_model('payments', 'Payment')
    Scholarship = apps.get_model('payments', 'Scholarship')
    
    for payment in Payment.objects.all():
        # 1. Establecer original_amount
        if payment.base_amount:
            payment.original_amount = payment.base_amount
        elif payment.amount:
            # Si no hay base_amount, usar amount como original_amount
            # (asumiendo que amount no incluye mora en registros antiguos sin base_amount)
            payment.original_amount = payment.amount
        else:
            # Si no hay ningún monto, saltar este registro
            continue
        
        # 2. Calcular descuento por beca
        scholarship_discount = Decimal('0.00')
        try:
            # Intentar obtener la beca del estudiante
            scholarship = Scholarship.objects.filter(
                student=payment.student,
                status='ACTIVA'
            ).first()
            
            if scholarship:
                # Verificar que la fecha de pago esté dentro del rango de vigencia
                payment_date = payment.payment_date
                if (scholarship.start_date <= payment_date and 
                    (not scholarship.end_date or scholarship.end_date >= payment_date)):
                    # Calcular descuento basado en el porcentaje de la beca
                    scholarship_discount = payment.original_amount * (scholarship.percentage / Decimal('100.00'))
        except Exception:
            # Si hay algún error al obtener la beca, continuar con descuento 0
            pass
        
        payment.scholarship_discount_amount = scholarship_discount
        
        # 3. Calcular monto final
        # final_amount = original_amount - scholarship_discount + penalty_amount
        payment.final_amount = payment.original_amount - scholarship_discount + payment.penalty_amount
        
        # Guardar sin triggers (usar update para evitar llamar save())
        Payment.objects.filter(pk=payment.pk).update(
            original_amount=payment.original_amount,
            scholarship_discount_amount=payment.scholarship_discount_amount,
            final_amount=payment.final_amount
        )


def reverse_populate_new_amount_fields(apps, schema_editor):
    """
    Operación reversa: No hay nada que revertir ya que los campos son nuevos.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_add_payment_traceability_fields'),
    ]

    operations = [
        # Agregar los nuevos campos
        migrations.AddField(
            model_name='payment',
            name='original_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Monto sin beca ni mora (monto base del pago)',
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                verbose_name='Monto original'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='scholarship_discount_amount',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0.00'),
                help_text='Monto de descuento aplicado según beca activa del estudiante',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
                verbose_name='Descuento por beca'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='final_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Monto final a pagar: original_amount - scholarship_discount_amount + penalty_amount',
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                verbose_name='Monto final'
            ),
        ),
        # Migración de datos: poblar los nuevos campos
        migrations.RunPython(
            populate_new_amount_fields,
            reverse_populate_new_amount_fields
        ),
    ]
