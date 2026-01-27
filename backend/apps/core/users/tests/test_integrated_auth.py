"""
Integrated Auth APIs Tests - Django TestCase Version
"""
import secrets
import pyotp
from unittest.mock import patch
from datetime import timedelta
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.utils import timezone
from apps.core.users.models import CustomUser

AUTH_LOGIN = '/api/users/auth/login/'
AUTH_LOGOUT = '/api/users/auth/logout/'
AUTH_REGISTER = '/api/users/auth/register/'
AUTH_ME = '/api/users/auth/me/'
AUTH_CHECK_EMAIL = '/api/users/auth/check-email/'
AUTH_FORGOT_PASSWORD = '/api/users/auth/forgot-password/'
AUTH_RESET_PASSWORD = '/api/users/auth/reset-password/'
AUTH_VERIFY_EMAIL = '/api/users/auth/verify-email/'
AUTH_RESEND_VERIFICATION = '/api/users/auth/resend-verification/'
AUTH_CHANGE_PASSWORD = '/api/users/auth/change-password/'
AUTH_VERIFY_2FA = '/api/users/auth/verify-2fa/'
AUTH_TOKEN_REFRESH = '/api/users/auth/refresh-token/'


def auth_social_login(provider):
    return f'/api/users/auth/social/{provider}/'


class TestIntegratedAuthAPIs(APITestCase):
    """Test cases for integrated auth APIs"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            role="recruiter",
            status="active"
        )
    
    def test_register_success(self):
        data = {
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'New User',
            'role': 'recruiter'
        }
        response = self.client.post(AUTH_REGISTER, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access_token', response.data)
        self.assertIn('refresh_token', response.data)
        self.assertEqual(response.data['user']['email'], 'newuser@example.com')

    def test_login_success(self):
        self.user.set_password('password123')
        self.user.save()
        
        data = {
            'email': self.user.email,
            'password': 'password123'
        }
        response = self.client.post(AUTH_LOGIN, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

    def test_auth_me_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(AUTH_ME)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_logout_success(self):
        self.user.set_password('password123')
        self.user.save()
        
        # Login first to get refresh token
        login_resp = self.client.post(AUTH_LOGIN, {'email': self.user.email, 'password': 'password123'})
        refresh_token = login_resp.data['refresh_token']
        
        # Logout
        self.client.force_authenticate(user=self.user)
        response = self.client.post(AUTH_LOGOUT, {'refresh_token': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_token_success(self):
        self.user.set_password('password123')
        self.user.save()
        login_resp = self.client.post(AUTH_LOGIN, {'email': self.user.email, 'password': 'password123'})
        refresh_token = login_resp.data['refresh_token']
        
        response = self.client.post(AUTH_TOKEN_REFRESH, {'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    # --- 2. Email & Password Flows ---

    def test_check_email_exists(self):
        response = self.client.post(AUTH_CHECK_EMAIL, {'email': self.user.email})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exists'])

    def test_check_email_not_exists(self):
        response = self.client.post(AUTH_CHECK_EMAIL, {'email': 'nobody@example.com'})
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
        self.user.set_password('oldpass123')
        self.user.save()
        self.client.force_authenticate(user=self.user)
        
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = self.client.post(AUTH_CHANGE_PASSWORD, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    # --- 3. Social Login (Mocked) ---

    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_google_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'email': 'googleuser@example.com',
            'name': 'Google User',
            'picture': 'http://avatar.url'
        }
        
        data = {
            'access_token': 'fake_google_token',
            'provider': 'google',
            'email': 'googleuser@example.com',
            'full_name': 'Google User'
        }
        response = self.client.post(auth_social_login('google'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'googleuser@example.com')
        self.assertTrue(CustomUser.objects.filter(email='googleuser@example.com').exists())

    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_facebook_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'id': '123',
            'name': 'FB User',
            'email': 'fbuser@example.com'
        }
        
        data = {
            'access_token': 'fake_fb_token',
            'provider': 'facebook',
            'email': 'fbuser@example.com',
            'full_name': 'FB User'
        }
        response = self.client.post(auth_social_login('facebook'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'fbuser@example.com')

    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_linkedin_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'localizedFirstName': 'LinkedIn',
            'localizedLastName': 'User',
            'id': 'linkedin123',
        }
        
        data = {
            'access_token': 'fake_linkedin_token',
            'provider': 'linkedin',
            'email': 'linkedinuser@example.com',
            'full_name': 'LinkedIn User'
        }
        response = self.client.post(auth_social_login('linkedin'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'linkedinuser@example.com')

    # --- 4. 2FA Verification ---

    def test_verify_2fa_success(self):
        secret = pyotp.random_base32()
        self.user.two_factor_secret = secret
        self.user.two_factor_enabled = True
        self.user.save()
        
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(AUTH_VERIFY_2FA, {'code': current_code})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)

    def test_verify_2fa_failure(self):
        secret = pyotp.random_base32()
        self.user.two_factor_secret = secret
        self.user.two_factor_enabled = True
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(AUTH_VERIFY_2FA, {'code': '000000'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
