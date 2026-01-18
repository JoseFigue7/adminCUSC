from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import io


def generate_contract(student, enrollment):
    """Genera un contrato PDF para el estudiante"""
    from datetime import datetime
    from django.utils import timezone
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Formatear fecha en español
        months_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        
        enrollment_date = enrollment.enrollment_date if hasattr(enrollment, 'enrollment_date') else timezone.now().date()
        date_formatted = f"{enrollment_date.day} de {months_es.get(enrollment_date.month, '')} de {enrollment_date.year}"
        
        # Obtener nombre completo del estudiante
        full_name = student.get_full_name() if hasattr(student, 'get_full_name') else (
            f"{student.first_name} {student.first_last_name or ''} {student.second_last_name or ''}".strip()
        )
        
        # Obtener nombre de la carrera
        career_name = 'N/A'
        if enrollment and hasattr(enrollment, 'career') and enrollment.career:
            career_name = enrollment.career.name
        elif student and hasattr(student, 'career') and student.career:
            career_name = student.career.name
        
        # Cargar el logo en base64 para incluirlo en el PDF
        logo_base64 = None
        try:
            import base64
            from django.conf import settings
            import os
            
            logo_path = os.path.join(settings.BASE_DIR, 'students', 'static', 'students', 'contracts', 'logo.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                    logo_base64 = f"data:image/png;base64,{logo_base64}"
        except Exception as logo_error:
            logger.warning(f'Error al cargar logo: {str(logo_error)}')
        
        context = {
            'student': student,
            'enrollment': enrollment,
            'date': date_formatted,
            'career': career_name,
            'full_name': full_name,  # Agregar nombre completo al contexto
            'student_name': full_name,  # Alias para compatibilidad
            'logo_base64': logo_base64,  # Logo en base64
            'institution_name': 'Colegio Santa Cecilia',
            'institution_acronym': 'CUSC',
            'institution_address': 'Calle Yaquis, Lt 1, Mz. 11, Esquina Huehuecoyotl, Colonia Culturas de México, Chalco, Estado de México, C.P. 56607',
            'institution_maps_url': 'https://maps.app.goo.gl/pEUgydbTAhGRzDQ97',  # URL de Google Maps proporcionada
        }
        
        try:
            html_string = render_to_string('contracts/student_contract.html', context)
        except Exception as template_error:
            logger.warning(f'Error al cargar template de contrato, usando template básico: {str(template_error)}')
            # Si no existe el template, crear uno básico
            html_string = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Contrato de Inscripción</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    h1 {{ font-size: 24px; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>CONTRATO DE INSCRIPCIÓN</h1>
                    <p>Colegio Santa Cecilia</p>
                </div>
                <div>
                    <p><strong>EL ESTUDIANTE:</strong> {full_name}, 
                    con carnet {student.carnet or 'N/A'}, identificado con CURP {student.curp or 'N/A'}, 
                    con domicilio en {student.address or 'No especificado'}, 
                    quien en lo sucesivo se denominará "EL ESTUDIANTE".</p>
                </div>
                <div>
                    <p><strong>LA INSTITUCIÓN:</strong> Colegio Santa Cecilia (CUSC), 
                    con domicilio en Calle Yaquis, Lt 1, Mz. 11, Esquina Huehuecoyotl, Colonia Culturas de México, Chalco, Estado de México, C.P. 56607, 
                    quien en lo sucesivo se denominará "LA INSTITUCIÓN".</p>
                </div>
                <div>
                    <h3>OBJETO DEL CONTRATO:</h3>
                    <p>EL ESTUDIANTE solicita su inscripción y LA INSTITUCIÓN acepta inscribirlo en la carrera de 
                    <strong>{career_name}</strong> para el ciclo escolar {enrollment.school_year if hasattr(enrollment, 'school_year') and enrollment.school_year else datetime.now().year}.</p>
                </div>
                <div style="margin-top: 50px;">
                    <p>Fecha de emisión: {date_formatted}</p>
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

