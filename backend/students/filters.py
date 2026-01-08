import django_filters
from django.db.models import Q
from .models import Student
from academics.models import Career


class StudentFilter(django_filters.FilterSet):
    """Filtros avanzados para estudiantes"""
    
    # Búsqueda por texto
    search = django_filters.CharFilter(method='filter_search', label='Búsqueda general')
    
    # Filtros por campos específicos
    carnet = django_filters.CharFilter(lookup_expr='icontains', label='Carnet')
    first_name = django_filters.CharFilter(lookup_expr='icontains', label='Nombre')
    last_name = django_filters.CharFilter(lookup_expr='icontains', label='Apellido')
    email = django_filters.CharFilter(lookup_expr='icontains', label='Email')
    
    # Filtros por relaciones
    career = django_filters.ModelChoiceFilter(queryset=Career.objects.filter(is_active=True), label='Carrera')
    
    # Filtros por estado
    is_active = django_filters.BooleanFilter(label='Activo')
    has_scholarship = django_filters.BooleanFilter(label='Tiene beca')
    scholarship_type = django_filters.ChoiceFilter(
        choices=[('COMPLETA', 'Beca Completa'), ('MEDIA', 'Media Beca'), ('NINGUNA', 'Sin Beca')],
        label='Tipo de beca'
    )
    pensum_closed = django_filters.BooleanFilter(label='Pensum cerrado')
    thesis_started = django_filters.BooleanFilter(label='Tesis iniciada')
    
    # Filtros por fecha
    enrollment_date_from = django_filters.DateFilter(field_name='enrollment_date', lookup_expr='gte', label='Fecha de inscripción desde')
    enrollment_date_to = django_filters.DateFilter(field_name='enrollment_date', lookup_expr='lte', label='Fecha de inscripción hasta')
    date_of_birth_from = django_filters.DateFilter(field_name='date_of_birth', lookup_expr='gte', label='Fecha de nacimiento desde')
    date_of_birth_to = django_filters.DateFilter(field_name='date_of_birth', lookup_expr='lte', label='Fecha de nacimiento hasta')
    
    # Filtros por género
    gender = django_filters.ChoiceFilter(choices=Student.GENDER_CHOICES, label='Género')
    
    class Meta:
        model = Student
        fields = []
    
    def filter_search(self, queryset, name, value):
        """Búsqueda general en múltiples campos"""
        if value:
            return queryset.filter(
                Q(carnet__icontains=value) |
                Q(first_name__icontains=value) |
                Q(last_name__icontains=value) |
                Q(email__icontains=value) |
                Q(phone__icontains=value) |
                Q(curp__icontains=value)
            )
        return queryset
