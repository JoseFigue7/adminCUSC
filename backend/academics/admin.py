from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Career, Cuatrimestre, Course, CourseEnrollment, CuatrimestreEnrollment, Thesis, CourseSchedule,
    AcademicPeriodConfig, MonthlyPaymentDueDate,
    CuatrimestreEnrollmentStatusHistory, ThesisStatusHistory
)


class CuatrimestreInline(admin.TabularInline):
    """Inline para cuatrimestres de carreras"""
    model = Cuatrimestre
    extra = 0
    fields = ('number', 'name')
    ordering = ('number',)


class CourseScheduleInline(admin.TabularInline):
    """Inline para horarios de cursos"""
    model = CourseSchedule
    extra = 1
    fields = ('day', 'start_time', 'end_time')
    ordering = ('day', 'start_time')


class CourseInline(admin.TabularInline):
    """Inline para cursos de cuatrimestres"""
    model = Course
    extra = 0
    fields = ('code', 'name', 'credits', 'is_required', 'prerequisite')
    ordering = ('code',)
    show_change_link = True


class CourseEnrollmentInline(admin.TabularInline):
    """Inline para cursos inscritos en un cuatrimestre"""
    model = CourseEnrollment
    extra = 0
    fields = ('course', 'status', 'final_grade')
    readonly_fields = ('enrollment_date',)
    show_change_link = True


