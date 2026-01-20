#!/bin/bash
# Script para iniciar el servidor Django en macOS con las variables de entorno correctas

cd "$(dirname "$0")"

# Configurar variables de entorno para Homebrew en macOS
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
export DYLD_LIBRARY_PATH="/opt/homebrew/lib:$DYLD_LIBRARY_PATH"
export PATH="/opt/homebrew/bin:$PATH"

# Activar entorno virtual
source venv/bin/activate

# Iniciar servidor en el puerto especificado (default 8004)
PORT=${1:-8004}
echo "🚀 Iniciando servidor Django en puerto $PORT..."
echo "📍 URL: http://localhost:$PORT"
echo ""
python manage.py runserver $PORT
