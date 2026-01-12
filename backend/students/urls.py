from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StudentViewSet, EnrollmentViewSet, StudentDocumentViewSet,
    PaisViewSet, EntidadFederativaViewSet, IdiomaViewSet,
    NecesidadEducativaEspecialViewSet, AntecedenteAcademicoViewSet,
    NivelEducativoViewSet, ModalidadEducativaViewSet, TurnoViewSet
)

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'documents', StudentDocumentViewSet, basename='document')

# Catálogos SEP
router.register(r'catalogos/paises', PaisViewSet, basename='pais')
router.register(r'catalogos/entidades-federativas', EntidadFederativaViewSet, basename='entidad-federativa')
router.register(r'catalogos/idiomas', IdiomaViewSet, basename='idioma')
router.register(r'catalogos/necesidades-educativas-especiales', NecesidadEducativaEspecialViewSet, basename='necesidad-educativa-especial')
router.register(r'catalogos/antecedentes-academicos', AntecedenteAcademicoViewSet, basename='antecedente-academico')
router.register(r'catalogos/niveles-educativos', NivelEducativoViewSet, basename='nivel-educativo')
router.register(r'catalogos/modalidades-educativas', ModalidadEducativaViewSet, basename='modalidad-educativa')
router.register(r'catalogos/turnos', TurnoViewSet, basename='turno')

urlpatterns = [
    path('', include(router.urls)),
]

