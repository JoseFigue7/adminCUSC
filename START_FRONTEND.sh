#!/bin/bash
# Script para iniciar el frontend de AdminCUSC

cd "$(dirname "$0")/frontend"

# Verificar que las dependencias estén instaladas
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando dependencias..."
    npm install
fi

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  Creando archivo .env..."
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:8004/api
PORT=3000
EOF
fi

echo "🚀 Iniciando frontend en puerto 3000..."
echo "📍 URL: http://localhost:3000"
echo "🔗 Backend API: http://localhost:8004/api"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

npm start
