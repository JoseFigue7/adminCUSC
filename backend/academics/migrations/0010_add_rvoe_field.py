# Generated manually for RVOE field addition

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0009_add_presencial_enrollment_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='career',
            name='rvoe',
            field=models.CharField(
                blank=True,
                help_text='Código RVOE de la carrera (ej: 20260159)',
                max_length=20,
                null=True,
                verbose_name='RVOE'
            ),
        ),
        # Data migration para poblar RVOE codes
        migrations.RunPython(
            lambda apps, schema_editor: populate_rvoe_codes(apps, schema_editor),
            reverse_code=migrations.RunPython.noop
        ),
    ]


def populate_rvoe_codes(apps, schema_editor):
    """Poblar códigos RVOE para las carreras existentes"""
    Career = apps.get_model('academics', 'Career')
    
    # Mapeo de nombres de carrera a RVOE codes
    rvoe_mapping = {
        'Licenciatura en Pedagogía': '20260159',
        'LICENCIATURA EN PEDAGOGÍA': '20260159',
        'Licenciatura en Criminología y Criminalística': '20260161',
        'LICENCIATURA EN CRIMINOLOGÍA Y CRIMINALÍSTICA': '20260161',
        'Licenciatura en Administración de Empresas y Negocios': '20260156',
        'LICENCIATURA EN ADMINISTRACIÓN DE EMPRESAS Y NEGOCIOS': '20260156',
        'Licenciatura en Derecho': '20260158',
        'LICENCIATURA EN DERECHO': '20260158',
        'Licenciatura en Mercadotecnia Digital y Publicidad': '20260160',
        'LICENCIATURA EN MERCADOTECNIA DIGITAL Y PUBLICIDAD': '20260160',
        'Licenciatura en Contaduría Pública y Finanzas': '20260157',
        'LICENCIATURA EN CONTADURÍA PÚBLICA Y FINANZAS': '20260157',
    }
    
    # Actualizar carreras existentes
    for career in Career.objects.all():
        # Buscar por nombre exacto o similar
        rvoe_code = None
        for name_pattern, code in rvoe_mapping.items():
            if name_pattern.upper() == career.name.upper():
                rvoe_code = code
                break
        
        if rvoe_code and not career.rvoe:
            career.rvoe = rvoe_code
            career.save(update_fields=['rvoe'])
