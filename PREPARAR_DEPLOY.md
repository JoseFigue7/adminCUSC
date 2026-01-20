# Preparación para Despliegue en Digital Ocean

## Archivos a Agregar al Repositorio

### ✅ Archivos Nuevos (Agregar al Git)

1. **Configuración de Producción:**
   - `backend/gunicorn_config.py` - Configuración de Gunicorn
   - `backend/.env.example` - Plantilla de variables de entorno
   - `frontend/.env.example` - Plantilla de variables de entorno para frontend
   - `nginx.conf.example` - Configuración de Nginx
   - `admincusc.service.example` - Servicio systemd para Gunicorn
   - `deploy.sh` - Script de despliegue automatizado
   - `DIGITAL_OCEAN_DEPLOY.md` - Guía completa de despliegue

2. **Scripts de Desarrollo:**
   - `backend/start_server.sh` - Script para iniciar backend localmente
   - `START_FRONTEND.sh` - Script para iniciar frontend
   - `backend/validate_setup.py` - Script de validación

### ✅ Archivos Modificados (Actualizar en Git)

1. **Backend:**
   - `backend/config/settings.py` - Configuración actualizada (CORS, WhiteNoise)
   - `backend/requirements.txt` - Agregado gunicorn y whitenoise

2. **Frontend:**
   - `frontend/src/services/api.ts` - URL actualizada a puerto 8004
   - `frontend/src/components/PaymentList.tsx` - URL actualizada
   - `frontend/src/components/PendingTransfers.tsx` - URL actualizada

### ❌ Archivos que NO deben subirse (ya están en .gitignore)

- `backend/.env` - Variables de entorno locales
- `frontend/.env` - Variables de entorno locales
- `backend/db.sqlite3` - Base de datos local
- `backend/venv/` - Entorno virtual
- `frontend/node_modules/` - Dependencias de Node
- `frontend/build/` - Build de producción

## Comandos para Preparar el Repositorio

```bash
# 1. Agregar archivos nuevos
git add backend/gunicorn_config.py
git add backend/.env.example
git add frontend/.env.example
git add nginx.conf.example
git add admincusc.service.example
git add deploy.sh
git add DIGITAL_OCEAN_DEPLOY.md
git add backend/start_server.sh
git add START_FRONTEND.sh
git add backend/validate_setup.py
git add PREPARAR_DEPLOY.md

# 2. Agregar archivos modificados
git add backend/config/settings.py
git add backend/requirements.txt
git add frontend/src/services/api.ts
git add frontend/src/components/PaymentList.tsx
git add frontend/src/components/PendingTransfers.tsx

# 3. Verificar que NO se agreguen archivos sensibles
git status

# 4. Hacer commit
git commit -m "Preparar proyecto para despliegue en Digital Ocean

- Agregar configuración de Gunicorn y Nginx
- Agregar scripts de despliegue
- Actualizar URLs del frontend
- Agregar documentación de despliegue
- Configurar CORS y WhiteNoise para producción"

# 5. Push al repositorio
git push origin main
```

## Verificación Pre-Despliegue

Antes de hacer push, verificar:

1. ✅ No hay archivos `.env` con información sensible
2. ✅ No hay `db.sqlite3` con datos de producción
3. ✅ Los archivos `.env.example` no contienen valores reales
4. ✅ No hay credenciales hardcodeadas en el código
5. ✅ Los scripts tienen permisos de ejecución

## Información Necesaria para el Despliegue

Cuando tengas la IP del servidor de Digital Ocean, necesitarás:

1. **IP del Droplet:** `XXX.XXX.XXX.XXX`
2. **Dominio (opcional):** `tu-dominio.com`
3. **Credenciales de MySQL:** (si usas MySQL en lugar de SQLite)
4. **Claves de Stripe:** (si vas a usar pagos con tarjeta)

## Próximos Pasos

1. Ejecutar los comandos de git arriba
2. Hacer push al repositorio
3. Proporcionar la IP del servidor
4. Seguir la guía en `DIGITAL_OCEAN_DEPLOY.md`
