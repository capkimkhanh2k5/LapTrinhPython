from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.email.models import EmailTemplate, EmailTemplateCategory, SentEmail
from apps.email.serializers import (
    EmailTemplateSerializer, 
    EmailTemplateCategorySerializer, 
    SentEmailSerializer
)
from apps.email.services import EmailService

class EmailTemplateCategoryViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplateCategory.objects.all()
    serializer_class = EmailTemplateCategorySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'slug'

class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'slug'

    @action(detail=True, methods=['post'], url_path='test-send')
    def test_send(self, request, slug=None):
        template = self.get_object()
        recipient = request.data.get('recipient')
        if not recipient:
            return Response({"error": "Recipient required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Test sending
        success = EmailService.send_email(
            recipient=recipient,
            subject=f"[TEST] {template.subject}",
            template_slug=template.slug,
            context=request.data.get('context', {})
        )
        
        if success:
            return Response({"status": "sent"})
        else:
            return Response({"status": "failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SentEmailViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SentEmail.objects.all()
    serializer_class = SentEmailSerializer
    permission_classes = [IsAdminUser]