@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name_display', 'total_credits_display', 
        'students_count', 'status_badge'
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    readonly_fields = ['id', 'created_at', 'updated_at', 'courses_count', 'students_count_link']
    inlines = [CuatrimestreInline]
    
    fieldsets = (
        ('Información de la Carrera', {
            'fields': (
                'code',
                'name',
                'description',
                'total_credits',
            ),
            'classes': ('wide',),
        }),
        ('Información SEP - Claves', {
            'fields': (
                ('institution_key', 'career_key'),
                'cct',
            ),
        }),
        ('Información SEP - RVOE', {
            'fields': (
                ('rvoe_agreement_number', 'rvoe_agreement_date'),
            ),
        }),
        ('Configuración de Becas', {
            'fields': (
                ('max_scholarships_full', 'max_scholarships_half'),
            ),
        }),
        ('Estado', {
            'fields': ('is_active',),
        }),
        ('Estadísticas', {
            'fields': ('courses_count', 'students_count_link'),
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
    
    def name_display(self, obj):
        """Nombre con link"""
        url = reverse('admin:academics_career_change', args=[obj.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            url,
            obj.name
        )
    name_display.short_description = 'Nombre'
    name_display.admin_order_field = 'name'
    
    def total_credits_display(self, obj):
        """Total de créditos"""
        return format_html(
            '<strong style="color: #007bff; font-size: 14px;">{} créditos</strong>',
            obj.total_credits
        )
    total_credits_display.short_description = 'Créditos'
    total_credits_display.admin_order_field = 'total_credits'
    
    def students_count(self, obj):
        """Cuenta de estudiantes"""
        count = obj.students.count()
        url = f"{reverse('admin:students_student_changelist')}?career__id__exact={obj.id}"
        return format_html(
            '<a href="{}">{} estudiante(s)</a>',
            url,
            count
        )
    students_count.short_description = 'Estudiantes'
    
    def courses_count(self, obj):
        """Cuenta de cursos"""
        return obj.courses.count()
    courses_count.short_description = 'Total de Cursos'
    
    def students_count_link(self, obj):
        """Link a estudiantes de la carrera"""
        count = obj.students.count()
        url = f"{reverse('admin:students_student_changelist')}?career__id__exact={obj.id}"
        return format_html(
            '<a href="{}">Ver {} estudiante(s)</a>',
            url,
            count
        )
    students_count_link.short_description = 'Estudiantes'
    
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


@admin.register(Cuatrimestre)
class CuatrimestreAdmin(admin.ModelAdmin):
    list_display = [
        'career_link', 'number', 'name', 'courses_count_display'
    ]
    list_filter = ['career']
    search_fields = ['name', 'career__name']
    readonly_fields = ['id', 'courses_count']
    inlines = [CourseInline]
    
    fieldsets = (
        ('Información del Cuatrimestre', {
            'fields': (
                'career',
                'number',
                'name',
            ),
        }),
        ('Estadísticas', {
            'fields': ('courses_count',),
            'classes': ('collapse',),
        }),
        ('Información del Sistema', {
            'fields': ('id',),
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
    
    def courses_count_display(self, obj):
        """Cuenta de cursos"""
        count = obj.courses.count()
        url = f"{reverse('admin:academics_course_changelist')}?cuatrimestre__id__exact={obj.id}"
        return format_html(
            '<a href="{}">{} curso(s)</a>',
            url,
            count
        )
    courses_count_display.short_description = 'Cursos'
    
    def courses_count(self, obj):
        """Cuenta de cursos (readonly)"""
        return obj.courses.count()
    courses_count.short_description = 'Total de Cursos'


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name_display', 'career_link', 'cuatrimestre_link',
        'credits_display', 'is_required_badge', 'prerequisite_link'
    ]
    list_filter = ['career', 'cuatrimestre', 'is_required']
    search_fields = ['code', 'name']
    raw_id_fields = ['prerequisite']
    readonly_fields = ['id', 'created_at', 'updated_at', 'enrollments_count']
    inlines = [CourseScheduleInline]
    
    fieldsets = (
        ('Información del Curso', {
            'fields': (
                'code',
                'name',
                'career',
                'cuatrimestre',
                ('credits', 'is_required'),
                'cost',
                'prerequisite',
            ),
        }),
        ('Estadísticas', {
            'fields': ('enrollments_count',),
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
    
    def name_display(self, obj):
        """Nombre con link"""
        url = reverse('admin:academics_course_change', args=[obj.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong></a>',
            url,
            obj.name
        )
    name_display.short_description = 'Nombre'
    name_display.admin_order_field = 'name'
    
    def career_link(self, obj):
        """Link a la carrera"""
        url = reverse('admin:academics_career_change', args=[obj.career.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.career.name
        )
    career_link.short_description = 'Carrera'
    career_link.admin_order_field = 'career__name'
    
    def cuatrimestre_link(self, obj):
        """Link al cuatrimestre"""
        url = reverse('admin:academics_cuatrimestre_change', args=[obj.cuatrimestre.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.cuatrimestre.name
        )
    cuatrimestre_link.short_description = 'Cuatrimestre'
    cuatrimestre_link.admin_order_field = 'cuatrimestre__number'
    
    def credits_display(self, obj):
        """Créditos del curso"""
        return format_html(
            '<strong style="color: #17a2b8;">{} créditos</strong>',
            obj.credits
        )
    credits_display.short_description = 'Créditos'
    credits_display.admin_order_field = 'credits'
    
    def is_required_badge(self, obj):
        """Badge para curso obligatorio"""
        if obj.is_required:
            return format_html(
                '<span style="background-color: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Obligatorio</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">Opcional</span>'
        )
    is_required_badge.short_description = 'Tipo'
    is_required_badge.admin_order_field = 'is_required'
    
    def prerequisite_link(self, obj):
        """Link al prerequisito"""
        if obj.prerequisite:
            url = reverse('admin:academics_course_change', args=[obj.prerequisite.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.prerequisite.name
            )
        return format_html('<span style="color: #999;">Ninguno</span>')
    prerequisite_link.short_description = 'Prerequisito'
    
    def enrollments_count(self, obj):
        """Cuenta de matrículas"""
        count = obj.enrollments.count()
        url = f"{reverse('admin:academics_courseenrollment_changelist')}?course__id__exact={obj.id}"
        return format_html(
            '<a href="{}">{} matrícula(s)</a>',
            url,
            count
        )
    enrollments_count.short_description = 'Matrículas'


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    """Admin para horarios de cursos"""
    list_display = ['course_link', 'day', 'start_time', 'end_time', 'schedule_display']
    list_filter = ['day', 'course__cuatrimestre', 'course__career']
    search_fields = ['course__code', 'course__name', 'day']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información del Horario', {
            'fields': (
                'course',
                'day',
                ('start_time', 'end_time'),
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
    
    def course_link(self, obj):
        """Link al curso"""
        if obj.course:
            url = reverse('admin:academics_course_change', args=[obj.course.pk])
            return format_html(
                '<a href="{}"><strong>{}</strong> - {}</a>',
                url,
                obj.course.code,
                obj.course.name
            )
        return '-'
    course_link.short_description = 'Curso'
    course_link.admin_order_field = 'course__code'
    
    def schedule_display(self, obj):
        """Mostrar horario formateado"""
        return f"{obj.day} {obj.start_time.strftime('%H:%M')}-{obj.end_time.strftime('%H:%M')}"
    schedule_display.short_description = 'Horario'
    schedule_display.admin_order_field = 'day'


@admin.register(CuatrimestreEnrollment)
class CuatrimestreEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'cuatrimestre_link', 'academic_year',
        'status_badge', 'courses_count_display', 'enrollment_date'
    ]
    list_filter = ['status', 'academic_year', 'cuatrimestre__career', 'enrollment_date']
    search_fields = [
        'student__first_name', 'student__first_last_name', 
        'cuatrimestre__name', 'cuatrimestre__career__name'
    ]
    raw_id_fields = ['student', 'cuatrimestre']
    readonly_fields = ['id', 'enrollment_date', 'created_at', 'updated_at', 'courses_count']
    inlines = [CourseEnrollmentInline]
    
    fieldsets = (
        ('Información de Inscripción', {
            'fields': (
                'student',
                'cuatrimestre',
                'academic_year',
                'enrollment_date',
            ),
        }),
        ('Estado', {
            'fields': (
                'status',
                'notes',
            ),
        }),
        ('Estadísticas', {
            'fields': ('courses_count',),
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
    
    def cuatrimestre_link(self, obj):
        """Link al cuatrimestre"""
        url = reverse('admin:academics_cuatrimestre_change', args=[obj.cuatrimestre.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong> - {}</a>',
            url,
            obj.cuatrimestre.name,
            obj.cuatrimestre.career.name
        )
    cuatrimestre_link.short_description = 'Cuatrimestre'
    cuatrimestre_link.admin_order_field = 'cuatrimestre__number'
    
    def courses_count_display(self, obj):
        """Cuenta de cursos inscritos"""
        count = obj.course_enrollments.count()
        url = f"{reverse('admin:academics_courseenrollment_changelist')}?cuatrimestre_enrollment__id__exact={obj.id}"
        return format_html(
            '<a href="{}">{} curso(s)</a>',
            url,
            count
        )
    courses_count_display.short_description = 'Cursos Inscritos'
    
    def courses_count(self, obj):
        """Cuenta de cursos (readonly)"""
        return obj.course_enrollments.count()
    courses_count.short_description = 'Total de Cursos'
    
    def status_badge(self, obj):
        """Badge para estado"""
        colors = {
            'PENDIENTE_PAGO': '#ffc107',
            'PENDIENTE_CONFIRMACION': '#17a2b8',
            'EN_CURSO': '#007bff',
            'FINALIZADO': '#28a745',
            'CANCELADO': '#dc3545'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'course_link', 'cuatrimestre_enrollment_display',
        'final_grade_display', 'status_badge', 'enrollment_date'
    ]
    list_filter = ['status', 'course__career', 'cuatrimestre_enrollment', 'enrollment_date']
    search_fields = ['student__first_name', 'student__first_last_name', 'course__name', 'course__code']
    raw_id_fields = ['student', 'course', 'cuatrimestre_enrollment']
    readonly_fields = ['id', 'enrollment_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de Matrícula', {
            'fields': (
                'student',
                'course',
                'cuatrimestre_enrollment',
                'enrollment_date',
            ),
        }),
        ('Calificación', {
            'fields': (
                'final_grade',
                'status',
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
    
    def cuatrimestre_enrollment_display(self, obj):
        """Display de inscripción al cuatrimestre"""
        if obj.cuatrimestre_enrollment:
            url = reverse('admin:academics_cuatrimestreenrollment_change', args=[obj.cuatrimestre_enrollment.pk])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                f"{obj.cuatrimestre_enrollment.cuatrimestre.name} {obj.cuatrimestre_enrollment.academic_year}"
            )
        return format_html('<span style="color: #999;">Sin cuatrimestre</span>')
    cuatrimestre_enrollment_display.short_description = 'Cuatrimestre'
    cuatrimestre_enrollment_display.admin_order_field = 'cuatrimestre_enrollment__academic_year'
    
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
    
    def course_link(self, obj):
        """Link al curso"""
        url = reverse('admin:academics_course_change', args=[obj.course.pk])
        return format_html(
            '<a href="{}"><strong>{}</strong> - {}</a>',
            url,
            obj.course.code,
            obj.course.name
        )
    course_link.short_description = 'Curso'
    course_link.admin_order_field = 'course__code'
    
    def final_grade_display(self, obj):
        """Calificación final"""
        if obj.final_grade is not None:
            grade_value = float(obj.final_grade)
            color = '#28a745' if grade_value >= 70 else '#dc3545'
            grade_formatted = f'{grade_value:.2f}'
            return format_html(
                '<strong style="color: {}; font-size: 14px;">{}</strong>',
                color,
                grade_formatted
            )
        return format_html('<span style="color: #999;">Sin calificar</span>')
    final_grade_display.short_description = 'Calificación'
    final_grade_display.admin_order_field = 'final_grade'
    
    def status_badge(self, obj):
        """Badge para estado"""
        colors = {
            'MATRICULADO': '#6c757d',
            'EN_CURSO': '#17a2b8',
            'APROBADO': '#28a745',
            'REPROBADO': '#dc3545',
            'RETIRADO': '#ffc107'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    status_badge.admin_order_field = 'status'


@admin.register(Thesis)
class ThesisAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'title_short', 'status_badge',
        'advisor_display', 'start_date', 'defense_date'
    ]
    list_filter = ['status', 'start_date']
    search_fields = ['student__first_name', 'student__first_last_name', 'title', 'advisor']
    readonly_fields = ['id', 'created_at', 'updated_at', 'document_link']
    
    fieldsets = (
        ('Información de la Tesis', {
            'fields': (
                'student',
                'title',
                'advisor',
                'status',
            ),
        }),
        ('Fechas', {
            'fields': (
                'start_date',
                'defense_date',
            ),
        }),
        ('Documentos', {
            'fields': (
                'document',
                'document_link',
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
    
    def title_short(self, obj):
        """Título corto"""
        if obj.title:
            title = obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
            return format_html('<strong>{}</strong>', title)
        return format_html('<span style="color: #999;">Sin título</span>')
    title_short.short_description = 'Título'
    title_short.admin_order_field = 'title'
    
    def status_badge(self, obj):
        """Badge para estado de la tesis"""
        colors = {
            'NO_INICIADA': '#6c757d',
            'SOLICITUD_ASESOR': '#17a2b8',
            'REVISION_TEMA': '#ffc107',
            'APROBACION_TEMA': '#28a745',
            'PRIMERA_REVISION': '#007bff',
            'SEGUNDA_REVISION': '#007bff',
            'TERCERA_REVISION': '#007bff',
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
    
    def advisor_display(self, obj):
        """Asesor"""
        if obj.advisor:
            return format_html('<strong>{}</strong>', obj.advisor)
        return format_html('<span style="color: #999;">Sin asignar</span>')
    advisor_display.short_description = 'Asesor'
    advisor_display.admin_order_field = 'advisor'
    
    def document_link(self, obj):
        """Link al documento"""
        if obj.document:
            return format_html(
                '<a href="{}" target="_blank">📄 Ver documento de tesis</a>',
                obj.document.url
            )
        return format_html('<span style="color: #999;">Sin documento</span>')
    document_link.short_description = 'Documento'


@admin.register(AcademicPeriodConfig)
class AcademicPeriodConfigAdmin(admin.ModelAdmin):
    """Admin para configuración de períodos académicos"""
    list_display = ['period', 'penalty_percentage', 'is_active_badge']
    list_filter = ['is_active', 'period']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información del Período', {
            'fields': (
                'period',
                'penalty_percentage',
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
    
    def is_active_badge(self, obj):
        """Badge para estado activo"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✓ Activa</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✗ Inactiva</span>'
        )
    is_active_badge.short_description = 'Estado'


@admin.register(MonthlyPaymentDueDate)
class MonthlyPaymentDueDateAdmin(admin.ModelAdmin):
    """Admin para fechas límite de pago mensuales"""
    list_display = ['month', 'due_day', 'is_active_badge']
    list_filter = ['is_active', 'month']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de Fecha Límite', {
            'fields': (
                'month',
                'due_day',
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
    
    def is_active_badge(self, obj):
        """Badge para estado activo"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✓ Activa</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold;">✗ Inactiva</span>'
        )
    is_active_badge.short_description = 'Estado'
