from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from django.utils.safestring import mark_safe
from .models import Payment, Scholarship, PaymentConfiguration, PaymentType


class ScholarshipInline(admin.StackedInline):
    """Inline para becas de estudiantes"""
    model = Scholarship
    can_delete = True
    verbose_name = "Beca"
    verbose_name_plural = "Beca"
    fields = ('scholarship_type', 'percentage', 'start_date', 'end_date', 'status', 'notes')
    extra = 0


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'payment_type_display', 'payment_period', 
        'amount_display', 'penalty_display', 'payment_method_badge',
        'status_badge', 'receipt_link', 'payment_date'
    ]
    list_filter = ['payment_method', 'status', 'year', 'month', 'payment_date', 'payment_type']
    search_fields = [
        'student__first_name', 'student__last_name', 
        'student__carnet', 'receipt_number', 'transaction_id',
        'payment_type__name', 'payment_type__code'
    ]
    readonly_fields = [
        'id', 'payment_date', 'created_at', 'updated_at',
        'student_scholarship_info', 'penalty_calculation_info'
    ]
    date_hierarchy = 'payment_date'
    
    fieldsets = (
        ('Información del Pago', {
            'fields': (
                'student',
                'payment_type',
                ('month', 'year', 'semester'),
                ('amount', 'base_amount', 'penalty_amount'),
                ('due_date', 'payment_date'),
                'payment_method',
                'status',
            ),
        }),
        ('Detalles del Método de Pago', {
            'fields': (
                'transfer_receipt',
                'receipt_number',
                'card_last_four',
                'transaction_id',
            ),
            'classes': ('collapse',),
        }),
        ('Información de Beca', {
            'fields': ('student_scholarship_info',),
            'classes': ('collapse',),
        }),
        ('Información de Mora', {
            'fields': ('penalty_calculation_info',),
            'classes': ('collapse',),
        }),
        ('Notas', {
            'fields': ('notes',),
        }),
        ('Información del Sistema', {
            'fields': (
                'id',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_payments', 'reject_payments', 'mark_as_review']
    
    def student_link(self, obj):
        """Link al estudiante"""
        url = reverse('admin:students_student_change', args=[obj.student.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong> ({})</a>',
            url,
            obj.student.get_full_name(),
            obj.student.carnet or 'Sin carnet'
        )
    student_link.short_description = 'Estudiante'
    student_link.admin_order_field = 'student__first_name'
    
    def payment_type_display(self, obj):
        """Tipo de pago"""
        if obj.payment_type:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{}</small>',
                obj.payment_type.name,
                obj.payment_type.code
            )
        return format_html('<span style="color: #999;">N/A</span>')
    payment_type_display.short_description = 'Tipo de Pago'
    payment_type_display.admin_order_field = 'payment_type__name'
    
    def payment_period(self, obj):
        """Período de pago"""
        if obj.month and obj.year:
            return format_html(
                '<strong>{}</strong> {}',
                obj.get_month_display(),
                obj.year
            )
        elif obj.semester and obj.year:
            return format_html(
                '<strong>Semestre {}</strong> {}',
                obj.semester,
                obj.year
            )
        elif obj.year:
            return format_html('<strong>{}</strong>', obj.year)
        return format_html('<span style="color: #999;">N/A</span>')
    payment_period.short_description = 'Período'
    payment_period.admin_order_field = 'year'
    
    def penalty_display(self, obj):
        """Mostrar información de mora"""
        if obj.penalty_amount and obj.penalty_amount > 0:
            penalty_str = f"MX${float(obj.penalty_amount):,.2f}"
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠ {}</span>',
                penalty_str
            )
        return format_html('<span style="color: #28a745;">✓ Sin mora</span>')
    penalty_display.short_description = 'Mora'
    penalty_display.admin_order_field = 'penalty_amount'
    
    def amount_display(self, obj):
        """Monto formateado"""
        amount_str = f"MX${float(obj.amount):,.2f}"
        return format_html(
            '<strong style="color: #28a745; font-size: 14px;">{}</strong>',
            amount_str
        )
    amount_display.short_description = 'Monto'
    amount_display.admin_order_field = 'amount'
    
    def payment_method_badge(self, obj):
        """Badge para método de pago"""
        colors = {
            'TRANSFERENCIA': '#007bff',
            'TARJETA': '#28a745',
            'EFECTIVO': '#17a2b8'
        }
        icons = {
            'TRANSFERENCIA': '🏦',
            'TARJETA': '💳',
            'EFECTIVO': '💵'
        }
        color = colors.get(obj.payment_method, '#6c757d')
        icon = icons.get(obj.payment_method, '💰')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{} {}</span>',
            color,
            icon,
            obj.get_payment_method_display()
        )
    payment_method_badge.short_description = 'Método'
    payment_method_badge.admin_order_field = 'payment_method'
    
    def status_badge(self, obj):
        """Badge para estado del pago"""
        colors = {
            'PENDIENTE': '#ffc107',
            'EN_REVISION': '#17a2b8',
            'APROBADO': '#28a745',
            'RECHAZADO': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def receipt_link(self, obj):
        """Link al comprobante"""
        if obj.transfer_receipt:
            return format_html(
                '<a href="{}" target="_blank">📄 Ver comprobante</a>',
                obj.transfer_receipt.url
            )
        if obj.receipt_number:
            return format_html(
                '<span style="color: #17a2b8;">Recibo: {}</span>',
                obj.receipt_number
            )
        return format_html('<span style="color: #999;">Sin comprobante</span>')
    receipt_link.short_description = 'Comprobante'
    
    def student_scholarship_info(self, obj):
        """Información de beca del estudiante"""
        if hasattr(obj.student, 'scholarship') and obj.student.scholarship:
            scholarship = obj.student.scholarship
            return format_html(
                '<div style="background-color: #e7f3ff; padding: 10px; border-radius: 5px;">'
                '<strong>Tipo:</strong> {}<br>'
                '<strong>Porcentaje:</strong> {}%<br>'
                '<strong>Estado:</strong> {}<br>'
                '<strong>Fecha inicio:</strong> {}'
                '</div>',
                scholarship.get_scholarship_type_display(),
                scholarship.percentage,
                scholarship.get_status_display(),
                scholarship.start_date.strftime('%d/%m/%Y')
            )
        return format_html('<span style="color: #999;">El estudiante no tiene beca activa</span>')
    student_scholarship_info.short_description = 'Información de Beca'
    
    def penalty_calculation_info(self, obj):
        """Información sobre el cálculo de mora"""
        if not obj.payment_type or not obj.payment_type.has_penalty:
            return format_html('<span style="color: #999;">Este tipo de pago no aplica mora</span>')
        
        if not obj.due_date:
            return format_html('<span style="color: #ffc107;">⚠ No hay fecha límite configurada</span>')
        
        due_date_str = obj.due_date.strftime('%d/%m/%Y')
        penalty_days = obj.payment_type.penalty_days_offset
        penalty_type_display = obj.payment_type.get_penalty_type_display() if obj.payment_type.penalty_type else 'N/A'
        
        penalty_amount_str = ''
        base_amount_str = ''
        if obj.penalty_amount and obj.penalty_amount > 0:
            penalty_amount_str = f"MX${float(obj.penalty_amount):,.2f}"
            if obj.base_amount:
                base_amount_str = f"MX${float(obj.base_amount):,.2f}"
        
        if penalty_amount_str and base_amount_str:
            return format_html(
                '<div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">'
                '<strong>Fecha límite:</strong> {}<br>'
                '<strong>Días de gracia:</strong> {}<br>'
                '<strong>Tipo de mora:</strong> {}<br>'
                '<strong style="color: #dc3545;">Mora aplicada:</strong> {}<br>'
                '<strong>Monto base:</strong> {}'
                '</div>',
                due_date_str, penalty_days, penalty_type_display, penalty_amount_str, base_amount_str
            )
        elif penalty_amount_str:
            return format_html(
                '<div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">'
                '<strong>Fecha límite:</strong> {}<br>'
                '<strong>Días de gracia:</strong> {}<br>'
                '<strong>Tipo de mora:</strong> {}<br>'
                '<strong style="color: #dc3545;">Mora aplicada:</strong> {}'
                '</div>',
                due_date_str, penalty_days, penalty_type_display, penalty_amount_str
            )
        else:
            return format_html(
                '<div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">'
                '<strong>Fecha límite:</strong> {}<br>'
                '<strong>Días de gracia:</strong> {}<br>'
                '<strong>Tipo de mora:</strong> {}'
                '</div>',
                due_date_str, penalty_days, penalty_type_display
            )
    penalty_calculation_info.short_description = 'Información de Mora'
    
    # Actions
    def approve_payments(self, request, queryset):
        """Aprobar pagos"""
        updated = queryset.update(status='APROBADO')
        self.message_user(request, f'{updated} pago(s) aprobado(s).')
    approve_payments.short_description = "Aprobar pagos seleccionados"
    
    def reject_payments(self, request, queryset):
        """Rechazar pagos"""
        updated = queryset.update(status='RECHAZADO')
        self.message_user(request, f'{updated} pago(s) rechazado(s).')
    reject_payments.short_description = "Rechazar pagos seleccionados"
    
    def mark_as_review(self, request, queryset):
        """Marcar como en revisión"""
        updated = queryset.update(status='EN_REVISION')
        self.message_user(request, f'{updated} pago(s) marcado(s) como en revisión.')
    mark_as_review.short_description = "Marcar como en revisión"


@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'scholarship_type_badge', 'percentage_display',
        'status_badge', 'duration_display', 'start_date'
    ]
    list_filter = ['scholarship_type', 'status', 'start_date']
    search_fields = ['student__first_name', 'student__last_name', 'student__carnet']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de la Beca', {
            'fields': (
                'student',
                'scholarship_type',
                'percentage',
                ('start_date', 'end_date'),
                'status',
            ),
        }),
        ('Notas', {
            'fields': ('notes',),
        }),
        ('Información del Sistema', {
            'fields': (
                'id',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    def student_link(self, obj):
        """Link al estudiante"""
        url = reverse('admin:students_student_change', args=[obj.student.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong> ({})</a>',
            url,
            obj.student.get_full_name(),
            obj.student.carnet or 'Sin carnet'
        )
    student_link.short_description = 'Estudiante'
    student_link.admin_order_field = 'student__first_name'
    
    def scholarship_type_badge(self, obj):
        """Badge para tipo de beca"""
        colors = {
            'COMPLETA': '#007bff',
            'MEDIA': '#17a2b8'
        }
        color = colors.get(obj.scholarship_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">🎓 {}</span>',
            color,
            obj.get_scholarship_type_display()
        )
    scholarship_type_badge.short_description = 'Tipo de Beca'
    scholarship_type_badge.admin_order_field = 'scholarship_type'
    
    def percentage_display(self, obj):
        """Porcentaje de descuento"""
        return format_html(
            '<strong style="color: #28a745; font-size: 14px;">{}%</strong>',
            obj.percentage
        )
    percentage_display.short_description = 'Descuento'
    percentage_display.admin_order_field = 'percentage'
    
    def status_badge(self, obj):
        """Badge para estado de la beca"""
        colors = {
            'ACTIVA': '#28a745',
            'SUSPENDIDA': '#ffc107',
            'FINALIZADA': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def duration_display(self, obj):
        """Duración de la beca"""
        if obj.end_date:
            return f"{obj.start_date.strftime('%d/%m/%Y')} - {obj.end_date.strftime('%d/%m/%Y')}"
        return f"Desde {obj.start_date.strftime('%d/%m/%Y')} (sin fin)"
    duration_display.short_description = 'Duración'


@admin.register(PaymentConfiguration)
class PaymentConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'career_link', 'monthly_amount_display', 'enrollment_fee_display',
        'status_badge', 'updated_at'
    ]
    list_filter = ['is_active', 'career']
    search_fields = ['career__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de Configuración', {
            'fields': (
                'career',
                ('monthly_amount', 'enrollment_fee'),
                'is_active',
            ),
        }),
        ('Información del Sistema', {
            'fields': (
                'id',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    def career_link(self, obj):
        """Link a la carrera"""
        url = reverse('admin:academics_career_change', args=[obj.career.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            url,
            obj.career.name
        )
    career_link.short_description = 'Carrera'
    career_link.admin_order_field = 'career__name'
    
    def monthly_amount_display(self, obj):
        """Monto mensual formateado"""
        amount_str = f"MX${float(obj.monthly_amount):,.2f}"
        return format_html(
            '<strong style="color: #007bff; font-size: 14px;">{}</strong>',
            amount_str
        )
    monthly_amount_display.short_description = 'Monto Mensual'
    monthly_amount_display.admin_order_field = 'monthly_amount'
    
    def enrollment_fee_display(self, obj):
        """Cuota de inscripción formateada"""
        fee_str = f"MX${float(obj.enrollment_fee):,.2f}"
        return format_html(
            '<strong style="color: #17a2b8; font-size: 14px;">{}</strong>',
            fee_str
        )
    enrollment_fee_display.short_description = 'Cuota de Inscripción'
    enrollment_fee_display.admin_order_field = 'enrollment_fee'
    
    def status_badge(self, obj):
        """Badge para estado"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✓ Activa</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✗ Inactiva</span>'
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'is_active'


@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'amount_display', 'penalty_display',
        'requirements_display', 'status_badge', 'updated_at'
    ]
    list_filter = [
        'is_active', 'has_penalty', 'requires_career', 'requires_semester', 
        'requires_month', 'requires_year', 'requires_quantity', 'penalty_type'
    ]
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información del Tipo de Pago', {
            'fields': (
                'code',
                'name',
                'description',
                'amount',
                'is_active',
            ),
        }),
        ('Campos Requeridos', {
            'fields': (
                'requires_career',
                'requires_semester',
                'requires_month',
                'requires_year',
                'requires_quantity',
            ),
            'description': 'Seleccione qué campos son requeridos para este tipo de pago',
        }),
        ('Configuración de Mora', {
            'fields': (
                'has_penalty',
                'penalty_due_date_field',
                'penalty_days_offset',
                'penalty_type',
                'penalty_amount',
                'penalty_percentage',
                'penalty_max_amount',
            ),
            'description': 'Configure las condiciones de mora para este tipo de pago. La mora se aplica después de la fecha límite más los días de gracia.',
            'classes': ('collapse',),
        }),
        ('Información del Sistema', {
            'fields': (
                'id',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    def amount_display(self, obj):
        """Monto formateado"""
        if obj.amount:
            amount_str = f"MX${float(obj.amount):,.2f}"
            return format_html(
                '<strong style="color: #28a745; font-size: 14px;">{}</strong>',
                amount_str
            )
        return format_html('<span style="color: #999;">Variable</span>')
    amount_display.short_description = 'Monto'
    amount_display.admin_order_field = 'amount'
    
    def penalty_display(self, obj):
        """Mostrar información de mora"""
        if not obj.has_penalty:
            return format_html('<span style="color: #999;">Sin mora</span>')
        
        penalty_info = []
        if obj.penalty_type:
            penalty_info.append(obj.get_penalty_type_display())
        
        if obj.penalty_amount:
            penalty_info.append(f"MX${float(obj.penalty_amount):.2f}")
        elif obj.penalty_percentage:
            penalty_info.append(f"{float(obj.penalty_percentage)}%")
        
        if obj.penalty_days_offset > 0:
            penalty_info.append(f"{obj.penalty_days_offset} días gracia")
        
        if penalty_info:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">⚠ {}</span>',
                ' | '.join(penalty_info)
            )
        return format_html('<span style="color: #ffc107;">⚠ Configurada</span>')
    penalty_display.short_description = 'Mora'
    penalty_display.admin_order_field = 'has_penalty'
    
    def requirements_display(self, obj):
        """Mostrar campos requeridos"""
        requirements = []
        if obj.requires_career:
            requirements.append('Carrera')
        if obj.requires_semester:
            requirements.append('Semestre')
        if obj.requires_month:
            requirements.append('Mes')
        if obj.requires_year:
            requirements.append('Año')
        if obj.requires_quantity:
            requirements.append('Cantidad')
        
        if requirements:
            return format_html(
                '<span style="color: #007bff;">{}</span>',
                ', '.join(requirements)
            )
        return format_html('<span style="color: #999;">Ninguno</span>')
    requirements_display.short_description = 'Campos Requeridos'
    
    def status_badge(self, obj):
        """Badge para estado"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✗ Inactivo</span>'
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'is_active'
