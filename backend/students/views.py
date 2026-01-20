from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from datetime import datetime
import logging
import os
from .models import (
    Student, Enrollment, StudentDocument,
    EnrollmentStatusHistory, StudentDocumentStatusHistory,
    Pais, EntidadFederativa, Idioma, NecesidadEducativaEspecial,
    AntecedenteAcademico, NivelEducativo, ModalidadEducativa, Turno
)
from .serializers import (
    StudentSerializer, EnrollmentSerializer, StudentDocumentSerializer,
    EnrollmentStatusHistorySerializer, StudentDocumentStatusHistorySerializer,
    PaisSerializer, EntidadFederativaSerializer, IdiomaSerializer,
    NecesidadEducativaEspecialSerializer, AntecedenteAcademicoSerializer,
    NivelEducativoSerializer, ModalidadEducativaSerializer, TurnoSerializer
)
from .filters import StudentFilter
from academics.models import Career
from .utils import generate_carnet_number, generate_contract
from users.permissions import HasPermission

logger = logging.getLogger(__name__)


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, HasPermission('manage_students')]
    filterset_class = StudentFilter
    search_fields = ['carnet', 'first_name', 'first_last_name', 'second_last_name', 'email', 'career__name']
    ordering_fields = ['enrollment_date', 'first_name', 'first_last_name', 'carnet']
    ordering = ['-enrollment_date']
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            # Permitir ver a usuarios autenticados
            return [permissions.IsAuthenticated()]
        # Para crear/editar/eliminar requiere permiso específico
        return [permissions.IsAuthenticated(), HasPermission('manage_students')]
    
    def create(self, request, *args, **kwargs):
        """Crear estudiante, generar carnet, crear inscripción y generar contrato automáticamente"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        career_id = request.data.get('career')
        if not career_id:
            return Response(
                {'error': 'career es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            career = Career.objects.get(id=career_id)
        except Career.DoesNotExist:
            return Response(
                {'error': 'Carrera no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        with transaction.atomic():
            # Crear estudiante
            student = serializer.save()
            
            # Generar carnet usando función utilitaria
            year = datetime.now().year
            student.carnet = generate_carnet_number(career.code, year)
            student.save()
            
            # Crear inscripción automáticamente con los datos básicos
            enrollment = Enrollment.objects.create(
                student=student,
                enrollment_status='INSCRIPCION',
                school_year=year,
                career=career,
                status='PENDIENTE',
                institutional_id=student.carnet,
                # Los campos CCT y RVOE se completan automáticamente en el save() del modelo
            )
            
            # Generar contrato PDF automáticamente
            try:
                pdf_file = generate_contract(student, enrollment)
                filename = f"contrato_{student.carnet}_{year}.pdf"
                enrollment.contract_file.save(filename, pdf_file, save=False)
                enrollment.contract_generated = True
                enrollment.save()
            except Exception as e:
                # Si falla la generación del contrato, registrar el error pero no fallar la creación del estudiante
                logger.error(f'Error al generar contrato para estudiante {student.id}: {str(e)}', exc_info=True)
                # Marcar el enrollment como creado pero sin contrato generado
                enrollment.contract_generated = False
                enrollment.save()
            
            # Crear documentos requeridos automáticamente para el estudiante
            try:
                required_documents = [
                    'BACHILLERATO_ORIGINAL',
                    'NACIMIENTO_ORIGINAL',
                    'CURP',
                    'MEDICO',
                    'FOTO_DIGITAL',
                    'DOMICILIO',
                ]
                
                documents_created = []
                for doc_type in required_documents:
                    doc, created = StudentDocument.objects.get_or_create(
                        student=student,
                        document_type=doc_type,
                        defaults={
                            'status': 'PENDIENTE',
                            'notes': ''
                        }
                    )
                    if created:
                        documents_created.append(doc_type)
                
                logger.info(f'Documentos requeridos creados para estudiante {student.id}: {len(documents_created)} de {len(required_documents)}')
            except Exception as e:
                logger.error(f'Error al crear documentos requeridos para estudiante {student.id}: {str(e)}', exc_info=True)
                # Continuar sin fallar la creación del estudiante
        
        # Retornar datos del estudiante con información de la inscripción
        student_data = StudentSerializer(student).data
        enrollment_data = EnrollmentSerializer(enrollment, context={'request': request}).data
        student_data['enrollment'] = enrollment_data
        
        return Response(student_data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Obtener progreso académico del estudiante"""
        student = self.get_object()
        from academics.models import CourseEnrollment
        
        # Validar que el estudiante tenga carrera
        if not student.career:
            return Response(
                {'error': 'El estudiante no tiene carrera asignada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        total_courses = student.career.courses.count()
        approved_courses = CourseEnrollment.objects.filter(
            student=student,
            status='APROBADO'
        ).count()
        
        # Evitar división por cero
        progress_percentage = (approved_courses / total_courses * 100) if total_courses > 0 else 0
        
        return Response({
            'total_courses': total_courses,
            'approved_courses': approved_courses,
            'progress_percentage': round(progress_percentage, 2),
            'pensum_closed': student.pensum_closed,
            'graduation_method_started': student.graduation_method_started,
        })


class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'school_year', 'status', 'enrollment_status', 'career']
    search_fields = ['student__first_name', 'student__first_last_name', 'student__carnet', 'institutional_id']
    ordering_fields = ['enrollment_date', 'school_year', 'status']
    ordering = ['-enrollment_date']
    
    def get_serializer_context(self):
        """Asegurar que el contexto de request esté disponible en el serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'generate_contract', 'upload_scanned_contract']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_students')]
    
    def get_queryset(self):
        """Permitir filtrar por estudiante y año escolar"""
        queryset = Enrollment.objects.all()
        student_id = self.request.query_params.get('student')
        school_year = self.request.query_params.get('school_year')
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if school_year:
            queryset = queryset.filter(school_year=school_year)
        
        return queryset.select_related('student', 'career', 'educational_level', 'shift', 'educational_modality')
    
    def create(self, request, *args, **kwargs):
        """Crear inscripción con validaciones SEP"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validar que el estudiante tenga carrera si no se especifica en la inscripción
        student_id = request.data.get('student')
        career_id = request.data.get('career')
        
        if student_id:
            try:
                student = Student.objects.get(id=student_id)
                # Si no se especifica career en la inscripción, usar la del estudiante
                if not career_id and student.career:
                    serializer.validated_data['career'] = student.career
                # Validar que la career del enrollment coincida con la del estudiante
                elif career_id and student.career:
                    career = Career.objects.get(id=career_id)
                    if student.career != career:
                        return Response(
                            {'error': 'La carrera de la inscripción debe coincidir con la carrera del estudiante'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
            except Student.DoesNotExist:
                return Response(
                    {'error': 'Estudiante no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Career.DoesNotExist:
                return Response(
                    {'error': 'Carrera no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        enrollment = serializer.save()
        
        # Pasar usuario para el historial de cambios
        user = request.user if request.user.is_authenticated else None
        enrollment._changed_by_user = user
        enrollment._status_change_notes = 'Inscripción creada'
        
        return Response(
            EnrollmentSerializer(enrollment, context={'request': request}).data, 
            status=status.HTTP_201_CREATED
        )
    
    def perform_update(self, serializer):
        """Capturar usuario que realiza el cambio"""
        user = self.request.user if self.request.user.is_authenticated else None
        instance = serializer.save()
        instance._changed_by_user = user
        instance._status_change_notes = self.request.data.get('notes', '') or ''
        return instance
    
    @action(detail=True, methods=['get'])
    def generate_contract(self, request, pk=None):
        """Generar e imprimir contrato PDF para la inscripción"""
        enrollment = self.get_object()
        
        try:
            # Verificar que el estudiante y la carrera existan
            if not enrollment.student:
                return Response(
                    {'error': 'No se encontró el estudiante asociado a esta inscripción'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generar contrato si no existe, o regenerar si ya existe
            pdf_file = generate_contract(enrollment.student, enrollment)
            
            # Guardar el archivo generado
            if not enrollment.student.carnet:
                filename = f"contrato_{enrollment.student.id}_{enrollment.school_year or datetime.now().year}.pdf"
            else:
                filename = f"contrato_{enrollment.student.carnet}_{enrollment.school_year or datetime.now().year}.pdf"
            
            enrollment.contract_file.save(filename, pdf_file, save=False)
            enrollment.contract_generated = True
            enrollment.save()
            
            # Retornar el PDF para descarga/impresión
            pdf_file.seek(0)
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'  # inline para mostrar en navegador
            return response
        except Exception as e:
            import traceback
            logger.error(f'Error al generar contrato para enrollment {enrollment.id}: {str(e)}')
            logger.error(traceback.format_exc())
            return Response(
                {
                    'error': 'Error al generar el contrato',
                    'detail': str(e),
                    'traceback': traceback.format_exc() if request.user.is_staff else None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def upload_scanned_contract(self, request, pk=None):
        """Subir contrato escaneado firmado por el estudiante"""
        enrollment = self.get_object()
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        
        # Validar que el archivo tenga nombre
        if not file.name:
            return Response(
                {'error': 'El archivo debe tener un nombre válido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tamaño del archivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return Response(
                {'error': f'El archivo es demasiado grande ({file.size / (1024*1024):.2f} MB). El tamaño máximo es 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el archivo no esté vacío
        if file.size == 0:
            return Response(
                {'error': 'El archivo está vacío.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar extensión de archivo
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_ext = os.path.splitext(file.name)[1].lower()
        
        if file_ext not in allowed_extensions:
            return Response(
                {'error': f'Formato de archivo no permitido ({file_ext}). Use: {", ".join(allowed_extensions)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar nombre de archivo (prevenir path traversal)
        if '..' in file.name or '/' in file.name or '\\' in file.name:
            return Response(
                {'error': 'El nombre del archivo contiene caracteres no permitidos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Guardar el archivo
        filename = f"contrato_escaneado_{enrollment.student.carnet}_{enrollment.id}.{file_ext[1:]}"
        enrollment.contract_scanned.save(filename, file, save=False)
        enrollment.contract_uploaded_at = datetime.now()
        enrollment.status = 'EN_REVISION'  # Cambiar estado a en revisión
        enrollment.save()
        
        serializer = self.get_serializer(enrollment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def approve_enrollment(self, request, pk=None):
        """Aprobar inscripción cuando el contrato escaneado ha sido verificado"""
        enrollment = self.get_object()
        
        if not enrollment.contract_scanned:
            return Response(
                {'error': 'No se ha subido el contrato escaneado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Aprobar la inscripción
        enrollment.status = 'APROBADA'
        enrollment.is_officially_enrolled = True
        enrollment.save()
        
        serializer = self.get_serializer(enrollment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def reject_enrollment(self, request, pk=None):
        """Rechazar inscripción"""
        enrollment = self.get_object()
        
        reason = request.data.get('reason', '')
        enrollment.status = 'RECHAZADA'
        enrollment.save()
        
        serializer = self.get_serializer(enrollment, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentDocumentViewSet(viewsets.ModelViewSet):
    queryset = StudentDocument.objects.all()
    serializer_class = StudentDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student', 'document_type', 'status']
    search_fields = ['student__first_name', 'student__first_last_name', 'student__carnet', 'document_type']
    ordering_fields = ['created_at', 'document_type', 'status']
    ordering = ['document_type']
    
    def get_queryset(self):
        """Permitir filtrar por estudiante"""
        queryset = StudentDocument.objects.all().select_related('student')
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        return queryset
    
    def perform_create(self, serializer):
        """Capturar usuario que crea el documento"""
        user = self.request.user if self.request.user.is_authenticated else None
        instance = serializer.save()
        instance._changed_by_user = user
        instance._status_change_notes = 'Documento creado'
        return instance
    
    def perform_update(self, serializer):
        """Capturar usuario que realiza el cambio"""
        user = self.request.user if self.request.user.is_authenticated else None
        instance = serializer.save()
        instance._changed_by_user = user
        instance._status_change_notes = self.request.data.get('notes', '') or ''
        return instance
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve', 'upload_file']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), HasPermission('manage_students')]
    
    @action(detail=True, methods=['post'])
    def upload_file(self, request, pk=None):
        """Subir archivo para un documento"""
        document = self.get_object()
        
        # No permitir subir/reemplazar archivos si el documento está aprobado
        if document.status == 'APROBADO':
            return Response(
                {'error': f'No se puede subir o reemplazar un archivo en el documento "{document.get_document_type_display()}" porque ya ha sido aprobado. Un documento aprobado no puede ser modificado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No se proporcionó archivo'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file = request.FILES['file']
        
        # Validar que el archivo tenga nombre
        if not file.name:
            return Response(
                {'error': 'El archivo debe tener un nombre válido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tamaño del archivo (máximo 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if file.size > max_size:
            return Response(
                {'error': f'El archivo es demasiado grande ({file.size / (1024*1024):.2f} MB). El tamaño máximo es 10MB.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar que el archivo no esté vacío
        if file.size == 0:
            return Response(
                {'error': 'El archivo está vacío.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar extensión de archivo
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_ext = os.path.splitext(file.name)[1].lower()
        if file_ext not in allowed_extensions:
            return Response(
                {'error': f'Extensión de archivo no permitida ({file_ext}). Solo se permiten: {", ".join(allowed_extensions)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar tipo MIME (content_type puede ser manipulado, pero es una primera línea de defensa)
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
        if file.content_type and file.content_type not in allowed_types:
            # Verificar extensión como segunda validación si el content_type no coincide
            if file_ext not in allowed_extensions:
                return Response(
                    {'error': 'Tipo de archivo no permitido. Solo se permiten PDF, JPG y PNG.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validar nombre de archivo (prevenir path traversal y caracteres especiales)
        if '..' in file.name or '/' in file.name or '\\' in file.name:
            return Response(
                {'error': 'El nombre del archivo contiene caracteres no permitidos.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Si ya existe un archivo, cambiar estado a RECIBIDO (reemplazo), si no, mantener PENDIENTE o cambiarlo a RECIBIDO
        is_replace = bool(document.file)
        document.file = file
        document.status = 'RECIBIDO'  # Cambiar a recibido cuando se sube/reemplaza
        document.save()
        
        serializer = self.get_serializer(document)
        action_text = 'reemplazado' if is_replace else 'subido'
        return Response({
            **serializer.data,
            'message': f'Documento {action_text} exitosamente'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Actualizar estado de un documento"""
        document = self.get_object()
        
        new_status = request.data.get('status')
        if new_status not in dict(StudentDocument.STATUS_CHOICES):
            return Response(
                {'error': 'Estado inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # No permitir cambiar el estado de un documento aprobado
        if document.status == 'APROBADO' and new_status != 'APROBADO':
            return Response(
                {'error': f'No se puede cambiar el estado del documento "{document.get_document_type_display()}" porque ya ha sido aprobado. Un documento aprobado no puede ser modificado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validación adicional: no se puede aprobar un documento que no tiene archivo
        if new_status == 'APROBADO' and not document.file:
            return Response(
                {'error': f'No se puede aprobar el documento "{document.get_document_type_display()}" porque no tiene archivo subido.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Actualizar estado (ya validamos que no se pueda cambiar de aprobado)
        document.status = new_status
        if 'notes' in request.data:
            document.notes = request.data['notes']
        document.save()
        
        serializer = self.get_serializer(document)
        status_change = 'aprobado' if new_status == 'APROBADO' else 'rechazado' if new_status == 'RECHAZADO' else 'actualizado'
        return Response({
            **serializer.data,
            'message': f'Estado del documento {status_change} exitosamente'
        }, status=status.HTTP_200_OK)


# ==================== VIEWSETS DE CATÁLOGOS SEP ====================

class PaisViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para catálogo de países"""
    queryset = Pais.objects.filter(is_active=True)
    serializer_class = PaisSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo']
    
    def get_queryset(self):
        """Ordenar países con México primero"""
        from django.db.models import Case, When, IntegerField
        queryset = Pais.objects.filter(is_active=True)
        
        # Ordenar con México primero, luego alfabéticamente
        queryset = queryset.annotate(
            priority=Case(
                When(codigo='MX', then=0),
                default=1,
                output_field=IntegerField()
            )
        ).order_by('priority', 'nombre')
        
        return queryset


class EntidadFederativaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para catálogo de entidades federativas"""
    queryset = EntidadFederativa.objects.filter(is_active=True).select_related('pais')
    serializer_class = EntidadFederativaSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre', 'codigo', 'pais__nombre']
    ordering_fields = ['pais', 'nombre', 'codigo']
    ordering = ['nombre']  # Ordenar por nombre por defecto
    filterset_fields = ['pais', 'pais_id']  # Permitir filtrar por país
    pagination_class = None  # Desactivar paginación para este endpoint
    
    def get_queryset(self):
        """Permitir filtrar por país"""
        queryset = EntidadFederativa.objects.filter(is_active=True).select_related('pais')
        
        # Filtrar por país si se proporciona el parámetro
        pais_id = self.request.query_params.get('pais') or self.request.query_params.get('pais_id')
        if pais_id:
            # Filtrar por UUID del país y excluir entidades sin país
            # Usar pais_id para filtrar directamente por la clave foránea
            queryset = queryset.filter(pais_id=pais_id, pais__isnull=False)
        else:
            # Si no se especifica país, solo mostrar entidades que tengan país asignado
            queryset = queryset.filter(pais__isnull=False)
        
        return queryset.order_by('nombre')


class IdiomaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para catálogo de idiomas"""
    queryset = Idioma.objects.filter(is_active=True)
    serializer_class = IdiomaSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo']
    ordering = ['nombre']


class NecesidadEducativaEspecialViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para catálogo de necesidades educativas especiales"""
    queryset = NecesidadEducativaEspecial.objects.filter(is_active=True)
    serializer_class = NecesidadEducativaEspecialSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo', 'tipo']
    ordering = ['nombre']


class AntecedenteAcademicoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para catálogo de antecedentes académicos"""
    queryset = AntecedenteAcademico.objects.filter(is_active=True)
    serializer_class = AntecedenteAcademicoSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo']
    ordering = ['nombre']


class NivelEducativoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para catálogo de niveles educativos"""
    queryset = NivelEducativo.objects.filter(is_active=True)
    serializer_class = NivelEducativoSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo']
    ordering = ['nombre']


class ModalidadEducativaViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para catálogo de modalidades educativas"""
    queryset = ModalidadEducativa.objects.filter(is_active=True)
    serializer_class = ModalidadEducativaSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo']
    ordering = ['nombre']


class TurnoViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para catálogo de turnos"""
    queryset = Turno.objects.filter(is_active=True)
    serializer_class = TurnoSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ['nombre', 'codigo']
    ordering_fields = ['nombre', 'codigo']
    ordering = ['nombre']


class EnrollmentStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar historial de cambios de estado de inscripciones"""
    queryset = EnrollmentStatusHistory.objects.all()
    serializer_class = EnrollmentStatusHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['enrollment', 'changed_by']
    search_fields = ['previous_status', 'new_status', 'comment']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']


class StudentDocumentStatusHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar historial de cambios de estado de documentos"""
    queryset = StudentDocumentStatusHistory.objects.all()
    serializer_class = StudentDocumentStatusHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['student_document', 'changed_by']
    search_fields = ['previous_status', 'new_status', 'comment']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']

