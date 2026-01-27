"""
New Auth Endpoints Tests - Django TestCase Version
"""
import secrets
from datetime import timedelta
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from apps.core.users.models import CustomUser


# ============================================================================
# URL PATHS
# ============================================================================
AUTH_CHECK_EMAIL = '/api/users/auth/check-email/'
AUTH_FORGOT_PASSWORD = '/api/users/auth/forgot-password/'
AUTH_RESET_PASSWORD = '/api/users/auth/reset-password/'
AUTH_VERIFY_EMAIL = '/api/users/auth/verify-email/'
AUTH_RESEND_VERIFICATION = '/api/users/auth/resend-verification/'
AUTH_CHANGE_PASSWORD = '/api/users/auth/change-password/'


class TestNewAuthAPIs(APITestCase):
    """Test cases for new auth endpoints"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role="recruiter",
            status="active"
        )
    
    def test_check_email_exists(self):
        response = self.client.post(AUTH_CHECK_EMAIL, {'email': self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])
    
    def test_check_email_not_exists(self):
        response = self.client.post(AUTH_CHECK_EMAIL, {'email': 'nonexist@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['exists'])
    
    def test_forgot_password_success(self):
        response = self.client.post(AUTH_FORGOT_PASSWORD, {'email': self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.password_reset_token)
    
    def test_reset_password_success(self):
        token = secrets.token_urlsafe(32)
        self.user.password_reset_token = token
        self.user.password_reset_expires = timezone.now() + timedelta(minutes=5)
        self.user.save()
        
        data = {
            'token': token,
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = self.client.post(AUTH_RESET_PASSWORD, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
    
    def test_verify_email_success(self):
        token = "verify123"
        self.user.email_verification_token = token
        self.user.email_verified = False
        self.user.save()
        
        response = self.client.post(AUTH_VERIFY_EMAIL, {'email_verification_token': token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
    
    def test_resend_verification_success(self):
        self.user.email_verified = False
        self.user.save()
        response = self.client.post(AUTH_RESEND_VERIFICATION, {'email': self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_verification_token)
    
    def test_change_password_success(self):
        self.user.set_password('oldpass')
        self.user.save()
        self.client.force_authenticate(user=self.user)
        
        data = {
            'old_password': 'oldpass',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = self.client.post(AUTH_CHANGE_PASSWORD, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))
