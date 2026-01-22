# Configuración de Email

Este documento explica cómo configurar el servidor de email para el sistema AdminCUSC.

## Configuración para Desarrollo

En desarrollo, los emails se muestran en la consola del servidor Django por defecto. No se requiere configuración adicional.

## Configuración para Producción

Para enviar emails reales en producción, configura las siguientes variables de entorno:

### Opción 1: Gmail (Recomendado para empezar)

```bash
# Backend SMTP
export EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"

# Configuración Gmail
export EMAIL_HOST="smtp.gmail.com"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
export EMAIL_USE_SSL="False"

# Credenciales de Gmail
# NOTA: Para Gmail, necesitas usar una "Contraseña de aplicación" en lugar de tu contraseña normal
# Ve a: https://myaccount.google.com/apppasswords
export EMAIL_HOST_USER="tu-email@gmail.com"
export EMAIL_HOST_PASSWORD="tu-contraseña-de-aplicacion"

# Email remitente
export DEFAULT_FROM_EMAIL="tu-email@gmail.com"
```

**Importante para Gmail:**
1. Activa la verificación en 2 pasos en tu cuenta de Google
2. Genera una "Contraseña de aplicación" desde: https://myaccount.google.com/apppasswords
3. Usa esa contraseña de aplicación (no tu contraseña normal) en `EMAIL_HOST_PASSWORD`

### Opción 2: Otros proveedores SMTP

#### Outlook/Hotmail
```bash
export EMAIL_HOST="smtp-mail.outlook.com"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
export EMAIL_HOST_USER="tu-email@outlook.com"
export EMAIL_HOST_PASSWORD="tu-contraseña"
export DEFAULT_FROM_EMAIL="tu-email@outlook.com"
```

#### SendGrid
```bash
export EMAIL_HOST="smtp.sendgrid.net"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
export EMAIL_HOST_USER="apikey"
export EMAIL_HOST_PASSWORD="tu-api-key-de-sendgrid"
export DEFAULT_FROM_EMAIL="noreply@tudominio.com"
```

#### Mailgun
```bash
export EMAIL_HOST="smtp.mailgun.org"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
export EMAIL_HOST_USER="postmaster@tudominio.mailgun.org"
export EMAIL_HOST_PASSWORD="tu-password-de-mailgun"
export DEFAULT_FROM_EMAIL="noreply@tudominio.com"
```

#### Servidor SMTP personalizado
```bash
export EMAIL_HOST="smtp.tudominio.com"
export EMAIL_PORT="587"  # o 465 para SSL
export EMAIL_USE_TLS="True"  # True para puerto 587, False para 465
export EMAIL_USE_SSL="False"  # True para puerto 465, False para 587
export EMAIL_HOST_USER="usuario@smtp.tudominio.com"
export EMAIL_HOST_PASSWORD="tu-contraseña"
export DEFAULT_FROM_EMAIL="noreply@tudominio.com"
```

## Configuración en archivo .env

Puedes crear un archivo `.env` en la raíz del proyecto `backend/` con:

```env
# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-contraseña-de-aplicacion
DEFAULT_FROM_EMAIL=tu-email@gmail.com
EMAIL_TIMEOUT=10
```

**Nota:** Asegúrate de que el archivo `.env` esté en `.gitignore` para no subir credenciales al repositorio.

## Verificación

Para verificar que la configuración funciona, puedes usar el shell de Django:

```bash
cd backend
python manage.py shell
```

Y ejecutar:

```python
from django.core.mail import send_mail
send_mail(
    'Prueba de Email',
    'Este es un mensaje de prueba.',
    'noreply@admincusc.local',
    ['tu-email-de-prueba@gmail.com'],
    fail_silently=False,
)
```

Si todo está configurado correctamente, deberías recibir el email.

## Troubleshooting

### Error: "SMTPAuthenticationError"
- Verifica que las credenciales sean correctas
- Para Gmail, asegúrate de usar una "Contraseña de aplicación"
- Verifica que la verificación en 2 pasos esté activada en Gmail

### Error: "Connection refused"
- Verifica que el puerto y el host sean correctos
- Verifica que el firewall no esté bloqueando la conexión
- Algunos proveedores requieren conexiones desde IPs autorizadas

### Los emails no llegan
- Revisa la carpeta de spam
- Verifica que el email del destinatario sea válido
- Revisa los logs del servidor para ver si hay errores

## Seguridad

- **NUNCA** subas credenciales de email al repositorio
- Usa variables de entorno o archivos `.env` que estén en `.gitignore`
- Considera usar servicios de email transaccional (SendGrid, Mailgun) para producción
- Para producción, considera usar un servicio de email dedicado en lugar de Gmail
