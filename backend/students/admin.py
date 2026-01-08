from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Student, Enrollment, StudentDocument


class StudentDocumentInline(admin.TabularInline):
    """Inline para documentos de estudiantes"""
    model = StudentDocument
    extra = 0
    fields = ('document_type', 'status', 'file', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = True
    show_change_link = True


class EnrollmentInline(admin.StackedInline):
    """Inline para inscripción de estudiantes"""
    model = Enrollment
    can_delete = False
    verbose_name = "Inscripción"
    verbose_name_plural = "Inscripción"
    fields = ('enrollment_date', 'status', 'contract_generated', 'contract_file')
    readonly_fields = ('enrollment_date',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        'carnet_display', 'full_name_display', 'email', 'career_link', 
        'status_badge', 'scholarship_badge', 'enrollment_date'
    ]
    list_filter = ['is_active', 'career', 'scholarship_type', 'pensum_closed', 'thesis_started', 'enrollment_date']
    search_fields = ['carnet', 'first_name', 'last_name', 'email', 'curp']
    readonly_fields = [
        'id', 'carnet', 'created_at', 'updated_at', 
        'student_documents_link', 'student_payments_link'
    ]
    inlines = [EnrollmentInline, StudentDocumentInline]
    
    fieldsets = (
        ('Información Personal', {
            'fields': (
                ('first_name', 'last_name'),
                ('email', 'phone'),
                ('date_of_birth', 'gender'),
                ('curp', 'address'),
            ),
            'classes': ('wide',),
        }),
        ('Información Académica', {
            'fields': (
                'career',
                'enrollment_date',
                ('pensum_closed', 'thesis_started'),
                'is_active',
            ),
        }),
        ('Información de Beca', {
            'fields': (
                'has_scholarship',
                'scholarship_type',
            ),
        }),
        ('Información del Sistema', {
            'fields': (
                'id',
                'carnet',
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
        ('Enlaces Relacionados', {
            'fields': (
                'student_documents_link',
                'student_payments_link',
            ),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['mark_active', 'mark_inactive', 'approve_enrollment']
    
    def carnet_display(self, obj):
        """Muestra el carnet con estilo"""
        if obj.carnet:
            return format_html(
                '<strong style="color: #007bff;">{}</strong>',
                obj.carnet
            )
        return format_html('<span style="color: #999;">Sin asignar</span>')
    carnet_display.short_description = 'Carnet'
    carnet_display.admin_order_field = 'carnet'
    
    def full_name_display(self, obj):
        """Muestra nombre completo con link"""
        url = reverse('admin:students_student_change', args=[obj.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            url,
            obj.get_full_name()
        )
    full_name_display.short_description = 'Nombre Completo'
    full_name_display.admin_order_field = 'first_name'
    
    def career_link(self, obj):
        """Muestra la carrera con link"""
        if obj.career:
            url = reverse('admin:academics_career_change', args=[obj.career.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.career.name
            )
        return '-'
    career_link.short_description = 'Carrera'
    career_link.admin_order_field = 'career__name'
    
    def status_badge(self, obj):
        """Badge para estado activo/inactivo"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✓ Activo</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✗ Inactivo</span>'
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'is_active'
    
    def scholarship_badge(self, obj):
        """Badge para tipo de beca"""
        colors = {
            'COMPLETA': '#007bff',
            'MEDIA': '#17a2b8',
            'NINGUNA': '#6c757d'
        }
        color = colors.get(obj.scholarship_type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_scholarship_type_display()
        )
    scholarship_badge.short_description = 'Beca'
    scholarship_badge.admin_order_field = 'scholarship_type'
    
    def student_documents_link(self, obj):
        """Link a documentos del estudiante"""
        count = obj.documents.count()
        url = f"{reverse('admin:students_studentdocument_changelist')}?student__id__exact={obj.id}"
        return format_html(
            '<a href="{}">Ver {} documento(s)</a>',
            url,
            count
        )
    student_documents_link.short_description = 'Documentos'
    
    def student_payments_link(self, obj):
        """Link a pagos del estudiante"""
        count = obj.payments.count()
        url = f"{reverse('admin:payments_payment_changelist')}?student__id__exact={obj.id}"
        return format_html(
            '<a href="{}">Ver {} pago(s)</a>',
            url,
            count
        )
    student_payments_link.short_description = 'Pagos'
    
    # Actions
    def mark_active(self, request, queryset):
        """Marcar estudiantes como activos"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} estudiante(s) marcado(s) como activo(s).')
    mark_active.short_description = "Marcar como activos"
    
    def mark_inactive(self, request, queryset):
        """Marcar estudiantes como inactivos"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} estudiante(s) marcado(s) como inactivo(s).')
    mark_inactive.short_description = "Marcar como inactivos"
    
    def approve_enrollment(self, request, queryset):
        """Aprobar inscripciones"""
        count = 0
        for student in queryset:
            if hasattr(student, 'enrollment'):
                student.enrollment.status = 'APROBADA'
                student.enrollment.save()
                count += 1
        self.message_user(request, f'{count} inscripción(es) aprobada(s).')
    approve_enrollment.short_description = "Aprobar inscripciones"


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'enrollment_date', 'status_badge', 
        'contract_status', 'contract_file_link'
    ]
    list_filter = ['status', 'contract_generated', 'enrollment_date']
    search_fields = ['student__first_name', 'student__last_name', 'student__carnet']
    readonly_fields = ['id', 'enrollment_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de Inscripción', {
            'fields': (
                'student',
                'enrollment_date',
                'status',
            ),
        }),
        ('Información de Contrato', {
            'fields': (
                'contract_generated',
                'contract_file',
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
    
    def status_badge(self, obj):
        """Badge para estado de inscripción"""
        colors = {
            'PENDIENTE': '#ffc107',
            'EN_REVISION': '#17a2b8',
            'APROBADA': '#28a745',
            'RECHAZADA': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'
    
    def contract_status(self, obj):
        """Estado del contrato"""
        if obj.contract_generated:
            return format_html(
                '<span style="color: #28a745;">✓ Generado</span>'
            )
        return format_html(
            '<span style="color: #ffc107;">⏳ Pendiente</span>'
        )
    contract_status.short_description = 'Contrato'
    contract_status.admin_order_field = 'contract_generated'
    
    def contract_file_link(self, obj):
        """Link al archivo de contrato"""
        if obj.contract_file:
            return format_html(
                '<a href="{}" target="_blank">Ver contrato</a>',
                obj.contract_file.url
            )
        return '-'
    contract_file_link.short_description = 'Archivo'


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'document_type_display', 'status_badge', 
        'file_link', 'created_at'
    ]
    list_filter = ['document_type', 'status', 'created_at']
    search_fields = ['student__first_name', 'student__last_name', 'student__carnet']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información del Documento', {
            'fields': (
                'student',
                'document_type',
                'status',
                'file',
                'notes',
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
    
    def student_link(self, obj):
        """Link al estudiante"""
        url = reverse('admin:students_student_change', args=[obj.student.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            url,
            obj.student.get_full_name()
        )
    student_link.short_description = 'Estudiante'
    student_link.admin_order_field = 'student__first_name'
    
    def document_type_display(self, obj):
        """Tipo de documento con icono"""
        return format_html(
            '<strong>{}</strong>',
            obj.get_document_type_display()
        )
    document_type_display.short_description = 'Tipo de Documento'
    document_type_display.admin_order_field = 'document_type'
    
    def status_badge(self, obj):
        """Badge para estado del documento"""
        colors = {
            'PENDIENTE': '#ffc107',
            'RECIBIDO': '#17a2b8',
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
    
    def file_link(self, obj):
        """Link al archivo"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📄 Ver archivo</a>',
                obj.file.url
            )
        return format_html('<span style="color: #999;">Sin archivo</span>')
    file_link.short_description = 'Archivo'
