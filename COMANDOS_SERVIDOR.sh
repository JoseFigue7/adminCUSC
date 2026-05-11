#!/bin/bash
# Comandos para ejecutar en el servidor 137.184.188.234
# Copia y pega estos comandos uno por uno o ejecuta el script completo

set -e

echo "🚀 Iniciando despliegue de AdminCUSC en el servidor..."
echo ""

# PASO 1: Actualizar sistema
echo "📦 PASO 1: Actualizando sistema..."
apt update && apt upgrade -y

# PASO 2: Instalar dependencias básicas
echo ""
echo "📦 PASO 2: Instalando dependencias básicas..."
apt install -y \
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
    libpangocairo-1.0-0 \
    certbot \
    python3-certbot-nginx

# PASO 3: Instalar Node.js usando NVM
echo ""
echo "📦 PASO 3: Instalando Node.js..."
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
nvm install --lts
nvm use --lts
nvm alias default node

# PASO 4: Configurar MySQL
echo ""
echo "📦 PASO 4: Configurando MySQL..."
echo "⚠️  IMPORTANTE: Necesitarás configurar MySQL manualmente"
echo "   Ejecuta: mysql_secure_installation"
echo ""
echo "   Luego crea la base de datos con:"
echo "   mysql -u root -p"
echo "   CREATE DATABASE admincusc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "   CREATE USER 'admincusc_user'@'localhost' IDENTIFIED BY 'TU_PASSWORD_SEGURA';"
echo "   GRANT ALL PRIVILEGES ON admincusc_db.* TO 'admincusc_user'@'localhost';"
echo "   FLUSH PRIVILEGES;"
echo "   EXIT;"

read -p "¿Ya configuraste MySQL? (s/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "⚠️  Configura MySQL primero y luego continúa..."
    exit 1
fi

# PASO 5: Crear directorio y clonar repositorio
echo ""
echo "📦 PASO 5: Clonando repositorio..."
mkdir -p /var/www/admincusc
cd /var/www/admincusc
git clone https://github.com/JoseFigue7/adminCUSC.git .

# PASO 6: Configurar Backend
echo ""
echo "📦 PASO 6: Configurando backend..."
cd /var/www/admincusc/backend

# Crear entorno virtual
python3.10 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Crear archivo .env
cp .env.example .env
echo ""
echo "⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones:"
echo "   nano /var/www/admincusc/backend/.env"
echo ""
echo "   Necesitas configurar:"
echo "   - SECRET_KEY (genera uno con: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
echo "   - DEBUG=False"
echo "   - ALLOWED_HOSTS=137.184.188.234,localhost"
echo "   - DB_PASSWORD (la contraseña que creaste para MySQL)"
echo ""

read -p "¿Ya configuraste el archivo .env? (s/n): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo "⚠️  Configura el .env primero..."
    exit 1
fi

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
echo ""
echo "📝 Crear superusuario de Django..."
python manage.py createsuperuser

# Crear roles
python manage.py init_roles

# Crear usuarios de prueba (opcional)
python manage.py seed_test_users

# Cargar datos iniciales
python manage.py seed_careers

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# PASO 7: Configurar Frontend
echo ""
echo "📦 PASO 7: Configurando frontend..."
cd /var/www/admincusc/frontend

# Configurar Node.js en el PATH
export PATH="$HOME/.nvm/versions/node/$(nvm version)/bin:$PATH"

# Instalar dependencias
npm install

# Crear archivo .env
cat > .env << EOF
REACT_APP_API_URL=http://137.184.188.234/api
PORT=3000
EOF

# Construir aplicación
npm run build

# PASO 8: Configurar Gunicorn
echo ""
echo "📦 PASO 8: Configurando Gunicorn..."
cp /var/www/admincusc/admincusc.service.example /etc/systemd/system/admincusc.service
systemctl daemon-reload
systemctl enable admincusc
systemctl start admincusc
systemctl status admincusc --no-pager

# PASO 9: Configurar Nginx
echo ""
echo "📦 PASO 9: Configurando Nginx..."
cp /var/www/admincusc/nginx.conf /etc/nginx/sites-available/admincusc
ln -sf /etc/nginx/sites-available/admincusc /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# PASO 10: Configurar permisos
echo ""
echo "📦 PASO 10: Configurando permisos..."
chown -R www-data:www-data /var/www/admincusc/backend
chown -R www-data:www-data /var/www/admincusc/backend/staticfiles
chown -R www-data:www-data /var/www/admincusc/backend/media

# PASO 11: Configurar Firewall
echo ""
echo "📦 PASO 11: Configurando firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable
ufw status

echo ""
echo "✅ ¡Despliegue completado!"
echo ""
echo "🌐 URLs de acceso:"
echo "   - API: http://137.184.188.234/api/"
echo "   - Admin: http://137.184.188.234/admin/"
echo "   - Swagger: http://137.184.188.234/swagger/"
echo ""
echo "📋 Comandos útiles:"
echo "   - Ver logs de Gunicorn: journalctl -u admincusc -f"
echo "   - Ver logs de Nginx: tail -f /var/log/nginx/error.log"
echo "   - Reiniciar servicios: systemctl restart admincusc && systemctl restart nginx"
