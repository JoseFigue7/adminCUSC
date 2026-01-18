# Sistema de Auditoría Completo

## Descripción

Sistema de auditoría global que registra todas las acciones realizadas en el sistema para cumplir con requisitos de universidad y SEP (Secretaría de Educación Pública).

## Características

- ✅ Registro automático de CREATE, UPDATE, DELETE
- ✅ Registro manual de acciones personalizadas (APPROVE, REJECT)
- ✅ Captura de usuario, IP, user agent
- ✅ Snapshot de datos (JSON)
- ✅ Comparación de cambios (para UPDATE)
- ✅ Configurable (activar/desactivar)
- ✅ Optimizado para performance
- ✅ API REST para consultas
- ✅ Admin de Django integrado

## Instalación

### 1. La app ya está instalada

La app `audit` ya está incluida en `INSTALLED_APPS` y el middleware configurado en `settings.py`.

### 2. Crear migraciones

```bash
cd backend
source venv/bin/activate  # o tu entorno virtual
python manage.py makemigrations audit
python manage.py migrate audit
```

### 3. Configuración (settings.py)

```python
# Auditoría activada por defecto
AUDIT_ENABLED = True

# Auditar todos los modelos (None = todos excepto AuditLog)
AUDIT_MODELS = None

# O auditar solo modelos específicos:
# AUDIT_MODELS = ['students.Student', 'payments.Payment', ...]

# Para desactivar:
# AUDIT_ENABLED = False
```

## Modelo AuditLog

### Campos

- **id**: UUID del registro
- **user**: Usuario que realizó la acción (ForeignKey, puede ser NULL)
- **username**: Nombre de usuario (cached, para casos donde se elimina el usuario)
- **action**: Acción realizada (CREATE, UPDATE, DELETE, APPROVE, REJECT, VIEW, EXPORT)
- **content_type**: Tipo de contenido (modelo afectado)
- **object_id**: ID del registro afectado
- **model_name**: Nombre del modelo (cached: app_label.ModelName)
- **data_snapshot**: Snapshot de datos actuales (JSON)
- **previous_data**: Datos anteriores (para UPDATE) (JSON)
- **changes**: Cambios realizados (JSON: {campo: {old, new}})
- **ip_address**: Dirección IP
- **user_agent**: User Agent del navegador
- **metadata**: Metadatos adicionales (JSON)
- **timestamp**: Fecha y hora de la acción

### Acciones Disponibles

```python
AuditAction.CREATE   # Crear
AuditAction.UPDATE   # Actualizar
AuditAction.DELETE   # Eliminar
AuditAction.APPROVE  # Aprobar
AuditAction.REJECT   # Rechazar
AuditAction.VIEW     # Consultar
AuditAction.EXPORT   # Exportar
```

## Uso

### 1. Auditoría Automática (CREATE, UPDATE, DELETE)

Las señales de Django capturan automáticamente estas acciones:

```python
from students.models import Student

# CREATE - Se registra automáticamente
student = Student.objects.create(
    student_id='123456',
    first_name='Juan',
    last_name='Pérez'
)

# UPDATE - Se registra automáticamente con cambios
student.first_name = 'Juan Carlos'
student.save()

# DELETE - Se registra automáticamente
student.delete()
```

### 2. Acciones Personalizadas (APPROVE, REJECT)

#### Opción A: Usar función helper

```python
from audit.helpers import log_audit_action
from audit.models import AuditAction
from payments.models import Payment

def approve_payment(request, payment_id):
    payment = Payment.objects.get(pk=payment_id)
    payment.status = 'APPROVED'
    payment.save()
    
    log_audit_action(
        instance=payment,
        action=AuditAction.APPROVE,
        metadata={'comment': 'Pago aprobado por coordinador'}
    )
```

#### Opción B: Usar decorador

```python
from audit.decorators import audit_action
from audit.models import AuditAction
from payments.models import Payment

@api_view(['POST'])
@audit_action(AuditAction.APPROVE, model_class=Payment, object_id_param='pk')
def approve_payment_api(request, pk):
    payment = Payment.objects.get(pk=pk)
    payment.status = 'APPROVED'
    payment.save()
    return Response({'status': 'approved'})
```

### 3. Agregar Metadatos Personalizados

```python
from students.models import Student

student = Student.objects.get(pk='some-id')
student.status = 'ENROLLED'
student._audit_metadata = {
    'comment': 'Estudiante matriculado después de aprobar documentos',
    'enrollment_period': '2024-1',
    'approved_by': 'coordinador@example.com'
}
student.save()
```

### 4. Consultar Registros de Auditoría

#### Via Django ORM

```python
from audit.models import AuditLog, AuditAction
from django.contrib.contenttypes.models import ContentType

# Todos los registros de un usuario
logs = AuditLog.objects.filter(user=request.user)

# Registros de un modelo específico
logs = AuditLog.objects.filter(model_name='students.Student')

# Registros de un objeto específico
from students.models import Student
student = Student.objects.get(pk='some-id')
logs = AuditLog.objects.filter(
    content_type=ContentType.objects.get_for_model(Student),
    object_id=str(student.pk)
)

# Registros de una acción específica
approved = AuditLog.objects.filter(action=AuditAction.APPROVE)

# Registros en un rango de fechas
from django.utils import timezone
from datetime import timedelta
last_week = timezone.now() - timedelta(days=7)
recent_logs = AuditLog.objects.filter(timestamp__gte=last_week)

# Ver cambios en UPDATE
update_logs = AuditLog.objects.filter(action=AuditAction.UPDATE)
for log in update_logs:
    changes = log.get_formatted_changes()
    print(f"Cambios: {changes}")
```

