from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, HttpResponse
import json
import logging
from django.db.models import Q, Sum, Count, Avg
from django.db.models.functions import TruncDate
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
        if self.action in ['list', 'retrieve', 'student_status', 'statistics', 'pending_count', 'pending_transfers']:
            # Permitir ver a usuarios autenticados
            return [permissions.IsAuthenticated()]
        # Para crear/editar/eliminar/aprobar/rechazar requiere permiso específico
        return [permissions.IsAuthenticated(), HasPermission('manage_payments')]
    
    def perform_create(self, serializer):
        """Asignar automáticamente carrera y usuario creador al crear un pago"""
        # Obtener el estudiante para asignar su carrera
        student_id = serializer.validated_data.get('student')
        user = self.request.user if self.request.user.is_authenticated else None
        
        # El modelo Payment.save() ya maneja la lógica de aprobación automática
        # Solo necesitamos asignar carrera y usuario creador
        save_data = {
            'career': student_id.career if student_id and student_id.career else None,
            'created_by': user,
        }
        
        # Pasar usuario para el historial de cambios
        payment = serializer.save(**save_data)
        payment._changed_by_user = user
        payment._status_change_notes = 'Pago creado'
        
        # No establecer status aquí, el modelo lo maneja automáticamente
        return payment
    
    def perform_update(self, serializer):
        """Capturar usuario que realiza el cambio"""
        user = self.request.user if self.request.user.is_authenticated else None
        instance = serializer.save()
        instance._changed_by_user = user
        instance._status_change_notes = getattr(self.request.data, 'notes', '') or ''
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
            try:
                daily_payments = approved_payments.filter(
                    payment_date__gte=last_15_days_start.date()
                ).annotate(
                    date=TruncDate('payment_date')
                ).values('date').annotate(
                    total=Sum('amount'),
                    count=Count('id')
                ).order_by('date')
            except Exception:
                # Fallback: agrupar por fecha manualmente si TruncDate falla
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


class ScholarshipViewSet(viewsets.ModelViewSet):
    queryset = Scholarship.objects.all()
    serializer_class = ScholarshipSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission('manage_scholarships')]
    
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
    permission_classes = [permissions.IsAuthenticated, HasPermission('manage_settings')]


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

