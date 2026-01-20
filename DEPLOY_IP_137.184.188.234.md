# Guía de Despliegue - Servidor 137.184.188.234

Esta guía está específicamente configurada para el droplet de Digital Ocean con IP: **137.184.188.234**

## Paso 1: Conectarse al Servidor

```bash
ssh root@137.184.188.234
# o si usas un usuario diferente:
ssh tu_usuario@137.184.188.234
```

## Paso 2: Configuración Inicial del Servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias básicas
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    nginx \
    git \
    mysql-server \
    python3-cffi \
    python3-brotli \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libpangocairo-1.0-0

# Instalar Node.js usando NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install --lts
nvm use --lts

# Instalar Certbot (para SSL si usas dominio)
sudo apt install -y certbot python3-certbot-nginx
```

## Paso 3: Configurar Base de Datos MySQL

```bash
# Configurar MySQL
sudo mysql_secure_installation

# Crear base de datos y usuario
sudo mysql -u root -p << EOF
CREATE DATABASE admincusc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'admincusc_user'@'localhost' IDENTIFIED BY 'TU_PASSWORD_SEGURA_AQUI';
GRANT ALL PRIVILEGES ON admincusc_db.* TO 'admincusc_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
EOF
```

**Nota:** Cambia `TU_PASSWORD_SEGURA_AQUI` por una contraseña segura y guárdala en un lugar seguro.

## Paso 4: Clonar el Repositorio

```bash
# Crear directorio para la aplicación
sudo mkdir -p /var/www/admincusc
sudo chown $USER:$USER /var/www/admincusc

# Clonar repositorio
cd /var/www/admincusc
git clone https://github.com/JoseFigue7/adminCUSC.git .

# O si ya tienes el código, usar scp desde tu máquina local:
# scp -r /ruta/local/adminCUSC/* root@137.184.188.234:/var/www/admincusc/
```

## Paso 5: Configurar Backend

```bash
cd /var/www/admincusc/backend

# Crear entorno virtual
python3.10 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Crear archivo .env
cp .env.example .env
nano .env
```

**Configurar archivo .env con estos valores:**

```env
# Django Configuration
SECRET_KEY=GENERA_UNA_SECRET_KEY_SEGURA_AQUI
DEBUG=False
ALLOWED_HOSTS=137.184.188.234,localhost

# Database Configuration
USE_SQLITE=False
DB_NAME=admincusc_db
DB_USER=admincusc_user
DB_PASSWORD=TU_PASSWORD_SEGURA_AQUI
DB_HOST=localhost
DB_PORT=3306

# Stripe Configuration (si lo usas)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Audit Configuration
AUDIT_ENABLED=True
```

**Generar SECRET_KEY:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

```bash
# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Crear roles
python manage.py init_roles

# Crear usuarios de prueba (opcional)
python manage.py seed_test_users

# Cargar datos iniciales (carreras y pensums)
python manage.py seed_careers

# Recolectar archivos estáticos
python manage.py collectstatic --noinput
```

## Paso 6: Configurar Gunicorn

```bash
# Copiar archivo de servicio systemd
sudo cp /var/www/admincusc/admincusc.service.example /etc/systemd/system/admincusc.service

# Editar el archivo si es necesario
sudo nano /etc/systemd/system/admincusc.service

# Activar y iniciar servicio
sudo systemctl daemon-reload
sudo systemctl enable admincusc
sudo systemctl start admincusc
sudo systemctl status admincusc
```

## Paso 7: Configurar Nginx

```bash
# Copiar configuración de Nginx
sudo cp /var/www/admincusc/nginx.conf /etc/nginx/sites-available/admincusc

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/admincusc /etc/nginx/sites-enabled/

# Eliminar sitio por defecto
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

## Paso 8: Configurar Frontend

```bash
cd /var/www/admincusc/frontend

# Instalar dependencias
npm install

# Crear archivo .env
cp .env.example .env
nano .env
```

**Configurar archivo .env del frontend:**

```env
REACT_APP_API_URL=http://137.184.188.234/api
PORT=3000
```

```bash
# Construir aplicación de producción
npm run build

# Los archivos de build estarán en la carpeta 'build'
# Configura Nginx para servir estos archivos estáticos si es necesario
```

## Paso 9: Configurar Firewall

```bash
# Permitir SSH, HTTP y HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## Paso 10: Configurar Permisos

```bash
# Asignar permisos correctos
sudo chown -R www-data:www-data /var/www/admincusc/backend
sudo chown -R www-data:www-data /var/www/admincusc/backend/staticfiles
sudo chown -R www-data:www-data /var/www/admincusc/backend/media
```

## Paso 11: Configurar SSL (Opcional - Si tienes dominio)

Si tienes un dominio apuntando a esta IP:

```bash
# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

# Verificar renovación automática
sudo certbot renew --dry-run
```

## Verificar Despliegue

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

## URLs de Acceso

- **Backend API:** http://137.184.188.234/api/
- **Admin Django:** http://137.184.188.234/admin/
- **Swagger UI:** http://137.184.188.234/swagger/
- **ReDoc:** http://137.184.188.234/redoc/
- **Frontend:** http://137.184.188.234/ (si está configurado)

## Comandos Útiles

```bash
# Reiniciar servicios
sudo systemctl restart admincusc
sudo systemctl restart nginx

# Ver logs
sudo journalctl -u admincusc -n 50
sudo tail -50 /var/log/nginx/error.log

# Actualizar código
cd /var/www/admincusc
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart admincusc
```

## Solución de Problemas

### Error 502 Bad Gateway
- Verificar que Gunicorn esté corriendo: `sudo systemctl status admincusc`
- Verificar logs: `sudo journalctl -u admincusc -n 50`

### Error de permisos
```bash
sudo chown -R www-data:www-data /var/www/admincusc
```

### Error de base de datos
- Verificar que MySQL esté corriendo: `sudo systemctl status mysql`
- Verificar credenciales en `.env`
