from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet, 
    ScholarshipViewSet, 
    PaymentConfigurationViewSet,
    PaymentTypeViewSet,
    get_student_by_carnet,
    create_payment_intent,
    process_public_payment,
    stripe_webhook
)

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'scholarships', ScholarshipViewSet, basename='scholarship')
router.register(r'configurations', PaymentConfigurationViewSet, basename='payment-config')
router.register(r'payment-types', PaymentTypeViewSet, basename='payment-type')

urlpatterns = [
    path('', include(router.urls)),
    path('public/student/', get_student_by_carnet, name='get-student-by-carnet'),
    path('public/payment-intent/', create_payment_intent, name='create-payment-intent'),
    path('public/payment/', process_public_payment, name='process-public-payment'),
    path('stripe/webhook/', stripe_webhook, name='stripe-webhook'),
]

