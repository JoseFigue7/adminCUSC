from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
import io


def generate_contract(student, enrollment):
    """Genera un contrato PDF para el estudiante"""
    from datetime import datetime
    
    context = {
        'student': student,
        'enrollment': enrollment,
        'date': enrollment.enrollment_date.strftime('%d de %B de %Y'),
        'career': student.career.name if student.career else 'N/A',
    }
    
    try:
        html_string = render_to_string('contracts/student_contract.html', context)
    except:
        # Si no existe el template, crear uno básico
        html_string = f"""
        <html>
        <head><meta charset="utf-8"></head>
        <body>
            <h1>Contrato de Inscripción</h1>
            <p><strong>Estudiante:</strong> {student.get_full_name()}</p>
            <p><strong>Carnet:</strong> {student.carnet}</p>
            <p><strong>Carrera:</strong> {context['career']}</p>
            <p><strong>Fecha de Inscripción:</strong> {context['date']}</p>
            <p>Este documento certifica la inscripción del estudiante en el sistema.</p>
        </body>
        </html>
        """
    
    html = HTML(string=html_string)
    
    pdf_file = io.BytesIO()
    html.write_pdf(pdf_file)
    pdf_file.seek(0)
    
    return pdf_file


def generate_carnet_number(career_code, year):
    """Genera número de carnet único"""
    from .models import Student
    
    career_code_str = str(career_code).zfill(3)
    year_str = str(year % 100).zfill(2)
    
    # Buscar último estudiante con este prefijo
    prefix = f"{career_code_str}{year_str}"
    last_student = Student.objects.filter(
        carnet__startswith=prefix
    ).order_by('-carnet').first()
    
    if last_student and last_student.carnet:
        last_number = int(last_student.carnet[-4:])
        new_number = str(last_number + 1).zfill(4)
    else:
        new_number = "0001"
    
    return f"{prefix}{new_number}"

