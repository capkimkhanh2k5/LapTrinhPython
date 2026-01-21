from rest_framework import serializers
from apps.email.models import EmailTemplate, EmailTemplateCategory, SentEmail

class EmailTemplateCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailTemplateCategory
        fields = ['id', 'name', 'slug', 'description']

class EmailTemplateSerializer(serializers.ModelSerializer):
    category = EmailTemplateCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=EmailTemplateCategory.objects.all(), source='category', write_only=True, required=False
    )
    
    class Meta:
        model = EmailTemplate
        fields = ['id', 'name', 'slug', 'category', 'category_id', 'subject', 'body', 'variables', 'is_active', 'created_at']

class SentEmailSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = SentEmail
        fields = ['id', 'recipient', 'subject', 'content', 'template_name', 'status', 'error_message', 'created_at']
