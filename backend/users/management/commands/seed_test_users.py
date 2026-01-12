"""
Comando para crear usuarios de prueba con diferentes roles
"""
from django.core.management.base import BaseCommand
from users.models import User, Role


class Command(BaseCommand):
    help = 'Crea usuarios de prueba con diferentes roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando usuarios de prueba...'))
        
        # Obtener roles
        try:
            super_admin_role = Role.objects.get(name='SUPER_ADMIN')
            admin_role = Role.objects.get(name='ADMIN')
            secretary_role = Role.objects.get(name='SECRETARY')
            academic_role = Role.objects.get(name='ACADEMIC_COORDINATOR')
            financial_role = Role.objects.get(name='FINANCIAL')
            viewer_role = Role.objects.get(name='VIEWER')
        except Role.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Error: Rol no encontrado. Ejecuta primero: python manage.py init_roles'))
            return
        
        # Usuarios de prueba
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@admincusc.com',
                'password': 'admin123',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'role': super_admin_role,
            },
            {
                'username': 'secretario',
                'email': 'secretario@admincusc.com',
                'password': 'secretario123',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'phone': '+521234567890',
                'role': secretary_role,
            },
            {
                'username': 'academico',
                'email': 'academico@admincusc.com',
                'password': 'academico123',
                'first_name': 'María',
                'last_name': 'García',
                'phone': '+521234567891',
                'role': academic_role,
            },
            {
                'username': 'financiero',
                'email': 'financiero@admincusc.com',
                'password': 'financiero123',
                'first_name': 'Carlos',
                'last_name': 'Rodríguez',
                'phone': '+521234567892',
                'role': financial_role,
            },
            {
                'username': 'consulta',
                'email': 'consulta@admincusc.com',
                'password': 'consulta123',
                'first_name': 'Ana',
                'last_name': 'López',
                'phone': '+521234567893',
                'role': viewer_role,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for user_data in test_users:
            role = user_data.pop('role')
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            
            if not created:
                # Actualizar datos si el usuario ya existe
                for key, value in user_data.items():
                    setattr(user, key, value)
                updated_count += 1
            else:
                created_count += 1
            
            # Establecer contraseña y rol
            user.set_password(password)
            user.role = role
            user.is_staff = True  # Para acceder al admin de Django
            user.save()
            
            status = 'creado' if created else 'actualizado'
            self.stdout.write(self.style.SUCCESS(
                f'✓ Usuario {user.username} ({user.get_full_name()}) - Rol: {role.get_name_display()} - {status}'
            ))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Proceso completado: {created_count} creados, {updated_count} actualizados'))
        self.stdout.write(self.style.WARNING('\n📝 Credenciales de prueba:'))
        self.stdout.write(self.style.WARNING('  Super Admin: admin / admin123'))
        self.stdout.write(self.style.WARNING('  Secretario: secretario / secretario123'))
        self.stdout.write(self.style.WARNING('  Académico: academico / academico123'))
        self.stdout.write(self.style.WARNING('  Financiero: financiero / financiero123'))
        self.stdout.write(self.style.WARNING('  Consulta: consulta / consulta123'))






