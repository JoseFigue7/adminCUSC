from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone


class Payment(models.Model):
    """Modelo para pagos de estudiantes"""
    
    PAYMENT_METHODS = [
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('EFECTIVO', 'Efectivo'),
    ]
    
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('NO_PAGADO', 'No Pagado'),
        ('EN_REVISION', 'En Revisión'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('MORA', 'Mora'),
    ]
    
    MONTHS = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='payments', verbose_name='Estudiante')
    career = models.ForeignKey(
        'academics.Career',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Carrera',
        help_text='Carrera del estudiante al momento del pago (para trazabilidad)'
    )
    payment_type = models.ForeignKey('PaymentType', on_delete=models.PROTECT, null=True, blank=True, related_name='payments', verbose_name='Tipo de pago')
    cuatrimestre_enrollment = models.ForeignKey(
        'academics.CuatrimestreEnrollment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Inscripción al Cuatrimestre',
        help_text='Inscripción al cuatrimestre relacionada con este pago (inscripción o colegiatura)'
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name='Método de pago')
    
    # DEPRECATED: Este campo se mantiene solo para compatibilidad con registros existentes y reportes.
    # Usar final_amount en su lugar. El campo amount se actualiza automáticamente con final_amount en save().
    # Hacer el campo opcional para evitar problemas de validación, se establecerá automáticamente en save()
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,  # Permitir null temporalmente hasta que se calcule en save()
        blank=True,  # Permitir blank para evitar ValidationError
        default=Decimal('0.00'),  # Valor por defecto para evitar ValidationError
        validators=[MinValueValidator(Decimal('0.00'))],  # Permitir 0 para pago 100 (gratis)
        verbose_name='Monto',
        help_text='DEPRECATED: Usar final_amount. Se mantiene para compatibilidad.'
    )
    
    # Nuevos campos para desglose de montos
    original_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],  # Permitir 0 para pago 100 (gratis)
        verbose_name='Monto original',
        help_text='Monto sin beca ni mora (monto base del pago)'
    )
    scholarship_discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Descuento por beca',
        help_text='Monto de descuento aplicado según beca activa del estudiante'
    )
    final_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],  # Permitir 0 para pago 100 (gratis)
        verbose_name='Monto final',
        help_text='Monto final a pagar: original_amount - scholarship_discount_amount + penalty_amount'
    )
    
    month = models.IntegerField(choices=MONTHS, null=True, blank=True, verbose_name='Mes')
    year = models.IntegerField(null=True, blank=True, verbose_name='Año')
    semester = models.IntegerField(null=True, blank=True, verbose_name='Semestre/Trimestre')
    quantity = models.IntegerField(null=True, blank=True, verbose_name='Cantidad')
    payment_date = models.DateField(null=True, blank=True, verbose_name='Fecha programada de pago', help_text='Fecha programada para el pago (día 1 del mes correspondiente para colegiaturas mensuales)')
    due_date = models.DateField(null=True, blank=True, verbose_name='Fecha límite de pago')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE', verbose_name='Estado')
    
    # Información de mora
    penalty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Monto de mora aplicado'
    )
    base_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],  # Permitir 0 para evitar ValidationError
        verbose_name='Monto base (sin mora)'
    )
    
    # Referencia del pago (número de recibo, referencia de transferencia, número de tarjeta, etc.)
    payment_reference = models.CharField(max_length=100, blank=True, verbose_name='Referencia de pago')
    
    # Comprobante de pago (imagen/PDF) - disponible para todos los métodos
    transfer_receipt = models.FileField(upload_to='payment_receipts/', null=True, blank=True, verbose_name='Comprobante de pago')
    
    # Para efectivo
    receipt_number = models.CharField(max_length=50, blank=True, verbose_name='Número de recibo')
    
    # Para tarjeta
    card_last_four = models.CharField(max_length=4, blank=True, verbose_name='Últimos 4 dígitos de tarjeta')
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name='ID de transacción')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name='Stripe Payment Intent ID', help_text='ID del Payment Intent de Stripe para rastrear el pago')
    
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    # Trazabilidad: usuarios que crearon y aprobaron el pago
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_created',
        verbose_name='Creado por',
        help_text='Usuario que creó el registro del pago'
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments_approved',
        verbose_name='Aprobado por',
        help_text='Usuario que aprobó el pago'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de aprobación')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-payment_date']
    
    def __str__(self):
        if self.payment_type:
            return f"Pago de {self.student.get_full_name()} - {self.payment_type.name}"
        return f"Pago de {self.student.get_full_name()} - {self.get_month_display() if self.month else 'N/A'} {self.year if self.year else ''}"
    
    def _get_active_scholarship(self):
        """
        Obtiene la beca activa del estudiante si existe y está vigente.
        
        Returns:
            Scholarship o None: La beca activa del estudiante, o None si no tiene beca activa.
        """
        if not self.student:
            return None
        
        try:
            scholarship = self.student.scholarship
            if not scholarship:
                return None
            
            # Verificar que la beca esté activa
            if scholarship.status != 'ACTIVA':
                return None
            
            # Verificar que la fecha de pago esté dentro del rango de vigencia de la beca
            payment_date = self.payment_date or timezone.now().date()
            if scholarship.start_date > payment_date:
                return None
            
            if scholarship.end_date and scholarship.end_date < payment_date:
                return None
            
            return scholarship
        except AttributeError:
            # El estudiante no tiene beca asociada
            return None
    
    def _calculate_amounts(self):
        """
        Calcula automáticamente los montos del pago:
        - original_amount: monto sin beca ni mora
        - scholarship_discount_amount: descuento según beca activa
        - penalty_amount: mora calculada sobre (original_amount - scholarship_discount_amount)
        - final_amount: original_amount - scholarship_discount_amount + penalty_amount
        
        Este método se ejecuta automáticamente en save().
        """
        # 1. Determinar original_amount (monto sin beca ni mora)
        # Si original_amount no está establecido, usar amount o base_amount como referencia
        if not self.original_amount:
            if self.base_amount:
                # Si existe base_amount, usarlo como original_amount
                self.original_amount = self.base_amount
            elif self.amount:
                # Si no hay base_amount pero hay amount, intentar inferir original_amount
                # Para registros existentes, el amount puede incluir mora, así que usamos base_amount si existe
                # Si no, asumimos que amount es el original (sin mora ni beca)
                self.original_amount = self.amount
            else:
                # Si no hay ningún monto, verificar si es pago 100 (gratis)
                # Cargar payment_type si no está cargado
                payment_type_code = None
                if self.payment_type:
                    payment_type_code = self.payment_type.code
                elif self.payment_type_id:
                    try:
                        from django.apps import apps
                        PaymentType = apps.get_model('payments', 'PaymentType')
                        payment_type = PaymentType.objects.get(id=self.payment_type_id)
                        payment_type_code = payment_type.code
                    except PaymentType.DoesNotExist:
                        pass
                
                if payment_type_code == '100':
                    # Para pago 100, establecer montos en 0
                    self.original_amount = Decimal('0.00')
                else:
                    # Si no hay ningún monto y no es pago gratis, usar 0 como fallback
                    # Esto evita ValidationError pero debería ser manejado por el serializer
                    self.original_amount = Decimal('0.00')
        
        # 2. Calcular descuento por beca
        scholarship = self._get_active_scholarship()
        if scholarship:
            # Calcular descuento basado en el porcentaje de la beca
            self.scholarship_discount_amount = self.original_amount * (scholarship.percentage / Decimal('100.00'))
        else:
            # Si el estudiante NO tiene beca activa, el descuento es 0
            self.scholarship_discount_amount = Decimal('0.00')
        
        # 3. Calcular mora sobre el monto después del descuento de beca
        # La mora se calcula sobre: original_amount - scholarship_discount_amount
        amount_after_scholarship = self.original_amount - self.scholarship_discount_amount
        
        if self.payment_type and self.payment_type.has_penalty and self.due_date:
            # Calcular mora sobre el monto después del descuento de beca
            calculated_penalty = self.payment_type.calculate_penalty(
                amount_after_scholarship,  # Base para cálculo de mora: original - descuento beca
                self.due_date,
                self.payment_date
            )
            self.penalty_amount = calculated_penalty
        else:
            # Si no hay configuración de mora, la mora es 0
            self.penalty_amount = Decimal('0.00')
        
        # 4. Calcular monto final: original - descuento + mora
        self.final_amount = self.original_amount - self.scholarship_discount_amount + self.penalty_amount
        
        # 5. Mantener compatibilidad: actualizar amount con final_amount para reportes existentes
        # DEPRECATED: amount se mantiene solo para compatibilidad
        # Para pago 100 (gratis), permitir amount = 0
        # Asegurarse de que amount siempre tenga un valor
        if self.final_amount is not None:
            self.amount = self.final_amount
        elif self.original_amount is not None:
            # Si final_amount no está calculado pero original_amount sí, usar original_amount
            self.amount = self.original_amount
        elif self.amount is None:
            # Si amount no está establecido, usar 0 como fallback
            self.amount = Decimal('0.00')
        
        # 6. Mantener base_amount para compatibilidad con código existente
        # base_amount ahora representa el monto después del descuento de beca (antes de mora)
        # Solo establecer base_amount si amount_after_scholarship es mayor a 0 (porque tiene MinValueValidator(0.01))
        if not self.base_amount:
            if amount_after_scholarship > Decimal('0.00'):
                self.base_amount = amount_after_scholarship
            else:
                # Si el monto después de beca es 0, no establecer base_amount (permitir null)
                self.base_amount = None
    
    def save(self, *args, **kwargs):
        """Calcular mora automáticamente, asignar carrera y aprobar pagos según método"""
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        
        # Asignar carrera del estudiante si no está asignada (para trazabilidad)
        if not self.career and self.student and self.student.career:
            self.career = self.student.career
        
        # Validación de negocio: transferencias no pueden ser aprobadas automáticamente al crear
        is_new_payment = not self.pk
        
        # Verificar si es pago 100 (gratis) - se aprueba automáticamente
        is_free_payment = False
        try:
            # Intentar obtener el código del tipo de pago
            if self.payment_type and hasattr(self.payment_type, 'code'):
                # Si payment_type está cargado, usar directamente
                if self.payment_type.code == '100':
                    is_free_payment = True
            elif self.payment_type_id:
                # Si no está cargado, obtenerlo desde la BD usando referencia diferida
                from django.apps import apps
                PaymentType = apps.get_model('payments', 'PaymentType')
                try:
                    payment_type = PaymentType.objects.get(id=self.payment_type_id)
                    if payment_type.code == '100':
                        is_free_payment = True
                except PaymentType.DoesNotExist:
                    pass
        except (AttributeError, Exception):
            # Si hay error, continuar sin marcar como gratis
            pass
        
        if is_new_payment:
            # Si es pago gratis (100), aprobar automáticamente sin importar el método
            if is_free_payment:
                self.status = 'APROBADO'
                if not self.approved_by and self.created_by:
                    self.approved_by = self.created_by
                if not self.approved_at:
                    self.approved_at = timezone.now()
            # Aprobar automáticamente solo pagos en efectivo
            # Los pagos con tarjeta quedan pendientes hasta que el webhook los confirme
            # Las transferencias pueden ser NO_PAGADO (para colegiaturas mensuales) o PENDIENTE
            elif self.payment_method == 'EFECTIVO':
                # Aprobar automáticamente pagos en efectivo
                # Incluso si el estado inicial era NO_PAGADO o MORA (para colegiaturas)
                # Cuando se registra un pago en efectivo, debe aprobarse automáticamente
                self.status = 'APROBADO'
                # Si no hay usuario aprobador, usar el creador
                if not self.approved_by and self.created_by:
                    self.approved_by = self.created_by
                if not self.approved_at:
                    self.approved_at = timezone.now()
            elif self.payment_method == 'TARJETA':
                # Los pagos con tarjeta quedan pendientes hasta que el webhook los confirme
                # El webhook payment_intent.succeeded es la única fuente de verdad
                # Solo cambiar estado si no es NO_PAGADO o MORA (para respetar estados de colegiatura)
                if self.status not in ['NO_PAGADO', 'MORA']:
                    self.status = 'PENDIENTE'
                # Limpiar campos de aprobación si se intentaron establecer
                if self.approved_by:
                    self.approved_by = None
                if self.approved_at:
                    self.approved_at = None
            elif self.payment_method == 'TRANSFERENCIA':
                # Las transferencias pueden ser NO_PAGADO (para colegiaturas mensuales) o PENDIENTE
                # Validar que no se intente crear una transferencia ya aprobada
                if self.status == 'APROBADO':
                    raise ValidationError(
                        'Las transferencias no pueden ser aprobadas automáticamente. '
                        'Deben quedar pendientes para confirmación manual.'
                    )
                # Solo cambiar estado si no es NO_PAGADO o MORA (para respetar estados de colegiatura)
                if self.status not in ['NO_PAGADO', 'MORA']:
                    self.status = 'PENDIENTE'
                # Limpiar campos de aprobación si se intentaron establecer
                if self.approved_by:
                    self.approved_by = None
                if self.approved_at:
                    self.approved_at = None
        
        # Calcular automáticamente todos los montos (original, descuento beca, mora, final)
        # Este método calcula:
        # - original_amount: monto sin beca ni mora
        # - scholarship_discount_amount: descuento según beca activa
        # - penalty_amount: mora calculada sobre (original_amount - scholarship_discount_amount)
        # - final_amount: original_amount - scholarship_discount_amount + penalty_amount
        # También actualiza amount para compatibilidad con código existente
        self._calculate_amounts()
        
        # Evaluar automáticamente si el pago debe estar en estado MORA
        # Solo si no está aprobado y tiene configuración de mora
        if self.status not in ['APROBADO', 'RECHAZADO', 'EN_REVISION']:
            if self.payment_type and self.due_date:
                if self.payment_type.has_penalty:
                    from datetime import date, timedelta
                    current_date = date.today()
                    # Calcular fecha efectiva de inicio de mora
                    grace_period_end = self.due_date + timedelta(days=self.payment_type.penalty_days_offset)
                    
                    # Si la fecha actual excede los días de gracia, cambiar a MORA
                    if current_date > grace_period_end:
                        # Solo cambiar a MORA si está en NO_PAGADO o PENDIENTE
                        if self.status in ['NO_PAGADO', 'PENDIENTE']:
                            self.status = 'MORA'
                    # Si la fecha actual no excede los días de gracia y está en MORA, volver a NO_PAGADO
                    elif self.status == 'MORA' and current_date <= grace_period_end:
                        self.status = 'NO_PAGADO'
        
        # Si payment_date no está establecido y es un nuevo pago, establecer la fecha actual
        if is_new_payment and not self.payment_date:
            self.payment_date = timezone.now().date()
        
        super().save(*args, **kwargs)


