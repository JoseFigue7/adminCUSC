from django.core.management.base import BaseCommand
from payments.models import PaymentType
from decimal import Decimal


class Command(BaseCommand):
    help = 'Poblar tipos de pago iniciales'

    def handle(self, *args, **options):
        payment_types = [
            {
                'code': '010',
                'name': 'Inscripción ordinaria',
                'description': 'Inscripción ordinaria para el ciclo académico',
                'amount': None,
                'requires_career': False,
                'requires_semester': True,
                'requires_month': False,
                'requires_year': True,
                'requires_quantity': False,
            },
            {
                'code': '100',
                'name': 'Inscripción al Cuatrimestre - Gratis',
                'description': 'Inscripción al cuatrimestre gratuita (solo disponible en temporadas específicas)',
                'amount': Decimal('0.00'),  # Siempre es 0 para inscripción gratis
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': True,
                'requires_quantity': False,
                'is_active': False,  # Por defecto inactivo, se activa en temporadas específicas
            },
            {
                'code': '101',
                'name': 'Inscripción al Cuatrimestre',
                'description': 'Pago de inscripción al cuatrimestre (requerido para asignar cursos)',
                'amount': None,  # Se configura por carrera en PaymentConfiguration
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': True,
                'requires_quantity': False,
            },
            {
                'code': '011',
                'name': 'Inscripción extraordinaria',
                'description': 'Inscripción extraordinaria para el ciclo académico',
                'amount': None,
                'requires_career': False,
                'requires_semester': True,
                'requires_month': False,
                'requires_year': True,
                'requires_quantity': False,
            },
            {
                'code': '111',
                'name': 'Pronto Pago',
                'description': 'Descuento por pronto pago',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '102',
                'name': 'Colegiatura de Cursos',
                'description': 'Pago mensual base de colegiatura por cursos',
                'amount': None,  # Se configura por carrera en PaymentConfiguration
                'requires_career': False,
                'requires_semester': False,
                'requires_month': True,
                'requires_year': True,
                'requires_quantity': False,
            },
            {
                'code': '103',
                'name': 'Colegiatura de Cursos con Media Beca',
                'description': 'Pago mensual de colegiatura por cursos con descuento de media beca aplicado',
                'amount': None,  # Se configura por carrera en PaymentConfiguration, ya incluye el descuento
                'requires_career': False,
                'requires_semester': False,
                'requires_month': True,
                'requires_year': True,
                'requires_quantity': False,
            },
            {
                'code': '105',
                'name': 'Colegiatura de Cursos con Beca Completa',
                'description': 'Pago de colegiatura por cursos con beca completa (valor 0, cuatrimestre completo pagado)',
                'amount': Decimal('0.00'),  # Siempre es 0 para beca completa
                'requires_career': False,
                'requires_semester': False,
                'requires_month': True,
                'requires_year': True,
                'requires_quantity': False,
            },
            {
                'code': '202',
                'name': 'Cursos libres idiomas intensivos',
                'description': 'Pago de cursos libres de idiomas intensivos',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '300',
                'name': 'Evaluación Primer Parcial Extraordinario',
                'description': 'Evaluación del primer parcial extraordinario',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '302',
                'name': 'Examen de Recuperación',
                'description': 'Pago por examen de recuperación',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '305',
                'name': 'Evaluación Segundo Parcial Extraordinario',
                'description': 'Evaluación del segundo parcial extraordinario',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '308',
                'name': 'Evaluación especial',
                'description': 'Pago por evaluación especial',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '309',
                'name': 'Evaluación por suficiencia',
                'description': 'Pago por evaluación por suficiencia',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '410',
                'name': 'Reposición carné',
                'description': 'Pago por reposición de carné estudiantil',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '411',
                'name': 'Certificación de cursos',
                'description': 'Pago por certificación de cursos',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '412',
                'name': 'Cierre de Pensum',
                'description': 'Pago por cierre de pensum',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '418',
                'name': 'Certificación de Matrícula',
                'description': 'Pago por certificación de matrícula',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': False,
            },
            {
                'code': '453',
                'name': 'Parqueo',
                'description': 'Pago de parqueo',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': True,
                'requires_year': True,
                'requires_quantity': False,
            },
            {
                'code': '476',
                'name': 'Abono multa',
                'description': 'Pago de abono de multa',
                'amount': None,
                'requires_career': False,
                'requires_semester': False,
                'requires_month': False,
                'requires_year': False,
                'requires_quantity': True,
            },
        ]

        created_count = 0
        updated_count = 0

        for pt_data in payment_types:
            # is_active puede estar especificado en pt_data, si no, usar True por defecto
            is_active = pt_data.get('is_active', True)
            payment_type, created = PaymentType.objects.update_or_create(
                code=pt_data['code'],
                defaults={
                    'name': pt_data['name'],
                    'description': pt_data['description'],
                    'amount': pt_data['amount'],
                    'requires_career': pt_data['requires_career'],
                    'requires_semester': pt_data['requires_semester'],
                    'requires_month': pt_data['requires_month'],
                    'requires_year': pt_data['requires_year'],
                    'requires_quantity': pt_data['requires_quantity'],
                    'is_active': is_active,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Creado: {payment_type.code} - {payment_type.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Actualizado: {payment_type.code} - {payment_type.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Proceso completado: {created_count} creados, {updated_count} actualizados'
            )
        )



