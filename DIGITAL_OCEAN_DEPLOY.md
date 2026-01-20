# Guía de Despliegue en Digital Ocean

Esta guía te ayudará a desplegar AdminCUSC en un Droplet de Digital Ocean.

## Requisitos Previos

- Un Droplet de Digital Ocean (recomendado: Ubuntu 22.04 LTS, mínimo 2GB RAM)
- Dominio configurado apuntando a la IP del Droplet (opcional pero recomendado)
- Acceso SSH al Droplet

## Paso 1: Configuración Inicial del Servidor

### 1.1 Actualizar el sistema

```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Instalar dependencias del sistema

```bash
# Python y pip
sudo apt install -y python3.10 python3.10-venv python3-pip

# Node.js (usar nvm para versión LTS)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install --lts
nvm use --lts

# Nginx
sudo apt install -y nginx

# MySQL (opcional, si usas MySQL en lugar de SQLite)
sudo apt install -y mysql-server

# Dependencias para WeasyPrint
sudo apt install -y \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0

# Certbot para SSL
sudo apt install -y certbot python3-certbot-nginx

# Git
sudo apt install -y git
```

## Paso 2: Configurar Base de Datos (MySQL)

Si vas a usar MySQL en lugar de SQLite:

```bash
# Configurar MySQL
sudo mysql_secure_installation

# Crear base de datos y usuario
sudo mysql -u root -p << EOF
CREATE DATABASE admincusc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'admincusc_user'@'localhost' IDENTIFIED BY 'tu_password_segura';
GRANT ALL PRIVILEGES ON admincusc_db.* TO 'admincusc_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
EOF
```

## Paso 3: Clonar el Repositorio

```bash
# Crear directorio para la aplicación
sudo mkdir -p /var/www/admincusc
sudo chown $USER:$USER /var/www/admincusc

# Clonar repositorio
cd /var/www/admincusc
git clone https://github.com/JoseFigue7/adminCUSC.git .

# O si ya tienes el código local, usar scp o rsync
```

## Paso 4: Configurar Backend

```bash
cd /var/www/admincusc/backend

# Crear entorno virtual
python3.10 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus valores
```

Configura tu archivo `.env` con estos valores:

```env
# Django Configuration
SECRET_KEY=tu-secret-key-super-segura-generada
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com,IP_DEL_DROPLET

# Database Configuration
USE_SQLITE=False
DB_NAME=admincusc_db
DB_USER=admincusc_user
DB_PASSWORD=tu_password_segura
DB_HOST=localhost
DB_PORT=3306

# Stripe Configuration (si lo usas)
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Audit Configuration
AUDIT_ENABLED=True
```

Generar SECRET_KEY:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

```bash
# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Cargar datos iniciales (carreras y pensums)
python manage.py seed_careers

# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

## Paso 5: Configurar Gunicorn

Crear archivo de servicio systemd para Gunicorn:

```bash
sudo nano /etc/systemd/system/admincusc.service
```

Contenido del archivo:

```ini
[Unit]
Description=AdminCUSC Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/admincusc/backend
Environment="PATH=/var/www/admincusc/backend/venv/bin"
ExecStart=/var/www/admincusc/backend/venv/bin/gunicorn \
    --config /var/www/admincusc/backend/gunicorn_config.py \
    config.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

Activar y iniciar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable admincusc
sudo systemctl start admincusc
sudo systemctl status admincusc
```

## Paso 6: Configurar Nginx

```bash
# Copiar configuración de ejemplo
sudo cp /var/www/admincusc/nginx.conf.example /etc/nginx/sites-available/admincusc

# Editar configuración
sudo nano /etc/nginx/sites-available/admincusc

# Actualizar el nombre del dominio en la configuración
# Reemplazar 'tu-dominio.com' con tu dominio real

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/admincusc /etc/nginx/sites-enabled/

# Eliminar sitio por defecto
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

## Paso 7: Configurar SSL con Let's Encrypt

```bash
# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Certbot configurará automáticamente Nginx y renovación
# Verificar renovación automática
sudo certbot renew --dry-run
```

## Paso 8: Configurar Frontend

```bash
cd /var/www/admincusc/frontend

# Instalar dependencias
npm install

# Configurar variable de entorno para la API
# Editar src/config.ts o el archivo de configuración correspondiente
# Cambiar la URL de la API a tu dominio de producción

# Construir aplicación de producción
npm run build

# Los archivos de build estarán en la carpeta 'build'
# Necesitarás configurar Nginx para servir estos archivos estáticos
```

## Paso 9: Configurar Firewall

```bash
# Permitir SSH, HTTP y HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## Paso 10: Configurar Backups

Configurar backups regulares de la base de datos:

```bash
# Crear script de backup
sudo nano /usr/local/bin/backup-admincusc.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/admincusc"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup de base de datos MySQL
mysqldump -u admincusc_user -p'password' admincusc_db > $BACKUP_DIR/db_$DATE.sql

# Backup de archivos media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/admincusc/backend/media

# Mantener solo los últimos 7 días
find $BACKUP_DIR -type f -mtime +7 -delete
```

```bash
sudo chmod +x /usr/local/bin/backup-admincusc.sh

# Agregar a crontab (backup diario a las 2 AM)
sudo crontab -e
# Agregar esta línea:
0 2 * * * /usr/local/bin/backup-admincusc.sh
```

## Monitoreo y Logs

```bash
# Ver logs de Gunicorn
sudo journalctl -u admincusc -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Verificar estado de servicios
sudo systemctl status admincusc
sudo systemctl status nginx
```

## Actualización del Código

Usar el script de despliegue proporcionado:

```bash
cd /var/www/admincusc
chmod +x deploy.sh
./deploy.sh
```

O manualmente:

```bash
cd /var/www/admincusc
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart admincusc

# Frontend
cd ../frontend
npm install
npm run build

# Recargar Nginx
sudo systemctl reload nginx
```

## Solución de Problemas

### Error 502 Bad Gateway
- Verificar que Gunicorn esté corriendo: `sudo systemctl status admincusc`
- Verificar logs: `sudo journalctl -u admincusc -n 50`

### Error de permisos
```bash
sudo chown -R www-data:www-data /var/www/admincusc/backend
sudo chown -R www-data:www-data /var/www/admincusc/backend/staticfiles
sudo chown -R www-data:www-data /var/www/admincusc/backend/media
```

### Error de base de datos
- Verificar que MySQL esté corriendo: `sudo systemctl status mysql`
- Verificar credenciales en `.env`

## Seguridad Adicional

1. **Configurar fail2ban** para proteger contra ataques de fuerza bruta:
```bash
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

2. **Configurar actualizaciones automáticas**:
```bash
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

3. **Deshabilitar root login** y usar solo usuarios con sudo.

## Recursos Adicionales

- [Digital Ocean Django Guide](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-22-04)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
