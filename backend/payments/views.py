from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime
from .models import Payment, Scholarship, PaymentConfiguration, PaymentType
from .serializers import PaymentSerializer, ScholarshipSerializer, PaymentConfigurationSerializer, PaymentTypeSerializer, PublicPaymentSerializer
from .filters import PaymentFilter
from .stripe_service import StripePaymentService
from students.models import Student
from academics.models import Career
from users.permissions import HasPermission


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = PaymentFilter
    search_fields = ['student__first_name', 'student__last_name', 'student__carnet', 'payment_method', 'receipt_number', 'payment_type__name', 'payment_type__code']
    ordering_fields = ['payment_date', 'amount', 'year', 'month', 'student__first_name', 'student__last_name']
    ordering = ['-payment_date']
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'student_status']:
            # Permitir ver a usuarios autenticados
            return [permissions.IsAuthenticated()]
        # Para crear/editar/eliminar/aprobar/rechazar requiere permiso específico
        return [permissions.IsAuthenticated(), HasPermission('manage_payments')]
    
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
        payment = self.get_object()
        payment.status = 'APROBADO'
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        """Rechazar un pago"""
        payment = self.get_object()
        payment.status = 'RECHAZADO'
        if 'notes' in request.data:
            payment.notes = request.data['notes']
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_receipt(self, request, pk=None):
        """Subir comprobante de transferencia para un pago"""
        payment = self.get_object()
        
        if payment.payment_method != 'TRANSFERENCIA':
            return Response(
                {'error': 'Este pago no es de tipo transferencia'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        payment.transfer_receipt = file
        payment.status = 'EN_REVISION'
        payment.save()
        
        serializer = self.get_serializer(payment)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        currency='gtq',  # Quetzales guatemaltecos
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
    
    # Confirmar el pago en Stripe
    if payment_intent_id:
        payment_result = StripePaymentService.confirm_payment(payment_intent_id)
        
        if not payment_result['success']:
            return Response(
                {'error': payment_result.get('error', 'Error al procesar el pago')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el pago fue exitoso
        if payment_result['status'] != 'succeeded':
            return Response(
                {'error': f"El pago no fue exitoso. Estado: {payment_result['status']}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener últimos 4 dígitos de la tarjeta
        card_last_four = StripePaymentService.get_card_last_four(payment_intent_id) or "0000"
        transaction_id = payment_intent_id
        payment_status = 'APROBADO'
    else:
        # Fallback: si no hay payment_intent_id, usar el método anterior (solo para desarrollo)
        return Response(
            {'error': 'payment_intent_id es requerido para procesar el pago'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
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
    
    # Crear el pago en la base de datos
    payment = Payment.objects.create(
        student=student,
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
        transaction_id=transaction_id,
        status=payment_status
    )
    
    return Response({
        'success': True,
        'payment_id': str(payment.id),
        'transaction_id': transaction_id,
        'amount': str(final_amount),
        'penalty_amount': str(payment.penalty_amount),
        'total_amount': str(payment.amount),
        'status': payment.status,
        'message': 'Pago procesado exitosamente'
    }, status=status.HTTP_201_CREATED)

