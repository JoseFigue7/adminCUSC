# Listado de Pruebas QA - AdminCUSC

Sistema de Gestión Estudiantil Administrativo. Este documento lista pruebas de QA para **backend** (API Django) y **frontend** (React).

---

## 1. BACKEND (API Django)

### 1.1 Autenticación y usuarios

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| B-AUTH-01 | Login con credenciales válidas | POST `/api/auth/login/` con `username` y `password` correctos | 200, devuelve `access`, `refresh` y `user` |
| B-AUTH-02 | Login con credenciales inválidas | POST con usuario/contraseña incorrectos | 401, mensaje de error |
| B-AUTH-03 | Login sin password | POST solo con `username` | 400, validación de campos |
| B-AUTH-04 | Refresh token | POST `/api/auth/refresh/` con `refresh` válido | 200, nuevo `access` |
| B-AUTH-05 | Refresh token expirado/inválido | POST con token inválido | 401 |
| B-AUTH-06 | Acceso a endpoint protegido sin token | GET `/api/students/students/` sin header Authorization | 401 |
| B-AUTH-07 | Acceso con token válido | GET con header `Authorization: Bearer <access>` | 200 (según endpoint) |
| B-AUTH-08 | Perfil de usuario | GET `/api/users/profile/` autenticado | 200, datos del usuario |
| B-AUTH-09 | Cambio de contraseña | POST con `old_password` y `new_password` | 200 o 400 si la actual es incorrecta |

### 1.2 Estudiantes

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| B-STU-01 | Listar estudiantes | GET `/api/students/students/` | 200, lista paginada |
| B-STU-02 | Listar con filtros | GET con `search`, `career`, `is_active`, etc. | 200, resultados filtrados |
| B-STU-03 | Crear estudiante | POST con datos válidos (nombre, apellidos, carrera, etc.) | 201, estudiante creado, carnet generado |
| B-STU-04 | Crear sin campos requeridos | POST sin `first_name` o `career` | 400, errores de validación |
| B-STU-05 | Obtener estudiante | GET `/api/students/students/{id}/` | 200, detalle del estudiante |
| B-STU-06 | Obtener inexistente | GET con ID que no existe | 404 |
| B-STU-07 | Actualizar estudiante | PATCH/PUT con datos válidos | 200, datos actualizados |
| B-STU-08 | Progreso académico | GET `/api/students/students/{id}/progress/` | 200, cursos aprobados/total |
| B-STU-09 | Catálogos SEP | GET catálogos (paises, entidades, idiomas, etc.) | 200, listas |

### 1.3 Inscripciones (Enrollments)

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| B-ENR-01 | Listar inscripciones | GET `/api/students/enrollments/` | 200, lista paginada |
| B-ENR-02 | Crear inscripción | POST con `student`, `school_year`, etc. | 201 |
| B-ENR-03 | Actualizar inscripción | PATCH con nuevos datos | 200 |
| B-ENR-04 | Historial de estado | GET historial de cambios de estado | 200 |

### 1.4 Académico (carreras, cursos, matrículas)

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| B-ACA-01 | Listar carreras | GET `/api/academics/careers/` | 200, lista de carreras |
| B-ACA-02 | Obtener pensum | GET `/api/academics/careers/{id}/pensum/` | 200, cursos del pensum |
| B-ACA-03 | Listar cuatrimestres | GET `/api/academics/cuatrimestres/` | 200 |
| B-ACA-04 | Listar cursos | GET `/api/academics/courses/` | 200 |
| B-ACA-05 | Matrícula por cuatrimestre | GET/POST cuatrimestre-enrollments | 200/201 |
| B-ACA-06 | Matrícula de cursos | GET/POST course enrollments | 200/201 |
| B-ACA-07 | Actualizar calificación | PATCH para actualizar nota de curso | 200 |
| B-ACA-08 | Método de graduación | CRUD método de graduación (tesis, etc.) | Según permiso |

### 1.5 Pagos

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| B-PAY-01 | Listar pagos | GET `/api/payments/payments/` | 200, lista paginada |
| B-PAY-02 | Filtrar pagos | GET con student, status, fecha | 200, filtrado correcto |
| B-PAY-03 | Crear pago | POST con student, tipo, monto, método | 201 |
| B-PAY-04 | Aprobar pago (transferencia) | PATCH `.../payments/{id}/approve/` | 200 |
| B-PAY-05 | Rechazar pago | PATCH `.../payments/{id}/reject/` | 200 |
| B-PAY-06 | Estado de pagos por estudiante | GET `student_status/?student_id={id}` | 200 |
| B-PAY-07 | Pagos pendientes de transferencia | GET endpoint de pendientes | 200 |
| B-PAY-08 | Público: estudiante por carnet | GET `/api/payments/public/student/?carnet=XXX` | 200 con datos o 404 |
| B-PAY-09 | Público: crear payment intent (Stripe) | POST `/api/payments/public/payment-intent/` | 201 o 400 según datos |
| B-PAY-10 | Tipos de pago activos | GET `/api/payments/payment-types/` | 200, solo activos |
| B-PAY-11 | Becas | GET/POST scholarships, límites por carrera | 200/201 |

