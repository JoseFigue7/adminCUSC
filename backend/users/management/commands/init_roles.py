from django.core.management.base import BaseCommand
from users.models import Role


class Command(BaseCommand):
    help = 'Inicializa los roles del sistema'

    def handle(self, *args, **options):
        roles_data = [
            {
                'name': 'SUPER_ADMIN',
                'description': 'Acceso total al sistema',
                'can_manage_students': True,
                'can_manage_payments': True,
                'can_manage_academics': True,
                'can_manage_scholarships': True,
                'can_manage_thesis': True,
                'can_view_reports': True,
                'can_manage_users': True,
                'can_manage_settings': True,
            },
            {
                'name': 'ADMIN',
                'description': 'Administrador general',
                'can_manage_students': True,
                'can_manage_payments': True,
                'can_manage_academics': True,
                'can_manage_scholarships': True,
                'can_manage_thesis': True,
                'can_view_reports': True,
                'can_manage_users': False,
                'can_manage_settings': False,
            },
            {
                'name': 'SECRETARY',
                'description': 'Secretario - Gestión de estudiantes y pagos',
                'can_manage_students': True,
                'can_manage_payments': True,
                'can_manage_academics': False,
                'can_manage_scholarships': False,
                'can_manage_thesis': False,
                'can_view_reports': True,
                'can_manage_users': False,
                'can_manage_settings': False,
            },
            {
                'name': 'ACADEMIC_COORDINATOR',
                'description': 'Coordinador Académico',
                'can_manage_students': False,
                'can_manage_payments': False,
                'can_manage_academics': True,
                'can_manage_scholarships': False,
                'can_manage_thesis': True,
                'can_view_reports': True,
                'can_manage_users': False,
                'can_manage_settings': False,
            },
            {
                'name': 'FINANCIAL',
                'description': 'Personal Financiero',
                'can_manage_students': False,
                'can_manage_payments': True,
                'can_manage_academics': False,
                'can_manage_scholarships': True,
                'can_manage_thesis': False,
                'can_view_reports': True,
                'can_manage_users': False,
                'can_manage_settings': False,
            },
            {
                'name': 'VIEWER',
                'description': 'Solo lectura',
                'can_manage_students': False,
                'can_manage_payments': False,
                'can_manage_academics': False,
                'can_manage_scholarships': False,
                'can_manage_thesis': False,
                'can_view_reports': True,
                'can_manage_users': False,
                'can_manage_settings': False,
            },
        ]

        created_count = 0
        updated_count = 0

        for role_data in roles_data:
            role, created = Role.objects.update_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Rol creado: {role.get_name_display()}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'→ Rol actualizado: {role.get_name_display()}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Proceso completado: {created_count} creados, {updated_count} actualizados'
            )
        )