class Scholarship(models.Model):
    """Modelo para becas"""
    
    SCHOLARSHIP_TYPES = [
        ('COMPLETA', 'Beca Completa'),
        ('MEDIA', 'Media Beca'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('SUSPENDIDA', 'Suspendida'),
        ('FINALIZADA', 'Finalizada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='scholarship', verbose_name='Estudiante')
    scholarship_type = models.CharField(max_length=20, choices=SCHOLARSHIP_TYPES, verbose_name='Tipo de beca')
    start_date = models.DateField(verbose_name='Fecha de inicio')
    end_date = models.DateField(null=True, blank=True, verbose_name='Fecha de fin')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVA', verbose_name='Estado')
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Porcentaje de descuento'
    )
    notes = models.TextField(blank=True, verbose_name='Notas')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Beca'
        verbose_name_plural = 'Becas'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Beca {self.get_scholarship_type_display()} - {self.student.get_full_name()}"


class PaymentType(models.Model):
    """Modelo para tipos de pago disponibles"""
    
    PENALTY_TYPE_CHOICES = [
        ('FIXED', 'Monto Fijo'),
        ('PERCENTAGE', 'Porcentaje'),
        ('DAILY_FIXED', 'Monto Fijo Diario'),
        ('DAILY_PERCENTAGE', 'Porcentaje Diario'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, verbose_name='Código')
    name = models.CharField(max_length=200, verbose_name='Nombre')
    description = models.TextField(blank=True, verbose_name='Descripción')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],  # Permitir 0.00 para pagos gratuitos (código 100)
        verbose_name='Monto fijo (opcional)'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    requires_career = models.BooleanField(default=False, verbose_name='Requiere carrera')
    requires_semester = models.BooleanField(default=False, verbose_name='Requiere semestre/trimestre')
    requires_month = models.BooleanField(default=False, verbose_name='Requiere mes')
    requires_year = models.BooleanField(default=False, verbose_name='Requiere año')
    requires_quantity = models.BooleanField(default=False, verbose_name='Requiere cantidad')
    
    # Configuración de mora
    has_penalty = models.BooleanField(default=False, verbose_name='Aplica mora')
    penalty_due_date_field = models.CharField(
        max_length=50,
        blank=True,
        help_text='Campo que determina la fecha límite (ej: "month", "semester", "year")',
        verbose_name='Campo de fecha límite'
    )
    penalty_days_offset = models.IntegerField(
        default=0,
        help_text='Días después de la fecha límite para aplicar mora (0 = mismo día)',
        verbose_name='Días de gracia'
    )
    penalty_type = models.CharField(
        max_length=20,
        choices=PENALTY_TYPE_CHOICES,
        blank=True,
        verbose_name='Tipo de mora'
    )
    penalty_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Monto fijo de mora (si tipo es FIXED o DAILY_FIXED)',
        verbose_name='Monto de mora'
    )
    penalty_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Porcentaje de mora sobre el monto base (si tipo es PERCENTAGE o DAILY_PERCENTAGE)',
        verbose_name='Porcentaje de mora (%)'
    )
    penalty_max_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text='Monto máximo de mora (opcional, 0 = sin límite)',
        verbose_name='Monto máximo de mora'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tipo de Pago'
        verbose_name_plural = 'Tipos de Pago'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def calculate_penalty(self, base_amount, due_date, payment_date=None):
        """
        Calcula la mora basada en la configuración del tipo de pago
        
        Args:
            base_amount: Monto base del pago
            due_date: Fecha límite de pago
            payment_date: Fecha de pago (si None, usa fecha actual)
        
        Returns:
            Decimal: Monto de mora calculado
        """
        if not self.has_penalty:
            return Decimal('0.00')
        
        from datetime import date
        if payment_date is None:
            payment_date = date.today()
        
        # Calcular fecha efectiva de inicio de mora
        from datetime import timedelta
        penalty_start_date = due_date + timedelta(days=self.penalty_days_offset)
        
        # Si el pago es antes de la fecha de inicio de mora, no hay mora
        if payment_date <= penalty_start_date:
            return Decimal('0.00')
        
        # Calcular días de mora
        days_overdue = (payment_date - penalty_start_date).days
        
        if days_overdue <= 0:
            return Decimal('0.00')
        
        penalty_amount = Decimal('0.00')
        
        if self.penalty_type in ['FIXED', 'DAILY_FIXED']:
            if self.penalty_amount:
                if self.penalty_type == 'FIXED':
                    # Mora fija única
                    penalty_amount = self.penalty_amount
                else:
                    # Mora fija diaria
                    penalty_amount = self.penalty_amount * days_overdue
        elif self.penalty_type in ['PERCENTAGE', 'DAILY_PERCENTAGE']:
            if self.penalty_percentage:
                if self.penalty_type == 'PERCENTAGE':
                    # Porcentaje único sobre el monto base
                    penalty_amount = base_amount * (self.penalty_percentage / Decimal('100.00'))
                else:
                    # Porcentaje diario sobre el monto base
                    penalty_amount = base_amount * (self.penalty_percentage / Decimal('100.00')) * days_overdue
        
        # Aplicar límite máximo si existe
        if self.penalty_max_amount and self.penalty_max_amount > 0:
            penalty_amount = min(penalty_amount, self.penalty_max_amount)
        
        return penalty_amount


