"""
Utilidades para generar recibos de pago en PDF y enviarlos por correo
"""
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.utils import timezone
from decimal import Decimal
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def generate_receipt_number(payment=None):
    """
    Genera un número de recibo automático para pagos en efectivo.
    Formato: REC-YYYYMMDD-XXXXX (ej: REC-20260115-00001)
    
    Args:
        payment: Instancia de Payment (opcional, solo para compatibilidad)
        
    Returns:
        str: Número de recibo generado
    """
    from .models import Payment
    
    # Obtener la fecha actual
    today = timezone.now().date()
    date_str = today.strftime('%Y%m%d')
    
    # Contar cuántos recibos se han generado hoy
    # Buscar el último número de recibo generado hoy
    last_receipt = Payment.objects.filter(
        payment_method='EFECTIVO',
        receipt_number__startswith=f'REC-{date_str}-',
        payment_date=today
    ).order_by('-receipt_number').first()
    
    if last_receipt and last_receipt.receipt_number:
        # Extraer el número secuencial del último recibo
        try:
            last_sequence = int(last_receipt.receipt_number.split('-')[-1])
            sequence = str(last_sequence + 1).zfill(5)
        except (ValueError, IndexError):
            # Si hay error al parsear, contar los recibos
            today_count = Payment.objects.filter(
                payment_method='EFECTIVO',
                receipt_number__startswith=f'REC-{date_str}',
                payment_date=today
            ).count()
            sequence = str(today_count + 1).zfill(5)
    else:
        # Si no hay recibos hoy, empezar con 00001
        sequence = '00001'
    
    return f'REC-{date_str}-{sequence}'


def generate_payment_receipt_pdf(payment):
    """
    Genera un recibo de pago en PDF.
    
    Args:
        payment: Instancia de Payment
        
    Returns:
        BytesIO: Archivo PDF en memoria
    """
    try:
        import base64
        import os
        from django.conf import settings
        
        student = payment.student
        payment_type = payment.payment_type
        
        # Cargar el logo
        logo_base64 = None
        try:
            logo_path = settings.BASE_DIR.parent / 'frontend' / 'public' / 'SC Logo.png'
            if not logo_path.exists():
                logo_path = os.path.join(settings.BASE_DIR, 'students', 'static', 'students', 'contracts', 'logo.png')
            
            if logo_path.exists():
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                    logo_base64 = f"data:image/png;base64,{logo_base64}"
        except Exception as logo_error:
            logger.warning(f'Error al cargar logo: {str(logo_error)}')
        
        # Formatear fecha en español
        months_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        
        # Fecha de emisión del recibo
        now = timezone.now()
        formatted_date = f"{now.day} de {months_es[now.month]} de {now.year}"
        
        # Fecha de pago (si existe)
        payment_date_formatted = None
        if payment.payment_date:
            payment_date_formatted = f"{payment.payment_date.day} de {months_es[payment.payment_date.month]} de {payment.payment_date.year}"
        
        # Usar ID del pago como número de recibo si no hay receipt_number
        receipt_number = payment.receipt_number or str(payment.id)[:8].upper()
        
        # Preparar datos para el template
        context = {
            'payment': payment,
            'student': student,
            'payment_type': payment_type,
            'logo_base64': logo_base64,
            'institution_name': 'Colegio Santa Cecilia',
            'date': formatted_date,
            'payment_date_formatted': payment_date_formatted,
            'receipt_number': receipt_number,
            'amount': getattr(payment, 'final_amount', None) or payment.amount or Decimal('0.00'),
            'payment_method_display': payment.get_payment_method_display(),
            'status_display': payment.get_status_display(),
        }
        
        # Renderizar el template HTML
        html_string = render_to_string('payments/receipt.html', context)
        
        # Generar PDF
        html = HTML(string=html_string, base_url=settings.BASE_DIR)
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file)
        pdf_file.seek(0)
        
        return pdf_file
        
    except Exception as e:
        logger.error(f'Error al generar recibo PDF: {str(e)}', exc_info=True)
        raise


def send_receipt_email(payment, pdf_file=None):
    """
    Envía el recibo de pago por correo electrónico al estudiante.
    
    Args:
        payment: Instancia de Payment
        pdf_file: Archivo PDF del recibo (opcional, se genera si no se proporciona)
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        from django.core.mail import EmailMessage
        from django.conf import settings
        
        student = payment.student
        
        if not student.email:
            logger.warning(f'Estudiante {student.id} no tiene correo electrónico')
            return False
        
        # Generar PDF si no se proporciona
        if pdf_file is None:
            pdf_file = generate_payment_receipt_pdf(payment)
        
        # Preparar el correo
        subject = f'Recibo de Pago - {payment.payment_type.name if payment.payment_type else "Pago"}'
        
        message = f"""
Estimado/a {student.get_full_name()},

Le enviamos el recibo de su pago realizado el {payment.payment_date.strftime('%d/%m/%Y') if payment.payment_date else 'N/A'}.

Detalles del pago:
- Tipo de pago: {payment.payment_type.name if payment.payment_type else 'N/A'}
- Monto: ${payment.final_amount or payment.amount or 0:.2f}
- Método de pago: {payment.get_payment_method_display()}
- Estado: {payment.get_status_display()}
- Número de recibo: {payment.receipt_number or 'N/A'}

El recibo en PDF se adjunta a este correo.

Saludos cordiales,
Colegio Santa Cecilia
        """
        
        # Obtener el email remitente de la configuración
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if not from_email:
            # Si no hay DEFAULT_FROM_EMAIL configurado, usar SERVER_EMAIL o un valor por defecto
            from_email = getattr(settings, 'SERVER_EMAIL', 'noreply@admincusc.local')
        
        # Crear el mensaje de correo
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=[student.email],
        )
        
        # Adjuntar el PDF
        pdf_file.seek(0)
        filename = f'recibo_{payment.receipt_number or payment.id}_{payment.payment_date.strftime("%Y%m%d") if payment.payment_date else "N/A"}.pdf'
        email.attach(filename, pdf_file.read(), 'application/pdf')
        
        # Enviar el correo
        email.send()
        
        logger.info(f'Recibo enviado por correo a {student.email} para el pago {payment.id}')
        return True
        
    except Exception as e:
        logger.error(f'Error al enviar recibo por correo: {str(e)}', exc_info=True)
        return False
