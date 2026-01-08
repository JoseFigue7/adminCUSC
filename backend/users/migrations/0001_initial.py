# Generated manually to avoid conflicts

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(choices=[('SUPER_ADMIN', 'Super Administrador'), ('ADMIN', 'Administrador'), ('SECRETARY', 'Secretario'), ('ACADEMIC_COORDINATOR', 'Coordinador Académico'), ('FINANCIAL', 'Financiero'), ('VIEWER', 'Consulta')], max_length=50, unique=True, verbose_name='Nombre del rol')),
                ('description', models.TextField(blank=True, verbose_name='Descripción')),
                ('can_manage_students', models.BooleanField(default=False, verbose_name='Puede gestionar estudiantes')),
                ('can_manage_payments', models.BooleanField(default=False, verbose_name='Puede gestionar pagos')),
                ('can_manage_academics', models.BooleanField(default=False, verbose_name='Puede gestionar académico')),
                ('can_manage_scholarships', models.BooleanField(default=False, verbose_name='Puede gestionar becas')),
                ('can_manage_thesis', models.BooleanField(default=False, verbose_name='Puede gestionar tesis')),
                ('can_view_reports', models.BooleanField(default=False, verbose_name='Puede ver reportes')),
                ('can_manage_users', models.BooleanField(default=False, verbose_name='Puede gestionar usuarios')),
                ('can_manage_settings', models.BooleanField(default=False, verbose_name='Puede gestionar configuraciones')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Rol',
                'verbose_name_plural': 'Roles',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('phone', models.CharField(blank=True, max_length=15, verbose_name='Teléfono')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('role', models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, related_name='users', to='users.role', verbose_name='Rol')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
                'ordering': ['-date_joined'],
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
