from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json
import logging
from django.db.models import Q, Sum, Count, Avg
from datetime import datetime, timedelta, date
from .models import Payment, Scholarship, PaymentConfiguration, PaymentType, StripeWebhookEvent
from .serializers import PaymentSerializer, ScholarshipSerializer, PaymentConfigurationSerializer, PaymentTypeSerializer, PublicPaymentSerializer
from .filters import PaymentFilter
from .stripe_service import StripePaymentService
import stripe
from students.models import Student
from academics.models import Career
from users.permissions import HasPermission
from decimal import Decimal

logger = logging.getLogger(__name__)


def _resolve_payment_type(value):
    """Resuelve payment_type por UUID o por código / 'code - name'."""
    if not value:
        return None
    s = str(value).strip()
    try:
        import uuid
        uuid.UUID(s)
        return PaymentType.objects.filter(id=s).first()
    except (ValueError, TypeError):
        pass
    code = s.split(' - ')[0].strip() if ' - ' in s else s
    return PaymentType.objects.filter(code=code, is_active=True).first()


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PaymentFilter
    search_fields = ['student__first_name', 'student__last_name', 'student__carnet', 'payment_method', 'receipt_number', 'payment_reference', 'transaction_id', 'payment_type__name', 'payment_type__code']
    ordering_fields = ['payment_date', 'amount', 'year', 'month', 'student__first_name', 'student__last_name']
    ordering = ['-payment_date']
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'student_status', 'statistics', 'pending_count', 'pending_transfers', 'my_accounting', 'student_accounting']:
            # Permitir ver a usuarios autenticados
            return [permissions.IsAuthenticated()]
        # Para crear/editar/eliminar/aprobar/rechazar requiere permiso específico
        return [permissions.IsAuthenticated(), HasPermission('manage_payments')]
    
    def perform_create(self, serializer):
        """Asignar automáticamente carrera y usuario creador al crear un pago"""
        from decimal import Decimal
        from django.core.exceptions import ValidationError
        from rest_framework import status
        from rest_framework.response import Response
        
        # Obtener el estudiante para asignar su carrera
        student_id = serializer.validated_data.get('student')
        user = self.request.user if self.request.user.is_authenticated else None
        
        # El modelo Payment.save() ya maneja la lógica de aprobación automática
        # Solo necesitamos asignar carrera y usuario creador
        save_data = {
            'career': student_id.career if student_id and student_id.career else None,
            'created_by': user,
        }
        
        # Asegurarse de que payment_type esté cargado para que el modelo pueda verificar el código
        payment_type_id = serializer.validated_data.get('payment_type')
        if payment_type_id:
            from .models import PaymentType
            try:
                payment_type = PaymentType.objects.get(id=payment_type_id)
                # Asignar el objeto payment_type para que esté disponible en save()
                serializer.validated_data['payment_type'] = payment_type
            except PaymentType.DoesNotExist:
                pass
        
        # Generar número de recibo automáticamente si es efectivo y no se proporcionó
        payment_method = serializer.validated_data.get('payment_method', 'TRANSFERENCIA')
        if payment_method == 'EFECTIVO' and not serializer.validated_data.get('receipt_number'):
            from .receipt_utils import generate_receipt_number
            serializer.validated_data['receipt_number'] = generate_receipt_number()
        
        # Pasar usuario para el historial de cambios
        try:
            payment = serializer.save(**save_data)
            payment._changed_by_user = user
            payment._status_change_notes = 'Pago creado'
            
            # Generar y enviar recibo automáticamente
            try:
                from .receipt_utils import generate_payment_receipt_pdf, send_receipt_email
                pdf_file = generate_payment_receipt_pdf(payment)
                send_receipt_email(payment, pdf_file)
            except Exception as receipt_error:
                logger.warning(f'Error al generar/enviar recibo automáticamente: {str(receipt_error)}')
                # No fallar la creación del pago si hay error con el recibo
            
            # No establecer status aquí, el modelo lo maneja automáticamente
            return payment
        except Exception as e:
            # Log el error completo para debugging
            import logging
            import traceback
            from django.core.exceptions import ValidationError as DjangoValidationError
            
            logger = logging.getLogger(__name__)
            error_type = type(e).__name__
            error_message = str(e)
            
            logger.error(f"Error al crear pago: {error_type}: {error_message}")
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            logger.error(f"Datos del serializer validados: {serializer.validated_data}")
            logger.error(f"Save data adicional: {save_data}")
            
            # Si es un ValidationError de Django, extraer los mensajes
            if isinstance(e, DjangoValidationError):
                error_messages = e.messages if hasattr(e, 'messages') else [error_message]
                error_dict = e.error_dict if hasattr(e, 'error_dict') else {}
                logger.error(f"Mensajes de validación: {error_messages}")
                logger.error(f"Dict de errores: {error_dict}")
                
                # Devolver un error más descriptivo
                return Response(
                    {
                        'error': 'Error de validación al crear el pago',
                        'details': error_messages,
                        'error_dict': {str(k): v for k, v in error_dict.items()},
                        'data': serializer.validated_data
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Re-raise el error para que Django REST Framework lo maneje
            raise
    
    @action(detail=False, methods=['post'])
    def create_enrollment_payment(self, request):
        """
        Endpoint específico para crear pagos de inscripción (100 y 101)
        Maneja la lógica de forma más simple sin depender de _calculate_amounts()
        """
        from decimal import Decimal
        from .models import Payment, PaymentType
        from students.models import Student
        from django.utils import timezone
        
        student_id = request.data.get('student')
        payment_type_id = request.data.get('payment_type')
        payment_method = request.data.get('payment_method', 'EFECTIVO')
        original_amount = request.data.get('original_amount')
        year = request.data.get('year')
        month = request.data.get('month')
        receipt_number = request.data.get('receipt_number', '')
        
        # Validaciones básicas
        if not student_id:
            return Response({'error': 'El estudiante es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        if not payment_type_id:
            return Response({'error': 'El tipo de pago es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        payment_type = _resolve_payment_type(payment_type_id)
        if not payment_type:
            return Response({'error': 'Tipo de pago no encontrado. Use el ID (UUID) o el código (ej. 100).'}, status=status.HTTP_404_NOT_FOUND)
        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Estudiante no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Validar que sea pago 100 o 101
        if payment_type.code not in ['100', '101']:
            return Response(
                {'error': 'Este endpoint solo es para pagos de inscripción (100 o 101)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Determinar el monto
        if payment_type.code == '100':
            # Pago 100 es gratis
            amount_value = Decimal('0.00')
            payment_method = 'EFECTIVO'  # Forzar efectivo para pago gratis
        elif payment_type.code == '101':
            # Pago 101 tiene costo
            if original_amount:
                try:
                    amount_value = Decimal(str(original_amount))
                except (ValueError, TypeError):
                    return Response({'error': 'Monto inválido'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                # Obtener el monto de PaymentConfiguration
                if not student.career:
                    return Response(
                        {'error': 'El estudiante no tiene una carrera asignada'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                try:
                    from .models import PaymentConfiguration
                    payment_config = PaymentConfiguration.objects.get(
                        career=student.career,
                        is_active=True
                    )
                    amount_value = payment_config.enrollment_fee or Decimal('0.00')
                except PaymentConfiguration.DoesNotExist:
                    return Response(
                        {'error': f'No se encontró configuración de pago para la carrera {student.career.name}'},
                        status=status.HTTP_404_NOT_FOUND
                    )
        else:
            amount_value = Decimal('0.00')
        
        # Generar número de recibo automáticamente si es efectivo y no se proporcionó
        if payment_method == 'EFECTIVO' and not receipt_number:
            from .receipt_utils import generate_receipt_number
            receipt_number = generate_receipt_number()
        
        # Crear el pago de forma simple
        try:
            payment = Payment.objects.create(
                student=student,
                career=student.career,
                payment_type=payment_type,
                payment_method=payment_method,
                original_amount=amount_value,
                final_amount=amount_value,
                amount=amount_value,  # Para compatibilidad
                scholarship_discount_amount=Decimal('0.00'),
                penalty_amount=Decimal('0.00'),
                year=year,
                month=month,
                payment_date=timezone.now().date(),
                status='APROBADO' if payment_type.code == '100' or payment_method == 'EFECTIVO' else 'PENDIENTE',
                receipt_number=receipt_number if payment_method == 'EFECTIVO' else '',
                created_by=request.user if request.user.is_authenticated else None,
                approved_by=request.user if (payment_type.code == '100' or payment_method == 'EFECTIVO') and request.user.is_authenticated else None,
                approved_at=timezone.now() if (payment_type.code == '100' or payment_method == 'EFECTIVO') else None,
            )
            
            # Generar y enviar recibo automáticamente
            try:
                from .receipt_utils import generate_payment_receipt_pdf, send_receipt_email
                pdf_file = generate_payment_receipt_pdf(payment)
                send_receipt_email(payment, pdf_file)
            except Exception as receipt_error:
                logger.warning(f'Error al generar/enviar recibo automáticamente: {str(receipt_error)}')
                # No fallar la creación del pago si hay error con el recibo
            
            serializer = self.get_serializer(payment)
            response_data = serializer.data
            # Agregar información sobre el recibo generado
            response_data['receipt_generated'] = True
            response_data['receipt_number'] = payment.receipt_number
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear pago de inscripción: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'Error al crear el pago: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_update(self, serializer):
        """Capturar usuario que realiza el cambio y aprobar automáticamente pagos en efectivo"""
        from django.utils import timezone
        user = self.request.user if self.request.user.is_authenticated else None
        
        # Obtener la instancia antes de guardar para verificar el método de pago
        instance = self.get_object()
        payment_method = serializer.validated_data.get('payment_method', instance.payment_method)
        
        # Guardar la instancia
        instance = serializer.save()
        instance._changed_by_user = user
        instance._status_change_notes = getattr(self.request.data, 'notes', '') or ''
        
        # Si el método de pago es EFECTIVO y el pago no está aprobado, aprobarlo automáticamente
        if payment_method == 'EFECTIVO' and instance.status != 'APROBADO':
            instance.status = 'APROBADO'
            if not instance.approved_by:
                instance.approved_by = user
            if not instance.approved_at:
                instance.approved_at = timezone.now()
            instance._status_change_notes = 'Pago aprobado automáticamente (efectivo)'
            instance.save()
        
        return instance
    
    @action(detail=False, methods=['get'])
    def pending_count(self, request):
        """Obtener el conteo de pagos pendientes (solo transferencias)"""
        # Solo contar transferencias pendientes
        pending_transfers = Payment.objects.filter(
            payment_method='TRANSFERENCIA',
            status__in=['PENDIENTE', 'EN_REVISION']
        )
        
        pending_count = pending_transfers.count()
        
        return Response({
            'pending_count': pending_count,
            'pending': pending_transfers.filter(status='PENDIENTE').count(),
            'in_review': pending_transfers.filter(status='EN_REVISION').count(),
        })
    
    @action(detail=False, methods=['get'])
    def pending_transfers(self, request):
        """Listar todos los pagos pendientes (solo transferencias)"""
        # Solo mostrar transferencias pendientes
        pending_payments = Payment.objects.filter(
            payment_method='TRANSFERENCIA',
            status__in=['PENDIENTE', 'EN_REVISION']
        ).select_related(
            'student', 
            'career', 
            'payment_type', 
            'created_by', 
            'approved_by'
        ).prefetch_related('student__career')
        
        # Aplicar filtros de búsqueda si existen
        search = request.query_params.get('search', None)
        if search:
            search_term = search.strip()
            pending_payments = pending_payments.filter(
                Q(student__first_name__icontains=search_term) |
                Q(student__first_last_name__icontains=search_term) |
                Q(student__second_last_name__icontains=search_term) |
                Q(student__carnet__icontains=search_term) |
                Q(student__email__icontains=search_term) |
                Q(payment_reference__icontains=search_term) |
                Q(payment_type__name__icontains=search_term) |
                Q(payment_type__code__icontains=search_term) |
                Q(career__name__icontains=search_term) |
                Q(career__code__icontains=search_term) |
                Q(notes__icontains=search_term)
            )
        
        # Ordenar por fecha de pago (más recientes primero)
        pending_payments = pending_payments.order_by('-payment_date', '-created_at')
        
        # Paginación
        page = self.paginate_queryset(pending_payments)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(pending_payments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def student_status(self, request):
        """Obtener estado de pagos de un estudiante"""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Obtener todos los pagos del estudiante
        payments = Payment.objects.filter(student_id=student_id, year=current_year)
        approved_payments = payments.filter(status='APROBADO')
        
        # Verificar si está al día
        months_paid = [p.month for p in approved_payments]
        is_up_to_date = current_month in months_paid
        
        # Calcular meses pendientes
        months_pending = []
        for month in range(1, current_month + 1):
            if month not in months_paid:
                months_pending.append(month)
        
        return Response({
            'is_up_to_date': is_up_to_date,
            'months_paid': months_paid,
            'months_pending': months_pending,
            'total_payments': payments.count(),
            'approved_payments': approved_payments.count(),
        })
    
    @action(detail=False, methods=['get'])
    def pending_students(self, request):
        """Obtener estudiantes con pagos pendientes"""
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        # Estudiantes que no tienen pago aprobado para el mes actual
        students_with_payment = Payment.objects.filter(
            year=current_year,
            month=current_month,
            status='APROBADO'
        ).values_list('student_id', flat=True)
        
        pending_students = Student.objects.filter(is_active=True).exclude(
            id__in=students_with_payment
        )
        
        serializer = PaymentSerializer(
            Payment.objects.filter(student__in=pending_students, year=current_year, month=current_month),
            many=True
        )
        
        return Response({
            'pending_count': pending_students.count(),
            'students': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def students_with_overdue(self, request):
        """Obtener estudiantes con pagos vencidos (mora)"""
        from django.db.models import Sum, Count
        from decimal import Decimal
        
        today = date.today()
        
        # Obtener pagos vencidos (due_date < hoy y no aprobados)
        overdue_payments = Payment.objects.filter(
            due_date__lt=today,
            status__in=['NO_PAGADO', 'MORA', 'PENDIENTE']
        ).select_related('student', 'student__career')
        
        # Agrupar por estudiante y calcular totales
        students_data = {}
        for payment in overdue_payments:
            student_id = str(payment.student.id)
            if student_id not in students_data:
                students_data[student_id] = {
                    'student_id': student_id,
                    'student_name': payment.student.get_full_name(),
                    'student_phone': payment.student.phone,
                    'total_overdue_amount': Decimal('0.00'),
                    'overdue_payments_count': 0,
                }
            
            # Sumar el monto final del pago vencido
            payment_amount = payment.final_amount or payment.amount or Decimal('0.00')
            students_data[student_id]['total_overdue_amount'] += payment_amount
            students_data[student_id]['overdue_payments_count'] += 1
        
        # Convertir a lista y formatear
        result = []
        for student_data in students_data.values():
            result.append({
                'student_id': student_data['student_id'],
                'student_name': student_data['student_name'],
                'student_phone': student_data['student_phone'],
                'total_overdue_amount': float(student_data['total_overdue_amount']),
                'overdue_payments_count': student_data['overdue_payments_count'],
            })
        
        # Ordenar por monto total descendente
        result.sort(key=lambda x: x['total_overdue_amount'], reverse=True)
        
        return Response({
            'count': len(result),
            'students': result
        })
    
    @action(detail=False, methods=['get'])
    def find_oldest_unpaid(self, request):
        """Buscar el pago más antiguo en estado NO_PAGADO o MORA para un estudiante y tipo de pago"""
        student_id = request.query_params.get('student_id')
        payment_type_id = request.query_params.get('payment_type_id')
        
        if not student_id or not payment_type_id:
            return Response(
                {'error': 'student_id y payment_type_id son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Buscar el pago más antiguo en NO_PAGADO o MORA para este estudiante y tipo de pago
        # Ordenar por due_date (más antigua primero), si no hay due_date, por payment_date
        unpaid_payment = Payment.objects.filter(
            student_id=student_id,
            payment_type_id=payment_type_id,
            status__in=['NO_PAGADO', 'MORA']  # Incluir también pagos en mora
        ).order_by(
            'due_date',  # Primero por fecha de vencimiento (más antigua)
            'payment_date',  # Si no hay due_date, por fecha de pago
            'created_at'  # Como último recurso, por fecha de creación
        ).first()
        
        if not unpaid_payment:
            return Response(
                {'error': 'No se encontró ningún pago pendiente para este estudiante y tipo de pago'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Recalcular montos (por si hay mora que aplicar)
        unpaid_payment.save()  # Esto recalcula automáticamente los montos
        
        # Serializar el pago encontrado
        serializer = self.get_serializer(unpaid_payment)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def get_payment_amount(self, request):
        """Obtener el monto del pago basado en el estudiante y tipo de pago"""
        student_id = request.query_params.get('student_id')
        payment_type_id = request.query_params.get('payment_type_id')
        
        if not student_id or not payment_type_id:
            return Response(
                {'error': 'student_id y payment_type_id son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            student = Student.objects.get(id=student_id)
            payment_type = PaymentType.objects.get(id=payment_type_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Estudiante no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PaymentType.DoesNotExist:
            return Response(
                {'error': 'Tipo de pago no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Si el tipo de pago tiene un monto fijo, devolverlo
        if payment_type.amount is not None:
            return Response({
                'amount': float(payment_type.amount),
                'original_amount': float(payment_type.amount),
                'final_amount': float(payment_type.amount),
            })
        
        # Si el tipo de pago es 101 (Inscripción al Cuatrimestre), obtener el monto de PaymentConfiguration
        if payment_type.code == '101':
            if not student.career:
                return Response(
                    {'error': 'El estudiante no tiene una carrera asignada'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                payment_config = PaymentConfiguration.objects.get(
                    career=student.career,
                    is_active=True
                )
                enrollment_fee = payment_config.enrollment_fee or Decimal('0.00')
                return Response({
                    'amount': float(enrollment_fee),
                    'original_amount': float(enrollment_fee),
                    'final_amount': float(enrollment_fee),
                })
            except PaymentConfiguration.DoesNotExist:
                return Response(
                    {'error': f'No se encontró configuración de pago para la carrera {student.career.name}'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Para otros tipos de pago sin monto fijo, devolver 0
        return Response({
            'amount': 0.0,
            'original_amount': 0.0,
            'final_amount': 0.0,
        })
    
    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        """Aprobar un pago"""
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        
        payment = self.get_object()
        
        # Validar que el pago no esté ya aprobado
        if payment.status == 'APROBADO':
            return Response(
                {'error': 'Este pago ya está aprobado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el pago no esté rechazado (requeriría un flujo diferente)
        if payment.status == 'RECHAZADO':
            return Response(
                {'error': 'No se puede aprobar un pago que ha sido rechazado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = 'APROBADO'
        payment.approved_by = request.user if request.user.is_authenticated else None
        payment.approved_at = timezone.now()
        
        # Pasar usuario para el historial de cambios
        user = request.user if request.user.is_authenticated else None
        payment._changed_by_user = user
        payment._status_change_notes = request.data.get('notes', '') or 'Pago aprobado'
        
        try:
            payment.save()
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        """Rechazar un pago"""
        payment = self.get_object()
        payment.status = 'RECHAZADO'
        if 'notes' in request.data:
            payment.notes = request.data['notes']
        
        # Pasar usuario para el historial de cambios
        user = request.user if request.user.is_authenticated else None
        payment._changed_by_user = user
        payment._status_change_notes = request.data.get('notes', '') or 'Pago rechazado'
        
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_receipt(self, request, pk=None):
        """Subir comprobante de pago (imagen/PDF) para cualquier método de pago"""
        payment = self.get_object()
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        
        # Validar tipo de archivo
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
        if file.content_type not in allowed_types:
            return Response(
                {'error': 'Tipo de archivo no permitido. Solo se permiten PDF, JPG y PNG.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tamaño (10MB máximo)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return Response(
                {'error': 'El archivo es demasiado grande. El tamaño máximo es 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.transfer_receipt = file
        # Si el pago está pendiente, cambiar a en revisión
        if payment.status == 'PENDIENTE':
            payment.status = 'EN_REVISION'
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def download_receipt(self, request, pk=None):
        """
        Descargar el recibo de pago en PDF
        """
        payment = self.get_object()
        
        try:
            from .receipt_utils import generate_payment_receipt_pdf
            pdf_file = generate_payment_receipt_pdf(payment)
            
            filename = f'recibo_{payment.receipt_number or payment.id}_{payment.payment_date.strftime("%Y%m%d") if payment.payment_date else "N/A"}.pdf'
            
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            logger.error(f'Error al generar recibo PDF: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Error al generar el recibo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def send_receipt_email(self, request, pk=None):
        """
        Enviar el recibo de pago por correo electrónico al estudiante
        """
        payment = self.get_object()
        
        try:
            from .receipt_utils import send_receipt_email
            success = send_receipt_email(payment)
            
            if success:
                return Response(
                    {'message': 'Recibo enviado por correo electrónico exitosamente'},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'No se pudo enviar el recibo. Verifique que el estudiante tenga un correo electrónico válido.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f'Error al enviar recibo por correo: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Error al enviar el recibo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['patch'])
    def update_reference(self, request, pk=None):
        """Actualizar la referencia de pago"""
        payment = self.get_object()
        
        if 'payment_reference' not in request.data:
            return Response(
                {'error': 'payment_reference es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.payment_reference = request.data['payment_reference']
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Obtener estadísticas de pagos por diferentes períodos"""
        try:
            today = date.today()
            
            # Filtros de fecha para diferentes períodos
            today_start = datetime.combine(today, datetime.min.time())
            week_start = today_start - timedelta(days=7)
            last_15_days_start = today_start - timedelta(days=15)
            month_start = today_start.replace(day=1)
            last_month_start = (month_start - timedelta(days=1)).replace(day=1)
            last_month_end = month_start - timedelta(days=1)
            
            # Filtrar solo pagos aprobados para estadísticas
            approved_payments = Payment.objects.filter(status='APROBADO')
            
            # Estadísticas del día
            today_payments = approved_payments.filter(
                payment_date=today
            )
            today_total = today_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            today_count = today_payments.count()
            
            # Estadísticas de la semana (últimos 7 días)
            week_payments = approved_payments.filter(
                payment_date__gte=week_start.date()
            )
            week_total = week_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            week_count = week_payments.count()
            
            # Estadísticas de los últimos 15 días
            last_15_payments = approved_payments.filter(
                payment_date__gte=last_15_days_start.date()
            )
            last_15_total = last_15_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            last_15_count = last_15_payments.count()
            
            # Estadísticas del mes actual
            month_payments = approved_payments.filter(
                payment_date__gte=month_start.date()
            )
            month_total = month_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            month_count = month_payments.count()
            
            # Estadísticas del mes anterior
            last_month_payments = approved_payments.filter(
                payment_date__gte=last_month_start.date(),
                payment_date__lte=last_month_end.date()
            )
            last_month_total = last_month_payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            last_month_count = last_month_payments.count()
            
            # Estadísticas por método de pago (últimos 30 días)
            last_30_days_start = today_start - timedelta(days=30)
            payments_by_method = approved_payments.filter(
                payment_date__gte=last_30_days_start.date()
            ).values('payment_method').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('-total')
            
            # Estadísticas por tipo de pago (últimos 30 días)
            payments_by_type = approved_payments.filter(
                payment_date__gte=last_30_days_start.date()
            ).values('payment_type__code', 'payment_type__name').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('-total').exclude(payment_type__isnull=True)
            
            # Estadísticas de colegiaturas (pagos con tipo relacionado a colegiaturas)
            # Filtrar por código que contenga "COLEG" o nombre que contenga "colegiatura"
            tuition_payments = approved_payments.filter(
                Q(payment_type__code__icontains='COLEG') | 
                Q(payment_type__name__icontains='colegiatura')
            )
            
            # Colegiaturas del día
            tuition_today = tuition_payments.filter(payment_date=today)
            tuition_today_total = tuition_today.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            tuition_today_count = tuition_today.count()
            
            # Colegiaturas de la semana
            tuition_week = tuition_payments.filter(payment_date__gte=week_start.date())
            tuition_week_total = tuition_week.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            tuition_week_count = tuition_week.count()
            
            # Colegiaturas de los últimos 15 días
            tuition_last_15 = tuition_payments.filter(payment_date__gte=last_15_days_start.date())
            tuition_last_15_total = tuition_last_15.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            tuition_last_15_count = tuition_last_15.count()
            
            # Colegiaturas del mes
            tuition_month = tuition_payments.filter(payment_date__gte=month_start.date())
            tuition_month_total = tuition_month.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            tuition_month_count = tuition_month.count()
            
            # Gráfica de pagos por día (últimos 15 días)
            # payment_date es un DateField, no necesita TruncDate
            daily_payments = approved_payments.filter(
                payment_date__gte=last_15_days_start.date()
            ).values('payment_date').annotate(
                total=Sum('amount'),
                count=Count('id')
            ).order_by('payment_date')
            
            # Gráfica de pagos por método de pago (últimos 30 días)
            method_chart = list(payments_by_method)
            
            # Gráfica de pagos por tipo (últimos 30 días)
            type_chart = list(payments_by_type)
            
            return Response({
                'periods': {
                'today': {
                    'total': float(today_total),
                    'count': today_count,
                    'average': float(today_total / today_count) if today_count > 0 else 0.0
                },
                'week': {
                    'total': float(week_total),
                    'count': week_count,
                    'average': float(week_total / week_count) if week_count > 0 else 0.0
                },
                'last_15_days': {
                    'total': float(last_15_total),
                    'count': last_15_count,
                    'average': float(last_15_total / last_15_count) if last_15_count > 0 else 0.0
                },
                'month': {
                    'total': float(month_total),
                    'count': month_count,
                    'average': float(month_total / month_count) if month_count > 0 else 0.0
                },
                'last_month': {
                    'total': float(last_month_total),
                    'count': last_month_count,
                    'average': float(last_month_total / last_month_count) if last_month_count > 0 else 0.0
                }
            },
            'tuition': {
                'today': {
                    'total': float(tuition_today_total),
                    'count': tuition_today_count,
                    'average': float(tuition_today_total / tuition_today_count) if tuition_today_count > 0 else 0.0
                },
                'week': {
                    'total': float(tuition_week_total),
                    'count': tuition_week_count,
                    'average': float(tuition_week_total / tuition_week_count) if tuition_week_count > 0 else 0.0
                },
                'last_15_days': {
                    'total': float(tuition_last_15_total),
                    'count': tuition_last_15_count,
                    'average': float(tuition_last_15_total / tuition_last_15_count) if tuition_last_15_count > 0 else 0.0
                },
                'month': {
                    'total': float(tuition_month_total),
                    'count': tuition_month_count,
                    'average': float(tuition_month_total / tuition_month_count) if tuition_month_count > 0 else 0.0
                }
            },
            'charts': {
                'daily': [
                    {
                        'date': str(item.get('date') or item.get('payment_date') or ''),
                        'total': float(item['total'] or 0),
                        'count': item['count'] or 0
                    }
                    for item in daily_payments if (item.get('date') or item.get('payment_date'))
                ],
                'by_method': [
                    {
                        'method': item.get('payment_method', ''),
                        'method_display': dict(Payment.PAYMENT_METHODS).get(item.get('payment_method', ''), item.get('payment_method', 'N/A')),
                        'total': float(item.get('total') or 0),
                        'count': item.get('count') or 0
                    }
                    for item in method_chart if item.get('payment_method')
                ],
                'by_type': [
                    {
                        'code': item.get('payment_type__code') or 'N/A',
                        'name': item.get('payment_type__name') or 'Sin tipo',
                        'total': float(item.get('total') or 0),
                        'count': item.get('count') or 0
                    }
                    for item in type_chart
                ]
                }
            })
        except Exception as e:
            import traceback
            error_detail = str(e)
            traceback_str = traceback.format_exc()
            print(f"Error in statistics endpoint: {error_detail}")
            print(traceback_str)
            return Response(
                {'error': 'Error al calcular las estadísticas', 'detail': error_detail},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='export/csv')
    def export_csv(self, request):
        """Exportar pagos filtrados a CSV"""
        from django.http import HttpResponse
        import csv
        
        # Obtener queryset filtrado usando el mismo filtro que list
        queryset = self.filter_queryset(self.get_queryset())
        
        # Aplicar ordenamiento si existe
        ordering = request.query_params.get('ordering', '-payment_date')
        if ordering:
            queryset = queryset.order_by(*ordering.split(','))
        
        # Crear respuesta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="pagos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        
        # Escribir encabezados
        writer.writerow([
            'ID',
            'Estudiante',
            'Carnet',
            'Tipo de Pago',
            'Código Tipo',
            'Monto',
            'Monto Original',
            'Descuento Beca',
            'Mora',
            'Mes',
            'Año',
            'Estado',
            'Método de Pago',
            'Fecha de Pago',
            'Referencia',
            'Número de Recibo',
            'Carrera',
            'Fecha de Creación',
            'Aprobado por',
            'Fecha de Aprobación'
        ])
        
        # Escribir datos
        for payment in queryset.select_related('student', 'payment_type', 'career', 'approved_by'):
            writer.writerow([
                str(payment.id),
                payment.student.get_full_name() if payment.student else '',
                payment.student.carnet if payment.student else '',
                payment.payment_type.name if payment.payment_type else '',
                payment.payment_type.code if payment.payment_type else '',
                str(payment.final_amount or payment.amount or '0.00'),
                str(payment.original_amount or payment.amount or '0.00'),
                str(payment.scholarship_discount_amount or '0.00'),
                str(payment.penalty_amount or '0.00'),
                payment.get_month_display() if payment.month else '',
                str(payment.year) if payment.year else '',
                payment.get_status_display(),
                payment.get_payment_method_display(),
                payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else '',
                payment.payment_reference or '',
                payment.receipt_number or '',
                payment.career.name if payment.career else '',
                payment.created_at.strftime('%Y-%m-%d %H:%M:%S') if payment.created_at else '',
                payment.approved_by.get_full_name() if payment.approved_by else '',
                payment.approved_at.strftime('%Y-%m-%d %H:%M:%S') if payment.approved_at else '',
            ])
        
        return response
    
    @action(detail=False, methods=['get'])
    def my_accounting(self, request):
        """Obtener contabilidad completa del estudiante asociado al usuario logueado"""
        from academics.models import CuatrimestreEnrollment
        from payments.models import PaymentType
        
        try:
            # Buscar estudiante por email del usuario logueado
            user_email = request.user.email
            try:
                student = Student.objects.get(email=user_email, is_active=True)
            except Student.DoesNotExist:
                return Response(
                    {'error': 'No se encontró un estudiante asociado a este usuario'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Student.MultipleObjectsReturned:
                # Si hay múltiples, tomar el primero activo
                student = Student.objects.filter(email=user_email, is_active=True).first()
            
            # Obtener todos los pagos del estudiante ordenados por fecha
            all_payments = Payment.objects.filter(student=student).select_related(
                'payment_type', 'career', 'cuatrimestre_enrollment'
            ).order_by('-payment_date', '-created_at')
            
            # Calcular pagos aprobados
            approved_payments = all_payments.filter(status='APROBADO')
            total_paid = approved_payments.aggregate(
                total=Sum('final_amount')
            )['total'] or Decimal('0.00')
            
            # Obtener pagos aprobados por mes/año para identificar meses pagados
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # Obtener inscripciones activas del estudiante
            active_enrollments = CuatrimestreEnrollment.objects.filter(
                student=student,
                status__in=['EN_CURSO', 'PENDIENTE_CONFIRMACION', 'PENDIENTE_PAGO']
            ).order_by('-academic_year', '-cuatrimestre__number')
            
            # Calcular deudas pendientes
            # Buscar tipos de pago mensuales (colegiaturas)
            monthly_payment_types = PaymentType.objects.filter(
                is_active=True,
                requires_month=True
            )
            
            # Calcular meses pagados en el año actual
            months_paid_this_year = set()
            for payment in approved_payments.filter(year=current_year):
                if payment.month:
                    months_paid_this_year.add(payment.month)
            
            # Calcular deudas pendientes del año actual
            pending_debts = []
            total_debt = Decimal('0.00')
            
            # Para cada mes del año actual hasta el mes actual
            for month in range(1, current_month + 1):
                if month not in months_paid_this_year:
                    # Hay una deuda pendiente para este mes
                    # Buscar el tipo de pago mensual aplicable
                    monthly_type = monthly_payment_types.first()
                    if monthly_type and monthly_type.amount:
                        # Calcular monto con beca si aplica
                        base_amount = monthly_type.amount
                        
                        # Verificar si el estudiante tiene beca activa
                        scholarship_discount = Decimal('0.00')
                        try:
                            scholarship = student.scholarship
                            if scholarship and scholarship.status == 'ACTIVA':
                                # Verificar que la beca esté vigente
                                today = date.today()
                                if (scholarship.start_date <= today and 
                                    (not scholarship.end_date or scholarship.end_date >= today)):
                                    scholarship_discount = base_amount * (scholarship.percentage / Decimal('100.00'))
                        except:
                            pass
                        
                        amount_after_scholarship = base_amount - scholarship_discount
                        
                        # Calcular mora si aplica
                        penalty_amount = Decimal('0.00')
                        if monthly_type.has_penalty:
                            # Fecha límite sería el último día del mes
                            import calendar
                            last_day = calendar.monthrange(current_year, month)[1]
                            due_date = date(current_year, month, last_day)
                            today = date.today()
                            penalty_amount = monthly_type.calculate_penalty(amount_after_scholarship, due_date, today)
                        
                        debt_amount = amount_after_scholarship + penalty_amount
                        total_debt += debt_amount
                        
                        pending_debts.append({
                            'month': month,
                            'month_display': dict(Payment.MONTHS)[month],
                            'year': current_year,
                            'amount': float(debt_amount),
                            'base_amount': float(amount_after_scholarship),
                            'penalty_amount': float(penalty_amount),
                            'payment_type': {
                                'id': str(monthly_type.id),
                                'code': monthly_type.code,
                                'name': monthly_type.name
                            }
                        })
            
            # Calcular balance (pagos aprobados - deudas pendientes)
            balance = total_paid - total_debt
            
            # Serializar pagos para la respuesta
            payments_data = []
            for payment in all_payments:
                payment_data = {
                    'id': str(payment.id),
                    'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                    'payment_method': payment.payment_method,
                    'payment_method_display': payment.get_payment_method_display(),
                    'status': payment.status,
                    'status_display': payment.get_status_display(),
                    'amount': float(payment.final_amount or payment.amount or 0),
                    'original_amount': float(payment.original_amount or payment.amount or 0),
                    'scholarship_discount': float(payment.scholarship_discount_amount or 0),
                    'penalty_amount': float(payment.penalty_amount or 0),
                    'month': payment.month,
                    'month_display': payment.get_month_display() if payment.month else None,
                    'year': payment.year,
                    'payment_type': {
                        'id': str(payment.payment_type.id) if payment.payment_type else None,
                        'code': payment.payment_type.code if payment.payment_type else None,
                        'name': payment.payment_type.name if payment.payment_type else None,
                    } if payment.payment_type else None,
                    'payment_reference': payment.payment_reference,
                    'receipt_number': payment.receipt_number,
                    'transfer_receipt': request.build_absolute_uri(payment.transfer_receipt.url) if payment.transfer_receipt else None,
                    'transaction_id': payment.transaction_id,
                    'card_last_four': payment.card_last_four,
                }
                payments_data.append(payment_data)
            
            return Response({
                'student': {
                    'id': str(student.id),
                    'carnet': student.carnet,
                    'full_name': student.get_full_name(),
                    'email': student.email,
                },
                'summary': {
                    'total_paid': float(total_paid),
                    'total_debt': float(total_debt),
                    'balance': float(balance),
                    'total_payments': all_payments.count(),
                    'approved_payments': approved_payments.count(),
                    'pending_payments': all_payments.filter(status__in=['PENDIENTE', 'EN_REVISION']).count(),
                },
                'pending_debts': pending_debts,
                'payments': payments_data,
            })
            
        except Exception as e:
            import traceback
            error_detail = str(e)
            traceback_str = traceback.format_exc()
            print(f"Error in my_accounting endpoint: {error_detail}")
            print(traceback_str)
            return Response(
                {'error': 'Error al obtener la contabilidad', 'detail': error_detail},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='student_accounting/(?P<student_id>[^/.]+)')
    def student_accounting(self, request, student_id=None):
        """Obtener contabilidad completa de un estudiante específico (para administradores)"""
        from academics.models import CuatrimestreEnrollment
        from payments.models import PaymentType
        
        try:
            # Buscar estudiante por ID
            try:
                student = Student.objects.get(id=student_id, is_active=True)
            except Student.DoesNotExist:
                return Response(
                    {'error': 'No se encontró el estudiante'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener todos los pagos del estudiante ordenados por fecha
            all_payments = Payment.objects.filter(student=student).select_related(
                'payment_type', 'career', 'cuatrimestre_enrollment'
            ).order_by('-payment_date', '-created_at')
            
            # Calcular pagos aprobados
            approved_payments = all_payments.filter(status='APROBADO')
            total_paid = approved_payments.aggregate(
                total=Sum('final_amount')
            )['total'] or Decimal('0.00')
            
            # Obtener pagos aprobados por mes/año para identificar meses pagados
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # Obtener inscripciones activas del estudiante
            active_enrollments = CuatrimestreEnrollment.objects.filter(
                student=student,
                status__in=['EN_CURSO', 'PENDIENTE_CONFIRMACION', 'PENDIENTE_PAGO']
            ).order_by('-academic_year', '-cuatrimestre__number')
            
            # Calcular deudas pendientes
            # Buscar tipos de pago mensuales (colegiaturas)
            monthly_payment_types = PaymentType.objects.filter(
                is_active=True,
                requires_month=True
            )
            
            # Calcular meses pagados en el año actual
            months_paid_this_year = set()
            for payment in approved_payments.filter(year=current_year):
                if payment.month:
                    months_paid_this_year.add(payment.month)
            
            # Calcular deudas pendientes del año actual
            pending_debts = []
            total_debt = Decimal('0.00')
            
            # Para cada mes del año actual hasta el mes actual
            for month in range(1, current_month + 1):
                if month not in months_paid_this_year:
                    # Hay una deuda pendiente para este mes
                    # Buscar el tipo de pago mensual aplicable
                    monthly_type = monthly_payment_types.first()
                    if monthly_type and monthly_type.amount:
                        # Calcular monto con beca si aplica
                        base_amount = monthly_type.amount
                        
                        # Verificar si el estudiante tiene beca activa
                        scholarship_discount = Decimal('0.00')
                        try:
                            scholarship = student.scholarship
                            if scholarship and scholarship.status == 'ACTIVA':
                                # Verificar que la beca esté vigente
                                today = date.today()
                                if (scholarship.start_date <= today and 
                                    (not scholarship.end_date or scholarship.end_date >= today)):
                                    scholarship_discount = base_amount * (scholarship.percentage / Decimal('100.00'))
                        except:
                            pass
                        
                        amount_after_scholarship = base_amount - scholarship_discount
                        
                        # Calcular mora si aplica
                        penalty_amount = Decimal('0.00')
                        if monthly_type.has_penalty:
                            # Fecha límite sería el último día del mes
                            import calendar
                            last_day = calendar.monthrange(current_year, month)[1]
                            due_date = date(current_year, month, last_day)
                            today = date.today()
                            penalty_amount = monthly_type.calculate_penalty(amount_after_scholarship, due_date, today)
                        
                        debt_amount = amount_after_scholarship + penalty_amount
                        total_debt += debt_amount
                        
                        pending_debts.append({
                            'month': month,
                            'month_display': dict(Payment.MONTHS)[month],
                            'year': current_year,
                            'amount': float(debt_amount),
                            'base_amount': float(amount_after_scholarship),
                            'penalty_amount': float(penalty_amount),
                            'payment_type': {
                                'id': str(monthly_type.id),
                                'code': monthly_type.code,
                                'name': monthly_type.name
                            }
                        })
            
            # Calcular balance (pagos aprobados - deudas pendientes)
            balance = total_paid - total_debt
            
            # Serializar pagos para la respuesta
            payments_data = []
            for payment in all_payments:
                payment_data = {
                    'id': str(payment.id),
                    'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                    'payment_method': payment.payment_method,
                    'payment_method_display': payment.get_payment_method_display(),
                    'status': payment.status,
                    'status_display': payment.get_status_display(),
                    'amount': float(payment.final_amount or payment.amount or 0),
                    'original_amount': float(payment.original_amount or payment.amount or 0),
                    'scholarship_discount': float(payment.scholarship_discount_amount or 0),
                    'penalty_amount': float(payment.penalty_amount or 0),
                    'month': payment.month,
                    'month_display': payment.get_month_display() if payment.month else None,
                    'year': payment.year,
                    'payment_type': {
                        'id': str(payment.payment_type.id) if payment.payment_type else None,
                        'code': payment.payment_type.code if payment.payment_type else None,
                        'name': payment.payment_type.name if payment.payment_type else None,
                    } if payment.payment_type else None,
                    'payment_reference': payment.payment_reference,
                    'receipt_number': payment.receipt_number,
                    'transfer_receipt': request.build_absolute_uri(payment.transfer_receipt.url) if payment.transfer_receipt else None,
                    'transaction_id': payment.transaction_id,
                    'card_last_four': payment.card_last_four,
                }
                payments_data.append(payment_data)
            
            return Response({
                'student': {
                    'id': str(student.id),
                    'carnet': student.carnet,
                    'full_name': student.get_full_name(),
                    'email': student.email,
                },
                'summary': {
                    'total_paid': float(total_paid),
                    'total_debt': float(total_debt),
                    'balance': float(balance),
                    'total_payments': all_payments.count(),
                    'approved_payments': approved_payments.count(),
                    'pending_payments': all_payments.filter(status__in=['PENDIENTE', 'EN_REVISION']).count(),
                },
                'pending_debts': pending_debts,
                'payments': payments_data,
            })
            
        except Exception as e:
            import traceback
            error_detail = str(e)
            traceback_str = traceback.format_exc()
            print(f"Error in student_accounting endpoint: {error_detail}")
            print(traceback_str)
            return Response(
                {'error': 'Error al obtener la contabilidad del estudiante', 'detail': error_detail},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ScholarshipViewSet(viewsets.ModelViewSet):
    queryset = Scholarship.objects.all()
    serializer_class = ScholarshipSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            # Permitir ver a usuarios autenticados
            return [permissions.IsAuthenticated()]
        # Para crear/editar/eliminar requiere permiso específico
        return [permissions.IsAuthenticated(), HasPermission('manage_scholarships')]
    
    def create(self, request, *args, **kwargs):
        """Crear beca y verificar límites por facultad"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        student_id = request.data.get('student')
        scholarship_type = request.data.get('scholarship_type')
        
        student = Student.objects.get(id=student_id)
        career = student.career
        
        # Verificar límites de becas (si existen en el modelo Career)
        # Por ahora, permitir crear becas sin límite estricto
        # TODO: Agregar campos max_scholarships_full y max_scholarships_half al modelo Career si se requiere
        
        if scholarship_type == 'COMPLETA':
            percentage = 100.00
        else:  # MEDIA
            percentage = 50.00
        
        # Actualizar estudiante si tiene el campo scholarship_type
        if hasattr(student, 'scholarship_type'):
            student.scholarship_type = scholarship_type
            student.save()
        
        # Crear beca
        scholarship = serializer.save(percentage=percentage)
        
        return Response(ScholarshipSerializer(scholarship).data, status=status.HTTP_201_CREATED)


class PaymentConfigurationViewSet(viewsets.ModelViewSet):
    queryset = PaymentConfiguration.objects.filter(is_active=True)
    serializer_class = PaymentConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            # Permitir ver a usuarios autenticados
            return [permissions.IsAuthenticated()]
        # Para crear/editar/eliminar requiere permiso específico
        return [permissions.IsAuthenticated(), HasPermission('manage_settings')]


class PaymentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Vista para tipos de pago (solo lectura)"""
    queryset = PaymentType.objects.filter(is_active=True)
    serializer_class = PaymentTypeSerializer
    permission_classes = [permissions.AllowAny]  # Público para que los estudiantes puedan ver los tipos


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_student_by_carnet(request):
    """Obtener información básica del estudiante por carné (público)"""
    carnet = request.query_params.get('carnet')
    
    if not carnet:
        return Response(
            {'error': 'El número de carné es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        student = Student.objects.get(carnet=carnet, is_active=True)
        return Response({
            'id': str(student.id),
            'carnet': student.carnet,
            'full_name': student.get_full_name(),
            'career': {
                'id': str(student.career.id),
                'name': student.career.name,
                'code': student.career.code
            },
            'has_scholarship': student.has_scholarship,
            'scholarship_type': student.scholarship_type
        })
    except Student.DoesNotExist:
        return Response(
            {'error': 'CARNÉ NO EXISTE: El número de carné no existe.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_payment_intent(request):
    """Crear un Payment Intent de Stripe para iniciar el pago"""
    carnet = request.data.get('carnet')
    payment_type_id = request.data.get('payment_type')
    amount = request.data.get('amount')
    
    if not all([carnet, payment_type_id, amount]):
        return Response(
            {'error': 'Faltan campos requeridos: carnet, payment_type, amount'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar estudiante
    try:
        student = Student.objects.get(carnet=carnet, is_active=True)
    except Student.DoesNotExist:
        return Response(
            {'error': 'CARNÉ NO EXISTE: El número de carné no existe.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar tipo de pago
    try:
        payment_type = PaymentType.objects.get(id=payment_type_id, is_active=True)
    except PaymentType.DoesNotExist:
        return Response(
            {'error': 'Tipo de pago no válido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Usar monto del tipo de pago si está definido, sino usar el proporcionado
    final_amount = payment_type.amount if payment_type.amount else float(amount)
    
    # Crear Payment Intent en Stripe
    metadata = {
        'student_id': str(student.id),
        'student_carnet': student.carnet,
        'payment_type_id': str(payment_type.id),
        'payment_type_code': payment_type.code,
    }
    
    result = StripePaymentService.create_payment_intent(
        amount=final_amount,
        currency='mxn',  # Pesos mexicanos
        metadata=metadata
    )
    
    if not result['success']:
        return Response(
            {'error': result.get('error', 'Error al crear la solicitud de pago')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'client_secret': result['client_secret'],
        'payment_intent_id': result['payment_intent_id'],
        'amount': final_amount,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def process_public_payment(request):
    """Procesar pago público con tarjeta usando Stripe"""
    serializer = PublicPaymentSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    carnet = serializer.validated_data['carnet']
    payment_type_id = serializer.validated_data['payment_type']
    amount = serializer.validated_data['amount']
    payment_intent_id = request.data.get('payment_intent_id')
    
    # Validar estudiante
    try:
        student = Student.objects.get(carnet=carnet, is_active=True)
    except Student.DoesNotExist:
        return Response(
            {'error': 'CARNÉ NO EXISTE: El número de carné no existe.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar tipo de pago
    try:
        payment_type = PaymentType.objects.get(id=payment_type_id, is_active=True)
    except PaymentType.DoesNotExist:
        return Response(
            {'error': 'Tipo de pago no válido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar campos requeridos según el tipo de pago
    if payment_type.requires_month and not serializer.validated_data.get('month'):
        return Response(
            {'error': f'El tipo de pago {payment_type.name} requiere especificar el mes'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if payment_type.requires_year and not serializer.validated_data.get('year'):
        return Response(
            {'error': f'El tipo de pago {payment_type.name} requiere especificar el año'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if payment_type.requires_semester and not serializer.validated_data.get('semester'):
        return Response(
            {'error': f'El tipo de pago {payment_type.name} requiere especificar el semestre/trimestre'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if payment_type.requires_quantity and not serializer.validated_data.get('quantity'):
        return Response(
            {'error': f'El tipo de pago {payment_type.name} requiere especificar la cantidad'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Usar monto del tipo de pago si está definido, sino usar el proporcionado
    final_amount = payment_type.amount if payment_type.amount else amount
    
    # Validar que se proporcionó payment_intent_id
    if not payment_intent_id:
        return Response(
            {'error': 'payment_intent_id es requerido para procesar el pago'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verificar que el Payment Intent existe en Stripe
    payment_result = StripePaymentService.confirm_payment(payment_intent_id)
    
    if not payment_result['success']:
        return Response(
            {'error': payment_result.get('error', 'Error al verificar el pago')},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Obtener últimos 4 dígitos de la tarjeta (opcional, puede no estar disponible aún)
    card_last_four = StripePaymentService.get_card_last_four(payment_intent_id) or ""
    
    # NOTA: El pago NO se aprueba aquí. Se crea con estado PENDIENTE.
    # El webhook payment_intent.succeeded será el que apruebe el pago.
    # Esto asegura que solo Stripe confirme el pago exitoso.
    
    # Calcular fecha límite si aplica mora
    due_date = None
    if payment_type.has_penalty:
        # Calcular fecha límite basada en el campo configurado
        current_date = datetime.now().date()
        if payment_type.requires_month and serializer.validated_data.get('month'):
            from datetime import date
            month = serializer.validated_data.get('month')
            year = serializer.validated_data.get('year') or datetime.now().year
            # Fecha límite sería el último día del mes
            import calendar
            last_day = calendar.monthrange(year, month)[1]
            due_date = date(year, month, last_day)
        elif payment_type.requires_semester and serializer.validated_data.get('semester'):
            # Para semestres, podrías configurar fechas específicas
            # Por ahora, usar fecha actual + días
            from datetime import timedelta
            due_date = current_date + timedelta(days=30)
        else:
            # Fecha límite por defecto
            from datetime import timedelta
            due_date = current_date + timedelta(days=30)
    
    # Crear el pago en la base de datos con estado PENDIENTE
    # El webhook payment_intent.succeeded será el que apruebe el pago
    payment = Payment.objects.create(
        student=student,
        career=student.career,  # Guardar carrera para trazabilidad
        payment_type=payment_type,
        payment_method='TARJETA',
        amount=final_amount,
        base_amount=final_amount,  # Monto base sin mora
        month=serializer.validated_data.get('month'),
        year=serializer.validated_data.get('year') or datetime.now().year,
        semester=serializer.validated_data.get('semester'),
        quantity=serializer.validated_data.get('quantity'),
        due_date=due_date,
        card_last_four=card_last_four,
        transaction_id=payment_intent_id,  # Guardar payment_intent_id como transaction_id
        stripe_payment_intent_id=payment_intent_id,  # Guardar también en el campo específico
        status='PENDIENTE',  # El webhook lo aprobará cuando el pago sea exitoso
        created_by=None  # Pago público, sin usuario creador
    )
    
    return Response({
        'success': True,
        'payment_id': str(payment.id),
        'transaction_id': payment_intent_id,
        'amount': str(final_amount),
        'penalty_amount': str(payment.penalty_amount),
        'total_amount': str(payment.amount),
        'status': payment.status,
        'message': 'Pago registrado. El pago será confirmado automáticamente cuando sea procesado por Stripe.'
    }, status=status.HTTP_201_CREATED)


logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Endpoint para recibir webhooks de Stripe.
    Este endpoint es la única fuente de verdad para confirmar pagos.
    
    Procesa eventos:
    - payment_intent.succeeded: Aprueba el pago en la BD
    - payment_intent.payment_failed: Marca el pago como rechazado
    """
    from django.conf import settings
    from django.utils import timezone
    
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET no está configurado")
        return JsonResponse({'error': 'Webhook secret no configurado'}, status=500)
    
    # Obtener la firma del header
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    if not sig_header:
        logger.warning("Webhook recibido sin firma")
        return JsonResponse({'error': 'Firma no proporcionada'}, status=400)
    
    # Obtener el payload como bytes
    payload = request.body
    
    try:
        # Validar la firma del webhook
        event = StripePaymentService.construct_webhook_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logger.error(f"Error al parsear el payload del webhook: {str(e)}")
        return JsonResponse({'error': 'Payload inválido'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Error al verificar la firma del webhook: {str(e)}")
        return JsonResponse({'error': 'Firma inválida'}, status=400)
    
    # Verificar si el evento ya fue procesado (idempotencia)
    event_id = event.get('id')
    event_type = event.get('type')
    
    webhook_event, created = StripeWebhookEvent.objects.get_or_create(
        stripe_event_id=event_id,
        defaults={
            'event_type': event_type,
            'raw_data': event,
            'processed': False,
        }
    )
    
    # Si el evento ya fue procesado, retornar éxito sin procesar de nuevo
    if webhook_event.processed:
        logger.info(f"Evento {event_id} ya fue procesado anteriormente")
        return JsonResponse({'status': 'already_processed'}, status=200)
    
    # Obtener el payment_intent_id del evento
    payment_intent_id = None
    if 'data' in event and 'object' in event['data']:
        payment_intent_id = event['data']['object'].get('id')
    
    # Actualizar el registro del evento con el payment_intent_id
    if payment_intent_id and not webhook_event.payment_intent_id:
        webhook_event.payment_intent_id = payment_intent_id
        webhook_event.save()
    
    # Procesar según el tipo de evento
    try:
        if event_type == 'payment_intent.succeeded':
            result = _handle_payment_intent_succeeded(payment_intent_id, event)
            if result['success']:
                webhook_event.processed = True
                webhook_event.processed_at = timezone.now()
                webhook_event.save()
                logger.info(f"Evento {event_id} procesado exitosamente")
                return JsonResponse({'status': 'success'}, status=200)
            else:
                webhook_event.error_message = result.get('error', 'Error desconocido')
                webhook_event.save()
                logger.error(f"Error al procesar evento {event_id}: {result.get('error')}")
                # Retornar 200 para que Stripe no reintente (el error ya está registrado)
                return JsonResponse({'status': 'error', 'error': result.get('error')}, status=200)
        
        elif event_type == 'payment_intent.payment_failed':
            result = _handle_payment_intent_failed(payment_intent_id, event)
            if result['success']:
                webhook_event.processed = True
                webhook_event.processed_at = timezone.now()
                webhook_event.save()
                logger.info(f"Evento {event_id} procesado exitosamente")
                return JsonResponse({'status': 'success'}, status=200)
            else:
                webhook_event.error_message = result.get('error', 'Error desconocido')
                webhook_event.save()
                logger.error(f"Error al procesar evento {event_id}: {result.get('error')}")
                return JsonResponse({'status': 'error', 'error': result.get('error')}, status=200)
        
        else:
            # Evento no manejado, pero registrarlo
            logger.info(f"Evento {event_type} recibido pero no procesado")
            webhook_event.processed = True
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            return JsonResponse({'status': 'ignored', 'event_type': event_type}, status=200)
    
    except Exception as e:
        logger.exception(f"Error inesperado al procesar evento {event_id}: {str(e)}")
        webhook_event.error_message = str(e)
        webhook_event.save()
        # Retornar 200 para que Stripe no reintente infinitamente
        return JsonResponse({'status': 'error', 'error': str(e)}, status=200)


def _handle_payment_intent_succeeded(payment_intent_id, event):
    """
    Manejar evento payment_intent.succeeded
    
    Busca el Payment por stripe_payment_intent_id y lo marca como APROBADO
    """
    from django.utils import timezone
    
    if not payment_intent_id:
        return {'success': False, 'error': 'payment_intent_id no encontrado en el evento'}
    
    try:
        # Buscar el pago por stripe_payment_intent_id
        payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
        
        if not payment:
            # Si no existe el pago, registrar en log pero no fallar el webhook
            logger.warning(f"Payment no encontrado para payment_intent_id: {payment_intent_id}")
            return {'success': True, 'warning': 'Payment no encontrado'}
        
        # Verificar que el pago no esté ya aprobado (idempotencia adicional)
        if payment.status == 'APROBADO':
            logger.info(f"Payment {payment.id} ya está aprobado, ignorando evento")
            return {'success': True, 'warning': 'Payment ya estaba aprobado'}
        
        # Obtener detalles del Payment Intent de Stripe
        intent_details = StripePaymentService.get_payment_intent_details(payment_intent_id)
        
        # Actualizar el pago
        payment.status = 'APROBADO'
        payment.approved_at = timezone.now()
        payment.transaction_id = payment_intent_id
        
        # Actualizar card_last_four si está disponible
        if intent_details.get('success') and intent_details.get('card_last_four'):
            payment.card_last_four = intent_details['card_last_four']
        
        # Guardar el pago (el modelo manejará el historial de cambios)
        payment._changed_by_user = None  # Webhook, sin usuario
        payment._status_change_notes = 'Pago aprobado automáticamente por webhook de Stripe'
        payment.save()
        
        logger.info(f"Payment {payment.id} aprobado exitosamente por webhook")
        return {'success': True, 'payment_id': str(payment.id)}
    
    except Exception as e:
        logger.exception(f"Error al procesar payment_intent.succeeded: {str(e)}")
        return {'success': False, 'error': str(e)}


def _handle_payment_intent_failed(payment_intent_id, event):
    """
    Manejar evento payment_intent.payment_failed
    
    Busca el Payment por stripe_payment_intent_id y lo marca como RECHAZADO
    """
    if not payment_intent_id:
        return {'success': False, 'error': 'payment_intent_id no encontrado en el evento'}
    
    try:
        # Buscar el pago por stripe_payment_intent_id
        payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent_id).first()
        
        if not payment:
            # Si no existe el pago, registrar en log pero no fallar el webhook
            logger.warning(f"Payment no encontrado para payment_intent_id: {payment_intent_id}")
            return {'success': True, 'warning': 'Payment no encontrado'}
        
        # Verificar que el pago no esté ya rechazado (idempotencia adicional)
        if payment.status == 'RECHAZADO':
            logger.info(f"Payment {payment.id} ya está rechazado, ignorando evento")
            return {'success': True, 'warning': 'Payment ya estaba rechazado'}
        
        # Obtener el mensaje de error del evento si está disponible
        error_message = 'Pago rechazado por Stripe'
        if 'data' in event and 'object' in event['data']:
            last_payment_error = event['data']['object'].get('last_payment_error')
            if last_payment_error:
                error_message = last_payment_error.get('message', error_message)
        
        # Actualizar el pago
        payment.status = 'RECHAZADO'
        if not payment.notes:
            payment.notes = error_message
        elif error_message not in payment.notes:
            payment.notes = f"{payment.notes}\n{error_message}"
        
        # Guardar el pago
        payment._changed_by_user = None  # Webhook, sin usuario
        payment._status_change_notes = f'Pago rechazado automáticamente por webhook de Stripe: {error_message}'
        payment.save()
        
        logger.info(f"Payment {payment.id} rechazado por webhook: {error_message}")
        return {'success': True, 'payment_id': str(payment.id)}
    
    except Exception as e:
        logger.exception(f"Error al procesar payment_intent.payment_failed: {str(e)}")
        return {'success': False, 'error': str(e)}

