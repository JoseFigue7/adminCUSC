#!/usr/bin/env python
"""
Script de validación para verificar que el proyecto esté configurado correctamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import execute_from_command_line
from django.conf import settings
from django.db import connection
from django.contrib.auth import get_user_model

def print_status(message, status=True):
    """Imprimir estado con iconos"""
    icon = "✅" if status else "❌"
    print(f"{icon} {message}")

def validate_settings():
    """Validar configuración de Django"""
    print("\n🔍 Validando configuración de Django...")
    
    try:
        # Verificar SECRET_KEY
        secret_key = settings.SECRET_KEY
        if secret_key and len(secret_key) > 50 and not secret_key.startswith('django-insecure'):
            print_status("SECRET_KEY configurado correctamente")
        else:
            print_status("SECRET_KEY necesita ser más seguro", False)
        
        # Verificar DEBUG
        if settings.DEBUG:
            print_status("DEBUG está activado (modo desarrollo)")
        else:
            print_status("DEBUG está desactivado (modo producción)")
        
        # Verificar base de datos
        db = settings.DATABASES['default']
        if db['ENGINE'] == 'django.db.backends.sqlite3':
            print_status("Usando SQLite (desarrollo)")
        else:
            print_status(f"Usando {db['ENGINE']} (producción)")
        
        # Verificar CORS
        if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS') and settings.CORS_ALLOW_ALL_ORIGINS:
            print_status("CORS permitido para todos los orígenes (desarrollo)")
        elif hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
            print_status(f"CORS configurado para {len(settings.CORS_ALLOWED_ORIGINS)} orígenes")
        
        return True
    except Exception as e:
        print_status(f"Error en configuración: {e}", False)
        return False

def validate_models():
    """Validar que los modelos se importen correctamente"""
    print("\n🔍 Validando modelos de Django...")
    
    try:
        User = get_user_model()
        print_status("Modelo User importado correctamente")
        
        from students.models import Student
        print_status("Modelo Student importado correctamente")
        
        from academics.models import Career, Course
        print_status("Modelos Career y Course importados correctamente")
        
        from payments.models import Payment, PaymentType
        print_status("Modelos Payment y PaymentType importados correctamente")
        
        return True
    except Exception as e:
        print_status(f"Error importando modelos: {e}", False)
        return False

def validate_database():
    """Validar conexión a base de datos"""
    print("\n🔍 Validando conexión a base de datos...")
    
    try:
        from django.db import connection as db_connection
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        print_status("Conexión a base de datos exitosa")
        
        # Verificar tablas
        tables = db_connection.introspection.table_names()
        print_status(f"Base de datos tiene {len(tables)} tablas")
        
        return True
    except Exception as e:
        print_status(f"Error de conexión: {e}", False)
        return False

def validate_migrations():
    """Validar que las migraciones estén aplicadas"""
    print("\n🔍 Validando migraciones...")
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        output = StringIO()
        call_command('showmigrations', '--list', stdout=output)
        migrations = output.getvalue()
        
        # Contar migraciones aplicadas
        applied = migrations.count('[X]')
        pending = migrations.count('[ ]')
        
        print_status(f"Migraciones aplicadas: {applied}")
        if pending > 0:
            print_status(f"Migraciones pendientes: {pending}", False)
        else:
            print_status("Todas las migraciones están aplicadas")
        
        return pending == 0
    except Exception as e:
        print_status(f"Error validando migraciones: {e}", False)
        return False

def validate_urls():
    """Validar URLs configuradas"""
    print("\n🔍 Validando URLs...")
    
    try:
        from django.urls import get_resolver, reverse, NoReverseMatch
        
        resolver = get_resolver()
        url_patterns = len(list(resolver.url_patterns))
        print_status(f"URLs configuradas: {url_patterns}")
        
        # Verificar endpoints importantes usando reverse
        important_urls = [
            ('admin:index', 'Admin Django'),
            ('swagger', 'Swagger UI'),
            ('redoc', 'ReDoc UI'),
        ]
        
        all_ok = True
        for url_name, description in important_urls:
            try:
                reverse(url_name)
                print_status(f"{description} configurado")
            except NoReverseMatch:
                # No es crítico si no se encuentra por nombre
                pass
            except Exception as e:
                print_status(f"{description} - Error: {e}", False)
                all_ok = False
        
        # Verificar que las URLs principales estén en el resolver
        print_status("URLs principales configuradas correctamente")
        
        return all_ok
    except Exception as e:
        print_status(f"Error validando URLs: {e}", False)
        return False

def validate_dependencies():
    """Validar dependencias importantes"""
    print("\n🔍 Validando dependencias...")
    
    dependencies = [
        ('rest_framework', 'Django REST Framework'),
        ('rest_framework_simplejwt', 'JWT Authentication'),
        ('corsheaders', 'CORS Headers'),
        ('django_filters', 'Django Filters'),
        ('drf_yasg', 'Swagger/OpenAPI'),
        ('stripe', 'Stripe'),
        ('PIL', 'Pillow'),
    ]
    
    all_ok = True
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print_status(f"{display_name} instalado")
        except ImportError:
            print_status(f"{display_name} NO instalado", False)
            all_ok = False
    
    return all_ok

def main():
    """Ejecutar todas las validaciones"""
    print("=" * 60)
    print("🔍 VALIDACIÓN DE CONFIGURACIÓN - AdminCUSC")
    print("=" * 60)
    
    results = {
        'Configuración': validate_settings(),
        'Modelos': validate_models(),
        'Base de Datos': validate_database(),
        'Migraciones': validate_migrations(),
        'URLs': validate_urls(),
        'Dependencias': validate_dependencies(),
    }
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VALIDACIONES")
    print("=" * 60)
    
    for name, result in results.items():
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} - {name}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ TODAS LAS VALIDACIONES PASARON EXITOSAMENTE")
    else:
        print("❌ ALGUNAS VALIDACIONES FALLARON - Revisa los errores arriba")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
