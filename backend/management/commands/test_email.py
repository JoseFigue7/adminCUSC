"""
Comando de Django para probar la configuración de email
Uso: python manage.py test_email <email_destino>
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Prueba la configuración de email enviando un correo de prueba'

    def add_arguments(self, parser):
        parser.add_argument(
            'email',
            type=str,
            help='Dirección de correo electrónico de destino para la prueba'
        )

    def handle(self, *args, **options):
        email_destino = options['email']
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Prueba de Configuración de Email'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        # Mostrar configuración actual
        self.stdout.write('Configuración actual:')
        self.stdout.write(f'  EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  EMAIL_HOST: {getattr(settings, "EMAIL_HOST", "N/A")}')
        self.stdout.write(f'  EMAIL_PORT: {getattr(settings, "EMAIL_PORT", "N/A")}')
        self.stdout.write(f'  EMAIL_USE_TLS: {getattr(settings, "EMAIL_USE_TLS", "N/A")}')
        self.stdout.write(f'  EMAIL_USE_SSL: {getattr(settings, "EMAIL_USE_SSL", "N/A")}')
        self.stdout.write(f'  EMAIL_HOST_USER: {getattr(settings, "EMAIL_HOST_USER", "N/A")}')
        self.stdout.write(f'  DEFAULT_FROM_EMAIL: {getattr(settings, "DEFAULT_FROM_EMAIL", "N/A")}')
        self.stdout.write('')
        
        # Intentar enviar email simple
        self.stdout.write(f'Enviando email de prueba a: {email_destino}')
        self.stdout.write('')
        
        try:
            send_mail(
                subject='Prueba de Email - Colegio Santa Cecilia',
                message='''
Este es un mensaje de prueba del sistema Colegio Santa Cecilia.

Si recibes este correo, significa que la configuración de email está funcionando correctamente.

Saludos,
Colegio Santa Cecilia
                ''',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@admincusc.local'),
                recipient_list=[email_destino],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS('✓ Email enviado exitosamente!'))
            self.stdout.write('')
            self.stdout.write(f'Por favor, revisa tu bandeja de entrada (y spam) en: {email_destino}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR('✗ Error al enviar el email:'))
            self.stdout.write(self.style.ERROR(f'  {str(e)}'))
            self.stdout.write('')
            self.stdout.write('Posibles soluciones:')
            self.stdout.write('  1. Verifica que las credenciales SMTP sean correctas')
            self.stdout.write('  2. Para Gmail, asegúrate de usar una "Contraseña de aplicación"')
            self.stdout.write('  3. Verifica que el firewall no esté bloqueando la conexión')
            self.stdout.write('  4. Revisa los logs del servidor para más detalles')
            self.stdout.write('')
            self.stdout.write('Para más información, consulta: EMAIL_CONFIG.md')
            sys.exit(1)
