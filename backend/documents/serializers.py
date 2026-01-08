from rest_framework import serializers
from .models import DocumentTemplate


class DocumentTemplateSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = DocumentTemplate
        fields = '__all__'

