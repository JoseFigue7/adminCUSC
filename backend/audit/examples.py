"""
Ejemplos de uso del sistema de auditoría

Este archivo contiene ejemplos de cómo usar el sistema de auditoría
en diferentes escenarios.
"""

from audit.models import AuditLog, AuditAction
from audit.helpers import log_audit_action
from audit.decorators import audit_action
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


# ============================================================================
# Ejemplo 1: Auditoría automática con señales (CREATE, UPDATE, DELETE)
# ============================================================================
# Las acciones CREATE, UPDATE y DELETE se registran automáticamente
# cuando guardas o eliminas instancias de modelos.

"""
# Ejemplo en una vista o método:
from students.models import Student
from academics.models import Course

# CREATE - Se registra automáticamente
student = Student.objects.create(
    student_id='123456',
    first_name='Juan',
    last_name='Pérez',
    email='juan@example.com'
)
# Esto automáticamente crea un registro de auditoría con action=CREATE

# UPDATE - Se registra automáticamente
student.first_name = 'Juan Carlos'
student.save()
# Esto automáticamente crea un registro de auditoría con action=UPDATE
# incluyendo los cambios realizados

# DELETE - Se registra automáticamente
student.delete()
# Esto automáticamente crea un registro de auditoría con action=DELETE
"""


# ============================================================================
# Ejemplo 2: Registrar acciones personalizadas con log_audit_action
# ============================================================================

"""
# En una vista o método que aprueba/rechaza algo:
from payments.models import Payment
from audit.helpers import log_audit_action
from audit.models import AuditAction

def approve_payment(request, payment_id):
    payment = Payment.objects.get(pk=payment_id)
    payment.status = 'APPROVED'
    payment.approved_by = request.user
    payment.save()
    
    # Registrar acción de aprobación
    log_audit_action(
        instance=payment,
        action=AuditAction.APPROVE,
        metadata={
            'comment': f'Pago aprobado por {request.user.username}',
            'amount': str(payment.amount)
        }
    )
    
    return Response({'status': 'approved'})

def reject_payment(request, payment_id, reason):
    payment = Payment.objects.get(pk=payment_id)
    payment.status = 'REJECTED'
    payment.rejected_by = request.user
    payment.save()
    
    # Registrar acción de rechazo
    log_audit_action(
        instance=payment,
        action=AuditAction.REJECT,
        metadata={
            'comment': reason,
            'rejected_by': request.user.username
        }
    )
    
    return Response({'status': 'rejected'})
"""


# ============================================================================
# Ejemplo 3: Usar decorador @audit_action
# ============================================================================

"""
from audit.decorators import audit_action
from audit.models import AuditAction

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_action(AuditAction.APPROVE, model_class=Payment, object_id_param='pk')
def approve_payment_api(request, pk):
    payment = Payment.objects.get(pk=pk)
    payment.status = 'APPROVED'
    payment.save()
    return Response({'status': 'approved'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@audit_action(AuditAction.REJECT, model_class=Payment, object_id_param='pk')
def reject_payment_api(request, pk):
    payment = Payment.objects.get(pk=pk)
    payment.status = 'REJECTED'
    payment.save()
    return Response({'status': 'rejected'})
"""


# ============================================================================
# Ejemplo 4: Consultar registros de auditoría
# ============================================================================

"""
# Obtener todos los registros de un usuario
from audit.models import AuditLog

user_logs = AuditLog.objects.filter(user=request.user)

# Obtener registros de un modelo específico
student_logs = AuditLog.objects.filter(model_name='students.Student')

# Obtener registros de un objeto específico
from students.models import Student
student = Student.objects.get(pk='some-id')
logs = AuditLog.objects.filter(
    content_type=ContentType.objects.get_for_model(Student),
    object_id=str(student.pk)
)

# Obtener registros de una acción específica
approved_actions = AuditLog.objects.filter(action=AuditAction.APPROVE)

# Obtener registros en un rango de fechas
from django.utils import timezone
from datetime import timedelta

last_week = timezone.now() - timedelta(days=7)
recent_logs = AuditLog.objects.filter(timestamp__gte=last_week)

# Obtener cambios realizados en un UPDATE
update_logs = AuditLog.objects.filter(action=AuditAction.UPDATE)
for log in update_logs:
    changes = log.get_formatted_changes()
    print(f"Campos modificados: {list(changes.keys())}")
    for field, values in changes.items():
        print(f"  {field}: {values['anterior']} -> {values['nuevo']}")
"""


# ============================================================================
# Ejemplo 5: Usar en ViewSets de DRF
# ============================================================================

