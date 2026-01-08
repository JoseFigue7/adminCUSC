# Escenarios de Prueba QA y Errores del Sistema - AdminCUSC

**Fecha de creación:** $(date)  
**Sistema:** AdminCUSC - Sistema de Gestión Estudiantil Administrativo  
**Versión:** 1.0

---

## Índice

1. [Escenarios de Prueba por Módulo](#escenarios-de-prueba-por-módulo)
2. [Errores Potenciales del Sistema](#errores-potenciales-del-sistema)
3. [Casos de Prueba de Integración](#casos-de-prueba-de-integración)
4. [Pruebas de Rendimiento](#pruebas-de-rendimiento)
5. [Pruebas de Seguridad](#pruebas-de-seguridad)
6. [Pruebas de Usabilidad](#pruebas-de-usabilidad)

---

## Escenarios de Prueba por Módulo

### 1. MÓDULO: Autenticación y Usuarios

#### 1.1 Login
- **TC-AUTH-001**: Login exitoso con credenciales válidas
- **TC-AUTH-002**: Login fallido con usuario incorrecto
- **TC-AUTH-003**: Login fallido con contraseña incorrecta
- **TC-AUTH-004**: Login con campos vacíos (usuario y/o contraseña)
- **TC-AUTH-005**: Login con usuario inactivo/deshabilitado
- **TC-AUTH-006**: Verificar que el token se guarda correctamente
- **TC-AUTH-007**: Verificar refresh token automático
- **TC-AUTH-008**: Logout exitoso
- **TC-AUTH-009**: Verificar redirección después del login
- **TC-AUTH-010**: Verificar expiración de sesión

#### 1.2 Registro de Usuarios
- **TC-AUTH-011**: Registro exitoso con datos válidos
- **TC-AUTH-012**: Registro fallido con email duplicado
- **TC-AUTH-013**: Registro fallido con username duplicado
- **TC-AUTH-014**: Registro fallido con contraseña menor a 8 caracteres
- **TC-AUTH-015**: Registro fallido con contraseñas que no coinciden
- **TC-AUTH-016**: Registro fallido con email inválido
- **TC-AUTH-017**: Validación de campos requeridos
- **TC-AUTH-018**: Verificar que el usuario se crea con rol por defecto

#### 1.3 Perfil de Usuario
- **TC-AUTH-019**: Ver información del perfil
- **TC-AUTH-020**: Cambiar contraseña exitosamente
- **TC-AUTH-021**: Cambiar contraseña con contraseña actual incorrecta
- **TC-AUTH-022**: Cambiar contraseña con nueva contraseña inválida
- **TC-AUTH-023**: Cambiar contraseña con confirmación que no coincide

---

### 2. MÓDULO: Gestión de Estudiantes

#### 2.1 Listado de Estudiantes
- **TC-STU-001**: Listar todos los estudiantes (paginado)
- **TC-STU-002**: Navegar entre páginas de estudiantes
- **TC-STU-003**: Buscar estudiante por carnet
- **TC-STU-004**: Buscar estudiante por nombre
- **TC-STU-005**: Buscar estudiante por apellido
- **TC-STU-006**: Buscar estudiante por email
- **TC-STU-007**: Buscar estudiante por carrera
- **TC-STU-008**: Filtrar estudiantes por carrera
- **TC-STU-009**: Filtrar estudiantes por estado (activo/inactivo)
- **TC-STU-010**: Ordenar estudiantes por fecha de inscripción
- **TC-STU-011**: Ordenar estudiantes por nombre
- **TC-STU-012**: Ordenar estudiantes por carnet
- **TC-STU-013**: Verificar que se muestran todos los campos correctos
- **TC-STU-014**: Verificar paginación con 0 estudiantes
- **TC-STU-015**: Verificar paginación con más de 20 estudiantes

#### 2.2 Crear Estudiante
- **TC-STU-016**: Crear estudiante con todos los datos válidos
- **TC-STU-017**: Verificar generación automática de carnet
- **TC-STU-018**: Crear estudiante sin carrera (debe fallar)
- **TC-STU-019**: Crear estudiante con email duplicado (debe fallar)
- **TC-STU-020**: Crear estudiante con CURP duplicado (debe fallar)
- **TC-STU-021**: Crear estudiante con teléfono inválido
- **TC-STU-022**: Crear estudiante con CURP inválido (menos de 18 caracteres)
- **TC-STU-023**: Crear estudiante con fecha de nacimiento futura (debe fallar)
- **TC-STU-024**: Crear estudiante con campos requeridos vacíos
- **TC-STU-025**: Verificar que se crea inscripción automáticamente
- **TC-STU-026**: Verificar formato de carnet (3 dígitos carrera + 2 año + 4 únicos)

#### 2.3 Editar Estudiante
- **TC-STU-027**: Editar información básica del estudiante
- **TC-STU-028**: Editar email (verificar que no esté duplicado)
- **TC-STU-029**: Editar teléfono
- **TC-STU-030**: Cambiar carrera del estudiante
- **TC-STU-031**: Activar/desactivar estudiante
- **TC-STU-032**: Editar con datos inválidos (debe fallar)
- **TC-STU-033**: Verificar que el carnet no se puede editar

#### 2.4 Ver Detalle de Estudiante
- **TC-STU-034**: Ver información completa del estudiante
- **TC-STU-035**: Ver documentos del estudiante
- **TC-STU-036**: Ver pagos del estudiante
- **TC-STU-037**: Ver progreso académico
- **TC-STU-038**: Ver matrículas de cursos
- **TC-STU-039**: Ver información de beca (si tiene)
- **TC-STU-040**: Ver información de tesis (si tiene)
- **TC-STU-041**: Acceder a estudiante inexistente (404)

#### 2.5 Documentos de Estudiante
- **TC-STU-042**: Listar documentos de un estudiante
- **TC-STU-043**: Subir documento (PDF válido)
- **TC-STU-044**: Subir documento (JPG válido)
- **TC-STU-045**: Subir documento (PNG válido)
- **TC-STU-046**: Subir documento mayor a 10MB (debe fallar)
- **TC-STU-047**: Subir documento con tipo de archivo inválido
- **TC-STU-048**: Actualizar estado de documento a APROBADO
- **TC-STU-049**: Actualizar estado de documento a RECHAZADO
- **TC-STU-050**: Actualizar estado de documento con notas
- **TC-STU-051**: Verificar que no se pueden duplicar tipos de documento
- **TC-STU-052**: Descargar documento subido
- **TC-STU-053**: Verificar tipos de documento requeridos:
  - Certificado de Bachillerato (Original + 2 copias)
  - Acta de Nacimiento (Original + 2 copias)
  - CURP
  - Certificado Médico
  - Fotografías (1 digital + 2 físicas)
  - Comprobante de Domicilio

#### 2.6 Inscripciones
- **TC-STU-054**: Listar todas las inscripciones
- **TC-STU-055**: Ver inscripción de un estudiante
- **TC-STU-056**: Generar contrato PDF para inscripción
- **TC-STU-057**: Descargar contrato generado
- **TC-STU-058**: Verificar que no se puede generar contrato dos veces
- **TC-STU-059**: Actualizar estado de inscripción
- **TC-STU-060**: Verificar creación automática de inscripción al crear estudiante

---

### 3. MÓDULO: Gestión Académica

#### 3.1 Carreras
- **TC-ACAD-001**: Listar todas las carreras activas
- **TC-ACAD-002**: Ver detalle de una carrera
- **TC-ACAD-003**: Ver pensum completo de una carrera
- **TC-ACAD-004**: Verificar que se muestran 6 carreras:
  - Licenciatura en Pedagogía (101)
  - Licenciatura en Criminología y Criminalística (102)
  - Licenciatura en Administración de Empresas y Negocios (103)
  - Licenciatura en Derecho (104)
  - Licenciatura en Mercadotecnia Digital y Publicidad (105)
  - Licenciatura en Contaduría Pública y Finanzas (106)
- **TC-ACAD-005**: Acceder a carrera inexistente (404)
- **TC-ACAD-006**: Verificar que las carreras inactivas no se muestran

#### 3.2 Pensum
- **TC-ACAD-007**: Ver pensum completo de carrera
- **TC-ACAD-008**: Verificar que se muestran todos los cursos
- **TC-ACAD-009**: Verificar que se muestran los cuatrimestres
- **TC-ACAD-010**: Verificar que se muestran los prerequisitos
- **TC-ACAD-011**: Verificar orden de cursos por cuatrimestre

#### 3.3 Cursos
- **TC-ACAD-012**: Listar todos los cursos
- **TC-ACAD-013**: Filtrar cursos por carrera
- **TC-ACAD-014**: Ver detalle de un curso
- **TC-ACAD-015**: Verificar información del curso (código, nombre, créditos)
- **TC-ACAD-016**: Verificar prerequisitos del curso

#### 3.4 Matrícula de Cursos
- **TC-ACAD-017**: Matricular estudiante en un curso
- **TC-ACAD-018**: Matricular estudiante sin cumplir prerequisito (debe fallar)
- **TC-ACAD-019**: Matricular estudiante en curso ya matriculado (debe fallar)
- **TC-ACAD-020**: Matricular estudiante en curso de otra carrera (debe fallar)
- **TC-ACAD-021**: Listar matrículas de un estudiante
- **TC-ACAD-022**: Ver matrícula específica
- **TC-ACAD-023**: Actualizar nota final de un curso
- **TC-ACAD-024**: Actualizar nota con valor menor a 0 (debe fallar)
- **TC-ACAD-025**: Actualizar nota con valor mayor a 100 (debe fallar)
- **TC-ACAD-026**: Verificar cambio automático de estado a APROBADO (nota >= 70)
- **TC-ACAD-027**: Verificar cambio automático de estado a REPROBADO (nota < 70)
- **TC-ACAD-028**: Verificar cierre automático de pensum cuando se aprueban todos los cursos
- **TC-ACAD-029**: Cambiar estado de matrícula manualmente
- **TC-ACAD-030**: Agregar notas a una matrícula

#### 3.5 Progreso Académico
- **TC-ACAD-031**: Ver progreso académico de un estudiante
- **TC-ACAD-032**: Verificar cálculo de cursos aprobados
- **TC-ACAD-033**: Verificar cálculo de porcentaje de progreso
- **TC-ACAD-034**: Verificar detección de pensum cerrado
- **TC-ACAD-035**: Verificar detección de tesis iniciada
- **TC-ACAD-036**: Ver progreso con 0 cursos aprobados
- **TC-ACAD-037**: Ver progreso con todos los cursos aprobados

#### 3.6 Tesis
- **TC-ACAD-038**: Listar todas las tesis
- **TC-ACAD-039**: Ver tesis de un estudiante
- **TC-ACAD-040**: Crear tesis para un estudiante
- **TC-ACAD-041**: Verificar que un estudiante solo puede tener una tesis
- **TC-ACAD-042**: Actualizar estado de tesis:
  - NO_INICIADA
  - SOLICITUD_ASESOR
  - REVISION_TEMA
  - APROBACION_TEMA
  - PRIMERA_REVISION
  - SEGUNDA_REVISION
  - TERCERA_REVISION
  - APROBADA
  - RECHAZADA
- **TC-ACAD-043**: Actualizar título de tesis
- **TC-ACAD-044**: Asignar asesor a tesis
- **TC-ACAD-045**: Actualizar fecha de inicio
- **TC-ACAD-046**: Actualizar fecha de defensa
- **TC-ACAD-047**: Subir documento de tesis
- **TC-ACAD-048**: Verificar que se marca thesis_started cuando se solicita asesor
- **TC-ACAD-049**: Acceder a tesis de estudiante sin tesis (404)

---

### 4. MÓDULO: Gestión de Pagos

#### 4.1 Listado de Pagos
- **TC-PAY-001**: Listar todos los pagos (paginado)
- **TC-PAY-002**: Navegar entre páginas de pagos
- **TC-PAY-003**: Filtrar pagos por estado (PENDIENTE, EN_REVISION, APROBADO, RECHAZADO)
- **TC-PAY-004**: Filtrar pagos por método (TRANSFERENCIA, TARJETA, EFECTIVO)
- **TC-PAY-005**: Filtrar pagos por mes
- **TC-PAY-006**: Filtrar pagos por año
- **TC-PAY-007**: Filtrar pagos por estudiante
- **TC-PAY-008**: Buscar pagos por nombre de estudiante
- **TC-PAY-009**: Buscar pagos por carnet
- **TC-PAY-010**: Buscar pagos por número de recibo
- **TC-PAY-011**: Ordenar pagos por fecha
- **TC-PAY-012**: Ordenar pagos por monto
- **TC-PAY-013**: Verificar que se muestran todos los campos correctos

#### 4.2 Crear Pago
- **TC-PAY-014**: Crear pago con método TRANSFERENCIA
- **TC-PAY-015**: Crear pago con método TARJETA
- **TC-PAY-016**: Crear pago con método EFECTIVO
- **TC-PAY-017**: Crear pago sin estudiante (debe fallar)
- **TC-PAY-018**: Crear pago sin monto (debe fallar)
- **TC-PAY-019**: Crear pago con monto negativo (debe fallar)
- **TC-PAY-020**: Crear pago con monto cero (debe fallar)
- **TC-PAY-021**: Crear pago sin mes (debe fallar)
- **TC-PAY-022**: Crear pago sin año (debe fallar)
- **TC-PAY-023**: Crear pago duplicado (mismo estudiante, mes y año) (debe fallar)
- **TC-PAY-024**: Crear pago EFECTIVO con número de recibo
- **TC-PAY-025**: Crear pago TARJETA con últimos 4 dígitos y transaction_id
- **TC-PAY-026**: Verificar que el estado inicial es PENDIENTE

#### 4.3 Subir Comprobante
- **TC-PAY-027**: Subir comprobante para pago TRANSFERENCIA
- **TC-PAY-028**: Subir comprobante con archivo PDF válido
- **TC-PAY-029**: Subir comprobante con archivo JPG válido
- **TC-PAY-030**: Subir comprobante con archivo PNG válido
- **TC-PAY-031**: Subir comprobante mayor a 10MB (debe fallar)
- **TC-PAY-032**: Subir comprobante con tipo de archivo inválido (debe fallar)
- **TC-PAY-033**: Subir comprobante para pago que no es TRANSFERENCIA (debe fallar)
- **TC-PAY-034**: Verificar que el estado cambia a EN_REVISION al subir comprobante
- **TC-PAY-035**: Descargar comprobante subido

#### 4.4 Aprobar Pago
- **TC-PAY-036**: Aprobar pago PENDIENTE
- **TC-PAY-037**: Aprobar pago EN_REVISION
- **TC-PAY-038**: Verificar que el estado cambia a APROBADO
- **TC-PAY-039**: Aprobar pago ya APROBADO (verificar comportamiento)
- **TC-PAY-040**: Aprobar pago RECHAZADO (verificar comportamiento)

#### 4.5 Rechazar Pago
- **TC-PAY-041**: Rechazar pago PENDIENTE
- **TC-PAY-042**: Rechazar pago EN_REVISION
- **TC-PAY-043**: Rechazar pago con motivo/notas
- **TC-PAY-044**: Rechazar pago sin motivo/notas
- **TC-PAY-045**: Verificar que el estado cambia a RECHAZADO
- **TC-PAY-046**: Verificar que las notas se guardan correctamente

#### 4.6 Estado de Pagos por Estudiante
- **TC-PAY-047**: Ver estado de pagos de un estudiante
- **TC-PAY-048**: Verificar cálculo de meses pagados
- **TC-PAY-049**: Verificar cálculo de meses pendientes
- **TC-PAY-050**: Verificar detección de estudiante al día
- **TC-PAY-051**: Verificar detección de estudiante con pagos pendientes
- **TC-PAY-052**: Ver estado con estudiante sin pagos
- **TC-PAY-053**: Ver estado con estudiante con todos los pagos aprobados

#### 4.7 Estudiantes con Pagos Pendientes
- **TC-PAY-054**: Listar estudiantes con pagos pendientes
- **TC-PAY-055**: Verificar que solo se muestran estudiantes activos
- **TC-PAY-056**: Verificar que se excluyen estudiantes con pago aprobado del mes actual

---

### 5. MÓDULO: Gestión de Becas

#### 5.1 Listado de Becas
- **TC-SCH-001**: Listar todas las becas
- **TC-SCH-002**: Filtrar becas por tipo (COMPLETA, MEDIA)
- **TC-SCH-003**: Filtrar becas por estado (ACTIVA, SUSPENDIDA, FINALIZADA)
- **TC-SCH-004**: Filtrar becas por estudiante
- **TC-SCH-005**: Verificar que se muestran todos los campos correctos

#### 5.2 Crear Beca
- **TC-SCH-006**: Crear beca COMPLETA para un estudiante
- **TC-SCH-007**: Crear beca MEDIA para un estudiante
- **TC-SCH-008**: Crear beca sin estudiante (debe fallar)
- **TC-SCH-009**: Crear beca sin tipo (debe fallar)
- **TC-SCH-010**: Crear beca sin fecha de inicio (debe fallar)
- **TC-SCH-011**: Crear segunda beca para estudiante que ya tiene (debe fallar)
- **TC-SCH-012**: Verificar que el porcentaje se calcula automáticamente (100% o 50%)
- **TC-SCH-013**: Verificar que se actualiza el campo has_scholarship del estudiante
- **TC-SCH-014**: Verificar que se actualiza el campo scholarship_type del estudiante
- **TC-SCH-015**: Verificar límites de becas por facultad (si está implementado)

#### 5.3 Actualizar Beca
- **TC-SCH-016**: Actualizar estado de beca a SUSPENDIDA
- **TC-SCH-017**: Actualizar estado de beca a FINALIZADA
- **TC-SCH-018**: Actualizar fecha de fin de beca
- **TC-SCH-019**: Actualizar notas de beca

---

### 6. MÓDULO: Reportes

#### 6.1 Reportes Generales
- **TC-REP-001**: Ver reporte general con estadísticas
- **TC-REP-002**: Ver reporte de estudiantes por carrera
- **TC-REP-003**: Ver reporte de pagos por mes
- **TC-REP-004**: Ver reporte académico con promedios
- **TC-REP-005**: Exportar reporte a CSV
- **TC-REP-006**: Exportar reporte a PDF
- **TC-REP-007**: Verificar que los datos del reporte son correctos
- **TC-REP-008**: Verificar formato de archivo CSV exportado
- **TC-REP-009**: Verificar formato de archivo PDF exportado

---

### 7. MÓDULO: Dashboard

#### 7.1 Panel Principal
- **TC-DASH-001**: Cargar dashboard con datos
- **TC-DASH-002**: Ver estadísticas de estudiantes (total y activos)
- **TC-DASH-003**: Ver estadísticas de pagos (total y pendientes)
- **TC-DASH-004**: Ver estadísticas de carreras
- **TC-DASH-005**: Ver lista de estudiantes recientes
- **TC-DASH-006**: Ver lista de pagos recientes
- **TC-DASH-007**: Navegar a lista completa de estudiantes desde dashboard
- **TC-DASH-008**: Navegar a lista completa de pagos desde dashboard
- **TC-DASH-009**: Verificar acciones rápidas (nuevo estudiante, gestionar pagos, progreso académico)
- **TC-DASH-010**: Verificar que se muestra mensaje cuando no hay datos
- **TC-DASH-011**: Verificar carga de datos con errores de red

---

### 8. MÓDULO: Interfaz de Usuario

#### 8.1 Navegación
- **TC-UI-001**: Navegar entre todas las secciones del menú
- **TC-UI-002**: Verificar que las rutas protegidas requieren autenticación
- **TC-UI-003**: Verificar redirección a login si no está autenticado
- **TC-UI-004**: Verificar que el menú se muestra correctamente
- **TC-UI-005**: Verificar que el menú se oculta en móvil

#### 8.2 Responsive Design
- **TC-UI-006**: Verificar diseño en desktop (1024px+)
- **TC-UI-007**: Verificar diseño en tablet (768px - 1023px)
- **TC-UI-008**: Verificar diseño en móvil (480px - 767px)
- **TC-UI-009**: Verificar que las tablas tienen scroll horizontal en móvil
- **TC-UI-010**: Verificar que los formularios se adaptan a pantallas pequeñas
- **TC-UI-011**: Verificar que los modales son responsive

#### 8.3 Notificaciones (Toast)
- **TC-UI-012**: Mostrar notificación de éxito
- **TC-UI-013**: Mostrar notificación de error
- **TC-UI-014**: Mostrar notificación de advertencia
- **TC-UI-015**: Mostrar notificación de información
- **TC-UI-016**: Verificar auto-cierre de notificaciones
- **TC-UI-017**: Verificar que se pueden cerrar manualmente
- **TC-UI-018**: Verificar que múltiples notificaciones se apilan correctamente

#### 8.4 Paginación
- **TC-UI-019**: Verificar componente de paginación
- **TC-UI-020**: Navegar a página siguiente
- **TC-UI-021**: Navegar a página anterior
- **TC-UI-022**: Navegar a página específica
- **TC-UI-023**: Verificar que se muestra el número de página actual
- **TC-UI-024**: Verificar que se muestra el total de páginas
- **TC-UI-025**: Verificar que se deshabilita botón "anterior" en primera página
- **TC-UI-026**: Verificar que se deshabilita botón "siguiente" en última página

#### 8.5 Búsqueda y Filtros
- **TC-UI-027**: Verificar componente de búsqueda avanzada
- **TC-UI-028**: Aplicar múltiples filtros simultáneos
- **TC-UI-029**: Limpiar filtros aplicados
- **TC-UI-030**: Verificar que los filtros persisten al cambiar de página
- **TC-UI-031**: Verificar que la búsqueda funciona en tiempo real

---

## Errores Potenciales del Sistema

### 1. ERRORES DE BACKEND

#### 1.1 Errores de Validación
- **ERR-BACK-001**: No se valida que el email sea único antes de crear estudiante
- **ERR-BACK-002**: No se valida que el CURP sea único antes de crear estudiante
- **ERR-BACK-003**: No se valida formato de teléfono correctamente
- **ERR-BACK-004**: No se valida que la fecha de nacimiento no sea futura
- **ERR-BACK-005**: No se valida que el monto de pago sea positivo
- **ERR-BACK-006**: No se valida que el mes esté entre 1 y 12
- **ERR-BACK-007**: No se valida que la nota esté entre 0 y 100
- **ERR-BACK-008**: No se valida que el archivo subido no exceda 10MB
- **ERR-BACK-009**: No se valida tipo de archivo permitido antes de subir
- **ERR-BACK-010**: No se valida que un estudiante no tenga dos becas activas

#### 1.2 Errores de Lógica de Negocio
- **ERR-BACK-011**: No se verifica límite de becas por facultad al crear beca
- **ERR-BACK-012**: No se verifica prerequisitos al matricular curso
- **ERR-BACK-013**: No se verifica que el curso pertenezca a la carrera del estudiante
- **ERR-BACK-014**: No se actualiza pensum_closed cuando se aprueba el último curso
- **ERR-BACK-015**: No se calcula correctamente el progreso académico
- **ERR-BACK-016**: No se verifica duplicado de pago (mismo estudiante, mes, año)
- **ERR-BACK-017**: No se verifica que el estudiante esté activo antes de operaciones
- **ERR-BACK-018**: No se genera carnet único correctamente (posible duplicado)
- **ERR-BACK-019**: No se crea inscripción automáticamente al crear estudiante
- **ERR-BACK-020**: No se actualiza estado de matrícula automáticamente al cambiar nota

#### 1.3 Errores de Base de Datos
- **ERR-BACK-021**: No se maneja transacción atómica al crear estudiante
- **ERR-BACK-022**: No se maneja error de integridad referencial
- **ERR-BACK-023**: No se maneja error de constraint único
- **ERR-BACK-024**: No se maneja error de foreign key
- **ERR-BACK-025**: No se optimizan queries (N+1 problem)
- **ERR-BACK-026**: No se usa select_related/prefetch_related donde corresponde
- **ERR-BACK-027**: No se maneja error de conexión a base de datos
- **ERR-BACK-028**: No se maneja timeout de base de datos

#### 1.4 Errores de Archivos
- **ERR-BACK-029**: No se valida tamaño de archivo antes de guardar
- **ERR-BACK-030**: No se valida tipo MIME del archivo
- **ERR-BACK-031**: No se maneja error al guardar archivo en disco
- **ERR-BACK-032**: No se maneja error al leer archivo existente
- **ERR-BACK-033**: No se limpian archivos huérfanos al eliminar registros
- **ERR-BACK-034**: No se valida que el directorio de media exista
- **ERR-BACK-035**: No se maneja error de espacio en disco

#### 1.5 Errores de Autenticación y Permisos
- **ERR-BACK-036**: No se verifica token JWT en todas las vistas protegidas
- **ERR-BACK-037**: No se maneja expiración de token correctamente
- **ERR-BACK-038**: No se verifica permiso específico antes de operaciones
- **ERR-BACK-039**: No se maneja error de refresh token inválido
- **ERR-BACK-040**: No se valida que el usuario esté activo

#### 1.6 Errores de API
- **ERR-BACK-041**: No se retorna código de estado HTTP correcto
- **ERR-BACK-042**: No se retorna mensaje de error descriptivo
- **ERR-BACK-043**: No se maneja error 500 (Internal Server Error)
- **ERR-BACK-044**: No se maneja error 404 (Not Found) correctamente
- **ERR-BACK-045**: No se maneja error 400 (Bad Request) con detalles
- **ERR-BACK-046**: No se valida Content-Type en requests
- **ERR-BACK-047**: No se maneja CORS correctamente
- **ERR-BACK-048**: No se limita rate limiting (posible ataque DDoS)

#### 1.7 Errores de Generación de PDF
- **ERR-BACK-049**: No se maneja error al generar contrato PDF
- **ERR-BACK-050**: No se valida que WeasyPrint esté instalado
- **ERR-BACK-051**: No se maneja error de memoria al generar PDF grande
- **ERR-BACK-052**: No se valida que el template HTML exista

---

### 2. ERRORES DE FRONTEND

#### 2.1 Errores de Validación
- **ERR-FRONT-001**: No se valida formulario antes de enviar
- **ERR-FRONT-002**: No se muestra mensaje de error en campos requeridos
- **ERR-FRONT-003**: No se valida formato de email en frontend
- **ERR-FRONT-004**: No se valida formato de teléfono en frontend
- **ERR-FRONT-005**: No se valida formato de CURP en frontend
- **ERR-FRONT-006**: No se valida que las contraseñas coincidan
- **ERR-FRONT-007**: No se valida tamaño de archivo antes de subir
- **ERR-FRONT-008**: No se valida tipo de archivo antes de subir
- **ERR-FRONT-009**: No se valida rango de notas (0-100)
- **ERR-FRONT-010**: No se valida que el mes esté entre 1 y 12

#### 2.2 Errores de Manejo de Estado
- **ERR-FRONT-011**: Estado no se actualiza después de crear registro
- **ERR-FRONT-012**: Estado no se actualiza después de editar registro
- **ERR-FRONT-013**: Estado no se actualiza después de eliminar registro
- **ERR-FRONT-014**: No se limpia estado al cambiar de página
- **ERR-FRONT-015**: No se resetea formulario después de envío exitoso
- **ERR-FRONT-016**: Estado de carga no se actualiza correctamente
- **ERR-FRONT-017**: No se maneja estado de error en componentes

#### 2.3 Errores de Llamadas API
- **ERR-FRONT-018**: No se maneja error de red (sin conexión)
- **ERR-FRONT-019**: No se maneja timeout de request
- **ERR-FRONT-020**: No se maneja error 401 (no autorizado)
- **ERR-FRONT-021**: No se maneja error 403 (prohibido)
- **ERR-FRONT-022**: No se maneja error 404 (no encontrado)
- **ERR-FRONT-023**: No se maneja error 500 (error del servidor)
- **ERR-FRONT-024**: No se muestra mensaje de error al usuario
- **ERR-FRONT-025**: No se retry automático en caso de error de red
- **ERR-FRONT-026**: No se cancela request al desmontar componente

#### 2.4 Errores de Autenticación
- **ERR-FRONT-027**: Token no se guarda en localStorage correctamente
- **ERR-FRONT-028**: Token no se envía en headers de requests
- **ERR-FRONT-029**: No se refresca token automáticamente
- **ERR-FRONT-030**: No se redirige a login cuando token expira
- **ERR-FRONT-031**: No se limpia token al hacer logout
- **ERR-FRONT-032**: No se valida que el usuario esté autenticado antes de mostrar datos

#### 2.5 Errores de UI/UX
- **ERR-FRONT-033**: No se muestra indicador de carga durante requests
- **ERR-FRONT-034**: No se muestra mensaje cuando no hay datos
- **ERR-FRONT-035**: No se muestra mensaje de éxito después de operación
- **ERR-FRONT-036**: Formularios no son accesibles por teclado
- **ERR-FRONT-037**: No hay feedback visual al hacer hover/click
- **ERR-FRONT-038**: Modales no se cierran al hacer click fuera
- **ERR-FRONT-039**: Modales no se cierran con tecla ESC
- **ERR-FRONT-040**: No hay confirmación antes de acciones destructivas

#### 2.6 Errores de Paginación
- **ERR-FRONT-041**: No se actualiza lista al cambiar de página
- **ERR-FRONT-042**: No se mantienen filtros al cambiar de página
- **ERR-FRONT-043**: No se resetea a página 1 al aplicar filtros
- **ERR-FRONT-044**: No se valida que la página solicitada exista
- **ERR-FRONT-045**: No se muestra correctamente el número de página actual

#### 2.7 Errores de Responsive
- **ERR-FRONT-046**: Tablas no tienen scroll horizontal en móvil
- **ERR-FRONT-047**: Formularios no se adaptan a pantallas pequeñas
- **ERR-FRONT-048**: Menú no se oculta correctamente en móvil
- **ERR-FRONT-049**: Modales no son responsive
- **ERR-FRONT-050**: Botones no son táctiles en móvil (muy pequeños)

#### 2.8 Errores de Rendimiento
- **ERR-FRONT-051**: No se usa lazy loading para componentes grandes
- **ERR-FRONT-052**: No se cachean datos que no cambian frecuentemente
- **ERR-FRONT-053**: Se hacen múltiples requests innecesarios
- **ERR-FRONT-054**: No se debounce en búsquedas
- **ERR-FRONT-055**: Imágenes no están optimizadas
- **ERR-FRONT-056**: No se usa memoización donde corresponde

#### 2.9 Errores de TypeScript
- **ERR-FRONT-057**: Tipos no están definidos correctamente
- **ERR-FRONT-058**: Props opcionales no se manejan correctamente
- **ERR-FRONT-059**: No se valida tipo de datos recibidos de API
- **ERR-FRONT-060**: Uso de `any` en lugar de tipos específicos

---

### 3. ERRORES DE INTEGRACIÓN

#### 3.1 Errores Frontend-Backend
- **ERR-INT-001**: Formato de datos enviado no coincide con esperado por backend
- **ERR-INT-002**: Formato de datos recibido no coincide con esperado por frontend
- **ERR-INT-003**: URLs de endpoints no coinciden
- **ERR-INT-004**: Headers requeridos no se envían
- **ERR-INT-005**: CORS no configurado correctamente
- **ERR-INT-006**: Timezone no se maneja consistentemente
- **ERR-INT-007**: Formato de fechas no coincide entre frontend y backend

#### 3.2 Errores de Archivos
- **ERR-INT-008**: Archivos no se suben correctamente (multipart/form-data)
- **ERR-INT-009**: URLs de archivos no son accesibles desde frontend
- **ERR-INT-010**: Archivos no se descargan correctamente
- **ERR-INT-011**: PDFs no se generan correctamente

---

### 4. ERRORES DE SEGURIDAD

#### 4.1 Errores de Autenticación
- **ERR-SEC-001**: Contraseñas no se hashean correctamente
- **ERR-SEC-002**: Tokens JWT no se validan correctamente
- **ERR-SEC-003**: Tokens no expiran correctamente
- **ERR-SEC-004**: Refresh tokens no se rotan
- **ERR-SEC-005**: No hay protección contra fuerza bruta en login

#### 4.2 Errores de Autorización
- **ERR-SEC-006**: Permisos no se verifican en todas las operaciones
- **ERR-SEC-007**: Usuarios pueden acceder a datos de otros usuarios
- **ERR-SEC-008**: No hay validación de roles en frontend
- **ERR-SEC-009**: Endpoints públicos no deberían ser públicos

#### 4.3 Errores de Validación de Entrada
- **ERR-SEC-010**: No se sanitiza entrada de usuario (XSS)
- **ERR-SEC-011**: No se valida entrada contra SQL injection
- **ERR-SEC-012**: No se valida tamaño máximo de request
- **ERR-SEC-013**: No se valida tipo de archivo subido (posible malware)

#### 4.4 Errores de Exposición de Datos
- **ERR-SEC-014**: Mensajes de error exponen información sensible
- **ERR-SEC-015**: Stack traces se muestran en producción
- **ERR-SEC-016**: IDs de UUID pueden ser predecibles
- **ERR-SEC-017**: Archivos privados son accesibles públicamente

---

### 5. ERRORES DE RENDIMIENTO

#### 5.1 Errores de Base de Datos
- **ERR-PERF-001**: Queries no están optimizadas (N+1)
- **ERR-PERF-002**: No hay índices en campos de búsqueda frecuente
- **ERR-PERF-003**: No se usa paginación en queries grandes
- **ERR-PERF-004**: No se cachean queries frecuentes
- **ERR-PERF-005**: Transacciones muy largas bloquean otras operaciones

#### 5.2 Errores de API
- **ERR-PERF-006**: No hay rate limiting
- **ERR-PERF-007**: No hay timeout en requests largos
- **ERR-PERF-008**: No se comprimen respuestas (gzip)
- **ERR-PERF-009**: No se cachean respuestas estáticas

#### 5.3 Errores de Frontend
- **ERR-PERF-010**: Bundle de JavaScript muy grande
- **ERR-PERF-011**: No se usa code splitting
- **ERR-PERF-012**: Imágenes no están optimizadas
- **ERR-PERF-013**: No se usa lazy loading para componentes

---

## Casos de Prueba de Integración

### 1. Flujo Completo de Inscripción de Estudiante
- **TC-INT-001**: Crear estudiante → Verificar generación de carnet → Crear inscripción automática → Generar contrato PDF → Subir documentos → Aprobar documentos → Verificar estado completo

### 2. Flujo Completo de Pago
- **TC-INT-002**: Crear pago TRANSFERENCIA → Subir comprobante → Cambiar estado a EN_REVISION → Aprobar pago → Verificar estado de estudiante al día

### 3. Flujo Completo Académico
- **TC-INT-003**: Matricular estudiante en cursos → Registrar notas → Verificar cambio de estado → Verificar progreso académico → Verificar cierre de pensum → Iniciar tesis

### 4. Flujo Completo de Beca
- **TC-INT-004**: Crear beca para estudiante → Verificar actualización de campos del estudiante → Verificar límites de becas → Actualizar estado de beca

---

## Pruebas de Rendimiento

### 1. Carga de Datos
- **TC-PERF-001**: Cargar lista de 1000 estudiantes (debe ser rápido)
- **TC-PERF-002**: Cargar lista de 5000 pagos (debe ser rápido)
- **TC-PERF-003**: Búsqueda en lista grande (debe ser rápida)
- **TC-PERF-004**: Generar reporte con muchos datos (debe completarse en tiempo razonable)

### 2. Operaciones Concurrentes
- **TC-PERF-005**: Múltiples usuarios creando estudiantes simultáneamente
- **TC-PERF-006**: Múltiples usuarios aprobando pagos simultáneamente
- **TC-PERF-007**: Múltiples usuarios subiendo archivos simultáneamente

---

## Pruebas de Seguridad

### 1. Autenticación
- **TC-SEC-001**: Intentar acceder a endpoint protegido sin token
- **TC-SEC-002**: Intentar acceder con token inválido
- **TC-SEC-003**: Intentar acceder con token expirado
- **TC-SEC-004**: Intentar hacer login con credenciales incorrectas múltiples veces

### 2. Autorización
- **TC-SEC-005**: Usuario sin permiso intenta crear estudiante
- **TC-SEC-006**: Usuario sin permiso intenta aprobar pago
- **TC-SEC-007**: Usuario intenta acceder a datos de otro usuario

### 3. Validación de Entrada
- **TC-SEC-008**: Intentar inyectar SQL en campos de búsqueda
- **TC-SEC-009**: Intentar inyectar XSS en campos de texto
- **TC-SEC-010**: Intentar subir archivo ejecutable como documento

---

## Pruebas de Usabilidad

### 1. Navegación
- **TC-UX-001**: Verificar que todas las rutas son accesibles
- **TC-UX-002**: Verificar que el breadcrumb muestra la ruta correcta
- **TC-UX-003**: Verificar que los botones de "volver" funcionan

### 2. Feedback al Usuario
- **TC-UX-004**: Verificar que se muestra mensaje de éxito después de crear registro
- **TC-UX-005**: Verificar que se muestra mensaje de error cuando falla operación
- **TC-UX-006**: Verificar que se muestra indicador de carga durante operaciones

### 3. Accesibilidad
- **TC-UX-007**: Verificar que todos los elementos son accesibles por teclado
- **TC-UX-008**: Verificar que hay suficiente contraste de colores
- **TC-UX-009**: Verificar que los formularios tienen labels asociados

---

## Resumen de Escenarios

### Total de Escenarios de Prueba: **~400+**

- **Autenticación y Usuarios**: 23 escenarios
- **Gestión de Estudiantes**: 60 escenarios
- **Gestión Académica**: 49 escenarios
- **Gestión de Pagos**: 56 escenarios
- **Gestión de Becas**: 19 escenarios
- **Reportes**: 9 escenarios
- **Dashboard**: 11 escenarios
- **Interfaz de Usuario**: 31 escenarios
- **Integración**: 4 escenarios
- **Rendimiento**: 7 escenarios
- **Seguridad**: 10 escenarios
- **Usabilidad**: 9 escenarios

### Total de Errores Potenciales: **~130+**

- **Backend**: 52 errores
- **Frontend**: 60 errores
- **Integración**: 11 errores
- **Seguridad**: 17 errores
- **Rendimiento**: 13 errores

---

## Notas Importantes

1. **Priorización**: Los escenarios marcados como críticos deben probarse primero
2. **Automatización**: Se recomienda automatizar los escenarios de regresión
3. **Documentación**: Todos los errores encontrados deben documentarse con pasos para reproducir
4. **Seguimiento**: Usar un sistema de seguimiento de bugs (Jira, GitHub Issues, etc.)
5. **Ambiente de Pruebas**: Usar datos de prueba, nunca datos de producción

---

**Última actualización:** $(date)  
**Mantenido por:** Equipo de QA