### 1.6 Documentos y certificados

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| B-DOC-01 | Listar documentos de estudiante | GET documentos por estudiante | 200 |
| B-DOC-02 | Subir documento | POST con file y tipo | 201 |
| B-CERT-01 | Certificados académicos | Endpoints de certificates | 200 según permiso |

### 1.7 Auditoría y exportación

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| B-AUD-01 | Listar logs de auditoría | GET `/api/audit/` (si existe) | 200, solo con permiso |
| B-EXP-01 | Exportar estudiantes | GET/POST export (CSV/Excel según API) | 200, archivo o datos |

### 1.8 Admin Django (interfaz /admin/)

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| B-ADM-01 | Login admin | Login con usuario staff | Redirección al índice admin |
| B-ADM-02 | Listar estudiantes | Ir a Students > Students | 200, tabla de estudiantes |
| B-ADM-03 | Agregar estudiante | Clic en "Añadir estudiante" | 200, formulario sin error 500 |
| B-ADM-04 | Editar estudiante | Editar un registro existente | Guardado correcto |
| B-ADM-05 | Estáticos admin | Carga de CSS/JS del admin | 200, sin 403/404 |
| B-ADM-06 | Carreras, cursos, pagos en admin | Navegar y editar | Sin errores 500 |

---

## 2. FRONTEND (React)

### 2.1 Autenticación y sesión

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-AUTH-01 | Login correcto | Usuario y contraseña válidos en /login | Redirección a /, menú con opciones |
| F-AUTH-02 | Login incorrecto | Credenciales inválidas | Mensaje de error, sin redirección |
| F-AUTH-03 | Logout | Clic en cerrar sesión | Redirección a /login, token eliminado |
| F-AUTH-04 | Ruta protegida sin login | Acceder a /students sin estar logueado | Redirección a /login |
| F-AUTH-05 | Refresh token | Dejar la app abierta, usar después de 1h | Renovación de token o redirect a login |
| F-AUTH-06 | Registro | Completar formulario en /register | Cuenta creada o mensaje de error |

### 2.2 Navegación y permisos

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-NAV-01 | Menú según rol | Login con admin, secretario, financiero, etc. | Solo se muestran opciones permitidas |
| F-NAV-02 | Acceso sin permiso | URL directa a /payments sin permiso | Redirección o mensaje de no autorizado |
| F-NAV-03 | Rutas públicas | /login, /pagos sin login | Página carga correctamente |
| F-NAV-04 | Ruta inexistente | URL como /ruta-falsa | Redirección a / o 404 según diseño |

### 2.3 Dashboard

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-DSH-01 | Carga del dashboard | Entrar a / | Gráficos/resúmenes sin error |
| F-DSH-02 | Datos mostrados | Revisar totales (estudiantes, pagos, etc.) | Coinciden con datos reales o mensaje de carga |
| F-DSH-03 | Enlaces del dashboard | Clic en tarjetas o enlaces | Navegación correcta |

### 2.4 Estudiantes

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-STU-01 | Listado de estudiantes | Ir a /students | Tabla con datos, paginación si aplica |
| F-STU-02 | Búsqueda y filtros | Usar buscador y filtros | Resultados filtrados correctamente |
| F-STU-03 | Crear estudiante | /students/new, llenar formulario y guardar | Estudiante creado, redirección o mensaje OK |
| F-STU-04 | Validación de formulario | Enviar sin campos requeridos (nombre, carrera, etc.) | Mensajes de error en campos |
| F-STU-05 | Editar estudiante | /students/:id/edit, modificar y guardar | Cambios guardados |
| F-STU-06 | Detalle de estudiante | /students/:id | Datos, documentos, enlaces correctos |
| F-STU-07 | Contabilidad del estudiante | /students/:id/accounting | Lista de pagos y estado |
| F-STU-08 | Exportar estudiantes | /exports, elegir opciones y descargar | Archivo descargado (CSV/Excel) |

### 2.5 Inscripciones

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-ENR-01 | Nueva inscripción | /enrollments/new | Formulario carga, guardado correcto |
| F-ENR-02 | Editar inscripción | /enrollments/:id/edit | Datos cargados, guardado OK |
| F-ENR-03 | Gestión de contrato | /enrollments/:id/contract | Vista/descarga de contrato sin error |

