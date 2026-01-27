"""
Authentication Edge Cases Tests - Django TestCase Version
"""
import secrets
import pyotp
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from apps.core.users.models import CustomUser


# ============================================================================
# URL PATHS
# ============================================================================
AUTH_LOGIN = '/api/users/auth/login/'
AUTH_LOGOUT = '/api/users/auth/logout/'
AUTH_REGISTER = '/api/users/auth/register/'
AUTH_REFRESH_TOKEN = '/api/users/auth/refresh-token/'
AUTH_VERIFY_EMAIL = '/api/users/auth/verify-email/'
AUTH_RESEND_VERIFICATION = '/api/users/auth/resend-verification/'
AUTH_FORGOT_PASSWORD = '/api/users/auth/forgot-password/'
AUTH_RESET_PASSWORD = '/api/users/auth/reset-password/'
AUTH_CHANGE_PASSWORD = '/api/users/auth/change-password/'
AUTH_VERIFY_2FA = '/api/users/auth/verify-2fa/'


def auth_social_login(provider):
    return f'/api/users/auth/social/{provider}/'


# ============================================================================
# TEST: REFRESH TOKEN API - Edge Cases
# ============================================================================

class TestRefreshTokenEdgeCases(APITestCase):
    """Test cases for refresh token edge cases"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="refresh@example.com",
            password="password123",
            full_name="Refresh User",
            role="recruiter",
            status="active"
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(self.refresh)
        self.access_token = str(self.refresh.access_token)
    
    def test_refresh_token_with_invalid_token(self):
        """Test refresh with invalid token → 401"""
        response = self.client.post(AUTH_REFRESH_TOKEN, {'refresh': 'invalid_token_here'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_refresh_token_with_empty_token(self):
        """Test refresh with empty token → 400"""
        response = self.client.post(AUTH_REFRESH_TOKEN, {'refresh': ''})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_refresh_token_without_token(self):
        """Test refresh without token → 400"""
        response = self.client.post(AUTH_REFRESH_TOKEN, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_refresh_token_with_blacklisted_token(self):
        """Test refresh with blacklisted token → 401"""
        # Blacklist token
        self.client.force_authenticate(user=self.user)
        self.client.post(AUTH_LOGOUT, {'refresh_token': self.refresh_token})
        
        # Try to refresh
        response = self.client.post(AUTH_REFRESH_TOKEN, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================================
# TEST: VERIFY EMAIL API - Edge Cases
# ============================================================================

class TestVerifyEmailEdgeCases(APITestCase):
    """Test cases for verify email edge cases"""
    
    def setUp(self):
        self.unverified_user = CustomUser.objects.create_user(
            email="unverified@example.com",
            password="password123",
            full_name="Unverified User",
            role="recruiter"
        )
        self.unverified_user.email_verified = False
        self.unverified_user.email_verification_token = "valid_verify_token_123"
        self.unverified_user.save()
    
    def test_verify_email_with_invalid_token(self):
        """Test verify with invalid token → 400"""
        response = self.client.post(AUTH_VERIFY_EMAIL, {
            'email_verification_token': 'invalid_token_not_exist'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_verify_email_with_empty_token(self):
        """Test verify with empty token → 400"""
        response = self.client.post(AUTH_VERIFY_EMAIL, {
            'email_verification_token': ''
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verify_email_without_token(self):
        """Test verify without token → 400"""
        response = self.client.post(AUTH_VERIFY_EMAIL, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verify_email_already_verified(self):
        """Test verify email that was already verified → token deleted after first verify"""
        token = self.unverified_user.email_verification_token
        
        # First verify - success
        response1 = self.client.post(AUTH_VERIFY_EMAIL, {'email_verification_token': token})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second verify - token already deleted
        response2 = self.client.post(AUTH_VERIFY_EMAIL, {'email_verification_token': token})
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TEST: RESEND VERIFICATION API - Edge Cases
# ============================================================================

class TestResendVerificationEdgeCases(APITestCase):
    """Test cases for resend verification edge cases"""
    
    def setUp(self):
        self.verified_user = CustomUser.objects.create_user(
            email="verified@example.com",
            password="password123",
            full_name="Verified User",
            role="recruiter"
        )
        self.verified_user.email_verified = True
        self.verified_user.save()
    
    def test_resend_verification_email_not_exist(self):
        """Test resend with non-existent email → 400"""
        response = self.client.post(AUTH_RESEND_VERIFICATION, {
            'email': 'notexist@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_resend_verification_email_already_verified(self):
        """Test resend with already verified email → 400"""
        response = self.client.post(AUTH_RESEND_VERIFICATION, {
            'email': self.verified_user.email
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)


# ============================================================================
# TEST: FORGOT PASSWORD API - Edge Cases
# ============================================================================

class TestForgotPasswordEdgeCases(APITestCase):
    """Test cases for forgot password edge cases"""
    
    def test_forgot_password_email_not_exist(self):
        """Test forgot password with non-existent email → 400"""
        response = self.client.post(AUTH_FORGOT_PASSWORD, {
            'email': 'notexist@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_forgot_password_invalid_email_format(self):
        """Test forgot password with invalid email format → 400"""
        response = self.client.post(AUTH_FORGOT_PASSWORD, {
            'email': 'invalid-email-format'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TEST: RESET PASSWORD API - Edge Cases
# ============================================================================

class TestResetPasswordEdgeCases(APITestCase):
    """Test cases for reset password edge cases"""
    
    def setUp(self):
        # User with valid reset token
        self.user = CustomUser.objects.create_user(
            email="reset@example.com",
            password="oldpassword123",
            full_name="Reset User",
            role="recruiter"
        )
        self.token = secrets.token_urlsafe(32)
        self.user.password_reset_token = self.token
        self.user.password_reset_expires = timezone.now() + timedelta(minutes=5)
        self.user.save()
        
        # User with expired token
        self.expired_user = CustomUser.objects.create_user(
            email="expired@example.com",
            password="oldpassword123",
            full_name="Expired User",
            role="recruiter"
        )
        self.expired_token = secrets.token_urlsafe(32)
        self.expired_user.password_reset_token = self.expired_token
        self.expired_user.password_reset_expires = timezone.now() - timedelta(minutes=1)
        self.expired_user.save()
    
    def test_reset_password_invalid_token(self):
        """Test reset with invalid token → 400"""
        response = self.client.post(AUTH_RESET_PASSWORD, {
            'token': 'invalid_token_not_exist',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_reset_password_expired_token(self):
        """Test reset with expired token → 400"""
        response = self.client.post(AUTH_RESET_PASSWORD, {
            'token': self.expired_token,
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_reset_password_missing_token(self):
        """Test reset without token → 400"""
        response = self.client.post(AUTH_RESET_PASSWORD, {
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TEST: CHANGE PASSWORD API - Edge Cases
# ============================================================================

class TestChangePasswordEdgeCases(APITestCase):
    """Test cases for change password edge cases"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="changepass@example.com",
            password="oldpassword123",
            full_name="Change Pass User",
            role="recruiter",
            status="active"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_change_password_wrong_old_password(self):
        """Test change password with wrong old_password → 400"""
        response = self.client.post(AUTH_CHANGE_PASSWORD, {
            'old_password': 'wrongoldpassword',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_change_password_without_authentication(self):
        """Test change password without being logged in → 401"""
        self.client.credentials()  # Clear credentials
        
        response = self.client.post(AUTH_CHANGE_PASSWORD, {
            'old_password': 'oldpassword123',
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================================
# TEST: SOCIAL LOGIN API - Edge Cases
# ============================================================================

class TestSocialLoginEdgeCases(APITestCase):
    """Test cases for social login edge cases"""
    
    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_google_invalid_token(self, mock_get):
        """Test Google login with invalid token → 400"""
        mock_get.return_value.status_code = 401  # Google returns error
        
        response = self.client.post(auth_social_login('google'), {
            'access_token': 'invalid_google_token',
            'provider': 'google',
            'email': 'test@example.com',
            'full_name': 'Test User'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_facebook_invalid_token(self, mock_get):
        """Test Facebook login with invalid token → 400"""
        mock_get.return_value.status_code = 401  # Facebook returns error
        
        response = self.client.post(auth_social_login('facebook'), {
            'access_token': 'invalid_fb_token',
            'provider': 'facebook',
            'email': 'test@example.com',
            'full_name': 'Test User'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_linkedin_invalid_token(self, mock_get):
        """Test LinkedIn login with invalid token → 400"""
        mock_get.return_value.status_code = 401  # LinkedIn returns error
        
        response = self.client.post(auth_social_login('linkedin'), {
            'access_token': 'invalid_linkedin_token',
            'provider': 'linkedin',
            'email': 'test@example.com',
            'full_name': 'Test User'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_social_login_unsupported_provider(self):
        """Test social login with unsupported provider → 400 or 404"""
        response = self.client.post(auth_social_login('twitter'), {
            'access_token': 'some_token',
            'provider': 'twitter',
            'email': 'test@example.com',
            'full_name': 'Test User'
        })
        # Can be 400 or 404 depending on URL pattern
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])
    
    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_existing_user(self, mock_get):
        """Test social login with existing user → login success"""
        # Create existing user
        existing_user = CustomUser.objects.create_user(
            email="existing@example.com",
            password="password123",
            full_name="Existing User",
            role="recruiter"
        )
        
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'email': 'existing@example.com',
            'name': 'Existing User'
        }
        
        response = self.client.post(auth_social_login('google'), {
            'access_token': 'valid_google_token',
            'provider': 'google',
            'email': 'existing@example.com',
            'full_name': 'Existing User'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)


# ============================================================================
# TEST: 2FA API - Edge Cases
# ============================================================================

class TestVerify2FAEdgeCases(APITestCase):
    """Test cases for 2FA verification edge cases"""
    
    def setUp(self):
        # User without 2FA
        self.user_no_2fa = CustomUser.objects.create_user(
            email="no2fa@example.com",
            password="password123",
            full_name="No 2FA User",
            role="recruiter",
            status="active"
        )
        self.user_no_2fa.two_factor_enabled = False
        self.user_no_2fa.save()
        
        # User with 2FA
        self.user_with_2fa = CustomUser.objects.create_user(
            email="with2fa@example.com",
            password="password123",
            full_name="With 2FA User",
            role="recruiter",
            status="active"
        )
        self.secret = pyotp.random_base32()
        self.user_with_2fa.two_factor_secret = self.secret
        self.user_with_2fa.two_factor_enabled = True
        self.user_with_2fa.save()
    
    def test_verify_2fa_not_enabled(self):
        """Test verify 2FA when 2FA is not enabled → 400"""
        refresh = RefreshToken.for_user(self.user_no_2fa)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.post(AUTH_VERIFY_2FA, {'code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
    
    def test_verify_2fa_wrong_code(self):
        """Test verify 2FA with wrong code → 400"""
        refresh = RefreshToken.for_user(self.user_with_2fa)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        response = self.client.post(AUTH_VERIFY_2FA, {'code': '000000'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_verify_2fa_without_authentication(self):
        """Test verify 2FA without being logged in → 401"""
        response = self.client.post(AUTH_VERIFY_2FA, {'code': '123456'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
