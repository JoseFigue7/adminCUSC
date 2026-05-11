from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from payments.models import Payment

# Plan de cuatrimestre: inscripción de cuatrimestre + colegiatura mensual / beca
PLAN_CODES = ('101', '102', '103', '105')
TUITION_CODES = ('102', '103', '105')


class Command(BaseCommand):
    help = (
        'Pasa a PENDIENTE pagos del plan (101 inscripción cuatrimestre, 102/103/105 colegiatura) '
        'que quedaron en APROBADO por error. Por defecto: con cuatrimestre_enrollment. '
        'Simulación sin --apply. En el servidor: desplegar el fix de Payment.save() y ejecutar con --apply.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplicar cambios en la base de datos.',
        )
        parser.add_argument(
            '--include-beca-completa-cero',
            action='store_true',
            help='Incluir tipo 105 con monto 0 (por defecto se omiten).',
        )
        parser.add_argument(
            '--include-orphan-tuition',
            action='store_true',
            help=(
                'Incluir 102/103/105 en APROBADO sin cuatrimestre_enrollment, sin comprobante ni recibo '
                '(p. ej. plan generado sin vincular). Revisar dry-run antes de --apply.'
            ),
        )
        parser.add_argument(
            '--student-id',
            type=str,
            default='',
            help='Limitar a un estudiante (UUID del estudiante).',
        )

    def handle(self, *args, **options):
        dry_run = not options['apply']
        include_zero_105 = options['include_beca_completa_cero']
        include_orphan = options['include_orphan_tuition']
        student_id = (options['student_id'] or '').strip()

        q_linked = Q(
            status='APROBADO',
            cuatrimestre_enrollment__isnull=False,
            payment_type__code__in=PLAN_CODES,
        )
        if student_id:
            q_linked &= Q(student_id=student_id)

        qs = Payment.objects.filter(q_linked).select_related('payment_type', 'student')

        if include_orphan:
            q_orphan = Q(
                status='APROBADO',
                cuatrimestre_enrollment__isnull=True,
                payment_type__code__in=TUITION_CODES,
            ) & (
                Q(transfer_receipt__isnull=True) | Q(transfer_receipt='')
            )
            if student_id:
                q_orphan &= Q(student_id=student_id)
            qs = Payment.objects.filter(q_linked | q_orphan).select_related(
                'payment_type', 'student'
            ).distinct()

        if not include_zero_105:
            qs = qs.exclude(payment_type__code='105', amount=Decimal('0.00'))

        count = qs.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No hay pagos que coincidan con el criterio.'))
            return

        self.stdout.write(f'Pagos a actualizar: {count}')
        for p in qs.order_by('student_id', 'payment_date')[:30]:
            ce = 'sí' if p.cuatrimestre_enrollment_id else 'no'
            self.stdout.write(
                f'  - {p.id} | carnet {p.student.carnet if p.student else "?"} | '
                f'tipo {p.payment_type.code if p.payment_type else "?"} | '
                f'monto {p.amount} | cuatrim. {ce}'
            )
        if count > 30:
            self.stdout.write(f'  ... y {count - 30} más')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    'Modo simulación. Ejecute: python manage.py revert_plan_payments_to_pending --apply'
                    + (' --include-orphan-tuition' if include_orphan else '')
                    + (f' --student-id={student_id}' if student_id else '')
                )
            )
            return

        with transaction.atomic():
            updated = qs.update(
                status='PENDIENTE',
                approved_by_id=None,
                approved_at=None,
            )
        self.stdout.write(self.style.SUCCESS(f'Actualizados {updated} pago(s) a PENDIENTE.'))
