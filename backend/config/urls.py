"""
URL configuration for adminCUSC project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="AdminCUSC API",
      default_version='v1',
      description="API para sistema de gestión estudiantil administrativo",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@admincusc.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('users.urls')),
    path('api/students/', include('students.urls')),
    path('api/academics/', include('academics.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/certificates/', include('certificates.urls')),
    path('api/audit/', include('audit.urls')),  # Rutas de auditoría
    path('api/exports/', include('exports.urls')),  # Rutas de exportación
    path('api/reports/', include('reports.urls')),  # Rutas de reportes
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

