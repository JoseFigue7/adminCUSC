#!/bin/bash
# Script de configuración rápida para el servidor 137.184.188.234
# Ejecutar este script en el servidor de Digital Ocean

set -e

SERVER_IP="137.184.188.234"
PROJECT_DIR="/var/www/admincusc"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"

echo "🚀 Configurando servidor $SERVER_IP para AdminCUSC..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Error: No se encontró el directorio backend en $PROJECT_DIR"
    echo "   Ejecuta primero: git clone https://github.com/JoseFigue7/adminCUSC.git $PROJECT_DIR"
    exit 1
fi

echo "📦 Configurando backend..."
cd $BACKEND_DIR

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    python3.10 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar/actualizar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Crear .env si no existe
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tus configuraciones:"
    echo "   nano $BACKEND_DIR/.env"
fi

# Ejecutar migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

echo ""
echo "⚛️  Configurando frontend..."
cd $FRONTEND_DIR

# Instalar dependencias
npm install

# Crear .env si no existe
if [ ! -f ".env" ]; then
    cat > .env << EOF
REACT_APP_API_URL=http://$SERVER_IP/api
PORT=3000
EOF
fi

# Construir aplicación
npm run build

echo ""
echo "🔧 Configurando servicios..."

# Copiar configuración de Gunicorn si no existe
if [ ! -f "/etc/systemd/system/admincusc.service" ]; then
    sudo cp $PROJECT_DIR/admincusc.service.example /etc/systemd/system/admincusc.service
    sudo systemctl daemon-reload
    sudo systemctl enable admincusc
fi

# Copiar configuración de Nginx si no existe
if [ ! -f "/etc/nginx/sites-available/admincusc" ]; then
    sudo cp $PROJECT_DIR/nginx.conf /etc/nginx/sites-available/admincusc
    sudo ln -sf /etc/nginx/sites-available/admincusc /etc/nginx/sites-enabled/admincusc
    sudo rm -f /etc/nginx/sites-enabled/default
fi

# Configurar permisos
sudo chown -R www-data:www-data $BACKEND_DIR
sudo chown -R www-data:www-data $BACKEND_DIR/staticfiles
sudo chown -R www-data:www-data $BACKEND_DIR/media

echo ""
echo "🔄 Reiniciando servicios..."
sudo systemctl restart admincusc
sudo systemctl restart nginx

echo ""
echo "✅ Configuración completada!"
echo ""
echo "📋 Verificar servicios:"
echo "   sudo systemctl status admincusc"
echo "   sudo systemctl status nginx"
echo ""
echo "🌐 URLs de acceso:"
echo "   - API: http://$SERVER_IP/api/"
echo "   - Admin: http://$SERVER_IP/admin/"
echo "   - Swagger: http://$SERVER_IP/swagger/"
echo ""
echo "⚠️  IMPORTANTE: Asegúrate de haber configurado el archivo .env en $BACKEND_DIR"
