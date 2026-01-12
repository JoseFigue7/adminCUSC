# Flujo Académico - Sistema de Inscripciones a Cuatrimestres

## Resumen del Flujo

Este documento describe el flujo académico implementado para el sistema de inscripciones a cuatrimestres.

## Flujo Principal

### 1. Inscripción a Cuatrimestre (CuatrimestreEnrollment)

**Reglas de Negocio:**
- Un estudiante puede tener múltiples inscripciones a cuatrimestres (historial)
- **IMPORTANTE**: Un estudiante solo puede tener **UNA inscripción con status='EN_CURSO' a la vez**
- Hasta que un cuatrimestre no esté **FINALIZADO**, no se puede inscribir a otro

**Estados de CuatrimestreEnrollment:**
- `PENDIENTE`: Inscripción creada pero no activa
- `INSCRITO`: Inscripción activa, lista para asignar cursos
- `EN_CURSO`: Cuatrimestre en desarrollo (solo puede haber uno a la vez)
- `FINALIZADO`: Cuatrimestre completado, notas subidas
- `CANCELADO`: Inscripción cancelada

### 2. Asignación de Cursos (CourseEnrollment)

**Reglas de Negocio:**
- Los cursos se asignan dentro de un `CuatrimestreEnrollment` específico
- **NO se puede inscribir a un curso que ya fue APROBADO** (regla importante)
- Un estudiante solo puede estar inscrito una vez en el mismo curso dentro del mismo cuatrimestre
- Los cursos deben pertenecer al cuatrimestre seleccionado

**Estados de CourseEnrollment:**
- `MATRICULADO`: Curso asignado, listo para comenzar
- `EN_CURSO`: Curso en desarrollo
- `APROBADO`: Curso aprobado (nota >= 70)
- `REPROBADO`: Curso reprobado (nota < 70)
- `RETIRADO`: Estudiante se retiró del curso

## Flujo Completo

```
1. Inscribir estudiante a un cuatrimestre
   └─> Crear CuatrimestreEnrollment (status='INSCRITO')
   
2. Asignar cursos al cuatrimestre
   └─> Crear CourseEnrollment (vinculado al CuatrimestreEnrollment)
   └─> Validar: curso no aprobado previamente
   └─> Validar: curso pertenece al cuatrimestre
   
3. Iniciar cuatrimestre
   └─> Cambiar CuatrimestreEnrollment status a 'EN_CURSO'
   └─> Validar: no hay otro EN_CURSO activo
   
4. Durante el cuatrimestre
   └─> Registrar asistencia, actividades, etc.
   └─> Subir notas parciales
   
5. Finalizar cuatrimestre
   └─> Subir notas finales de todos los cursos
   └─> Cambiar CourseEnrollment status a APROBADO/REPROBADO
   └─> Cambiar CuatrimestreEnrollment status a 'FINALIZADO'
   
6. Inscribirse al siguiente cuatrimestre
   └─> Solo posible si no hay otro EN_CURSO
   └─> Repetir desde paso 1
```

## Validaciones Implementadas

### CuatrimestreEnrollment

1. **Validación de carrera**: El cuatrimestre debe pertenecer a la carrera del estudiante
2. **Validación de año académico**: Debe estar entre 1900 y 9999
3. **Validación de unicidad EN_CURSO**: Un estudiante solo puede tener un cuatrimestre EN_CURSO a la vez
4. **Validación de unicidad**: Un estudiante solo puede inscribirse una vez al mismo cuatrimestre en el mismo año

### CourseEnrollment

1. **Validación de carrera**: El curso debe pertenecer a la carrera del estudiante
2. **Validación de cuatrimestre**: Si hay cuatrimestre_enrollment, el curso debe pertenecer a ese cuatrimestre
3. **Validación de cursos aprobados**: NO se puede inscribir a un curso que ya fue APROBADO
4. **Validación de unicidad**: Un estudiante solo puede estar inscrito una vez en el mismo curso dentro del mismo cuatrimestre
5. **Validación de nota final**: Debe estar entre 0 y 100

## Endpoints API

### CuatrimestreEnrollment

- `GET /api/academics/cuatrimestre-enrollments/` - Listar inscripciones
- `GET /api/academics/cuatrimestre-enrollments/?student_id={id}` - Inscripciones de un estudiante
- `POST /api/academics/cuatrimestre-enrollments/` - Crear inscripción
- `POST /api/academics/cuatrimestre-enrollments/{id}/enroll_courses/` - Asignar cursos
- `GET /api/academics/cuatrimestre-enrollments/{id}/courses/` - Ver cursos del cuatrimestre
- `PATCH /api/academics/cuatrimestre-enrollments/{id}/` - Actualizar inscripción

### CourseEnrollment

- `GET /api/academics/enrollments/?student_id={id}` - Cursos de un estudiante
- `GET /api/academics/enrollments/?cuatrimestre_enrollment_id={id}` - Cursos de un cuatrimestre
- `POST /api/academics/enrollments/` - Crear inscripción a curso
- `PATCH /api/academics/enrollments/{id}/update_grade/` - Actualizar nota

## Notas Importantes

1. **Un cuatrimestre EN_CURSO bloquea nuevas inscripciones**: Esto asegura que el estudiante complete un período antes de comenzar otro

2. **Los cursos aprobados no se pueden repetir**: Una vez que un estudiante aprueba un curso, no puede volver a inscribirse

3. **El sistema mantiene historial**: Todas las inscripciones se guardan, permitiendo ver el historial completo del estudiante

4. **Compatibilidad hacia atrás**: El sistema permite CourseEnrollment sin cuatrimestre_enrollment para mantener compatibilidad con datos existentes


