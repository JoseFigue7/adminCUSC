#!/bin/bash
# Script para preparar el repositorio para despliegue

set -e

echo "🚀 Preparando repositorio para despliegue en Digital Ocean..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "backend/manage.py" ]; then
    echo "❌ Error: No se encontró backend/manage.py"
    echo "   Ejecuta este script desde la raíz del proyecto"
    exit 1
fi

# Verificar que no haya archivos sensibles
echo "🔍 Verificando archivos sensibles..."
if [ -f "backend/.env" ]; then
    echo "⚠️  ADVERTENCIA: backend/.env existe (no se subirá por .gitignore)"
fi
if [ -f "frontend/.env" ]; then
    echo "⚠️  ADVERTENCIA: frontend/.env existe (no se subirá por .gitignore)"
fi
if [ -f "backend/db.sqlite3" ]; then
    echo "⚠️  ADVERTENCIA: backend/db.sqlite3 existe (no se subirá por .gitignore)"
fi

echo ""
echo "✅ Verificación completada"
echo ""

# Mostrar estado de git
echo "📋 Estado actual del repositorio:"
echo ""
git status --short

echo ""
echo "📝 Archivos que se agregarán:"
echo ""
echo "Archivos nuevos:"
git status --short | grep "^??" | sed 's/^?? /  + /' || echo "  (ninguno)"

echo ""
echo "Archivos modificados:"
git status --short | grep "^ M" | sed 's/^ M /  ~ /' || echo "  (ninguno)"

echo ""
read -p "¿Deseas agregar estos archivos al repositorio? (s/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo ""
    echo "📦 Agregando archivos..."
    
    # Agregar archivos nuevos
    git add backend/gunicorn_config.py
    git add backend/.env.example
    git add frontend/.env.example
    git add nginx.conf.example
    git add admincusc.service.example
    git add deploy.sh
    git add DIGITAL_OCEAN_DEPLOY.md
    git add PREPARAR_DEPLOY.md
    git add backend/start_server.sh
    git add START_FRONTEND.sh
    git add backend/validate_setup.py
    
    # Agregar archivos modificados
    git add backend/config/settings.py
    git add backend/requirements.txt
    git add frontend/src/services/api.ts
    git add frontend/src/components/PaymentList.tsx
    git add frontend/src/components/PendingTransfers.tsx
    
    echo "✅ Archivos agregados"
    echo ""
    echo "📋 Estado después de agregar:"
    git status --short
    
    echo ""
    echo "💡 Próximo paso:"
    echo "   git commit -m 'Preparar proyecto para despliegue en Digital Ocean'"
    echo "   git push origin main"
else
    echo "❌ Operación cancelada"
    exit 1
fi
