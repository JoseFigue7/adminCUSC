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
        import base64
        import os
        from django.conf import settings
        
        student = cuatrimestre_enrollment.student
        cuatrimestre = cuatrimestre_enrollment.cuatrimestre
        career = cuatrimestre.career
        
        # Cargar el logo en base64 para marca de agua
        logo_base64 = None
        try:
            logo_path = os.path.join(settings.BASE_DIR, 'students', 'static', 'students', 'contracts', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                    logo_base64 = f"data:image/png;base64,{logo_base64}"
        except Exception as logo_error:
            logger.warning(f'Error al cargar logo: {str(logo_error)}')
        
        # Obtener cursos con horarios (solo para mostrar, no para calcular costo)
        # Si hay pre_assign_course_ids, usar esos (antes de confirmar)
        # Si no, usar los course_enrollments existentes (después de confirmar)
        courses_data = []
        total_credits = 0
        
        pre_assigned_ids = cuatrimestre_enrollment.pre_assign_course_ids or []
        
        if pre_assigned_ids:
            # Obtener cursos desde los IDs pre-asignados (antes de confirmar)
            from uuid import UUID
            from .models import Course
            course_uuids = [UUID(cid) for cid in pre_assigned_ids]
            courses = Course.objects.filter(id__in=course_uuids).prefetch_related('schedules')
        else:
            # Obtener cursos desde CourseEnrollment (después de confirmar)
            course_enrollments = cuatrimestre_enrollment.course_enrollments.select_related(
                'course'
            ).prefetch_related('course__schedules').all()
            courses = [enrollment.course for enrollment in course_enrollments]
        
        for course in courses:
            schedules = [
                {
                    'day': schedule.day,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M')
                }
                for schedule in course.schedules.all()
            ]
            
            total_credits += course.credits
            
            courses_data.append({
                'code': course.code,
                'name': course.name,
                'credits': course.credits,
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
            1: 'Febrero - Mayo',
            2: 'Junio - Agosto',
            3: 'Septiembre - Diciembre'
        }
        period_name = period_names.get(period, '')
        
        # Formatear carrera con RVOE
        career_display = career.name
        if career.rvoe:
            career_display = f"{career.name} ({career.rvoe})"
        
        context = {
            'student': {
                'full_name': student.get_full_name(),
                'carnet': student.carnet or 'N/A',
                'email': student.email or 'N/A',
                'phone': student.phone or 'N/A'
            },
            'career': career_display,
            'cuatrimestre': cuatrimestre.name,
            'academic_year': cuatrimestre_enrollment.academic_year,
            'period': period_name,
            'courses': courses_data,
            'total_credits': total_credits,
            'date': date_formatted,
            'is_preview': True,  # Indica que es una boleta de preview
            'institution_name': 'Colegio Santa Cecilia',
            'institution_acronym': 'CUSC',
            'logo_base64': logo_base64
        }
        
        # Generar contenido de la boleta (se duplicará)
        watermark_img = f'<img src="{logo_base64}" alt="Logo" class="watermark-img" />' if logo_base64 else ""
        
        boleta_content_template = """
            <div class="boleta-content">
                {watermark}
                <div class="header">
                    <h1>{institution_name}</h1>
                    <h2>BOLETA DE ASIGNACIÓN ACADÉMICA</h2>
                    <p class="date-text">{date}</p>
                </div>
                
                <div class="info-section">
                    <div class="info-row">
                        <span class="info-label">Estudiante:</span>
                        <span>{full_name}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Carnet:</span>
                        <span>{carnet}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Carrera:</span>
                        <span>{career}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Cuatrimestre:</span>
                        <span>{cuatrimestre}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Año Académico:</span>
                        <span>{academic_year}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Período:</span>
                        <span>{period}</span>
                    </div>
                </div>
                
                <h3 class="courses-title">Cursos Asignados</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Nombre del Curso</th>
                            <th>Créditos</th>
                            <th>Horarios</th>
                        </tr>
                    </thead>
                    <tbody>
                        {courses_rows}
                        <tr class="total-row">
                            <td colspan="2"><strong>TOTAL</strong></td>
                            <td><strong>{total_credits}</strong></td>
                            <td></td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="signature-section">
                    <p class="signature-label">Firma del Estudiante</p>
                    <div class="signature-line"></div>
                </div>
            </div>
        """
        
        # Generar filas de cursos
        courses_rows_html = ""
        for course in courses_data:
            schedules_str = ', '.join([
                f"{s['day']} {s['start_time']}-{s['end_time']}"
                for s in course['schedules']
            ]) if course['schedules'] else 'Sin horario'
            
            courses_rows_html += f"""
                        <tr>
                            <td>{course['code']}</td>
                            <td>{course['name']}</td>
                            <td>{course['credits']}</td>
                            <td class="schedules-cell">{schedules_str}</td>
                        </tr>
            """
        
        # Formatear contenido de la boleta con los datos
        boleta_content = boleta_content_template.format(
            watermark=watermark_img,
            institution_name=context['institution_name'],
            date=context['date'],
            full_name=context['student']['full_name'],
            carnet=context['student']['carnet'],
            career=context['career'],
            cuatrimestre=context['cuatrimestre'],
            academic_year=context['academic_year'],
            period=context['period'],
            courses_rows=courses_rows_html,
            total_credits=total_credits
        )
        
        # Estilos de marca de agua
        watermark_style = ""
        if logo_base64:
            watermark_style = """
                .watermark-img {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    opacity: 0.08;
                    width: 300px;
                    height: auto;
                    z-index: 0;
                    pointer-events: none;
                }
            """
        
        html_string = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Boleta de Asignación Académica</title>
            <style>
                @page {{
                    size: letter;
                    margin: 0.7cm;
                }}
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 8pt;
                    line-height: 1.3;
                    margin: 0;
                    padding: 0;
                    position: relative;
                }}
                {watermark_style}
                .page-container {{
                    position: relative;
                    width: 100%;
                    height: 26cm;
                    overflow: hidden;
                }}
                .boleta-wrapper {{
                    height: 13cm;
                    position: relative;
                    page-break-inside: avoid;
                    padding: 8px;
                    overflow: hidden;
                }}
                .boleta-wrapper.upper {{
                    border-bottom: 2px dashed #ccc;
                }}
                .boleta-content {{
                    position: relative;
                    width: 100%;
                    height: 100%;
                    display: flex;
                    flex-direction: column;
                    z-index: 1;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 8px;
                    border-bottom: 1px solid #333;
                    padding-bottom: 5px;
                }}
                .header h1 {{
                    font-size: 12pt;
                    font-weight: bold;
                    margin: 0;
                    line-height: 1.2;
                }}
                .header h2 {{
                    font-size: 10pt;
                    font-weight: normal;
                    margin: 2px 0;
                    line-height: 1.2;
                }}
                .date-text {{
                    font-size: 8pt;
                    color: #666;
                    margin-top: 3px;
                }}
                .info-section {{
                    margin-bottom: 6px;
                }}
                .info-row {{
                    margin-bottom: 3px;
                    font-size: 8pt;
                    line-height: 1.2;
                }}
                .info-label {{
                    font-weight: bold;
                    display: inline-block;
                    width: 110px;
                }}
                .courses-title {{
                    font-size: 9pt;
                    margin: 5px 0 3px 0;
                    font-weight: bold;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 5px 0;
                    font-size: 7pt;
                    line-height: 1.2;
                }}
                table th {{
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    padding: 4px 5px;
                    text-align: left;
                    font-weight: bold;
                    font-size: 7pt;
                }}
                table td {{
                    border: 1px solid #dee2e6;
                    padding: 3px 5px;
                    font-size: 7pt;
                }}
                .schedules-cell {{
                    font-size: 6pt;
                }}
                .total-row {{
                    font-weight: bold;
                    background-color: #f8f9fa;
                }}
                .signature-section {{
                    margin-top: 10px;
                    text-align: center;
                }}
                .signature-label {{
                    font-size: 8pt;
                    margin-bottom: 5px;
                }}
                .signature-line {{
                    border-top: 1px solid #333;
                    width: 200px;
                    margin: 20px auto 0;
                }}
            </style>
        </head>
        <body>
            <div class="page-container">
                <div class="boleta-wrapper upper">
                    {boleta_content}
                </div>
                <div class="boleta-wrapper lower">
                    {boleta_content}
                </div>
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
            1: 'Febrero - Mayo',
            2: 'Junio - Agosto',
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
        
        # Cargar el logo en base64 para marca de agua
        logo_base64 = None
        try:
            import base64
            from pathlib import Path
            from django.conf import settings
            # Usar el logo desde frontend/public/SC Logo.png
            # BASE_DIR apunta a backend/, así que necesitamos ir un nivel arriba
            logo_path = settings.BASE_DIR.parent / 'frontend' / 'public' / 'SC Logo.png'
            if logo_path.exists():
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                    logo_base64 = f"data:image/png;base64,{logo_base64}"
        except Exception as logo_error:
            logger.warning(f'Error al cargar logo: {str(logo_error)}')
        
        # Calcular total con descuento (10% de descuento si paga completo)
        # total_amount ya es el total del cuatrimestre (suma de todos los pagos mensuales)
        total_with_discount = total_amount * Decimal('0.90')
        discount_amount = total_amount * Decimal('0.10')
        
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
                    position: relative;
                }}
                .watermark {{
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    opacity: 0.08;
                    z-index: -1;
                    width: 500px;
                    height: 500px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .watermark img {{
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
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
            {f'<div class="watermark"><img src="{logo_base64}" alt="Logo"></div>' if logo_base64 else ''}
            <div class="header">
                <h1>Colegio Santa Cecilia</h1>
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
            
            {f'''
            <div style="margin-top: 25px; padding: 15px; background-color: #e7f3ff; border: 2px solid #2196F3; border-radius: 5px;">
                <h4 style="margin-top: 0; color: #1565C0; font-size: 12pt;">Acceso a Plataforma</h4>
                <div style="margin-top: 10px;">
                    <div class="info-row" style="margin-bottom: 8px;">
                        <span class="info-label" style="font-weight: bold; color: #1565C0;">Usuario:</span>
                        <span style="font-family: monospace; font-size: 11pt; font-weight: bold;">{student.moodle_username or 'N/A'}</span>
                    </div>
                    <div class="info-row" style="margin-bottom: 0;">
                        <span class="info-label" style="font-weight: bold; color: #1565C0;">Contraseña:</span>
                        <span style="font-family: monospace; font-size: 11pt; font-weight: bold;">{student.moodle_password or 'N/A'}</span>
                    </div>
                </div>
                <p style="margin-top: 10px; margin-bottom: 0; font-size: 9pt; color: #1565C0; font-style: italic;">
                    Estas credenciales son para acceder a la plataforma Moodle. No son para este sistema administrativo.
                </p>
            </div>
            ''' if (student.moodle_username and student.moodle_password) else ''}
            
            <h3 style="margin-top: 30px;">Pagos Mensuales</h3>
            <table>
                <thead>
                    <tr>
                        <th>Mes</th>
                        <th>Año</th>
                        <th>Fecha Límite</th>
                        <th>Monto</th>
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
                    </tr>
            """
        
        html_string += f"""
                    <tr class="total-row">
                        <td colspan="3"><strong>TOTAL</strong></td>
                        <td><strong>${total_amount:,.2f}</strong></td>
                    </tr>
                </tbody>
            </table>
            
            <div style="margin-top: 20px; padding: 10px; border: 1px solid #dee2e6; border-radius: 4px; background-color: #f8f9fa;">
                <p style="margin: 0; font-size: 9pt; color: #495057; line-height: 1.5;">
                    <strong>Descuento por Pago Completo:</strong> Si realiza el pago completo del cuatrimestre, obtendrá un 10% de descuento. 
                    Total sin descuento: <strong>${total_amount:,.2f}</strong> | 
                    Descuento (10%): <strong>${discount_amount:,.2f}</strong> | 
                    <strong>Total con descuento: ${total_with_discount:,.2f}</strong>. 
                    Para aplicar este descuento, contacte a la administración antes de realizar los pagos.
                </p>
            </div>
            
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
