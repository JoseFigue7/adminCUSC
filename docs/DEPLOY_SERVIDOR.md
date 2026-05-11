# Despliegue en el servidor

## Build del frontend con poca RAM

Si `npm run build` falla con **"JavaScript heap out of memory"**, limita la memoria de Node o compila en tu máquina:

**En el servidor (dar más memoria a Node):**
```bash
cd /var/www/admincusc/frontend
export NODE_OPTIONS=--max-old-space-size=4096
npm run build
```

Si sigue fallando, **compila en tu Mac** y sube el build:
```bash
# En tu Mac
cd frontend && npm run build
# Subir solo la carpeta build (por rsync o comprimir y subir)
rsync -avz build/ usuario@146.190.37.214:/var/www/admincusc/frontend/build/
```

## Collectstatic

Después del build del frontend:
```bash
cd /var/www/admincusc/backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput
systemctl restart admincusc
```

Los avisos de "Found another file with the destination path..." se pueden ignorar; se usa la primera ruta encontrada.
