"""
Email Views Tests - Django TestCase Version
"""
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.email.models import EmailTemplate, EmailTemplateCategory

User = get_user_model()


class TestEmailTemplateViewSet(APITestCase):
    """Tests for EmailTemplate ViewSet"""
    
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            email="admin@email-test.com",
            password="password123",
            first_name="Admin",
            last_name="User"
        )
        cls.regular_user = User.objects.create_user(
            email="user@email-test.com",
            password="password123",
            first_name="Regular",
            last_name="User"
        )
        cls.category = EmailTemplateCategory.objects.create(
            name="Notifications",
            slug="notifications"
        )
        cls.email_template = EmailTemplate.objects.create(
            name="Welcome Email",
            slug="welcome-email",
            category=cls.category,
            subject="Welcome {{ name }}",
            body="Hello {{ name }}, welcome to our platform!",
            variables={"name": "User Name"}
        )
    
    def test_list_templates_admin(self):
        """Admin users can list email templates"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('emailtemplate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    def test_create_template_admin(self):
        """Admin users can create email templates"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('emailtemplate-list')
        data = {
            "name": "New Template",
            "slug": "new-template",
            "category_id": self.category.id,
            "subject": "New Subject",
            "body": "Body content"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_access_denied_regular_user(self):
        """Regular users cannot access email templates"""
        self.client.force_authenticate(user=self.regular_user)
        url = reverse('emailtemplate-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_test_send_action(self):
        """Admin can test send an email template"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('emailtemplate-test-send', kwargs={'slug': self.email_template.slug})
        data = {
            "recipient": "tester@example.com",
            "context": {"name": "Tester"}
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'sent')