"""
from rest_framework import viewsets
from payments.models import Payment
from payments.serializers import PaymentSerializer
from audit.helpers import log_audit_action
from audit.models import AuditAction

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        instance = self.get_object()
        
        # Registrar aprobación si cambió el estado
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
"""


# ============================================================================
# Ejemplo 6: Agregar metadatos personalizados en saves
# ============================================================================

"""
# Puedes agregar metadatos personalizados usando el atributo _audit_metadata
# en la instancia antes de guardar:

from students.models import Student

student = Student.objects.get(pk='some-id')
student.status = 'ENROLLED'
student._audit_metadata = {
    'comment': 'Estudiante matriculado después de aprobar documentos',
    'enrollment_period': '2024-1'
}
student.save()

# El registro de auditoría incluirá estos metadatos
"""


# ============================================================================
# Ejemplo 7: Filtrar y buscar registros de auditoría via API
# ============================================================================

"""
# GET /api/audit/audit-logs/
# Obtener todos los registros de auditoría (solo para admins)

# GET /api/audit/audit-logs/?action=APPROVE
# Filtrar por acción

# GET /api/audit/audit-logs/?model_name=students.Student
# Filtrar por modelo

# GET /api/audit/audit-logs/?username=admin
# Filtrar por usuario

# GET /api/audit/audit-logs/?date_from=2024-01-01&date_to=2024-12-31
# Filtrar por rango de fechas

# GET /api/audit/audit-logs/?search=juan
# Buscar en username, model_name, object_id, ip_address

# GET /api/audit/audit-logs/?ordering=-timestamp
# Ordenar por timestamp descendente
"""


# ============================================================================
# Ejemplo 8: Desactivar auditoría para ciertos modelos
# ============================================================================

"""
# En settings.py, puedes especificar qué modelos auditar:

# Auditar todos los modelos (por defecto)
AUDIT_MODELS = None

# Auditar solo modelos específicos
AUDIT_MODELS = [
    'students.Student',
    'students.Enrollment',
    'payments.Payment',
    'academics.Course',
]

# Desactivar auditoría completamente
AUDIT_ENABLED = False
"""


# ============================================================================
# Ejemplo 9: Obtener historial completo de un objeto
# ============================================================================

"""
def get_object_audit_history(instance):
    '''Obtiene el historial completo de auditoría de un objeto'''
    from django.contrib.contenttypes.models import ContentType
    
    content_type = ContentType.objects.get_for_model(instance.__class__)
    logs = AuditLog.objects.filter(
        content_type=content_type,
        object_id=str(instance.pk)
    ).order_by('-timestamp')
    
    return logs

# Uso:
student = Student.objects.get(pk='some-id')
history = get_object_audit_history(student)

for log in history:
    print(f"{log.timestamp}: {log.get_action_display()} por {log.username}")
    if log.action == AuditAction.UPDATE and log.changes:
        print(f"  Cambios: {log.get_formatted_changes()}")
"""


# ============================================================================
# Ejemplo 10: Reporte de auditoría para universidad/SEP
# ============================================================================

"""
def generate_audit_report(start_date, end_date, model_name=None):
    '''Genera un reporte de auditoría para un período específico'''
    from django.contrib.contenttypes.models import ContentType
    
    queryset = AuditLog.objects.filter(
        timestamp__gte=start_date,
        timestamp__lte=end_date
    )
    
    if model_name:
        queryset = queryset.filter(model_name=model_name)
    
    report_data = {
        'period': f"{start_date} - {end_date}",
        'total_actions': queryset.count(),
        'by_action': {},
        'by_model': {},
        'by_user': {},
        'details': []
    }
    
    # Agrupar por acción
    for action_code, action_display in AuditAction.choices:
        count = queryset.filter(action=action_code).count()
        if count > 0:
            report_data['by_action'][action_display] = count
    
    # Agrupar por modelo
    for log in queryset.values('model_name').distinct():
        model_name = log['model_name']
        count = queryset.filter(model_name=model_name).count()
        report_data['by_model'][model_name] = count
    
    # Agrupar por usuario
    for log in queryset.values('username').distinct():
        username = log['username'] or 'Sistema'
        count = queryset.filter(username=username).count()
        report_data['by_user'][username] = count
    
    # Detalles (últimos 100 registros)
    report_data['details'] = list(
        queryset.order_by('-timestamp')[:100].values(
            'timestamp', 'username', 'action', 'model_name', 'object_id'
        )
    )
    
    return report_data

# Uso:
from django.utils import timezone
from datetime import timedelta

start_date = timezone.now() - timedelta(days=30)
end_date = timezone.now()

report = generate_audit_report(start_date, end_date)
print(f"Total de acciones: {report['total_actions']}")
print(f"Por acción: {report['by_action']}")
print(f"Por modelo: {report['by_model']}")
"""
