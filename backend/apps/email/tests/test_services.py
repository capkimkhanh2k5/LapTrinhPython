"""
Email Services Tests - Django TestCase Version
"""
from django.test import TestCase

from apps.email.services import EmailService
from apps.email.models import SentEmail, EmailTemplate, EmailTemplateCategory


class TestEmailService(TestCase):
    """Tests for EmailService"""
    
    @classmethod
    def setUpTestData(cls):
        cls.category = EmailTemplateCategory.objects.create(
            name="Notifications",
            slug="notifications-svc"
        )
        cls.email_template = EmailTemplate.objects.create(
            name="Welcome Email",
            slug="welcome-email-svc",
            category=cls.category,
            subject="Welcome {{ name }}",
            body="Hello {{ name }}, welcome to our platform!",
            variables={"name": "User Name"}
        )
    
    def test_send_email_no_template_success(self):
        """EmailService can send email without template"""
        success = EmailService.send_email(
            recipient="test@example.com",
            subject="Test Simple",
            body="Simple Content"
        )
        self.assertTrue(success)
        self.assertEqual(SentEmail.objects.count(), 1)
        log = SentEmail.objects.first()
        self.assertEqual(log.status, SentEmail.Status.SENT)
        self.assertEqual(log.content, "Simple Content")
    
    def test_send_email_template_rendering(self):
        """EmailService can render email templates with context"""
        context = {"name": "John Doe"}
        success = EmailService.send_email(
            recipient="john@example.com",
            subject=None,  # Should auto-fill from template
            template_slug=self.email_template.slug,
            context=context
        )
        self.assertTrue(success)
        log = SentEmail.objects.last()
        # Note: Subject rendering depends on implementation
        # Body should be rendered correctly
        self.assertEqual(log.content, "Hello John Doe, welcome to our platform!")
    
    def test_send_email_invalid_template(self):
        """EmailService returns False for invalid template slug"""
        success = EmailService.send_email(
            recipient="test@example.com",
            subject="Fail",
            template_slug="invalid-slug"
        )
        self.assertFalse(success)
        # Should not log if template missing
        self.assertEqual(SentEmail.objects.filter(recipient="test@example.com").count(), 0)
