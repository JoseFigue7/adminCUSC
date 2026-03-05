from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Payment(models.Model):
    """Modelo para pagos de estudiantes"""
    
    PAYMENT_METHODS = [
        ('TRANSFERENCIA', 'Transferencia'),
        ('TARJETA', 'Tarjeta'),
        ('EFECTIVO', 'Efectivo'),
    ]
    
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_REVISION', 'En Revisión'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
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
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto'
    )
    month = models.IntegerField(choices=MONTHS, null=True, blank=True, verbose_name='Mes')
    year = models.IntegerField(null=True, blank=True, verbose_name='Año')
    semester = models.IntegerField(null=True, blank=True, verbose_name='Semestre/Trimestre')
    quantity = models.IntegerField(null=True, blank=True, verbose_name='Cantidad')
    payment_date = models.DateField(auto_now_add=True, verbose_name='Fecha de pago')
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
        validators=[MinValueValidator(Decimal('0.01'))],
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
    
    def save(self, *args, **kwargs):
        """Calcular mora automáticamente, asignar carrera y aprobar pagos según método"""
        from django.utils import timezone
        from django.core.exceptions import ValidationError
        
        # Asignar carrera del estudiante si no está asignada (para trazabilidad)
        if not self.career and self.student and self.student.career:
            self.career = self.student.career
        
        # Aprobar automáticamente todos los pagos al crear o actualizar (efectivo, tarjeta y transferencia)
        is_new_payment = not self.pk
        
        # Si es un pago nuevo:
        # - Solo aprobar si NO tiene cuatrimestre_enrollment (pagos generados automáticamente deben quedar pendientes)
        # Si es una actualización (pago existente):
        # - Aprobar automáticamente SIEMPRE que no esté ya aprobado o rechazado
        #   (independientemente de si tiene cuatrimestre_enrollment, porque se está actualizando desde el formulario)
        if is_new_payment:
            # Para pagos nuevos: solo aprobar si no tienen cuatrimestre_enrollment
            should_auto_approve = (
                not self.cuatrimestre_enrollment and 
                self.status != 'APROBADO' and 
                self.status != 'RECHAZADO'
            )
        else:
            # Para actualizaciones: aprobar automáticamente siempre que no esté ya aprobado o rechazado
            # Esto permite que los pagos 102 (que tienen cuatrimestre_enrollment) se aprueben cuando se actualizan desde el formulario
            should_auto_approve = (
                self.status != 'APROBADO' and 
                self.status != 'RECHAZADO'
            )
        
        if should_auto_approve:
            # Aprobar automáticamente todos los métodos de pago (efectivo, tarjeta y transferencia)
            self.status = 'APROBADO'
            # Si no hay usuario aprobador, usar el creador o el usuario actual
            if not self.approved_by:
                if self.created_by:
                    self.approved_by = self.created_by
                # Si es una actualización y no hay creador, usar el usuario actual si está disponible
                elif hasattr(self, '_current_user') and self._current_user:
                    self.approved_by = self._current_user
            if not self.approved_at:
                self.approved_at = timezone.now()
        
        # Calcular mora automáticamente si hay fecha límite y tipo de pago
        if self.payment_type and self.payment_type.has_penalty and self.due_date:
            # Calcular mora si no se ha calculado ya
            if self.penalty_amount == Decimal('0.00') or not self.base_amount:
                # Establecer monto base
                if not self.base_amount:
                    self.base_amount = self.amount
                
                # Calcular mora
                calculated_penalty = self.payment_type.calculate_penalty(
                    self.base_amount,
                    self.due_date,
                    self.payment_date
                )
                self.penalty_amount = calculated_penalty
                
                # Actualizar monto total si es necesario
                # El monto total sería base_amount + penalty_amount
                if self.amount == self.base_amount:
                    self.amount = self.base_amount + self.penalty_amount
        
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
        validators=[MinValueValidator(Decimal('0.01'))],
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

