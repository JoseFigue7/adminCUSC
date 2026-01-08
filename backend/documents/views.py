from rest_framework import viewsets
from .models import DocumentTemplate
from .serializers import DocumentTemplateSerializer


class DocumentTemplateViewSet(viewsets.ModelViewSet):
    queryset = DocumentTemplate.objects.filter(is_active=True)
    serializer_class = DocumentTemplateSerializer

