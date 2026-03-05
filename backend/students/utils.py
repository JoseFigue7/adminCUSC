from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import io
import os
from pathlib import Path
from django.conf import settings


def generate_contract(student, enrollment):
    """Genera un contrato PDF para el estudiante usando el formato de contrato.txt"""
    from datetime import datetime
    from django.utils import timezone
    import logging
    from academics.models import CourseEnrollment
    from payments.models import PaymentType
    from decimal import Decimal
    
    logger = logging.getLogger(__name__)
    
    try:
        # VALIDACIÓN: Verificar que el estudiante tenga cursos asignados
        course_enrollments = CourseEnrollment.objects.filter(student=student)
        if not course_enrollments.exists():
            raise ValueError('No se puede generar el contrato: el estudiante no tiene cursos asignados.')
        
        # Leer el archivo contrato.txt de la raíz del proyecto
        # BASE_DIR apunta a backend/, así que necesitamos subir un nivel para llegar a la raíz
        # La estructura es: proyecto/backend/config/settings.py
        # Entonces BASE_DIR = proyecto/backend
        # Y queremos: proyecto/contrato.txt
        project_root = Path(settings.BASE_DIR).parent
        contract_file_path = project_root / 'contrato.txt'
        
        # Si no existe, intentar rutas alternativas
        if not contract_file_path.exists():
            # Intentar con la ruta relativa desde el archivo actual
            current_file = Path(__file__).resolve()
            # Desde backend/students/utils.py subir 3 niveles para llegar a la raíz
            alt_path = current_file.parent.parent.parent / 'contrato.txt'
            if alt_path.exists():
                contract_file_path = alt_path
            else:
                # Último intento: buscar desde el directorio de trabajo actual
                cwd_path = Path.cwd() / 'contrato.txt'
                if cwd_path.exists():
                    contract_file_path = cwd_path
                else:
                    logger.error(f'No se encontró contrato.txt. Buscado en: {project_root / "contrato.txt"}, {alt_path}, {cwd_path}')
                    raise FileNotFoundError(
                        f'No se encontró el archivo contrato.txt en la raíz del proyecto.\n'
                        f'Buscado en:\n'
                        f'1. {project_root / "contrato.txt"}\n'
                        f'2. {alt_path}\n'
                        f'3. {cwd_path}\n'
                        f'BASE_DIR: {settings.BASE_DIR}\n'
                        f'Archivo actual: {current_file}'
                    )
        
        logger.info(f'Leyendo contrato desde: {contract_file_path}')
        with open(contract_file_path, 'r', encoding='utf-8') as f:
            contract_template = f.read()
        
        # Obtener datos del estudiante para reemplazar variables
        full_name = student.get_full_name() if hasattr(student, 'get_full_name') else (
            f"{student.first_name} {student.first_last_name or ''} {student.second_last_name or ''}".strip()
        )
        
        # Obtener país de nacimiento
        birth_country = 'No especificado'
        if student.birth_country:
            birth_country = student.birth_country.nombre
        
        # Obtener dirección
        address = student.address or 'No especificado'
        
        # Obtener fecha actual formateada
        from datetime import date
        months_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        today = date.today()
        fecha_actual = f"{today.day} de {months_es.get(today.month, '')} de {today.year}"
        
        # Obtener valores de pago
        # Buscar PaymentType con código 101 (inscripción)
        payment_type_101 = PaymentType.objects.filter(code='101', is_active=True).first()
        enrollment_value = 'No especificado'
        if payment_type_101 and payment_type_101.amount:
            # Formato mexicano: $1,234.56
            enrollment_value = f"${payment_type_101.amount:,.2f}"
        
        # Verificar si el estudiante tiene beca activa para determinar el código de pago
        scholarship = getattr(student, 'scholarship', None)
        scholarship_type = None
        payment_code = '102'  # Por defecto sin beca
        
        if scholarship and scholarship.status == 'ACTIVA':
            scholarship_type = scholarship.scholarship_type
            if scholarship_type == 'COMPLETA':
                payment_code = '105'
            elif scholarship_type == 'MEDIA':
                payment_code = '103'
        
        # Buscar PaymentType según el código correspondiente (102, 103 o 105)
        payment_type = PaymentType.objects.filter(code=payment_code, is_active=True).first()
        monthly_tuition_value = 'No especificado'
        
        if payment_type:
            if payment_code == '105':
                # Beca completa: monto es 0
                monthly_tuition_value = "$0.00"
            elif payment_code == '103':
                # Media beca: obtener monto base del 102 y aplicar 50% de descuento
                payment_type_102 = PaymentType.objects.filter(code='102', is_active=True).first()
                if payment_type_102 and payment_type_102.amount:
                    base_amount = payment_type_102.amount
                    discounted_amount = base_amount * Decimal('0.50')
                    monthly_tuition_value = f"${discounted_amount:,.2f}"
            else:
                # Sin beca: monto normal
                if payment_type.amount:
                    monthly_tuition_value = f"${payment_type.amount:,.2f}"
        
        # Reemplazar variables en el contrato
        contract_content = contract_template
        contract_content = contract_content.replace('$NombreCompletoEstudiante', full_name)
        contract_content = contract_content.replace('$NombreCompletoEstudainte', full_name)  # Corregir typo en el template
        contract_content = contract_content.replace('$valordepago101', enrollment_value)
        contract_content = contract_content.replace('$valordepago102', monthly_tuition_value)
        # Agregar código de pago si hay una variable para ello en el contrato
        contract_content = contract_content.replace('$codigopago102', payment_code)
        contract_content = contract_content.replace('$codigopago', payment_code)
        contract_content = contract_content.replace('$PaísdeNacimiento', birth_country)
        contract_content = contract_content.replace('$Dirección', address)
        # Reemplazar fecha actual (puede venir con # o $, en mayúsculas o minúsculas)
        contract_content = contract_content.replace('#FechaActual', fecha_actual)
        contract_content = contract_content.replace('$FechaActual', fecha_actual)
        contract_content = contract_content.replace('#FECHAACTUAL', fecha_actual)
        contract_content = contract_content.replace('$FECHAACTUAL', fecha_actual)
        
        # Convertir el contenido del contrato a HTML
        import html as html_escape
        import re
        
        # Escapar primero para evitar inyección de código
        contract_escaped = html_escape.escape(contract_content)
        
        # Procesar la sección de firmas ANTES de convertir guiones bajos
        # Buscar y reemplazar la sección de firmas con formato mejorado
        signature_marker = 'Firma de Centro de Capacitación'
        if signature_marker in contract_escaped:
            # Dividir el contenido en dos partes: antes y después de las firmas
            parts = contract_escaped.split(signature_marker)
            if len(parts) > 1:
                # Crear la sección de firmas mejorada
                signature_section = f'''<br><br><div class="signature-section">
    <div class="signature-box">
        <p style="margin-bottom: 10px; font-weight: bold; text-align: center;">Firma de Colegio Santa Cecilia</p>
        <div class="signature-line">
            <p style="margin: 0; font-size: 10px; text-align: center;">Lic. Gustavo Adolfo Argeta Mendez</p>
        </div>
    </div>
    <div class="signature-box">
        <p style="margin-bottom: 10px; font-weight: bold; text-align: center;">Firma del ESTUDIANTE</p>
        <div class="signature-line">
            <p style="margin: 0; font-size: 10px; text-align: center;">{html_escape.escape(full_name)}</p>
        </div>
    </div>
</div>'''
                # Reemplazar desde el marcador hasta el final
                contract_escaped = parts[0] + signature_section
        
        # Reemplazar secuencias de guiones bajos con campos subrayados
        def replace_underscore_sequence(match):
            underscores = match.group(0)
            length = len(underscores)
            # Crear un span con subrayado que tenga el ancho apropiado
            return f'<span class="underline-field" style="border-bottom: 1px solid black; padding: 0 3px; display: inline-block; min-width: {max(length * 0.4, 2)}em;">&nbsp;</span>'
        
        # Reemplazar todas las secuencias de guiones bajos
        contract_escaped = re.sub(r'_+', replace_underscore_sequence, contract_escaped)
        
        # Convertir saltos de línea a <br>
        contract_html = contract_escaped.replace('\n', '<br>')
        
        # Crear HTML con el contenido del contrato
        html_string = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Contrato de Prestación de Servicios Educativos</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.8;
            font-size: 11px;
        }}
        .contract-content {{
            text-align: justify;
        }}
        .underline-field {{
            border-bottom: 1px solid black;
            padding: 0 3px;
            display: inline-block;
            min-width: 2em;
        }}
        .signature-section {{
            margin-top: 60px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            page-break-inside: avoid;
        }}
        .signature-box {{
            width: 45%;
            text-align: center;
        }}
        .signature-line {{
            border-top: 2px solid black;
            padding-top: 5px;
            margin-top: 50px;
        }}
        @media print {{
            .signature-section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="contract-content">
{contract_html}
    </div>
</body>
</html>"""
        
        # Generar PDF
        html = HTML(string=html_string)
        pdf_file = io.BytesIO()
        html.write_pdf(pdf_file)
        pdf_file.seek(0)
        
        return pdf_file
        
    except Exception as e:
        logger.error(f'Error al generar contrato: {str(e)}', exc_info=True)
        raise


def generate_carnet_number(career_code, year):
    """
    Genera número de carnet único de forma segura (previene race conditions)
    
    Args:
        career_code: Código de la carrera (int)
        year: Año de inscripción (int)
    
    Returns:
        str: Número de carnet único en formato CCCIAA#### (C=Career, I=Institucional, A=Año, #=Secuencial)
    """
    from .models import Student
    from django.db import transaction
    import time
    
    # Validar entrada
    if not career_code or not year:
        raise ValueError('career_code y year son requeridos para generar el carnet')
    
    career_code_str = str(career_code).zfill(3)
    year_str = str(year % 100).zfill(2)
    prefix = f"{career_code_str}{year_str}"
    
    # Usar transacción para prevenir race conditions
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            with transaction.atomic():
                # Buscar último estudiante con este prefijo (lock en la fila)
                last_student = Student.objects.filter(
                    carnet__startswith=prefix
                ).select_for_update().order_by('-carnet').first()
                
                if last_student and last_student.carnet and len(last_student.carnet) >= 9:
                    try:
                        last_number = int(last_student.carnet[-4:])
                        new_number = str(last_number + 1).zfill(4)
                    except (ValueError, IndexError):
                        # Si hay error al parsear, empezar desde 0001
                        new_number = "0001"
                else:
                    new_number = "0001"
                
                # Verificar que el carnet no existe antes de retornar
                new_carnet = f"{prefix}{new_number}"
                if not Student.objects.filter(carnet=new_carnet).exists():
                    return new_carnet
                
                # Si el carnet existe, incrementar y reintentar
                new_number = str(int(new_number) + 1).zfill(4)
                
        except Exception as e:
            if attempt == max_attempts - 1:
                # Si falla después de varios intentos, usar timestamp como fallback
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f'Error al generar carnet único después de {max_attempts} intentos: {str(e)}')
                timestamp_suffix = str(int(time.time()))[-4:]  # Últimos 4 dígitos del timestamp
                return f"{prefix}{timestamp_suffix}"
            time.sleep(0.1)  # Pequeño delay antes de reintentar
    
    # Fallback final
    timestamp_suffix = str(int(time.time()))[-4:]
    return f"{prefix}{timestamp_suffix}"
