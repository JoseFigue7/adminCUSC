#!/bin/bash

# Script de despliegue para Digital Ocean
# Uso: ./deploy.sh

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue de AdminCUSC..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables de entorno (ajustar según tu configuración)
PROJECT_DIR="/var/www/admincusc"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

# Verificar que estamos en el directorio correcto
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: No se encontró el directorio backend${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Actualizando código desde Git...${NC}"
cd $PROJECT_DIR
git pull origin main

echo -e "${YELLOW}🐍 Configurando backend...${NC}"
cd $BACKEND_DIR

# Activar entorno virtual
source $VENV_DIR/bin/activate

# Instalar/actualizar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate --noinput

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Cargar datos iniciales si es necesario
# python manage.py seed_careers

echo -e "${YELLOW}⚛️  Configurando frontend...${NC}"
cd $FRONTEND_DIR

# Instalar/actualizar dependencias
npm install

# Construir aplicación de producción
npm run build

echo -e "${YELLOW}🔄 Reiniciando servicios...${NC}"

# Reiniciar Gunicorn
sudo systemctl restart admincusc

# Recargar Nginx
sudo systemctl reload nginx

echo -e "${GREEN}✅ Despliegue completado exitosamente!${NC}"
