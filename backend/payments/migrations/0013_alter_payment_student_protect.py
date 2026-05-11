# Generated manually: evita borrar estudiantes por accidente junto con todo su historial de pagos.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0012_sync_payment_schema'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='student',
            field=models.ForeignKey(
                help_text='No se puede eliminar el estudiante mientras existan pagos asociados; borre o reasigne los pagos primero.',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='payments',
                to='students.student',
                verbose_name='Estudiante',
            ),
        ),
    ]
