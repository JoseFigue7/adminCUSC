# Generated manually for flujo presencial guiado de inscripción

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0008_add_en_curso_index'),
    ]

    operations = [
        # Agregar nuevos campos booleanos
        migrations.AddField(
            model_name='cuatrimestreenrollment',
            name='is_first_enrollment',
            field=models.BooleanField(
                default=False,
                help_text='Indica si esta es la primera inscripción del estudiante (exoneración de cuota de inscripción)',
                verbose_name='Primera inscripción'
            ),
        ),
        migrations.AddField(
            model_name='cuatrimestreenrollment',
            name='is_enrollment_fee_exempt',
            field=models.BooleanField(
                default=False,
                help_text='Si es primera inscripción, se omite el pago de inscripción',
                verbose_name='Exonerado de cuota de inscripción'
            ),
        ),
        # Actualizar STATUS_CHOICES para incluir nuevos estados
        migrations.AlterField(
            model_name='cuatrimestreenrollment',
            name='status',
            field=models.CharField(
                choices=[
                    ('PRE_INSCRIPCION', 'Pre-inscripción'),
                    ('CURSOS_PREASIGNADOS', 'Cursos Pre-asignados'),
                    ('PENDIENTE_PAGO', 'Pendiente de Pago'),
                    ('PENDIENTE_CONFIRMACION', 'Pendiente de Confirmación'),
                    ('EN_CURSO', 'En Curso'),
                    ('FINALIZADO', 'Finalizado'),
                    ('CANCELADO', 'Cancelado'),
                ],
                default='PRE_INSCRIPCION',
                max_length=25,
                verbose_name='Estado'
            ),
        ),
    ]