### 2.6 Pagos

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-PAY-01 | Listado de pagos | /payments | Tabla con pagos, filtros |
| F-PAY-02 | Nuevo pago | /payments/new | Formulario (estudiante, tipo, monto, método) |
| F-PAY-03 | Registrar transferencia | Subir comprobante, guardar | Pago creado en estado pendiente |
| F-PAY-04 | Aprobar/rechazar transferencias | /payments/pending-transfers | Aprobar o rechazar, lista actualizada |
| F-PAY-05 | Pago con tarjeta (Stripe) | Si está habilitado, flujo de pago | Redirección o confirmación según flujo |
| F-PAY-06 | Recibo/descarga | Descargar recibo de un pago | PDF o archivo descargado |

### 2.7 Académico

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-ACA-01 | Progreso académico | /academics | Lista o resumen de estudiantes/carreras |
| F-ACA-02 | Matrícula de cursos | /courses/enroll | Formulario y guardado de matrícula |
| F-ACA-03 | Matrícula por cuatrimestre | /cuatrimestre-enrollments | Alta/consulta de matrículas |
| F-ACA-04 | Carga de calificaciones | /grades/upload | Subida de archivo o formulario, sin error 500 |
| F-ACA-05 | Pensum de carrera | /careers/:id/pensum | Cursos del pensum mostrados |
| F-ACA-06 | Método de graduación | /graduation-method | CRUD o listado según pantalla |

### 2.8 Becas

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-BEC-01 | Listado de becas | /scholarships | Lista y filtros |
| F-BEC-02 | Asignar/editar beca | Formulario de beca | Guardado y validación de límites |

### 2.9 Perfil de usuario

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-PRF-01 | Ver perfil | /profile | Datos del usuario actual |
| F-PRF-02 | Cambiar contraseña | Formulario en perfil | Mensaje de éxito o error |

### 2.10 Pago público (sin login)

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-PUB-01 | Página de pagos | Ir a /pagos | Formulario por carnet |
| F-PUB-02 | Consultar por carnet | Ingresar carnet válido | Datos del estudiante y opciones de pago |
| F-PUB-03 | Carnet inexistente | Ingresar carnet que no existe | Mensaje de error claro |
| F-PUB-04 | Completar pago (transferencia/tarjeta) | Según flujo implementado | Confirmación o mensaje de error |

### 2.11 UI/UX y técnico

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| F-UI-01 | Tema claro/oscuro | Cambiar tema si existe | Estilos aplicados correctamente |
| F-UI-02 | Mensajes toast | Acciones que muestran notificación | Toast visible y se oculta |
| F-UI-03 | Carga y errores | Acciones lentas o fallidas | Spinner o mensaje de error |
| F-UI-04 | Responsive | Usar en móvil o redimensionar | Sin elementos rotos, navegación usable |
| F-UI-05 | Estáticos (JS/CSS) | Cargar cualquier página | Sin 403/404 en /static/js o /static/css |
| F-UI-06 | Recarga en ruta interna | F5 en /students o /payments | Página carga sin blanco ni error de ruta |

---

## 3. PRUEBAS INTEGRADAS (Frontend + Backend)

| ID | Caso de prueba | Pasos | Resultado esperado |
|----|----------------|-------|--------------------|
| I-01 | Flujo completo: alta estudiante y pago | Crear estudiante en front, luego registrar un pago | Datos coherentes en backend y listados |
| I-02 | Flujo: inscripción y contrato | Crear inscripción, generar/ver contrato | Contrato generado y accesible |
| I-03 | CORS | Llamadas desde front (otro puerto/dominio) a API | Sin error CORS, respuestas correctas |
| I-04 | Paginación | Listados con muchos registros | Páginas siguientes cargan bien |
| I-05 | Permisos por rol | Usuario con rol “consulta” intenta crear pago | 403 o mensaje de no autorizado en front |

---

## 4. RESUMEN POR PRIORIDAD

- **Críticas:** B-AUTH-01 a 07, B-STU-01 a 05, F-AUTH-01 a 04, F-STU-01 a 05, F-PAY-01 a 04, B-ADM-03, F-UI-05.
- **Altas:** Resto de auth, pagos públicos, académico, documentos, exportación.
- **Medias:** Auditoría, certificados, reportes, tema UI, responsive.

Documento de referencia para ejecutar pruebas manuales o convertirlas en casos de prueba automatizados (API con Postman/pytest, frontend con Jest/Cypress/Playwright).
