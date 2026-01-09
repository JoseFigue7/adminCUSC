"""
Comando para crear las tablas de usuarios manualmente
Úsalo si hay conflictos con las migraciones existentes
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Crea las tablas de usuarios manualmente'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # Crear tabla de roles
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users_role (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        description TEXT NOT NULL,
                        can_manage_students INTEGER NOT NULL DEFAULT 0,
                        can_manage_payments INTEGER NOT NULL DEFAULT 0,
                        can_manage_academics INTEGER NOT NULL DEFAULT 0,
                        can_manage_scholarships INTEGER NOT NULL DEFAULT 0,
                        can_manage_thesis INTEGER NOT NULL DEFAULT 0,
                        can_view_reports INTEGER NOT NULL DEFAULT 0,
                        can_manage_users INTEGER NOT NULL DEFAULT 0,
                        can_manage_settings INTEGER NOT NULL DEFAULT 0,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL
                    )
                """)
                
                # Crear tabla de usuarios (simplificada, sin conflictos)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users_user (
                        id TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        last_login DATETIME,
                        is_superuser INTEGER NOT NULL DEFAULT 0,
                        username TEXT NOT NULL UNIQUE,
                        first_name TEXT NOT NULL,
                        last_name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        is_staff INTEGER NOT NULL DEFAULT 0,
                        is_active INTEGER NOT NULL DEFAULT 1,
                        date_joined DATETIME NOT NULL,
                        phone TEXT NOT NULL DEFAULT '',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        role_id TEXT,
                        FOREIGN KEY (role_id) REFERENCES users_role(id)
                    )
                """)
                
                # Crear índices
                cursor.execute("CREATE INDEX IF NOT EXISTS users_user_role_id ON users_user(role_id)")
                
                self.stdout.write(self.style.SUCCESS('✓ Tablas de usuarios creadas exitosamente'))
                self.stdout.write(self.style.SUCCESS('✓ Ahora puedes ejecutar: python manage.py init_roles'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
                self.stdout.write(self.style.WARNING('Las tablas pueden ya existir. Intenta ejecutar: python manage.py migrate users --fake'))




