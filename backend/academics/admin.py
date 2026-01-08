from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Career, Cuatrimestre, Course, CourseEnrollment, Thesis


class CuatrimestreInline(admin.TabularInline):
    """Inline para cuatrimestres de carreras"""
    model = Cuatrimestre
    extra = 0
    fields = ('number', 'name')
    ordering = ('number',)


class CourseInline(admin.TabularInline):
    """Inline para cursos de cuatrimestres"""
    model = Course
    extra = 0
    fields = ('code', 'name', 'credits', 'is_required', 'prerequisite')
    ordering = ('code',)
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
    
    fieldsets = (
        ('Información del Curso', {
            'fields': (
                'code',
                'name',
                'career',
                'cuatrimestre',
                ('credits', 'is_required'),
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


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'student_link', 'course_link', 'final_grade_display',
        'status_badge', 'enrollment_date'
    ]
    list_filter = ['status', 'course__career', 'enrollment_date']
    search_fields = ['student__first_name', 'student__last_name', 'course__name', 'course__code']
    raw_id_fields = ['student', 'course']
    readonly_fields = ['id', 'enrollment_date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Información de Matrícula', {
            'fields': (
                'student',
                'course',
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
            color = '#28a745' if float(obj.final_grade) >= 70 else '#dc3545'
            return format_html(
                '<strong style="color: {}; font-size: 14px;">{:.2f}</strong>',
                color,
                float(obj.final_grade)
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
    search_fields = ['student__first_name', 'student__last_name', 'title', 'advisor']
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
