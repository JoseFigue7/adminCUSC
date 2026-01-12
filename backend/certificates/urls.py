from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegistrationStatusViewSet, DocumentTypeViewSet,
    AcademicCertificateViewSet, CourseCertificateViewSet,
    UniversityTitleViewSet
)

router = DefaultRouter()
router.register(r'registration-statuses', RegistrationStatusViewSet, basename='registration-status')
router.register(r'document-types', DocumentTypeViewSet, basename='document-type')
router.register(r'academic-certificates', AcademicCertificateViewSet, basename='academic-certificate')
router.register(r'course-certificates', CourseCertificateViewSet, basename='course-certificate')
router.register(r'university-titles', UniversityTitleViewSet, basename='university-title')

urlpatterns = [
    path('', include(router.urls)),
]