class PaymentConfiguration(models.Model):
    """Modelo para configuración de pagos por carrera"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    career = models.ForeignKey('academics.Career', on_delete=models.CASCADE, related_name='payment_configs', verbose_name='Carrera')
    monthly_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto mensual'
    )
    enrollment_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Cuota de inscripción'
    )
    is_active = models.BooleanField(default=True, verbose_name='Activa')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración de Pago'
        verbose_name_plural = 'Configuraciones de Pago'
        unique_together = ['career']
    
    def __str__(self):
        return f"Configuración de pago - {self.career.name}"


# ==================== MODELO DE HISTORIAL DE ESTADO ====================

class PaymentStatusHistory(models.Model):
    """Modelo para rastrear cambios de estado en Payment"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Foreign key al modelo principal
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Pago'
    )
    
    # Estados
    previous_status = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='Estado anterior'
    )
    new_status = models.CharField(
        max_length=50,
        verbose_name='Estado nuevo'
    )
    
    # Usuario que realizó el cambio
    changed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_status_changes',
        verbose_name='Cambiado por'
    )
    
    # Timestamp
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de cambio')
    
    # Comentario opcional
    comment = models.TextField(blank=True, verbose_name='Comentario')
    
    class Meta:
        verbose_name = 'Historial de Estado de Pago'
        verbose_name_plural = 'Historial de Estados de Pagos'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['payment', 'changed_at']),
            models.Index(fields=['changed_at']),
            models.Index(fields=['payment']),
        ]
    
    def __str__(self):
        return f"Pago {self.payment.id} - {self.previous_status or 'N/A'} → {self.new_status} ({self.changed_at})"


class StripeWebhookEvent(models.Model):
    """Modelo para rastrear eventos de webhook de Stripe y garantizar idempotencia"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stripe_event_id = models.CharField(max_length=255, unique=True, verbose_name='Stripe Event ID', help_text='ID único del evento de Stripe')
    event_type = models.CharField(max_length=100, verbose_name='Tipo de evento', help_text='Tipo de evento de Stripe (ej: payment_intent.succeeded)')
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Payment Intent ID', help_text='ID del Payment Intent relacionado')
    processed = models.BooleanField(default=False, verbose_name='Procesado', help_text='Indica si el evento ya fue procesado')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de procesamiento')
    error_message = models.TextField(blank=True, verbose_name='Mensaje de error', help_text='Mensaje de error si el procesamiento falló')
    raw_data = models.JSONField(null=True, blank=True, verbose_name='Datos del evento', help_text='Datos completos del evento para debugging')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Evento de Webhook de Stripe'
        verbose_name_plural = 'Eventos de Webhook de Stripe'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_event_id']),
            models.Index(fields=['payment_intent_id']),
            models.Index(fields=['processed']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.stripe_event_id} ({'Procesado' if self.processed else 'Pendiente'})"