#### Via API REST

```bash
# Listar todos los registros (solo admins)
GET /api/audit/audit-logs/

# Filtrar por acción
GET /api/audit/audit-logs/?action=APPROVE

# Filtrar por modelo
GET /api/audit/audit-logs/?model_name=students.Student

# Filtrar por usuario
GET /api/audit/audit-logs/?username=admin

# Filtrar por rango de fechas
GET /api/audit/audit-logs/?date_from=2024-01-01&date_to=2024-12-31

# Buscar
GET /api/audit/audit-logs/?search=juan

# Ordenar
GET /api/audit/audit-logs/?ordering=-timestamp
```

### 5. Admin de Django

El modelo `AuditLog` está registrado en el admin de Django con:

- Vista de lista con filtros (acción, fecha, modelo, usuario)
- Vista detallada con todos los datos formateados
- Búsqueda por usuario, modelo, ID de objeto, IP
- Solo lectura (no se pueden crear/editar manualmente)
- Solo superadmins pueden eliminar registros

Acceso: `/admin/audit/auditlog/`

## Ejemplos Avanzados

### Ejemplo: Aprobar/Rechazar en ViewSet

```python
from rest_framework import viewsets
from audit.helpers import log_audit_action
from audit.models import AuditAction

class PaymentViewSet(viewsets.ModelViewSet):
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        
        if 'status' in request.data:
            if request.data['status'] == 'APPROVED':
                log_audit_action(
                    instance=instance,
                    action=AuditAction.APPROVE,
                    metadata={'changed_by': request.user.username}
                )
            elif request.data['status'] == 'REJECTED':
                log_audit_action(
                    instance=instance,
                    action=AuditAction.REJECT,
                    metadata={
                        'changed_by': request.user.username,
                        'reason': request.data.get('rejection_reason', '')
                    }
                )
        return response
```

### Ejemplo: Historial Completo de un Objeto

```python
def get_object_audit_history(instance):
    from django.contrib.contenttypes.models import ContentType
    
    content_type = ContentType.objects.get_for_model(instance.__class__)
    logs = AuditLog.objects.filter(
        content_type=content_type,
        object_id=str(instance.pk)
    ).order_by('-timestamp')
    
    return logs

# Uso
student = Student.objects.get(pk='some-id')
history = get_object_audit_history(student)
for log in history:
    print(f"{log.timestamp}: {log.get_action_display()} por {log.username}")
```

### Ejemplo: Reporte de Auditoría

```python
def generate_audit_report(start_date, end_date, model_name=None):
    from django.contrib.contenttypes.models import ContentType
    
    queryset = AuditLog.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    if model_name:
        queryset = queryset.filter(model_name=model_name)
    
    report = {
        'period': f"{start_date} - {end_date}",
        'total_actions': queryset.count(),
        'by_action': {},
        'by_model': {},
        'by_user': {}
    }
    
    for action_code, action_display in AuditAction.choices:
        count = queryset.filter(action=action_code).count()
        if count > 0:
            report['by_action'][action_display] = count
    
    # ... más agrupaciones
    
    return report
```

## Configuración y Optimización

### Performance

- El sistema usa índices en campos clave (timestamp, user, action, model_name)
- Las señales son asíncronas y no bloquean el flujo principal
- Los errores en auditoría no afectan las operaciones principales
- Los snapshots de datos son mínimos (excluyen campos como password, created_at, updated_at)

### Desactivar Auditoría

#### Globalmente

```python
# settings.py
AUDIT_ENABLED = False
```

#### Para Modelos Específicos

```python
# settings.py
AUDIT_MODELS = [
    'students.Student',
    'payments.Payment',
    # ... solo estos modelos serán auditados
]
```

#### Temporalmente en Código

```python
from audit.utils import is_audit_enabled

# La función is_audit_enabled() siempre respeta la configuración
if is_audit_enabled():
    log_audit_action(...)
```

## Estructura de Archivos

```
backend/audit/
├── __init__.py          # Configuración de la app
├── apps.py              # Configuración de la app Django
├── models.py            # Modelo AuditLog
├── signals.py           # Señales para CREATE/UPDATE/DELETE
├── middleware.py        # Middleware para capturar request
├── utils.py             # Utilidades (snapshots, comparaciones)
├── helpers.py           # Funciones helper para acciones personalizadas
├── decorators.py        # Decoradores para acciones personalizadas
├── admin.py             # Admin de Django
├── serializers.py       # Serializers para API REST
├── views.py             # Views para API REST
├── urls.py              # URLs de la API
├── tests.py             # Tests unitarios
└── examples.py          # Ejemplos de uso
```

## Consideraciones Importantes

1. **Backup**: Los registros de auditoría deben incluirse en los backups regulares
2. **Retención**: Considera políticas de retención de datos (ej: 7 años para SEP)
3. **Performance**: En sistemas grandes, considera particionar la tabla o usar archivo
4. **Privacidad**: Los datos sensibles deben manejarse con cuidado (ej: passwords nunca se incluyen)
5. **Integridad**: Los registros no deben modificarse ni eliminarse excepto por políticas de retención

## Migraciones

```bash
# Crear migraciones
python manage.py makemigrations audit

# Aplicar migraciones
python manage.py migrate audit

# Ver estado de migraciones
python manage.py showmigrations audit
```

## Soporte

Para más información o problemas, consulta:
- `backend/audit/examples.py` - Ejemplos completos
- `backend/audit/tests.py` - Tests unitarios
- Admin de Django en `/admin/audit/auditlog/`
- API REST en `/api/audit/audit-logs/`
