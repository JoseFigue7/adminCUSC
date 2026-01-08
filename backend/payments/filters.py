import django_filters
from django.db.models import Q
from .models import Payment
from students.models import Student
from academics.models import Career


class PaymentFilter(django_filters.FilterSet):
    """Filtros avanzados para pagos"""
    
    # Búsqueda por texto
    search = django_filters.CharFilter(method='filter_search', label='Búsqueda general')
    
    # Filtros por estudiante
    student = django_filters.ModelChoiceFilter(queryset=Student.objects.all(), label='Estudiante')
    student_carnet = django_filters.CharFilter(field_name='student__carnet', lookup_expr='icontains', label='Carnet del estudiante')
    student_name = django_filters.CharFilter(method='filter_student_name', label='Nombre del estudiante')
    
    # Filtros por carrera (a través del estudiante)
    career = django_filters.ModelChoiceFilter(field_name='student__career', queryset=Career.objects.filter(is_active=True), label='Carrera')
    
    # Filtros por estado y método
    status = django_filters.ChoiceFilter(choices=Payment.STATUS_CHOICES, label='Estado')
    payment_method = django_filters.ChoiceFilter(choices=Payment.PAYMENT_METHODS, label='Método de pago')
    payment_type = django_filters.UUIDFilter(field_name='payment_type', label='Tipo de pago')
    
    # Filtros por fecha
    payment_date_from = django_filters.DateFilter(field_name='payment_date', lookup_expr='gte', label='Fecha de pago desde')
    payment_date_to = django_filters.DateFilter(field_name='payment_date', lookup_expr='lte', label='Fecha de pago hasta')
    
    # Filtros por mes y año
    month = django_filters.NumberFilter(label='Mes')
    year = django_filters.NumberFilter(label='Año')
    
    # Filtros por monto
    amount_min = django_filters.NumberFilter(field_name='amount', lookup_expr='gte', label='Monto mínimo')
    amount_max = django_filters.NumberFilter(field_name='amount', lookup_expr='lte', label='Monto máximo')
    
    class Meta:
        model = Payment
        fields = []
    
    def filter_search(self, queryset, name, value):
        """Búsqueda general en múltiples campos"""
        if value:
            return queryset.filter(
                Q(student__carnet__icontains=value) |
                Q(student__first_name__icontains=value) |
                Q(student__last_name__icontains=value) |
                Q(student__email__icontains=value) |
                Q(receipt_number__icontains=value) |
                Q(transaction_id__icontains=value) |
                Q(notes__icontains=value) |
                Q(payment_type__name__icontains=value) |
                Q(payment_type__code__icontains=value)
            )
        return queryset
    
    def filter_student_name(self, queryset, name, value):
        """Búsqueda por nombre completo del estudiante"""
        if value:
            return queryset.filter(
                Q(student__first_name__icontains=value) |
                Q(student__last_name__icontains=value)
            )
        return queryset
