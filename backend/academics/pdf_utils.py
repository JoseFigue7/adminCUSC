"""
Utilidades para generar PDFs del flujo de inscripción
"""
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.utils import timezone
from decimal import Decimal
import io
import logging

logger = logging.getLogger(__name__)


def generate_assignment_boleta(cuatrimestre_enrollment):
    """
    Genera una boleta académica en PDF con información de asignación de cursos.
    Esta boleta es SOLO INFORMATIVA (preview) antes de confirmar la asignación.
    
    Args:
        cuatrimestre_enrollment: CuatrimestreEnrollment con cursos pre-asignados
        
    Returns:
        BytesIO: Archivo PDF en memoria
    """
    try:
        student = cuatrimestre_enrollment.student
        cuatrimestre = cuatrimestre_enrollment.cuatrimestre
        career = cuatrimestre.career
        
        # Obtener cursos con horarios
        course_enrollments = cuatrimestre_enrollment.course_enrollments.select_related(
            'course'
        ).prefetch_related('course__schedules').all()
        
        courses_data = []
        total_credits = 0
        total_cost = Decimal('0.00')
        
        for enrollment in course_enrollments:
            course = enrollment.course
            schedules = [
                {
                    'day': schedule.day,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M')
                }
                for schedule in course.schedules.all()
            ]
            
            course_cost = course.cost or Decimal('0.00')
            total_cost += course_cost
            total_credits += course.credits
            
            courses_data.append({
                'code': course.code,
                'name': course.name,
                'credits': course.credits,
                'cost': course_cost,
                'schedules': schedules
            })
        
        # Formatear fecha
        months_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        current_date = timezone.now().date()
        date_formatted = f"{current_date.day} de {months_es.get(current_date.month, '')} de {current_date.year}"
        
        # Obtener período académico
        from .models import get_academic_period
        period = get_academic_period(cuatrimestre.number)
        period_names = {
            1: 'Enero - Abril',
            2: 'Mayo - Agosto',
            3: 'Septiembre - Diciembre'
        }
        period_name = period_names.get(period, '')
        
        context = {
            'student': {
                'full_name': student.get_full_name(),
                'carnet': student.carnet or 'N/A',
                'email': student.email or 'N/A',
                'phone': student.phone or 'N/A'
            },
            'career': career.name,
            'cuatrimestre': cuatrimestre.name,
            'academic_year': cuatrimestre_enrollment.academic_year,
            'period': period_name,
            'courses': courses_data,
            'total_credits': total_credits,
            'total_cost': total_cost,
            'date': date_formatted,
            'is_preview': True,  # Indica que es una boleta de preview
            'institution_name': 'Centro Universitario Santa Cecilia',
            'institution_acronym': 'CUSC'
        }
        
        # Generar HTML
        html_string = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Boleta de Asignación Académica</title>
            <style>
                @page {{
                    size: letter;
                    margin: 2cm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 15px;
                }}
                .header h1 {{
                    font-size: 18pt;
                    font-weight: bold;
                    margin: 0;
                }}
                .header h2 {{
                    font-size: 14pt;
                    font-weight: normal;
                    margin: 5px 0;
                }}
                .info-section {{
                    margin-bottom: 20px;
                }}
                .info-row {{
                    margin-bottom: 8px;
                }}
                .info-label {{
                    font-weight: bold;
                    display: inline-block;
                    width: 150px;
                }}
                .warning-box {{
                    background-color: #fff3cd;
                    border: 2px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .warning-box strong {{
                    color: #856404;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                table th {{
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 10px;
                    text-align: left;
                    font-weight: bold;
                }}
                table td {{
                    border: 1px solid #dee2e6;
                    padding: 8px;
                }}
                .total-row {{
                    font-weight: bold;
                    background-color: #f8f9fa;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 9pt;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{context['institution_name']}</h1>
                <h2>BOLETA DE ASIGNACIÓN ACADÉMICA</h2>
                <p style="font-size: 10pt; color: #666;">{context['date']}</p>
            </div>
            
            <div class="warning-box">
                <strong>⚠️ BOLETA INFORMATIVA (PREVIEW)</strong><br>
                Esta boleta muestra la asignación propuesta de cursos. 
                La asignación NO está confirmada hasta que se presione "Confirmar asignación".
            </div>
            
            <div class="info-section">
                <div class="info-row">
                    <span class="info-label">Estudiante:</span>
                    <span>{context['student']['full_name']}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Carnet:</span>
                    <span>{context['student']['carnet']}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Carrera:</span>
                    <span>{context['career']}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Cuatrimestre:</span>
                    <span>{context['cuatrimestre']}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Año Académico:</span>
                    <span>{context['academic_year']}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Período:</span>
                    <span>{context['period']}</span>
                </div>
            </div>
            
            <h3 style="margin-top: 30px;">Cursos Asignados</h3>
            <table>
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Nombre del Curso</th>
                        <th>Créditos</th>
                        <th>Horarios</th>
                        <th>Costo</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for course in courses_data:
            schedules_str = ', '.join([
                f"{s['day']} {s['start_time']}-{s['end_time']}"
                for s in course['schedules']
            ]) if course['schedules'] else 'Sin horario'
            
            html_string += f"""
                    <tr>
                        <td>{course['code']}</td>
                        <td>{course['name']}</td>
                        <td>{course['credits']}</td>
                        <td>{schedules_str}</td>
                        <td>${course['cost']:,.2f}</td>
                    </tr>
            """
        
        html_string += f"""
                    <tr class="total-row">
                        <td colspan="2"><strong>TOTAL</strong></td>
                        <td><strong>{total_credits}</strong></td>
                        <td></td>
                        <td><strong>${total_cost:,.2f}</strong></td>
                    </tr>
                </tbody>
            </table>
            
            <div class="footer">
                <p>Este documento es una boleta informativa. La asignación se confirmará al presionar "Confirmar asignación".</p>
                <p>Generado el {context['date']}</p>
            </div>
        </body>
        </html>
        """
        
        # Generar PDF
        html = HTML(string=html_string)
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file)
        pdf_file.seek(0)
        
        return pdf_file
        
    except Exception as e:
        logger.error(f'Error al generar boleta de asignación: {str(e)}', exc_info=True)
        raise


def generate_payment_voucher(cuatrimestre_enrollment):
    """
    Genera un talonario de pagos en PDF con los pagos mensuales del cuatrimestre.
    
    Args:
        cuatrimestre_enrollment: CuatrimestreEnrollment confirmado con pagos generados
        
    Returns:
        BytesIO: Archivo PDF en memoria
    """
    try:
        from payments.models import Payment
        
        student = cuatrimestre_enrollment.student
        cuatrimestre = cuatrimestre_enrollment.cuatrimestre
        career = cuatrimestre.career
        
        # Obtener pagos mensuales relacionados
        payments = Payment.objects.filter(
            cuatrimestre_enrollment=cuatrimestre_enrollment
        ).order_by('month', 'year').all()
        
        if not payments.exists():
            raise ValueError('No hay pagos generados para este cuatrimestre')
        
        # Formatear fecha
        months_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        current_date = timezone.now().date()
        date_formatted = f"{current_date.day} de {months_es.get(current_date.month, '')} de {current_date.year}"
        
        # Obtener período académico
        from .models import get_academic_period
        period = get_academic_period(cuatrimestre.number)
        period_names = {
            1: 'Enero - Abril',
            2: 'Mayo - Agosto',
            3: 'Septiembre - Diciembre'
        }
        period_name = period_names.get(period, '')
        
        payments_data = []
        total_amount = Decimal('0.00')
        
        for payment in payments:
            month_name = dict(Payment.MONTHS)[payment.month] if payment.month else 'N/A'
            due_date_str = payment.due_date.strftime('%d/%m/%Y') if payment.due_date else 'N/A'
            amount = payment.final_amount or payment.amount
            total_amount += amount
            
            payments_data.append({
                'month': month_name,
                'year': payment.year or cuatrimestre_enrollment.academic_year,
                'due_date': due_date_str,
                'amount': amount,
                'payment_id': str(payment.id)[:8],  # Primeros 8 caracteres del UUID
                'reference': payment.payment_reference or f"PAGO-{payment.id}"
            })
        
        # Generar HTML
        html_string = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Talonario de Pagos</title>
            <style>
                @page {{
                    size: letter;
                    margin: 2cm;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.4;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 15px;
                }}
                .header h1 {{
                    font-size: 18pt;
                    font-weight: bold;
                    margin: 0;
                }}
                .header h2 {{
                    font-size: 14pt;
                    font-weight: normal;
                    margin: 5px 0;
                }}
                .info-section {{
                    margin-bottom: 20px;
                }}
                .info-row {{
                    margin-bottom: 8px;
                }}
                .info-label {{
                    font-weight: bold;
                    display: inline-block;
                    width: 150px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                table th {{
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 10px;
                    text-align: left;
                    font-weight: bold;
                }}
                table td {{
                    border: 1px solid #dee2e6;
                    padding: 8px;
                }}
                .total-row {{
                    font-weight: bold;
                    background-color: #f8f9fa;
                }}
                .payment-item {{
                    margin-bottom: 20px;
                    padding: 15px;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                }}
                .footer {{
                    margin-top: 30px;
                    text-align: center;
                    font-size: 9pt;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Centro Universitario Santa Cecilia</h1>
                <h2>TALONARIO DE PAGOS</h2>
                <p style="font-size: 10pt; color: #666;">{date_formatted}</p>
            </div>
            
            <div class="info-section">
                <div class="info-row">
                    <span class="info-label">Estudiante:</span>
                    <span>{student.get_full_name()}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Carnet:</span>
                    <span>{student.carnet or 'N/A'}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Carrera:</span>
                    <span>{career.name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Cuatrimestre:</span>
                    <span>{cuatrimestre.name}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Año Académico:</span>
                    <span>{cuatrimestre_enrollment.academic_year}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Período:</span>
                    <span>{period_name}</span>
                </div>
            </div>
            
            <h3 style="margin-top: 30px;">Pagos Mensuales</h3>
            <table>
                <thead>
                    <tr>
                        <th>Mes</th>
                        <th>Año</th>
                        <th>Fecha Límite</th>
                        <th>Monto</th>
                        <th>Referencia</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for payment_data in payments_data:
            html_string += f"""
                    <tr>
                        <td>{payment_data['month']}</td>
                        <td>{payment_data['year']}</td>
                        <td>{payment_data['due_date']}</td>
                        <td>${payment_data['amount']:,.2f}</td>
                        <td>{payment_data['reference']}</td>
                    </tr>
            """
        
        html_string += f"""
                    <tr class="total-row">
                        <td colspan="3"><strong>TOTAL</strong></td>
                        <td><strong>${total_amount:,.2f}</strong></td>
                        <td></td>
                    </tr>
                </tbody>
            </table>
            
            <div class="footer">
                <p>Este talonario contiene los pagos mensuales del cuatrimestre.</p>
                <p>Generado el {date_formatted}</p>
            </div>
        </body>
        </html>
        """
        
        # Generar PDF
        html = HTML(string=html_string)
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file)
        pdf_file.seek(0)
        
        return pdf_file
        
    except Exception as e:
        logger.error(f'Error al generar talonario de pagos: {str(e)}', exc_info=True)
        raise
