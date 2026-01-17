import pytest
import secrets
import pyotp
from unittest.mock import patch
from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from apps.core.users.models import CustomUser

@pytest.mark.django_db
class TestIntegratedAuthAPIs:
    
    # --- 1. Register & Login & Logout & Me ---
    
    def test_register_success(self, api_client):
        url = reverse('register')
        data = {
            'email': 'newuser@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'full_name': 'New User',
            'role': 'recruiter'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'access_token' in response.data
        assert 'refresh_token' in response.data
        assert response.data['user']['email'] == 'newuser@example.com'

    def test_login_success(self, api_client, user):
        user.set_password('password123')
        user.save()
        
        url = reverse('login')
        data = {
            'email': user.email,
            'password': 'password123'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.data

    def test_auth_me_success(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('auth-me')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == user.email

    def test_logout_success(self, api_client, user):
        user.set_password('password123')
        user.save()
        
        # Login first to get refresh token
        login_resp = api_client.post(reverse('login'), {'email': user.email, 'password': 'password123'})
        refresh_token = login_resp.data['refresh_token']
        
        # Logout
        url = reverse('logout')
        api_client.force_authenticate(user=user)
        response = api_client.post(url, {'refresh_token': refresh_token})
        # Check views.py: LogoutView returns 200 OK
        assert response.status_code == status.HTTP_200_OK

    def test_refresh_token_success(self, api_client, user):
        user.set_password('password123')
        user.save()
        login_resp = api_client.post(reverse('login'), {'email': user.email, 'password': 'password123'})
        refresh_token = login_resp.data['refresh_token']
        
        url = reverse('token-refresh')
        response = api_client.post(url, {'refresh': refresh_token})
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data

    # --- 2. Email & Password Flows ---

    def test_check_email_exists(self, api_client, user):
        url = reverse('check-email')
        response = api_client.post(url, {'email': user.email})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['exists'] is True

    def test_check_email_not_exists(self, api_client):
        url = reverse('check-email')
        response = api_client.post(url, {'email': 'nobody@example.com'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['exists'] is False

    def test_forgot_password_success(self, api_client, user):
        url = reverse('forgot-password')
        response = api_client.post(url, {'email': user.email})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.password_reset_token is not None

    def test_reset_password_success(self, api_client, user):
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = timezone.now() + timedelta(minutes=5)
        user.save()

        url = reverse('reset-password')
        data = {
            'token': token,
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('newpass123')

    def test_verify_email_success(self, api_client, user):
        token = "verify123"
        user.email_verification_token = token
        user.email_verified = False
        user.save()
        
        url = reverse('verify-email')
        response = api_client.post(url, {'email_verification_token': token})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.email_verified is True

    def test_resend_verification_success(self, api_client, user):
        user.email_verified = False
        user.save()
        url = reverse('resend-verification')
        response = api_client.post(url, {'email': user.email})
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.email_verification_token is not None

    def test_change_password_success(self, api_client, user):
        user.set_password('oldpass123')
        user.save()
        api_client.force_authenticate(user=user)
        
        url = reverse('change-password')
        data = {
            'old_password': 'oldpass123',
            'new_password': 'newpass123',
            'new_password_confirm': 'newpass123'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        user.refresh_from_db()
        assert user.check_password('newpass123')

    # --- 3. Social Login (Mocked) ---

    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_google_success(self, mock_get, api_client):
        # Mock response from Google
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'email': 'googleuser@example.com',
            'name': 'Google User',
            'picture': 'http://avatar.url'
        }
        
        url = reverse('social-login', args=['google'])
        data = {
            'access_token': 'fake_google_token',
            'provider': 'google',
            'email': 'googleuser@example.com',
            'full_name': 'Google User'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['email'] == 'googleuser@example.com'
        assert CustomUser.objects.filter(email='googleuser@example.com').exists()

    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_facebook_success(self, mock_get, api_client):
        # Mock response from Facebook
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'id': '123',
            'name': 'FB User',
            'email': 'fbuser@example.com'
        }
        
        url = reverse('social-login', args=['facebook'])
        data = {
            'access_token': 'fake_fb_token',
            'provider': 'facebook',
            'email': 'fbuser@example.com',
            'full_name': 'FB User'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['email'] == 'fbuser@example.com'

    @patch('apps.core.users.services.auth.requests.get')
    def test_social_login_linkedin_success(self, mock_get, api_client):
        # Mock response from LinkedIn
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            'localizedFirstName': 'LinkedIn',
            'localizedLastName': 'User',
            'id': 'linkedin123',
            # Note: LinkedIn email logic is complex in real API, but our mock simplifies it for now
            # In our verify_social_token service we just return response.json(), 
            # so we assume LinkedIn returns correct structure or we handle it.
            # However, looking at services/auth.py:
            # return response.json()
            # And then: email = social_user_data.get('email') or data.email
            # So if LinkedIn response doesn't have email, it falls back to data.email.
        }
        
        url = reverse('social-login', args=['linkedin'])
        data = {
            'access_token': 'fake_linkedin_token',
            'provider': 'linkedin',
            'email': 'linkedinuser@example.com',
            'full_name': 'LinkedIn User'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user']['email'] == 'linkedinuser@example.com'

    # --- 4. 2FA Verification ---

    def test_verify_2fa_success(self, api_client, user):
        # Setup 2FA
        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        user.two_factor_enabled = True
        user.save()
        
        totp = pyotp.TOTP(secret)
        current_code = totp.now()
        
        api_client.force_authenticate(user=user)
        url = reverse('verify-2fa')
        response = api_client.post(url, {'code': current_code})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data is True

    def test_verify_2fa_failure(self, api_client, user):
        # Setup 2FA
        secret = pyotp.random_base32()
        user.two_factor_secret = secret
        user.two_factor_enabled = True
        user.save()
        
        api_client.force_authenticate(user=user)
        url = reverse('verify-2fa')
        response = api_client.post(url, {'code': '000000'}) # Invalid code
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
