# Generated manually: alinea payments con models.py (tablas huérfanas + campos obligatorios).

from decimal import Decimal

import django.core.validators
from django.db import migrations, models
from django.utils import timezone


def forwards_fix_payment_rows(apps, schema_editor):
    """Evita fallos al pasar amount/payment_date a NOT NULL y estados antiguos a choices actuales."""
    Payment = apps.get_model('payments', 'Payment')
    today = timezone.now().date()
    legacy_to_pending = {'NO_PAGADO', 'MORA'}
    for p in Payment.objects.all().iterator(chunk_size=500):
        changed = []
        if p.amount is None:
            fa = getattr(p, 'final_amount', None) or getattr(p, 'original_amount', None)
            p.amount = fa if fa is not None else Decimal('0.01')
            changed.append('amount')
        if p.payment_date is None:
            p.payment_date = today
            changed.append('payment_date')
        if p.status in legacy_to_pending:
            p.status = 'PENDIENTE'
            changed.append('status')
        if changed:
            p.save(update_fields=changed)


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0011_alter_payment_base_amount'),
    ]

    operations = [
        migrations.RunPython(forwards_fix_payment_rows, backwards_noop),
        migrations.DeleteModel(
            name='PaymentStatusHistory',
        ),
        migrations.DeleteModel(
            name='StripeWebhookEvent',
        ),
        migrations.AlterField(
            model_name='payment',
            name='amount',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                verbose_name='Monto',
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='base_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                verbose_name='Monto base (sin mora)',
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='final_amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Monto final: original_amount - scholarship_discount_amount + penalty_amount',
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.00'))],
                verbose_name='Monto final',
            ),
        ),
        migrations.AlterField(
            model_name='payment',
            name='payment_date',
            field=models.DateField(auto_now_add=True, verbose_name='Fecha de pago'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('EN_REVISION', 'En Revisión'),
                    ('APROBADO', 'Aprobado'),
                    ('RECHAZADO', 'Rechazado'),
                ],
                default='PENDIENTE',
                max_length=20,
                verbose_name='Estado',
            ),
        ),
        migrations.AlterField(
            model_name='paymenttype',
            name='amount',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(Decimal('0.01'))],
                verbose_name='Monto fijo (opcional)',
            ),
        ),
    ]
