# Guía de Testing y Datos de Prueba

Este documento explica cómo poblar la base de datos con datos de prueba y cómo probar la funcionalidad de subida de archivos.

## Poblar Base de Datos con Datos de Prueba

### Prerequisitos

1. Asegúrate de que las carreras estén creadas:
```bash
cd backend
source venv/bin/activate
python manage.py seed_careers
```

### Crear Datos de Prueba

El comando `seed_test_data` crea estudiantes completos con:
- Información personal
- Documentos (con archivos de prueba)
- Pagos (con comprobantes de prueba)
- Inscripciones en cursos
- Becas (para algunos estudiantes)
- Tesis (para estudiantes avanzados)

#### Uso básico:
```bash
cd backend
source venv/bin/activate
python manage.py seed_test_data --students 20
```

#### Opciones disponibles:

- `--students N`: Número de estudiantes a crear (default: 20)
- `--clear`: Eliminar todos los datos existentes antes de crear nuevos

#### Ejemplos:

```bash
# Crear 10 estudiantes sin eliminar datos existentes
python manage.py seed_test_data --students 10

# Crear 50 estudiantes eliminando datos previos
python manage.py seed_test_data --students 50 --clear

# Crear 100 estudiantes para pruebas exhaustivas
python manage.py seed_test_data --students 100 --clear
```

### Datos Generados

Para cada estudiante se crea:

1. **Información Personal:**
   - Nombre y apellidos aleatorios
   - Email único
   - Teléfono
   - Fecha de nacimiento (18-30 años)
   - CURP generado
   - Dirección
   - Carnet generado automáticamente

2. **Documentos (80% de probabilidad cada uno):**
   - Certificado de Bachillerato (Original + 2 copias)
   - Acta de Nacimiento (Original + 2 copias)
   - CURP
   - Certificado Médico
   - Fotografías (1 digital + 2 físicas)
   - Comprobante de Domicilio
   - Archivos de prueba (imágenes JPG para fotos, PDFs para documentos)

3. **Pagos:**
   - Pagos para los últimos 6 meses
   - Diferentes métodos: Transferencia, Tarjeta, Efectivo
   - Comprobantes de transferencia (PDFs de prueba)
   - Estados variados: Pendiente, En Revisión, Aprobado

4. **Inscripciones en Cursos:**
   - 30-80% de los cursos de la carrera
   - Estados: Matriculado, En Curso, Aprobado, Reprobado
   - Notas finales para cursos aprobados/reprobados

5. **Becas (25% de estudiantes):**
   - Beca Completa o Media Beca
   - Fechas de inicio y fin
   - Estados: Activa, Suspendida, Finalizada

6. **Tesis (16% de estudiantes):**
   - Títulos variados
   - Asesores asignados
   - Estados progresivos: Revisión de Tema, Aprobación, Revisiones, Aprobada

## Subida de Archivos

### Documentos de Estudiantes

#### Subir archivo a un documento existente:
```bash
POST /api/students/documents/{id}/upload_file/
Content-Type: multipart/form-data

{
  "file": <archivo>
}
```

#### Actualizar estado de documento:
```bash
PATCH /api/students/documents/{id}/update_status/
Content-Type: application/json

{
  "status": "APROBADO",
  "notes": "Documento verificado correctamente"
}
```

### Comprobantes de Pago

#### Subir comprobante de transferencia:
```bash
POST /api/payments/payments/{id}/upload_receipt/
Content-Type: multipart/form-data

{
  "file": <archivo>
}
```

## Estructura de Archivos

Los archivos se guardan en:
- Documentos de estudiantes: `media/student_documents/`
- Comprobantes de pago: `media/payment_receipts/`
- Contratos: `media/contracts/`
- Tesis: `media/thesis/`

## Verificar Datos Creados

### Desde el Admin de Django:
```bash
python manage.py createsuperuser  # Si no tienes usuario admin
python manage.py runserver
# Visitar http://localhost:8000/admin/
```

### Desde la API:
```bash
# Listar estudiantes
curl http://localhost:8000/api/students/students/

# Listar pagos
curl http://localhost:8000/api/payments/payments/

# Listar documentos
curl http://localhost:8000/api/students/documents/
```

## Limpiar Datos de Prueba

Para eliminar todos los datos de prueba:

```bash
python manage.py seed_test_data --students 0 --clear
```

O manualmente desde el shell de Django:
```python
python manage.py shell
>>> from students.models import Student
>>> from payments.models import Payment
>>> Student.objects.all().delete()
>>> Payment.objects.all().delete()
```

## Notas Importantes

1. **Archivos de Prueba**: Los archivos generados son simulados (imágenes simples y PDFs de texto). En producción, estos serían archivos reales subidos por los usuarios.

2. **Rendimiento**: Crear muchos estudiantes puede tomar tiempo. Se recomienda empezar con 20-50 para pruebas iniciales.

3. **Datos Realistas**: Los datos generados son aleatorios pero realistas, con distribuciones que simulan un entorno real (no todos tienen todos los documentos, no todos están al día con pagos, etc.).

4. **Carnets Únicos**: Los carnets se generan automáticamente con el formato: `{código_carrera}{año}{4_dígitos_únicos}`

5. **CURP**: Los CURPs generados son simulados y no son válidos para uso real.







