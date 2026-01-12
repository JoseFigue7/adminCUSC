from django.contrib import admin
from .models import (
    RegistrationStatus, DocumentType, AcademicCertificate,
    CourseCertificate, UniversityTitle
)


@admin.register(RegistrationStatus)
class RegistrationStatusAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('codigo', 'nombre')
    ordering = ('nombre',)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('codigo', 'nombre')
    ordering = ('nombre',)


@admin.register(AcademicCertificate)
class AcademicCertificateAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'registration_status', 'document_type',
        'school_year', 'curp', 'general_average', 'is_sep_registered',
        'created_at'
    )
    list_filter = ('registration_status', 'document_type', 'is_sep_registered', 'school_year')
    search_fields = ('student__first_name', 'student__first_last_name', 'curp', 'document_folio')
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('student', 'curp')
        }),
        ('Información SEP', {
            'fields': (
                'registration_status', 'document_type', 'school_year',
                'general_average', 'issuance_date', 'document_folio'
            )
        }),
        ('Registro SEP', {
            'fields': ('is_sep_registered', 'sep_registration_date')
        }),
        ('Archivos', {
            'fields': ('certificate_file',)
        }),
        ('Información Adicional', {
            'fields': ('notes',)
        }),
        ('Información del Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CourseCertificate)
class CourseCertificateAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'certificate_name', 'total_courses',
        'average_grade', 'issuance_date', 'is_printed'
    )
    list_filter = ('is_printed', 'issuance_date')
    search_fields = ('student__first_name', 'student__first_last_name', 'certificate_name')
    readonly_fields = ('id', 'created_at', 'updated_at', 'total_courses', 'average_grade')
    filter_horizontal = ('course_enrollments',)
    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('student',)
        }),
        ('Información del Certificado', {
            'fields': ('certificate_name', 'course_enrollments', 'total_courses', 'average_grade')
        }),
        ('Fechas', {
            'fields': ('issuance_date',)
        }),
        ('Estado', {
            'fields': ('is_printed',)
        }),
        ('Archivos', {
            'fields': ('certificate_file',)
        }),
        ('Información Adicional', {
            'fields': ('notes',)
        }),
        ('Información del Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UniversityTitle)
class UniversityTitleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'student', 'title_name', 'pensum_completed',
        'all_courses_approved', 'requirements_met', 'is_printed'
    )
    list_filter = ('requirements_met', 'is_printed', 'pensum_completed', 'all_courses_approved')
    search_fields = ('student__first_name', 'student__first_last_name', 'title_name')
    readonly_fields = (
        'id', 'created_at', 'updated_at', 'pensum_completed',
        'all_courses_approved', 'average_grade'
    )
    fieldsets = (
        ('Información del Estudiante', {
            'fields': ('student',)
        }),
        ('Información del Título', {
            'fields': ('title_name',)
        }),
        ('Requisitos', {
            'fields': (
                'pensum_completed', 'all_courses_approved', 'thesis_approved',
                'average_grade', 'requirements_met'
            )
        }),
        ('Registro SEP', {
            'fields': ('academic_certificate',)
        }),
        ('Fechas', {
            'fields': ('issuance_date',)
        }),
        ('Estado', {
            'fields': ('is_printed',)
        }),
        ('Archivos', {
            'fields': ('title_file',)
        }),
        ('Información Adicional', {
            'fields': ('notes',)
        }),
        ('Información del Sistema', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['validate_requirements_action']
    
    def validate_requirements_action(self, request, queryset):
        """Acción para validar requisitos de títulos seleccionados"""
        updated = 0
        for title in queryset:
            if title.validate_requirements():
                updated += 1
        self.message_user(request, f'{updated} títulos actualizados correctamente.')
    validate_requirements_action.short_description = 'Validar requisitos de títulos seleccionados'
