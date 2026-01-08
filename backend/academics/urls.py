from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CareerViewSet, CuatrimestreViewSet, CourseViewSet,
    CourseEnrollmentViewSet, ThesisViewSet
)

router = DefaultRouter()
router.register(r'careers', CareerViewSet, basename='career')
router.register(r'cuatrimestres', CuatrimestreViewSet, basename='cuatrimestre')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'enrollments', CourseEnrollmentViewSet, basename='course-enrollment')
router.register(r'thesis', ThesisViewSet, basename='thesis')

urlpatterns = [
    path('', include(router.urls)),
]

