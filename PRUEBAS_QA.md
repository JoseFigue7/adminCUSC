# Plan de Pruebas QA - Sistema AdminCUSC

Este documento contiene el plan completo de pruebas para validar todas las funcionalidades del sistema de gestión estudiantil AdminCUSC.

## Índice

1. [Autenticación y Usuarios](#1-autenticación-y-usuarios)
2. [Gestión de Estudiantes](#2-gestión-de-estudiantes)
3. [Gestión Académica](#3-gestión-académica)
4. [Gestión de Pagos](#4-gestión-de-pagos)
5. [Sistema de Becas](#5-sistema-de-becas)
6. [Gestión de Documentos](#6-gestión-de-documentos)
7. [Certificados](#7-certificados)
8. [Auditoría](#8-auditoría)
9. [Exportación de Datos](#9-exportación-de-datos)
10. [Interfaz de Usuario](#10-interfaz-de-usuario)
11. [Integración y Rendimiento](#11-integración-y-rendimiento)

---

## 1. Autenticación y Usuarios

### 1.1 Login y Autenticación

#### TC-AUTH-001: Login exitoso
- **Precondiciones**: Usuario existe en el sistema
- **Pasos**:
  1. Navegar a la página de login
  2. Ingresar username y password válidos
  3. Hacer clic en "Iniciar Sesión"
- **Resultado Esperado**: 
  - Usuario es redirigido al dashboard
  - Token JWT es almacenado
  - Se muestra información del usuario logueado

#### TC-AUTH-002: Login con credenciales inválidas
- **Precondiciones**: Ninguna
- **Pasos**:
  1. Ingresar username incorrecto o password incorrecto
  2. Hacer clic en "Iniciar Sesión"
- **Resultado Esperado**: 
  - Mensaje de error: "Credenciales inválidas"
  - No se genera token
  - Usuario permanece en página de login

#### TC-AUTH-003: Refresh token
- **Precondiciones**: Usuario autenticado
- **Pasos**:
  1. Esperar a que el token expire o esté próximo a expirar
  2. Realizar una petición API
- **Resultado Esperado**: 
  - Token se renueva automáticamente
  - Usuario no es deslogueado

#### TC-AUTH-004: Logout
- **Precondiciones**: Usuario autenticado
- **Pasos**:
  1. Hacer clic en "Cerrar Sesión"
- **Resultado Esperado**: 
  - Token es eliminado
  - Usuario es redirigido a página de login
  - No se puede acceder a rutas protegidas

### 1.2 Gestión de Usuarios

#### TC-USER-001: Crear usuario
- **Precondiciones**: Usuario con rol SUPER_ADMIN o ADMIN
- **Pasos**:
  1. Navegar a "Gestión de Usuarios"
  2. Hacer clic en "Nuevo Usuario"
  3. Completar formulario (username, email, password, rol, teléfono)
  4. Guardar
- **Resultado Esperado**: 
  - Usuario es creado exitosamente
  - Se muestra mensaje de confirmación
  - Usuario aparece en la lista

#### TC-USER-002: Editar usuario
- **Precondiciones**: Usuario existe
- **Pasos**:
  1. Seleccionar usuario de la lista
  2. Hacer clic en "Editar"
  3. Modificar campos (email, teléfono, rol)
  4. Guardar cambios
- **Resultado Esperado**: 
  - Cambios se guardan correctamente
  - Se muestra mensaje de confirmación

#### TC-USER-003: Desactivar usuario
- **Precondiciones**: Usuario activo existe
- **Pasos**:
  1. Seleccionar usuario
  2. Cambiar estado a "Inactivo"
  3. Guardar
- **Resultado Esperado**: 
  - Usuario no puede iniciar sesión
  - Estado se refleja en la lista

#### TC-USER-004: Validar permisos por rol
- **Precondiciones**: Múltiples usuarios con diferentes roles
- **Pasos**:
  1. Login con usuario SECRETARY
  2. Intentar acceder a "Gestión de Usuarios"
  3. Login con usuario SUPER_ADMIN
  4. Verificar acceso completo
- **Resultado Esperado**: 
  - SECRETARY no puede acceder a gestión de usuarios
  - SUPER_ADMIN tiene acceso completo
  - Mensajes de error apropiados para accesos no autorizados

---

## 2. Gestión de Estudiantes

### 2.1 Inscripción de Estudiantes

#### TC-STU-001: Crear nuevo estudiante
- **Precondiciones**: Usuario con permisos de gestión de estudiantes
- **Pasos**:
  1. Navegar a "Estudiantes" > "Nuevo Estudiante"
  2. Completar datos personales:
     - Nombres y apellidos
     - Fecha de nacimiento
     - CURP
     - Email
     - Teléfono
     - Dirección
  3. Seleccionar carrera
  4. Guardar
- **Resultado Esperado**: 
  - Estudiante es creado
  - Se genera carnet automáticamente (formato: 3 dígitos carrera + 2 dígitos año + 4 dígitos único)
  - Se muestra mensaje de éxito

#### TC-STU-002: Validar formato de carnet
- **Precondiciones**: Estudiante creado
- **Pasos**:
  1. Verificar carnet generado
- **Resultado Esperado**: 
  - Formato: XXXYYZZZZ (ej: 101240001)
  - Carnet es único
  - No se puede modificar manualmente

#### TC-STU-003: Validar campos obligatorios
- **Precondiciones**: Formulario de nuevo estudiante abierto
- **Pasos**:
  1. Intentar guardar sin completar campos obligatorios
  2. Verificar validaciones
- **Resultado Esperado**: 
  - Mensajes de error para campos obligatorios
  - Formulario no se envía
  - Campos con error se resaltan

#### TC-STU-004: Validar formato de CURP
- **Precondiciones**: Formulario de estudiante
- **Pasos**:
  1. Ingresar CURP con formato incorrecto
  2. Intentar guardar
- **Resultado Esperado**: 
  - Mensaje de error: "CURP inválido"
  - Formato debe ser 18 caracteres alfanuméricos

#### TC-STU-005: Validar formato de teléfono
- **Precondiciones**: Formulario de estudiante
- **Pasos**:
  1. Ingresar teléfono con caracteres inválidos
  2. Intentar guardar
- **Resultado Esperado**: 
  - Mensaje de error: "El número telefónico solo puede contener el signo + y números"
  - Acepta formatos: +1234567890, +525512345678, 1234567890

### 2.2 Búsqueda y Filtrado

#### TC-STU-006: Buscar estudiante por carnet
- **Precondiciones**: Estudiantes existentes
- **Pasos**:
  1. Navegar a lista de estudiantes
  2. Ingresar carnet en búsqueda
  3. Presionar Enter o clic en buscar
- **Resultado Esperado**: 
  - Se muestra solo el estudiante con ese carnet
  - Resultados se actualizan en tiempo real

#### TC-STU-007: Buscar estudiante por nombre
- **Precondiciones**: Estudiantes existentes
- **Pasos**:
  1. Ingresar nombre o apellido en búsqueda
  2. Ver resultados
- **Resultado Esperado**: 
  - Se muestran todos los estudiantes que coinciden
  - Búsqueda es case-insensitive
  - Búsqueda parcial funciona

#### TC-STU-008: Filtrar por carrera
- **Precondiciones**: Estudiantes de múltiples carreras
- **Pasos**:
  1. Seleccionar carrera en filtro
  2. Ver resultados
- **Resultado Esperado**: 
  - Solo se muestran estudiantes de la carrera seleccionada
  - Contador muestra cantidad correcta

#### TC-STU-009: Paginación de resultados
- **Precondiciones**: Más de 20 estudiantes
- **Pasos**:
  1. Navegar a lista de estudiantes
  2. Verificar paginación
  3. Cambiar de página
- **Resultado Esperado**: 
  - Se muestran 20 estudiantes por página
  - Botones de navegación funcionan
  - Número de página se actualiza

### 2.3 Edición y Actualización

#### TC-STU-010: Editar información de estudiante
- **Precondiciones**: Estudiante existente
- **Pasos**:
  1. Seleccionar estudiante
  2. Hacer clic en "Editar"
  3. Modificar información (email, teléfono, dirección)
  4. Guardar
- **Resultado Esperado**: 
  - Cambios se guardan correctamente
  - Carnet no se puede modificar
  - Se muestra mensaje de confirmación

#### TC-STU-011: Ver progreso académico
- **Precondiciones**: Estudiante con matrículas
- **Pasos**:
  1. Abrir perfil de estudiante
  2. Navegar a "Progreso Académico"
- **Resultado Esperado**: 
  - Se muestra porcentaje de cursos completados
  - Lista de cursos aprobados/pendientes
  - Información de cuatrimestres

### 2.4 Documentos de Estudiante

#### TC-STU-012: Cargar documento de estudiante
- **Precondiciones**: Estudiante creado
- **Pasos**:
  1. Abrir perfil de estudiante
  2. Ir a sección "Documentos"
  3. Seleccionar tipo de documento
  4. Cargar archivo PDF
  5. Guardar
- **Resultado Esperado**: 
  - Archivo se carga correctamente
  - Se muestra en la lista de documentos
  - Estado inicial: "Pendiente"

#### TC-STU-013: Validar tipos de documentos requeridos
- **Precondiciones**: Estudiante nuevo
- **Pasos**:
  1. Verificar lista de documentos requeridos
- **Resultado Esperado**: 
  - Certificado de bachillerato (original + 2 copias)
  - Acta de nacimiento (original + 2 copias)
  - CURP
  - Certificado médico
  - Fotografías (1 digital + 2 físicas)
  - Comprobante de domicilio

#### TC-STU-014: Cambiar estado de documento
- **Precondiciones**: Documento cargado
- **Pasos**:
  1. Seleccionar documento
  2. Cambiar estado (Pendiente → Revisado → Aprobado)
  3. Guardar
- **Resultado Esperado**: 
  - Estado se actualiza
  - Se registra en historial
  - Fecha y usuario se registran

---

## 3. Gestión Académica

### 3.1 Carreras y Pensums

#### TC-ACAD-001: Listar carreras
- **Precondiciones**: Carreras cargadas en el sistema
- **Pasos**:
  1. Navegar a "Académico" > "Carreras"
- **Resultado Esperado**: 
  - Se muestran las 6 carreras:
    1. Licenciatura en Pedagogía (101)
    2. Licenciatura en Criminología y Criminalística (102)
    3. Licenciatura en Administración de Empresas y Negocios (103)
    4. Licenciatura en Derecho (104)
    5. Licenciatura en Mercadotecnia Digital y Publicidad (105)
    6. Licenciatura en Contaduría Pública y Finanzas (106)

#### TC-ACAD-002: Ver pensum de carrera
- **Precondiciones**: Carrera seleccionada
- **Pasos**:
  1. Seleccionar carrera
  2. Hacer clic en "Ver Pensum"
- **Resultado Esperado**: 
  - Se muestra estructura completa del pensum
  - Cursos organizados por cuatrimestres
  - Códigos, nombres, créditos, prerrequisitos

#### TC-ACAD-003: Validar estructura de pensum
- **Precondiciones**: Pensum cargado
- **Pasos**:
  1. Verificar organización por cuatrimestres
  2. Verificar prerrequisitos
- **Resultado Esperado**: 
  - Cursos están en orden lógico
  - Prerrequisitos están correctamente definidos
  - Total de créditos es correcto

### 3.2 Matrícula de Estudiantes

#### TC-ACAD-004: Matricular estudiante en curso
- **Precondiciones**: Estudiante y curso existentes
- **Pasos**:
  1. Seleccionar estudiante
  2. Ir a "Matrícula"
  3. Seleccionar cuatrimestre
  4. Seleccionar cursos
  5. Guardar matrícula
- **Resultado Esperado**: 
  - Estudiante queda matriculado
  - Se valida que cumpla prerrequisitos
  - Estado inicial: "En curso"

#### TC-ACAD-005: Validar prerrequisitos
- **Precondiciones**: Curso con prerrequisitos
- **Pasos**:
  1. Intentar matricular estudiante en curso sin prerrequisitos
- **Resultado Esperado**: 
  - Mensaje de error: "No cumple con los prerrequisitos"
  - Matrícula no se completa

#### TC-ACAD-006: Matrícula en cuatrimestre completo
- **Precondiciones**: Estudiante activo
- **Pasos**:
  1. Matricular estudiante en todos los cursos de un cuatrimestre
- **Resultado Esperado**: 
  - Todos los cursos se matriculan correctamente
  - Se crea registro de cuatrimestre enrollment

### 3.3 Registro de Notas

#### TC-ACAD-007: Registrar nota final
- **Precondiciones**: Estudiante matriculado en curso
- **Pasos**:
  1. Navegar a "Matrículas"
  2. Seleccionar matrícula
  3. Ingresar nota final (0-100)
  4. Guardar
- **Resultado Esperado**: 
  - Nota se guarda correctamente
  - Estado cambia a "Aprobado" si nota >= 70
  - Estado cambia a "Reprobado" si nota < 70

#### TC-ACAD-008: Validar rango de notas
- **Precondiciones**: Formulario de nota abierto
- **Pasos**:
  1. Ingresar nota menor a 0
  2. Ingresar nota mayor a 100
  3. Ingresar nota válida
- **Resultado Esperado**: 
  - Mensajes de error para valores fuera de rango
  - Solo acepta valores 0-100

#### TC-ACAD-009: Actualizar nota existente
- **Precondiciones**: Nota ya registrada
- **Pasos**:
  1. Modificar nota
  2. Guardar
- **Resultado Esperado**: 
  - Nota se actualiza
  - Estado se recalcula automáticamente
  - Se registra en historial

### 3.4 Cierre de Pensum

#### TC-ACAD-010: Verificar cierre automático de pensum
- **Precondiciones**: Estudiante con todos los cursos aprobados
- **Pasos**:
  1. Verificar que estudiante completó todos los cursos
  2. Verificar estado de pensum
- **Resultado Esperado**: 
  - Pensum se marca como "Completado"
  - Estudiante puede solicitar título

### 3.5 Gestión de Tesis

#### TC-ACAD-011: Solicitar asesor de tesis
- **Precondiciones**: Estudiante con pensum casi completo
- **Pasos**:
  1. Navegar a "Tesis" en perfil de estudiante
  2. Hacer clic en "Solicitar Asesor"
  3. Completar formulario
  4. Enviar solicitud
- **Resultado Esperado**: 
  - Solicitud se crea
  - Estado: "Solicitud de asesor"
  - Se notifica al coordinador académico

#### TC-ACAD-012: Revisión de tema de tesis
- **Precondiciones**: Solicitud de asesor aprobada
- **Pasos**:
  1. Asignar asesor
  2. Estudiante envía tema
  3. Asesor revisa tema
- **Resultado Esperado**: 
  - Estado cambia a "Revisión de tema"
  - Se puede aprobar o rechazar tema

#### TC-ACAD-013: Aprobación de tema
- **Precondiciones**: Tema en revisión
- **Pasos**:
  1. Asesor aprueba tema
- **Resultado Esperado**: 
  - Estado cambia a "Tema aprobado"
  - Estudiante puede continuar con revisiones

#### TC-ACAD-014: Revisiones de tesis
- **Precondiciones**: Tema aprobado
- **Pasos**:
  1. Estudiante entrega primera revisión
  2. Asesor revisa y aprueba/rechaza
  3. Repetir para segunda y tercera revisión
- **Resultado Esperado**: 
  - Estados se actualizan correctamente
  - Se registra cada revisión
  - Progreso: Primera → Segunda → Tercera

#### TC-ACAD-015: Aprobación final de tesis
- **Precondiciones**: Tercera revisión aprobada
- **Pasos**:
  1. Asesor aprueba tesis final
- **Resultado Esperado**: 
  - Estado: "Aprobado"
  - Estudiante puede solicitar título universitario

---

## 4. Gestión de Pagos

### 4.1 Creación de Pagos

#### TC-PAY-001: Crear pago por transferencia
- **Precondiciones**: Estudiante activo
- **Pasos**:
  1. Navegar a "Pagos" > "Nuevo Pago"
  2. Seleccionar estudiante
  3. Seleccionar tipo de pago: "Transferencia"
  4. Ingresar monto
  5. Cargar comprobante
  6. Guardar
- **Resultado Esperado**: 
  - Pago se crea con estado "Pendiente"
  - Comprobante se almacena
  - Se muestra en lista de pagos pendientes

#### TC-PAY-002: Crear pago con tarjeta
- **Precondiciones**: Estudiante activo, Stripe configurado
- **Pasos**:
  1. Seleccionar tipo de pago: "Tarjeta"
  2. Ingresar datos de tarjeta (modo prueba)
  3. Confirmar pago
- **Resultado Esperado**: 
  - Pago se procesa a través de Stripe
  - Estado: "Aprobado" si es exitoso
  - Se genera recibo automáticamente

#### TC-PAY-003: Crear pago en efectivo
- **Precondiciones**: Usuario con permisos financieros
- **Pasos**:
  1. Seleccionar tipo de pago: "Efectivo"
  2. Ingresar monto y número de recibo
  3. Guardar
- **Resultado Esperado**: 
  - Pago se crea con estado "Aprobado"
  - Número de recibo se registra
  - Se genera recibo

### 4.2 Aprobación y Rechazo de Pagos

#### TC-PAY-004: Aprobar pago pendiente
- **Precondiciones**: Pago con transferencia pendiente
- **Pasos**:
  1. Abrir pago pendiente
  2. Revisar comprobante
  3. Hacer clic en "Aprobar"
- **Resultado Esperado**: 
  - Estado cambia a "Aprobado"
  - Estudiante queda al día
  - Se genera recibo

#### TC-PAY-005: Rechazar pago
- **Precondiciones**: Pago pendiente
- **Pasos**:
  1. Abrir pago
  2. Hacer clic en "Rechazar"
  3. Ingresar motivo de rechazo
  4. Confirmar
- **Resultado Esperado**: 
  - Estado cambia a "Rechazado"
  - Motivo se registra
  - Estudiante permanece pendiente

### 4.3 Consulta de Estado de Pagos

#### TC-PAY-006: Ver estado de pagos de estudiante
- **Precondiciones**: Estudiante con pagos
- **Pasos**:
  1. Abrir perfil de estudiante
  2. Ir a sección "Pagos"
- **Resultado Esperado**: 
  - Se muestra historial completo de pagos
  - Estado actual: "Al día" o "Pendiente"
  - Montos y fechas correctas

#### TC-PAY-007: Filtrar pagos por estado
- **Precondiciones**: Pagos con diferentes estados
- **Pasos**:
  1. Navegar a lista de pagos
  2. Filtrar por "Pendientes"
  3. Filtrar por "Aprobados"
- **Resultado Esperado**: 
  - Filtros funcionan correctamente
  - Contadores se actualizan

#### TC-PAY-008: Buscar pago por estudiante
- **Precondiciones**: Múltiples pagos
- **Pasos**:
  1. Buscar por nombre o carnet de estudiante
- **Resultado Esperado**: 
  - Se muestran solo pagos del estudiante
  - Búsqueda es eficiente

### 4.4 Generación de Recibos

#### TC-PAY-009: Generar recibo de pago
- **Precondiciones**: Pago aprobado
- **Pasos**:
  1. Abrir pago aprobado
  2. Hacer clic en "Generar Recibo"
  3. Descargar PDF
- **Resultado Esperado**: 
  - PDF se genera correctamente
  - Contiene información completa:
    - Datos del estudiante
    - Monto y fecha
    - Número de recibo
    - Método de pago

#### TC-PAY-010: Validar formato de recibo
- **Precondiciones**: Recibo generado
- **Pasos**:
  1. Abrir PDF del recibo
  2. Verificar información
- **Resultado Esperado**: 
  - Formato es profesional
  - Información es correcta y legible
  - Logo de la institución visible

### 4.5 Pagos Públicos (Portal de Estudiantes)

#### TC-PAY-011: Buscar estudiante por carnet (público)
- **Precondiciones**: Estudiante activo
- **Pasos**:
  1. Acceder a portal público de pagos
  2. Ingresar carnet
  3. Buscar
- **Resultado Esperado**: 
  - Se muestra información del estudiante
  - Se muestran pagos pendientes

#### TC-PAY-012: Procesar pago público con tarjeta
- **Precondiciones**: Estudiante encontrado
- **Pasos**:
  1. Seleccionar monto a pagar
  2. Ingresar datos de tarjeta
  3. Confirmar pago
- **Resultado Esperado**: 
  - Pago se procesa correctamente
  - Estado se actualiza automáticamente
  - Se envía confirmación

---

## 5. Sistema de Becas

### 5.1 Asignación de Becas

#### TC-SCH-001: Asignar beca completa
- **Precondiciones**: Estudiante activo, límite de becas no alcanzado
- **Pasos**:
  1. Navegar a "Becas" > "Nueva Beca"
  2. Seleccionar estudiante
  3. Seleccionar tipo: "Beca Completa"
  4. Guardar
- **Resultado Esperado**: 
  - Beca se asigna correctamente
  - Estudiante queda exento de pagos
  - Contador de becas se actualiza

#### TC-SCH-002: Asignar media beca
- **Precondiciones**: Estudiante activo
- **Pasos**:
  1. Seleccionar tipo: "Media Beca"
  2. Guardar
- **Resultado Esperado**: 
  - Estudiante paga 50% del monto
  - Beca se registra correctamente

#### TC-SCH-003: Validar límite de becas por facultad
- **Precondiciones**: Límite configurado (ej: 5 becas por facultad)
- **Pasos**:
  1. Intentar asignar beca cuando límite está alcanzado
- **Resultado Esperado**: 
  - Mensaje de error: "Límite de becas alcanzado para esta facultad"
  - Beca no se asigna

#### TC-SCH-004: Verificar control automático de límites
- **Precondiciones**: Sistema con límites configurados
- **Pasos**:
  1. Asignar becas hasta alcanzar límite
  2. Intentar asignar una más
- **Resultado Esperado**: 
  - Sistema previene asignación excedente
  - Mensaje de advertencia claro

### 5.2 Gestión de Becas

#### TC-SCH-005: Editar beca
- **Precondiciones**: Beca asignada
- **Pasos**:
  1. Seleccionar beca
  2. Modificar tipo (completa ↔ media)
  3. Guardar
- **Resultado Esperado**: 
  - Cambios se guardan
  - Descuentos se recalculan

#### TC-SCH-006: Cancelar beca
- **Precondiciones**: Beca activa
- **Pasos**:
  1. Seleccionar beca
  2. Cambiar estado a "Cancelada"
  3. Guardar
- **Resultado Esperado**: 
  - Beca se cancela
  - Estudiante vuelve a pagar monto completo
  - Contador se actualiza

#### TC-SCH-007: Listar becas activas
- **Precondiciones**: Múltiples becas
- **Pasos**:
  1. Navegar a lista de becas
  2. Filtrar por "Activas"
- **Resultado Esperado**: 
  - Se muestran solo becas activas
  - Información completa y correcta

---

## 6. Gestión de Documentos

### 6.1 Plantillas de Documentos

#### TC-DOC-001: Crear plantilla de documento
- **Precondiciones**: Usuario con permisos
- **Pasos**:
  1. Navegar a "Documentos" > "Plantillas"
  2. Crear nueva plantilla
  3. Definir campos variables
  4. Guardar
- **Resultado Esperado**: 
  - Plantilla se guarda
  - Se puede usar para generar documentos

#### TC-DOC-002: Generar documento desde plantilla
- **Precondiciones**: Plantilla creada, estudiante seleccionado
- **Pasos**:
  1. Seleccionar plantilla
  2. Seleccionar estudiante
  3. Generar documento
- **Resultado Esperado**: 
  - Documento se genera con datos del estudiante
  - Campos variables se rellenan correctamente
  - PDF se descarga

### 6.2 Documentos de Estudiante

#### TC-DOC-003: Ver historial de documentos
- **Precondiciones**: Estudiante con documentos
- **Pasos**:
  1. Abrir perfil de estudiante
  2. Ver sección "Documentos"
- **Resultado Esperado**: 
  - Lista completa de documentos
  - Estados y fechas correctas
  - Historial de cambios visible

---

## 7. Certificados

### 7.1 Certificados Académicos

#### TC-CERT-001: Generar certificado académico
- **Precondiciones**: Estudiante con cursos aprobados
- **Pasos**:
  1. Navegar a "Certificados" > "Certificado Académico"
  2. Seleccionar estudiante
  3. Generar certificado
- **Resultado Esperado**: 
  - PDF se genera con información académica
  - Incluye cursos aprobados, notas, créditos
  - Formato oficial

#### TC-CERT-002: Validar información del certificado
- **Precondiciones**: Certificado generado
- **Pasos**:
  1. Revisar contenido del certificado
- **Resultado Esperado**: 
  - Datos del estudiante correctos
  - Carrera y pensum correctos
  - Notas y créditos exactos
  - Fecha de emisión presente

### 7.2 Certificados de Cursos

#### TC-CERT-003: Generar certificado de curso
- **Precondiciones**: Estudiante con curso aprobado
- **Pasos**:
  1. Seleccionar curso específico
  2. Generar certificado
- **Resultado Esperado**: 
  - Certificado del curso se genera
  - Incluye información del curso y nota

### 7.3 Títulos Universitarios

#### TC-CERT-004: Solicitar título universitario
- **Precondiciones**: Estudiante con pensum completo y tesis aprobada
- **Pasos**:
  1. Navegar a "Títulos" > "Nuevo Título"
  2. Seleccionar estudiante
  3. Verificar requisitos
  4. Generar solicitud
- **Resultado Esperado**: 
  - Solicitud se crea
  - Se valida que cumpla todos los requisitos
  - Estado: "En proceso"

#### TC-CERT-005: Aprobar título universitario
- **Precondiciones**: Solicitud de título creada
- **Pasos**:
  1. Revisar solicitud
  2. Aprobar título
- **Resultado Esperado**: 
  - Estado cambia a "Aprobado"
  - Se genera documento oficial
  - Se registra fecha de emisión

---

## 8. Auditoría

### 8.1 Registro de Actividades

#### TC-AUDIT-001: Verificar registro de acciones
- **Precondiciones**: Realizar acciones en el sistema
- **Pasos**:
  1. Crear/editar/eliminar registros
  2. Navegar a "Auditoría" > "Logs"
- **Resultado Esperado**: 
  - Todas las acciones se registran
  - Incluye: usuario, acción, fecha, modelo afectado
  - Información detallada disponible

#### TC-AUDIT-002: Filtrar logs por usuario
- **Precondiciones**: Logs de múltiples usuarios
- **Pasos**:
  1. Filtrar por usuario específico
- **Resultado Esperado**: 
  - Solo se muestran acciones de ese usuario
  - Filtro funciona correctamente

#### TC-AUDIT-003: Filtrar logs por fecha
- **Precondiciones**: Logs de diferentes fechas
- **Pasos**:
  1. Seleccionar rango de fechas
  2. Ver resultados
- **Resultado Esperado**: 
  - Solo se muestran logs del rango seleccionado
  - Filtro por fecha funciona

#### TC-AUDIT-004: Exportar logs de auditoría
- **Precondiciones**: Logs existentes
- **Pasos**:
  1. Seleccionar logs
  2. Exportar a CSV/Excel
- **Resultado Esperado**: 
  - Archivo se genera correctamente
  - Información completa y formateada

---

## 9. Exportación de Datos

### 9.1 Exportación de Estudiantes

#### TC-EXP-001: Exportar lista de estudiantes
- **Precondiciones**: Estudiantes en el sistema
- **Pasos**:
  1. Navegar a "Exportaciones"
  2. Seleccionar "Estudiantes"
  3. Aplicar filtros (opcional)
  4. Exportar a CSV/Excel
- **Resultado Esperado**: 
  - Archivo se genera
  - Incluye todos los campos relevantes
  - Formato es correcto y legible

#### TC-EXP-002: Exportar con filtros
- **Precondiciones**: Estudiantes de múltiples carreras
- **Pasos**:
  1. Filtrar por carrera
  2. Exportar
- **Resultado Esperado**: 
  - Solo se exportan estudiantes del filtro aplicado
  - Filtros se respetan

### 9.2 Exportación de Pagos

#### TC-EXP-003: Exportar reporte de pagos
- **Precondiciones**: Pagos registrados
- **Pasos**:
  1. Seleccionar "Pagos"
  2. Definir rango de fechas
  3. Exportar
- **Resultado Esperado**: 
  - Reporte incluye todos los pagos del período
  - Totales y subtotales correctos
  - Formato adecuado para análisis

### 9.3 Exportación Académica

#### TC-EXP-004: Exportar matrículas
- **Precondiciones**: Matrículas existentes
- **Pasos**:
  1. Exportar matrículas por cuatrimestre
- **Resultado Esperado**: 
  - Datos completos de matrículas
  - Información de estudiantes y cursos

---

## 10. Interfaz de Usuario

### 10.1 Navegación

#### TC-UI-001: Navegación entre módulos
- **Precondiciones**: Usuario autenticado
- **Pasos**:
  1. Navegar entre diferentes secciones del menú
- **Resultado Esperado**: 
  - Navegación es fluida
  - Menú se mantiene visible
  - URLs se actualizan correctamente

#### TC-UI-002: Responsive design
- **Precondiciones**: Acceso desde diferentes dispositivos
- **Pasos**:
  1. Abrir en desktop (1920x1080)
  2. Abrir en tablet (768x1024)
  3. Abrir en móvil (375x667)
- **Resultado Esperado**: 
  - Interfaz se adapta correctamente
  - Elementos son accesibles
  - No hay overflow horizontal

#### TC-UI-003: Mensajes de confirmación
- **Precondiciones**: Realizar acciones
- **Pasos**:
  1. Crear/editar/eliminar registros
- **Resultado Esperado**: 
  - Mensajes de éxito/error se muestran
  - Mensajes son claros y descriptivos
  - Desaparecen después de unos segundos

### 10.2 Formularios

#### TC-UI-004: Validación en tiempo real
- **Precondiciones**: Formulario abierto
- **Pasos**:
  1. Ingresar datos inválidos
  2. Ver validaciones
- **Resultado Esperado**: 
  - Errores se muestran inmediatamente
  - Campos se resaltan
  - Mensajes son específicos

#### TC-UI-005: Autocompletado y sugerencias
- **Precondiciones**: Campos con opciones
- **Pasos**:
  1. Escribir en campos de búsqueda/selección
- **Resultado Esperado**: 
  - Sugerencias aparecen
  - Búsqueda es eficiente
  - Resultados relevantes

### 10.3 Tablas y Listas

#### TC-UI-006: Ordenamiento de columnas
- **Precondiciones**: Tabla con datos
- **Pasos**:
  1. Hacer clic en encabezados de columna
- **Resultado Esperado**: 
  - Datos se ordenan ascendente/descendente
  - Indicador visual de ordenamiento
  - Funciona en todas las columnas ordenables

#### TC-UI-007: Búsqueda en tiempo real
- **Precondiciones**: Lista con múltiples elementos
- **Pasos**:
  1. Escribir en campo de búsqueda
- **Resultado Esperado**: 
  - Resultados se filtran en tiempo real
  - Búsqueda es rápida
  - No requiere presionar Enter

---

## 11. Integración y Rendimiento

### 11.1 Integración con Stripe

#### TC-INT-001: Webhook de Stripe
- **Precondiciones**: Pago procesado en Stripe
- **Pasos**:
  1. Procesar pago con tarjeta
  2. Verificar webhook recibido
- **Resultado Esperado**: 
  - Webhook se recibe correctamente
  - Estado de pago se actualiza automáticamente
  - No hay duplicados

#### TC-INT-002: Manejo de errores de Stripe
- **Precondiciones**: Configuración de Stripe
- **Pasos**:
  1. Simular error de tarjeta rechazada
  2. Verificar manejo de error
- **Resultado Esperado**: 
  - Error se maneja correctamente
  - Mensaje claro al usuario
  - Pago no se registra como exitoso

### 11.2 Rendimiento

#### TC-PERF-001: Carga de listas grandes
- **Precondiciones**: Más de 1000 estudiantes
- **Pasos**:
  1. Cargar lista de estudiantes
  2. Medir tiempo de carga
- **Resultado Esperado**: 
  - Página carga en menos de 3 segundos
  - Paginación funciona correctamente
  - No hay bloqueos de UI

#### TC-PERF-002: Búsqueda eficiente
- **Precondiciones**: Base de datos grande
- **Pasos**:
  1. Realizar búsquedas frecuentes
- **Resultado Esperado**: 
  - Resultados aparecen en menos de 1 segundo
  - No hay timeouts
  - Búsqueda es optimizada

#### TC-PERF-003: Generación de PDFs
- **Precondiciones**: Documentos a generar
- **Pasos**:
  1. Generar múltiples PDFs
- **Resultado Esperado**: 
  - PDFs se generan en tiempo razonable (< 5 segundos)
  - No hay errores de memoria
  - Calidad de PDF es buena

### 11.3 Seguridad

#### TC-SEC-001: Validación de permisos en API
- **Precondiciones**: Usuario con permisos limitados
- **Pasos**:
  1. Intentar acceder a endpoints sin permisos
  2. Verificar respuestas
- **Resultado Esperado**: 
  - Endpoints retornan 403 Forbidden
  - Mensajes de error apropiados
  - No se exponen datos sensibles

#### TC-SEC-002: Protección CSRF
- **Precondiciones**: Formularios en el sistema
- **Pasos**:
  1. Verificar tokens CSRF
- **Resultado Esperado**: 
  - Tokens se generan correctamente
  - Formularios sin token son rechazados

#### TC-SEC-003: Validación de entrada
- **Precondiciones**: Formularios con campos
- **Pasos**:
  1. Intentar inyección SQL/XSS
  2. Enviar datos maliciosos
- **Resultado Esperado**: 
  - Entradas maliciosas son rechazadas
  - Datos se sanitizan
  - No hay vulnerabilidades explotables

---

## Checklist de Pruebas por Módulo

### Módulo de Autenticación
- [ ] TC-AUTH-001: Login exitoso
- [ ] TC-AUTH-002: Login con credenciales inválidas
- [ ] TC-AUTH-003: Refresh token
- [ ] TC-AUTH-004: Logout
- [ ] TC-USER-001: Crear usuario
- [ ] TC-USER-002: Editar usuario
- [ ] TC-USER-003: Desactivar usuario
- [ ] TC-USER-004: Validar permisos por rol

### Módulo de Estudiantes
- [ ] TC-STU-001: Crear nuevo estudiante
- [ ] TC-STU-002: Validar formato de carnet
- [ ] TC-STU-003: Validar campos obligatorios
- [ ] TC-STU-004: Validar formato de CURP
- [ ] TC-STU-005: Validar formato de teléfono
- [ ] TC-STU-006: Buscar estudiante por carnet
- [ ] TC-STU-007: Buscar estudiante por nombre
- [ ] TC-STU-008: Filtrar por carrera
- [ ] TC-STU-009: Paginación de resultados
- [ ] TC-STU-010: Editar información de estudiante
- [ ] TC-STU-011: Ver progreso académico
- [ ] TC-STU-012: Cargar documento de estudiante
- [ ] TC-STU-013: Validar tipos de documentos requeridos
- [ ] TC-STU-014: Cambiar estado de documento

### Módulo Académico
- [ ] TC-ACAD-001: Listar carreras
- [ ] TC-ACAD-002: Ver pensum de carrera
- [ ] TC-ACAD-003: Validar estructura de pensum
- [ ] TC-ACAD-004: Matricular estudiante en curso
- [ ] TC-ACAD-005: Validar prerrequisitos
- [ ] TC-ACAD-006: Matrícula en cuatrimestre completo
- [ ] TC-ACAD-007: Registrar nota final
- [ ] TC-ACAD-008: Validar rango de notas
- [ ] TC-ACAD-009: Actualizar nota existente
- [ ] TC-ACAD-010: Verificar cierre automático de pensum
- [ ] TC-ACAD-011: Solicitar asesor de tesis
- [ ] TC-ACAD-012: Revisión de tema de tesis
- [ ] TC-ACAD-013: Aprobación de tema
- [ ] TC-ACAD-014: Revisiones de tesis
- [ ] TC-ACAD-015: Aprobación final de tesis

### Módulo de Pagos
- [ ] TC-PAY-001: Crear pago por transferencia
- [ ] TC-PAY-002: Crear pago con tarjeta
- [ ] TC-PAY-003: Crear pago en efectivo
- [ ] TC-PAY-004: Aprobar pago pendiente
- [ ] TC-PAY-005: Rechazar pago
- [ ] TC-PAY-006: Ver estado de pagos de estudiante
- [ ] TC-PAY-007: Filtrar pagos por estado
- [ ] TC-PAY-008: Buscar pago por estudiante
- [ ] TC-PAY-009: Generar recibo de pago
- [ ] TC-PAY-010: Validar formato de recibo
- [ ] TC-PAY-011: Buscar estudiante por carnet (público)
- [ ] TC-PAY-012: Procesar pago público con tarjeta

### Módulo de Becas
- [ ] TC-SCH-001: Asignar beca completa
- [ ] TC-SCH-002: Asignar media beca
- [ ] TC-SCH-003: Validar límite de becas por facultad
- [ ] TC-SCH-004: Verificar control automático de límites
- [ ] TC-SCH-005: Editar beca
- [ ] TC-SCH-006: Cancelar beca
- [ ] TC-SCH-007: Listar becas activas

### Módulo de Documentos
- [ ] TC-DOC-001: Crear plantilla de documento
- [ ] TC-DOC-002: Generar documento desde plantilla
- [ ] TC-DOC-003: Ver historial de documentos

### Módulo de Certificados
- [ ] TC-CERT-001: Generar certificado académico
- [ ] TC-CERT-002: Validar información del certificado
- [ ] TC-CERT-003: Generar certificado de curso
- [ ] TC-CERT-004: Solicitar título universitario
- [ ] TC-CERT-005: Aprobar título universitario

### Módulo de Auditoría
- [ ] TC-AUDIT-001: Verificar registro de acciones
- [ ] TC-AUDIT-002: Filtrar logs por usuario
- [ ] TC-AUDIT-003: Filtrar logs por fecha
- [ ] TC-AUDIT-004: Exportar logs de auditoría

### Módulo de Exportación
- [ ] TC-EXP-001: Exportar lista de estudiantes
- [ ] TC-EXP-002: Exportar con filtros
- [ ] TC-EXP-003: Exportar reporte de pagos
- [ ] TC-EXP-004: Exportar matrículas

### Interfaz de Usuario
- [ ] TC-UI-001: Navegación entre módulos
- [ ] TC-UI-002: Responsive design
- [ ] TC-UI-003: Mensajes de confirmación
- [ ] TC-UI-004: Validación en tiempo real
- [ ] TC-UI-005: Autocompletado y sugerencias
- [ ] TC-UI-006: Ordenamiento de columnas
- [ ] TC-UI-007: Búsqueda en tiempo real

### Integración y Rendimiento
- [ ] TC-INT-001: Webhook de Stripe
- [ ] TC-INT-002: Manejo de errores de Stripe
- [ ] TC-PERF-001: Carga de listas grandes
- [ ] TC-PERF-002: Búsqueda eficiente
- [ ] TC-PERF-003: Generación de PDFs
- [ ] TC-SEC-001: Validación de permisos en API
- [ ] TC-SEC-002: Protección CSRF
- [ ] TC-SEC-003: Validación de entrada

---

## Notas para QA

### Datos de Prueba Recomendados

1. **Usuarios de prueba con diferentes roles:**
   - SUPER_ADMIN: Acceso completo
   - ADMIN: Gestión general
   - SECRETARY: Gestión de estudiantes
   - ACADEMIC_COORDINATOR: Gestión académica
   - FINANCIAL: Gestión de pagos
   - VIEWER: Solo consulta

2. **Estudiantes de prueba:**
   - Al menos 5 estudiantes por carrera
   - Estudiantes en diferentes estados (nuevos, activos, graduados)
   - Estudiantes con y sin becas
   - Estudiantes con pagos pendientes y al día

3. **Datos académicos:**
   - Todas las 6 carreras cargadas
   - Pensums completos
   - Cursos con prerrequisitos
   - Matrículas en diferentes estados

### Ambiente de Pruebas

- **Backend**: `http://localhost:8000` (desarrollo)
- **Frontend**: `http://localhost:3000` (desarrollo)
- **API Docs**: `http://localhost:8000/swagger/`
- **Base de datos**: SQLite para pruebas rápidas, MySQL para pruebas completas

### Herramientas Recomendadas

- **Postman/Insomnia**: Para pruebas de API
- **Browser DevTools**: Para debugging de frontend
- **Selenium/Cypress**: Para pruebas automatizadas (opcional)
- **Stripe Test Mode**: Para pruebas de pagos

### Reporte de Bugs

Al encontrar un bug, documentar:
1. **ID del Test Case**: TC-XXX-XXX
2. **Descripción**: Qué se intentó hacer
3. **Resultado Esperado**: Qué debería pasar
4. **Resultado Actual**: Qué pasó realmente
5. **Pasos para Reproducir**: Pasos detallados
6. **Screenshots/Logs**: Evidencia
7. **Severidad**: Crítico, Alto, Medio, Bajo
8. **Prioridad**: P1, P2, P3, P4

---

## Conclusión

Este plan de pruebas cubre todas las funcionalidades principales del sistema AdminCUSC. Se recomienda ejecutar las pruebas en el orden sugerido, comenzando por autenticación y usuarios, luego estudiantes, y continuando con los demás módulos.

**Última actualización**: [Fecha]
**Versión del sistema**: [Versión]
**Responsable QA**: [Nombre]
