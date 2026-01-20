from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CareerViewSet, CuatrimestreViewSet, CourseViewSet,
    CourseEnrollmentViewSet, CuatrimestreEnrollmentViewSet, GraduationMethodViewSet
)

router = DefaultRouter()
router.register(r'careers', CareerViewSet, basename='career')
router.register(r'cuatrimestres', CuatrimestreViewSet, basename='cuatrimestre')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'cuatrimestre-enrollments', CuatrimestreEnrollmentViewSet, basename='cuatrimestre-enrollment')
router.register(r'enrollments', CourseEnrollmentViewSet, basename='course-enrollment')
router.register(r'graduation-methods', GraduationMethodViewSet, basename='graduation-method')

urlpatterns = [
    path('', include(router.urls)),
]

