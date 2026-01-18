# Lógica del Programa - AdminCUSC

## Índice
1. [Arquitectura General](#arquitectura-general)
2. [Modelos Principales y Relaciones](#modelos-principales-y-relaciones)
3. [Lógica de Negocio Clave](#lógica-de-negocio-clave)
4. [Flujos Principales](#flujos-principales)
5. [Reglas de Negocio](#reglas-de-negocio)
6. [Integraciones](#integraciones)
7. [Sistema de Permisos](#sistema-de-permisos)

---

## Arquitectura General

### Stack Tecnológico
- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: React 18 + TypeScript
- **Base de Datos**: SQLite (desarrollo) / MySQL (producción)
- **Autenticación**: JWT (JSON Web Tokens) con `rest_framework_simplejwt`
- **Pagos**: Integración con Stripe para pagos con tarjeta

### Estructura de Aplicaciones Django

El sistema está dividido en las siguientes aplicaciones Django:

1. **`users`**: Gestión de usuarios y roles
2. **`students`**: Gestión de estudiantes e inscripciones
3. **`academics`**: Gestión académica (carreras, cursos, pensums, tesis)
4. **`payments`**: Gestión de pagos y becas
5. **`documents`**: Gestión de documentos
6. **`certificates`**: Gestión de certificados
7. **`reports`**: Generación de reportes

---

## Modelos Principales y Relaciones

### 1. Estudiantes (`students` app)

#### `Student` - Modelo Principal de Estudiante
- **Campos clave**:
  - `carnet`: Número único generado automáticamente (formato: `CCCIAA####`)
  - `first_name`, `first_last_name`, `second_last_name`: Nombre completo según SEP
  - `curp`: Clave única de 18 caracteres (validación con regex)
  - `email`: Correo único
  - `phone`: Teléfono mexicano validado (formato: `+52XXXXXXXXXX`)
  - `career`: ForeignKey a `Career`
  - `has_scholarship`, `scholarship_type`: Información de beca
  - `pensum_closed`: Indica si completó el pensum
  - `thesis_started`: Indica si inició tesis

#### `Enrollment` - Inscripciones de Estudiantes
- Permite múltiples inscripciones por estudiante (una por año/carrera)
- **Campos SEP requeridos**:
  - `enrollment_status`: INSCRIPCION o REINSCRIPCION
  - `school_year`: Año del ciclo escolar
  - `institutional_id`: Matrícula institucional (usa carnet si no se especifica)
  - `cct`: Clave del Centro de Trabajo (se toma de la carrera si no se especifica)
  - `rvoe_agreement_number` y `rvoe_agreement_date`: Datos del RVOE
- **Estados administrativos**: PENDIENTE, EN_REVISION, APROBADA, RECHAZADA
- **Gestión de contratos**:
  - `contract_generated`: Indica si se generó el PDF
  - `contract_file`: Archivo PDF generado
  - `contract_scanned`: Contrato escaneado subido por el estudiante
  - `is_officially_enrolled`: True cuando el contrato escaneado está aprobado

#### `StudentDocument` - Documentos Requeridos
- Tipos de documentos:
  - Certificado de Bachillerato (original + 2 copias)
  - Acta de Nacimiento (original + 2 copias)
  - CURP, Certificado Médico
  - Fotografías (1 digital + 2 físicas)
  - Comprobante de Domicilio
- Estados: PENDIENTE, RECIBIDO, APROBADO, RECHAZADO

### 2. Académico (`academics` app)

#### `Career` - Carreras
- **Campos clave**:
  - `code`: Código único de 3 dígitos (101-106)
  - `name`: Nombre de la carrera
  - `total_credits`: Total de créditos del pensum
  - `max_scholarships_full` y `max_scholarships_half`: Límites de becas
  - **Campos SEP**: `institution_key`, `career_key`, `cct`, `rvoe_agreement_number`, `rvoe_agreement_date`

#### `Cuatrimestre` - Cuatrimestres por Carrera
- Relación: `Career` → `Cuatrimestre` (1:N)
- `number`: Número del cuatrimestre (1-9)
- Cada carrera tiene 9 cuatrimestres

#### `Course` - Cursos
- Relación: `Cuatrimestre` → `Course` (1:N)
- **Campos clave**:
  - `code`: Código del curso
  - `name`: Nombre del curso
  - `credits`: Créditos del curso
  - `cost`: Costo de la colegiatura para este curso
  - `is_required`: Si es obligatorio
  - `prerequisite`: Curso prerequisito (opcional)
- **Método `get_academic_period()`**: Determina el período académico (1, 2 o 3) basado en el número de cuatrimestre:
  - Período 1 (Enero-Abril): Cuatrimestres 1, 4, 7
  - Período 2 (Mayo-Agosto): Cuatrimestres 2, 5, 8
  - Período 3 (Septiembre-Diciembre): Cuatrimestres 3, 6, 9

#### `CourseSchedule` - Horarios de Cursos
- Relación: `Course` → `CourseSchedule` (1:N)
- Define días y horarios de cada curso
- Método `overlaps_with()`: Verifica si hay traslape de horarios

#### `CuatrimestreEnrollment` - Inscripción a Cuatrimestre
- Relación: `Student` → `CuatrimestreEnrollment` (1:N)
- **Estados**:
  - `PENDIENTE_PAGO`: Esperando pago
  - `PENDIENTE_CONFIRMACION`: Pagado, esperando asignación de cursos
  - `EN_CURSO`: Activo
  - `FINALIZADO`: Completado
  - `CANCELADO`: Cancelado
- **Regla importante**: Un estudiante solo puede tener UNA inscripción `EN_CURSO` a la vez
- Método `calculate_total_tuition()`: Calcula el costo total basado en los cursos asignados

#### `CourseEnrollment` - Matrícula en Cursos
- Relación: `Student` → `CourseEnrollment` (1:N)
- Relación: `Course` → `CourseEnrollment` (1:N)
- Relación opcional: `CuatrimestreEnrollment` → `CourseEnrollment` (1:N)
- **Estados**: MATRICULADO, EN_CURSO, APROBADO, REPROBADO, RETIRADO
- **Reglas importantes**:
  - No se puede inscribir a un curso ya aprobado
  - Se puede reasignar cursos reprobados
  - Si hay `cuatrimestre_enrollment`, solo una inscripción por cuatrimestre
- **Actualización automática**: Si `final_grade >= 70`, estado cambia a APROBADO; si < 70, a REPROBADO

#### `Thesis` - Tesis
- Relación: `Student` → `Thesis` (1:1)
- **Estados**:
  - NO_INICIADA → SOLICITUD_ASESOR → REVISION_TEMA → APROBACION_TEMA
  - → PRIMERA_REVISION → SEGUNDA_REVISION → TERCERA_REVISION → APROBADA

### 3. Pagos (`payments` app)

#### `PaymentType` - Tipos de Pago
- Define los tipos de pago disponibles (Inscripción, Colegiatura, etc.)
- **Configuración de mora**:
  - `has_penalty`: Si aplica mora
  - `penalty_type`: FIXED, PERCENTAGE, DAILY_FIXED, DAILY_PERCENTAGE
  - `penalty_amount` o `penalty_percentage`: Monto o porcentaje de mora
  - `penalty_max_amount`: Límite máximo de mora
  - `penalty_days_offset`: Días de gracia antes de aplicar mora
- Método `calculate_penalty()`: Calcula la mora basada en la configuración

#### `Payment` - Pagos
- Relación: `Student` → `Payment` (1:N)
- Relación opcional: `CuatrimestreEnrollment` → `Payment` (1:N)
- **Métodos de pago**: TRANSFERENCIA, TARJETA, EFECTIVO
- **Estados**: PENDIENTE, EN_REVISION, APROBADO, RECHAZADO
- **Campos de mora**:
  - `base_amount`: Monto base (sin mora)
  - `penalty_amount`: Monto de mora aplicado
  - `amount`: Monto total (base + mora)
- **Lógica automática en `save()`**:
  - **Transferencias**: Siempre quedan PENDIENTE al crear (requieren aprobación manual)
  - **Efectivo y Tarjeta**: Se aprueban automáticamente al crear
  - **Cálculo de mora**: Se calcula automáticamente si hay `payment_type`, `due_date` y `has_penalty`
- **Trazabilidad**: `created_by`, `approved_by`, `approved_at`

#### `Scholarship` - Becas
- Relación: `Student` → `Scholarship` (1:1)
- Tipos: COMPLETA (100%), MEDIA (50%)
- Estados: ACTIVA, SUSPENDIDA, FINALIZADA

#### `PaymentConfiguration` - Configuración de Pagos por Carrera
- Relación: `Career` → `PaymentConfiguration` (1:1)
- Define `monthly_amount` y `enrollment_fee` por carrera

#### `AcademicPeriodConfig` - Configuración de Períodos Académicos
- Define el porcentaje de mora por período académico (1, 2 o 3)

#### `MonthlyPaymentDueDate` - Fechas Límite de Pago Mensual
- Define el día límite de pago para cada mes (ej: día 10 de cada mes)

### 4. Usuarios (`users` app)

#### `Role` - Roles de Usuario
- Tipos: SUPER_ADMIN, ADMIN, SECRETARY, ACADEMIC_COORDINATOR, FINANCIAL, VIEWER
- Permisos granulares:
  - `can_manage_students`, `can_manage_payments`, `can_manage_academics`
  - `can_manage_scholarships`, `can_manage_thesis`, `can_view_reports`
  - `can_manage_users`, `can_manage_settings`

#### `User` - Usuarios
- Extiende `AbstractUser` de Django
- Relación: `Role` → `User` (1:N)
- Método `has_permission()`: Verifica permisos basados en el rol

---

## Lógica de Negocio Clave

### 1. Generación Automática de Carnet

**Función**: `generate_carnet_number(career_code, year)` en `students/utils.py`

**Formato**: `CCCIAA####`
- `CCC`: Código de carrera (3 dígitos, ej: 101)
- `II`: Año de inscripción (2 dígitos, ej: 26 para 2026)
- `####`: Número secuencial (4 dígitos, ej: 0001)

**Lógica**:
1. Se genera el prefijo `CCCII` basado en carrera y año
2. Se busca el último estudiante con ese prefijo
3. Se incrementa el número secuencial
4. Se verifica unicidad con transacciones atómicas para prevenir race conditions
5. Si hay conflictos, se reintenta hasta 10 veces
6. Fallback: usa timestamp si falla después de varios intentos

**Ejemplo**: Estudiante de Pedagogía (101) en 2026 → `101260001`

### 2. Generación Automática de Contratos

**Función**: `generate_contract(student, enrollment)` en `students/utils.py`

**Proceso**:
1. Obtiene datos del estudiante y la inscripción
2. Carga template HTML (`contracts/student_contract.html`)
3. Genera PDF usando WeasyPrint
4. Guarda el archivo en `media/contracts/`
5. Actualiza `enrollment.contract_generated = True` y `enrollment.contract_file`

**Flujo completo**:
- Al crear estudiante → se crea inscripción → se genera contrato automáticamente

### 3. Cálculo de Mora en Pagos

**Lógica en `Payment.save()`**:

1. Si el pago tiene `payment_type` con `has_penalty = True` y `due_date`:
   - Se establece `base_amount` (monto sin mora)
   - Se llama a `payment_type.calculate_penalty()`
   - Se calcula `penalty_amount`
   - Se actualiza `amount = base_amount + penalty_amount`

2. **Tipos de mora**:
   - **FIXED**: Monto fijo único
   - **PERCENTAGE**: Porcentaje único sobre el monto base
   - **DAILY_FIXED**: Monto fijo por cada día de retraso
   - **DAILY_PERCENTAGE**: Porcentaje diario sobre el monto base

3. **Días de gracia**: Se respetan `penalty_days_offset` antes de aplicar mora

4. **Límite máximo**: Si existe `penalty_max_amount`, se aplica como tope

### 4. Aprobación Automática de Pagos

**Lógica en `Payment.save()`**:

- **Efectivo y Tarjeta**: Se aprueban automáticamente al crear
  - `status = 'APROBADO'`
  - `approved_by = created_by`
  - `approved_at = timezone.now()`

- **Transferencia**: Siempre queda `PENDIENTE` al crear
  - Requiere aprobación manual por un administrador
  - Validación: no se puede crear una transferencia ya aprobada

### 5. Períodos Académicos

**Mapeo de Cuatrimestres a Períodos**:
- **Período 1** (Enero-Abril): Cuatrimestres 1, 4, 7
- **Período 2** (Mayo-Agosto): Cuatrimestres 2, 5, 8
- **Período 3** (Septiembre-Diciembre): Cuatrimestres 3, 6, 9

**Uso**: Se usa para calcular mora y configurar fechas límite de pago por período.

### 6. Cierre de Pensum

**Lógica**:
- Cuando un estudiante aprueba todos los cursos requeridos de su carrera:
  - `student.pensum_closed = True`
  - Puede iniciar el proceso de tesis

### 7. Control de Becas

**Límites por Carrera**:
- Cada carrera tiene `max_scholarships_full` y `max_scholarships_half`
- Al asignar una beca, se verifica que no se excedan los límites
- Un estudiante solo puede tener una beca activa a la vez

---

## Flujos Principales

### Flujo 1: Inscripción de Nuevo Estudiante

1. **Crear Estudiante** (`POST /api/students/students/`)
   - Se validan datos (CURP, teléfono, email único)
   - Se asigna carrera
   - Se genera carnet automáticamente
   - Se crea inscripción (`Enrollment`) automáticamente
   - Se genera contrato PDF automáticamente
   - Se crean registros de documentos requeridos (`StudentDocument`)

2. **Subir Documentos**
   - El estudiante sube documentos requeridos
   - Administrador revisa y aprueba/rechaza

3. **Aprobar Inscripción**
   - Administrador cambia `enrollment.status = 'APROBADA'`
   - Se puede subir contrato escaneado
   - Cuando se aprueba el contrato escaneado: `is_officially_enrolled = True`

### Flujo 2: Inscripción a Cuatrimestre y Cursos

1. **Crear Inscripción a Cuatrimestre** (`POST /api/academics/cuatrimestre-enrollments/`)
   - Estado inicial: `PENDIENTE_PAGO`
   - Se valida que el estudiante no tenga otra inscripción `EN_CURSO`

2. **Realizar Pago**
   - Se crea `Payment` con `cuatrimestre_enrollment` relacionado
   - Si es efectivo/tarjeta: se aprueba automáticamente
   - Si es transferencia: queda pendiente de aprobación

3. **Aprobar Pago** (si es transferencia)
   - Administrador aprueba el pago
   - Estado de inscripción cambia a `PENDIENTE_CONFIRMACION`

4. **Asignar Cursos**
   - Se crean `CourseEnrollment` relacionados con `cuatrimestre_enrollment`
   - Se valida que los cursos pertenezcan al cuatrimestre
   - Se valida que no se inscriba a cursos ya aprobados

5. **Confirmar Asignación**
   - Estado de inscripción cambia a `EN_CURSO`
   - El estudiante puede ver sus cursos y horarios

### Flujo 3: Registro de Notas

1. **Actualizar Nota** (`PATCH /api/academics/enrollments/{id}/update_grade/`)
   - Se actualiza `final_grade` en `CourseEnrollment`
   - Automáticamente se actualiza `status`:
     - Si `final_grade >= 70`: `status = 'APROBADO'`
     - Si `final_grade < 70`: `status = 'REPROBADO'`

2. **Verificar Cierre de Pensum**
   - Si todos los cursos requeridos están aprobados: `pensum_closed = True`

### Flujo 4: Proceso de Tesis

1. **Iniciar Tesis**
   - Se crea `Thesis` para el estudiante
   - Estado: `NO_INICIADA`

2. **Solicitar Asesor**
   - Estado: `SOLICITUD_ASESOR`

3. **Revisión y Aprobación de Tema**
   - Estados: `REVISION_TEMA` → `APROBACION_TEMA`

4. **Revisiones**
   - Estados: `PRIMERA_REVISION` → `SEGUNDA_REVISION` → `TERCERA_REVISION`

5. **Aprobación Final**
   - Estado: `APROBADA`
   - Se registra `defense_date`

### Flujo 5: Pago con Stripe

1. **Crear Payment Intent** (`POST /api/payments/stripe/create-intent/`)
   - Se llama a `StripePaymentService.create_payment_intent()`
   - Se convierte monto a centavos (Stripe usa la unidad más pequeña)
   - Se retorna `client_secret` para el frontend

2. **Procesar Pago en Frontend**
   - Se usa Stripe Elements para capturar datos de tarjeta
   - Se confirma el pago con `client_secret`

3. **Webhook de Stripe** (opcional)
   - Stripe notifica cuando el pago se completa
   - Se actualiza el estado del pago en la base de datos

4. **Confirmar Pago**
   - Se llama a `StripePaymentService.confirm_payment()`
   - Se actualiza `Payment` con `transaction_id` y `card_last_four`
   - Estado: `APROBADO` automáticamente

---

## Reglas de Negocio

### Estudiantes

1. **Carnet único**: Cada estudiante tiene un carnet único generado automáticamente
2. **CURP único**: No puede haber dos estudiantes con el mismo CURP
3. **Email único**: No puede haber dos estudiantes con el mismo email
4. **Teléfono mexicano**: Debe comenzar con `+52` seguido de 10 dígitos
5. **Carrera requerida**: Todo estudiante debe tener una carrera asignada

### Inscripciones

1. **Una inscripción por año/carrera**: Un estudiante solo puede tener una inscripción por año escolar y carrera
2. **Carrera consistente**: La carrera de la inscripción debe coincidir con la del estudiante
3. **Campos automáticos**: Si no se especifican, se toman de la carrera o del estudiante:
   - `institutional_id` → usa `student.carnet`
   - `cct`, `rvoe_agreement_number`, `rvoe_agreement_date` → se toman de `career`
   - `school_year` → usa año actual si no se especifica

### Cursos

1. **No re-inscripción a cursos aprobados**: Un estudiante no puede inscribirse a un curso que ya aprobó
2. **Re-asignación de cursos reprobados**: Se puede reasignar cursos que fueron reprobados
3. **Cursos del cuatrimestre**: Los cursos asignados deben pertenecer al cuatrimestre de la inscripción
4. **Carrera consistente**: Los cursos deben pertenecer a la carrera del estudiante

### Inscripciones a Cuatrimestres

1. **Una inscripción EN_CURSO a la vez**: Un estudiante solo puede tener una inscripción `EN_CURSO` simultáneamente
2. **Carrera consistente**: El cuatrimestre debe pertenecer a la carrera del estudiante

### Pagos

1. **Aprobación automática**: Efectivo y tarjeta se aprueban automáticamente; transferencias requieren aprobación manual
2. **Cálculo de mora**: Se calcula automáticamente si hay `payment_type`, `due_date` y `has_penalty`
3. **Trazabilidad**: Se registra quién creó y quién aprobó cada pago

### Becas

1. **Límites por carrera**: No se pueden exceder los límites de becas completas y medias becas por carrera
2. **Una beca activa**: Un estudiante solo puede tener una beca activa a la vez

### Tesis

1. **Una tesis por estudiante**: Relación 1:1 entre `Student` y `Thesis`
2. **Pensum cerrado**: Idealmente, el estudiante debe tener `pensum_closed = True` antes de iniciar tesis

---

## Integraciones

### Stripe

**Servicio**: `StripePaymentService` en `payments/stripe_service.py`

**Funcionalidades**:
- `create_payment_intent()`: Crea un Payment Intent en Stripe
- `confirm_payment()`: Confirma un pago
- `retrieve_payment_intent()`: Obtiene información de un pago
- `get_card_last_four()`: Obtiene los últimos 4 dígitos de la tarjeta

**Configuración**:
- `STRIPE_SECRET_KEY`: Clave secreta de Stripe
- `STRIPE_PUBLISHABLE_KEY`: Clave pública (para frontend)
- `STRIPE_WEBHOOK_SECRET`: Secreto para validar webhooks

**Flujo**:
1. Backend crea Payment Intent y retorna `client_secret`
2. Frontend usa Stripe Elements para capturar datos de tarjeta
3. Frontend confirma el pago con `client_secret`
4. Backend actualiza el registro de `Payment` con la información de Stripe

### WeasyPrint

**Uso**: Generación de contratos PDF

**Proceso**:
1. Se carga template HTML (`contracts/student_contract.html`)
2. Se renderiza con datos del estudiante e inscripción
3. Se genera PDF usando `weasyprint.HTML.write_pdf()`
4. Se guarda en `media/contracts/`

---

## Sistema de Permisos

### Roles Predefinidos

1. **SUPER_ADMIN**: Tiene todos los permisos
2. **ADMIN**: Gestión completa del sistema
3. **SECRETARY**: Gestión de estudiantes e inscripciones
4. **ACADEMIC_COORDINATOR**: Gestión académica y tesis
5. **FINANCIAL**: Gestión de pagos y becas
6. **VIEWER**: Solo consulta (sin permisos de edición)

### Permisos Granulares

Cada rol tiene permisos específicos:
- `can_manage_students`: Crear/editar/eliminar estudiantes
- `can_manage_payments`: Gestionar pagos
- `can_manage_academics`: Gestionar cursos, inscripciones, notas
- `can_manage_scholarships`: Asignar/suspender becas
- `can_manage_thesis`: Gestionar tesis
- `can_view_reports`: Ver reportes
- `can_manage_users`: Gestionar usuarios y roles
- `can_manage_settings`: Configurar sistema

### Implementación

- **Backend**: Permisos verificados en las vistas con `HasPermission` custom permission class
- **Frontend**: Los permisos se pueden verificar en el contexto de autenticación

---

## Validaciones Importantes

### Validación de CURP
- Formato: `^[A-Z]{4}\d{6}[HM][A-Z]{5}[0-9A-Z]\d$`
- 18 caracteres: 4 letras + 6 dígitos + H/M + 5 letras + 1 alfanumérico + 1 dígito

### Validación de Teléfono Mexicano
- Debe comenzar con `+52`
- Seguido de exactamente 10 dígitos
- El primer dígito del código de área (LADA) debe ser entre 2 y 9

### Validación de Campos SEP
- `institution_key`, `career_key`, `cct`: Exactamente 10 caracteres
- `rvoe_agreement_date`: Formato `aaaammdd` (8 dígitos)

---

## Consideraciones de Rendimiento

1. **Transacciones atómicas**: Se usan para prevenir race conditions en la generación de carnets
2. **Índices de base de datos**: Se definen en modelos clave para optimizar consultas
3. **Select related**: Se usan en vistas para evitar N+1 queries
4. **Paginación**: Todos los endpoints de listado tienen paginación (20 items por página)

---

## Notas Finales

- El sistema está diseñado para cumplir con los requisitos de la SEP (Secretaría de Educación Pública) de México
- Los campos SEP son opcionales temporalmente para facilitar la migración, pero deberían completarse para reportes oficiales
- El sistema soporta múltiples inscripciones por estudiante (una por año/carrera)
- La lógica de mora es flexible y configurable por tipo de pago
- El sistema de permisos es granular y extensible
