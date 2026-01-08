# AdminCUSC - Sistema de Gestión Estudiantil Administrativo

Sistema completo para la gestión administrativa de estudiantes, incluyendo inscripciones, pagos, seguimiento académico, y gestión de tesis.

## Stack Tecnológico

- **Frontend**: React 18 + TypeScript
- **Backend**: Django 4.2 + Django REST Framework
- **Base de Datos**: MySQL (SQLite para desarrollo)

## Estructura del Proyecto

```
adminCUSC/
├── backend/          # API Django
│   ├── config/      # Configuración del proyecto
│   ├── students/    # App de estudiantes
│   ├── academics/   # App académica (carreras, cursos, pensums)
│   ├── payments/    # App de pagos y becas
│   └── documents/   # App de documentos
└── frontend/         # Aplicación Angular
```

## Características Principales

### Gestión de Estudiantes
- Inscripción de estudiantes con datos personales completos
- Generación automática de carnet (formato: 3 dígitos carrera + 2 dígitos año + 4 dígitos único)
- Gestión de documentos requeridos:
  - Certificado de bachillerato (original + 2 copias)
  - Acta de nacimiento (original + 2 copias)
  - CURP
  - Certificado médico
  - Fotografías (1 digital + 2 físicas)
  - Comprobante de domicilio

### Gestión Académica
- 6 carreras disponibles con pensums completos
- Matrícula de estudiantes en cursos
- Registro de notas finales por curso
- Seguimiento de progreso académico (cursos aprobados/total)
- Cierre de pensum automático
- Gestión de tesis con estados:
  - Solicitud de asesor
  - Revisión de tema
  - Aprobación de tema
  - Revisiones (primera, segunda, tercera)
  - Aprobación final

### Gestión de Pagos
- Tres métodos de pago:
  - **Transferencia**: Con carga de comprobante y validación
  - **Tarjeta**: Integrado en plataforma
  - **Efectivo**: Registrado por administrador con número de recibo
- Control de estudiantes al día y pendientes
- Reportes de pagos pendientes

### Sistema de Becas
- Beca completa y media beca
- Límite de becados por facultad
- Control automático de límites

## Instalación

### Backend (Django)

1. Navegar a la carpeta backend:
```bash
cd backend
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar base de datos MySQL:
   - Crear base de datos: `admincusc_db`
   - Copiar `.env.example` a `.env` y configurar credenciales

5. Ejecutar migraciones:
```bash
python manage.py migrate
```

6. Crear superusuario:
```bash
python manage.py createsuperuser
```

7. Cargar datos iniciales (carreras y pensums):
```bash
python manage.py seed_careers
```

8. Ejecutar servidor:
```bash
python manage.py runserver
```

### Frontend (React)

1. Navegar a la carpeta frontend:
```bash
cd frontend
```

2. Instalar dependencias (ya están instaladas con create-react-app):
```bash
npm install
```

3. Ejecutar servidor de desarrollo:
```bash
npm start
```

El frontend estará disponible en `http://localhost:3000`

## API Endpoints

### Estudiantes
- `GET /api/students/students/` - Listar estudiantes
- `POST /api/students/students/` - Crear estudiante
- `GET /api/students/students/{id}/` - Obtener estudiante
- `GET /api/students/students/{id}/progress/` - Progreso académico

### Académico
- `GET /api/academics/careers/` - Listar carreras
- `GET /api/academics/careers/{id}/pensum/` - Obtener pensum
- `GET /api/academics/enrollments/` - Listar matrículas
- `PATCH /api/academics/enrollments/{id}/update_grade/` - Actualizar nota

### Pagos
- `GET /api/payments/payments/` - Listar pagos
- `POST /api/payments/payments/` - Crear pago
- `GET /api/payments/payments/student_status/?student_id={id}` - Estado de pagos
- `PATCH /api/payments/payments/{id}/approve/` - Aprobar pago
- `PATCH /api/payments/payments/{id}/reject/` - Rechazar pago

## Carreras Disponibles

1. Licenciatura en Pedagogía (Código: 101)
2. Licenciatura en Criminología y Criminalística (Código: 102)
3. Licenciatura en Administración de Empresas y Negocios (Código: 103)
4. Licenciatura en Derecho (Código: 104)
5. Licenciatura en Mercadotecnia Digital y Publicidad (Código: 105)
6. Licenciatura en Contaduría Pública y Finanzas (Código: 106)

## Próximas Mejoras

- Integración con Moodle
- Generación automática de contratos PDF
- Dashboard con estadísticas
- Notificaciones por email
- Sistema de reportes avanzado

## Licencia

Este proyecto es privado y de uso exclusivo para CUSC.

