# Guía de Instalación - AdminCUSC

## Requisitos Previos

- Python 3.9 o superior
- Node.js 18 o superior
- MySQL 8.0 o superior
- pip (gestor de paquetes de Python)
- npm (gestor de paquetes de Node.js)

## Instalación del Backend (Django)

### 1. Configurar entorno virtual

```bash
cd backend
python -m venv venv

# En Linux/Mac:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

**Nota:** El proyecto usa `PyMySQL` en lugar de `mysqlclient` para evitar problemas de compilación. PyMySQL es una implementación pura de Python que no requiere librerías del sistema.

### 3. Configurar base de datos MySQL

1. Crear base de datos:
```sql
CREATE DATABASE admincusc_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. Crear usuario (opcional):
```sql
CREATE USER 'admincusc_user'@'localhost' IDENTIFIED BY 'tu_password';
GRANT ALL PRIVILEGES ON admincusc_db.* TO 'admincusc_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Configurar variables de entorno

Copiar el archivo `.env.example` a `.env`:
```bash
cp .env.example .env
```

Editar `.env` con tus credenciales:
```
SECRET_KEY=tu-secret-key-aqui
DEBUG=True
DB_NAME=admincusc_db
DB_USER=root
DB_PASSWORD=tu-password-mysql
DB_HOST=localhost
DB_PORT=3306
```

### 5. Ejecutar migraciones

```bash
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Cargar datos iniciales (carreras y pensums)

```bash
python manage.py seed_careers
```

Este comando cargará todas las carreras y sus respectivos pensums en la base de datos.

### 8. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

El backend estará disponible en `http://localhost:8000`
La documentación de la API (Swagger) estará en `http://localhost:8000/swagger/`

## Instalación del Frontend (Angular)

### 1. Instalar dependencias

```bash
cd frontend
npm install
```

### 2. Configurar URL del backend

Si el backend está en una URL diferente a `http://localhost:8000`, editar:
`src/app/services/api.service.ts` y cambiar la constante `API_URL`.

### 3. Ejecutar servidor de desarrollo

```bash
npm start
```

El frontend estará disponible en `http://localhost:4200`

## Verificación de Instalación

### Backend

1. Acceder a `http://localhost:8000/admin/` y hacer login con el superusuario creado
2. Verificar que las carreras estén cargadas en la sección "Academics > Careers"
3. Acceder a `http://localhost:8000/swagger/` para ver la documentación de la API

### Frontend

1. Abrir `http://localhost:4200`
2. Verificar que la página carga correctamente
3. Intentar crear un estudiante de prueba

## Solución de Problemas

### Error al instalar dependencias

Si tienes problemas, asegúrate de estar usando el entorno virtual:
```bash
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

El proyecto usa `PyMySQL` que no requiere compilación, por lo que debería instalarse sin problemas.

### Error de conexión a MySQL

- Verificar que MySQL esté corriendo
- Verificar credenciales en `.env`
- Verificar que la base de datos existe
- Verificar permisos del usuario

### Error CORS en el frontend

Verificar que `CORS_ALLOWED_ORIGINS` en `backend/config/settings.py` incluya `http://localhost:4200`

### Error al generar contratos PDF

Instalar dependencias del sistema para WeasyPrint:

**Linux:**
```bash
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0
```

**macOS:**
```bash
brew install pango
```

## Estructura de Archivos Importantes

```
backend/
├── config/
│   └── settings.py          # Configuración principal
├── students/
│   ├── models.py            # Modelos de estudiantes
│   ├── views.py             # Vistas/API de estudiantes
│   └── utils.py             # Utilidades (generación de carnet, contratos)
├── academics/
│   ├── models.py            # Modelos académicos
│   └── management/commands/
│       └── seed_careers.py   # Comando para cargar carreras
└── requirements.txt          # Dependencias Python

frontend/
├── src/
│   ├── app/
│   │   ├── components/      # Componentes Angular
│   │   ├── services/         # Servicios (API)
│   │   └── app.routes.ts     # Rutas de la aplicación
│   └── main.ts              # Punto de entrada
└── package.json             # Dependencias Node.js
```

## Próximos Pasos

1. Configurar producción (usar variables de entorno seguras)
2. Configurar servidor web (Nginx + Gunicorn para Django)
3. Configurar SSL/HTTPS
4. Implementar backups de base de datos
5. Configurar integración con Moodle (si es necesario)

