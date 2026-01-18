# Generated manually for payment traceability

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0007_add_course_cost_and_period_config'),
        ('users', '0002_alter_user_last_login'),
        ('payments', '0004_add_cuatrimestre_enrollment_relation'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='career',
            field=models.ForeignKey(
                blank=True,
                help_text='Carrera del estudiante al momento del pago (para trazabilidad)',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payments',
                to='academics.career',
                verbose_name='Carrera'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                help_text='Usuario que creó el registro del pago',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payments_created',
                to='users.user',
                verbose_name='Creado por'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='approved_by',
            field=models.ForeignKey(
                blank=True,
                help_text='Usuario que aprobó el pago',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payments_approved',
                to='users.user',
                verbose_name='Aprobado por'
            ),
        ),
        migrations.AddField(
            model_name='payment',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de aprobación'),
        ),
    ]
