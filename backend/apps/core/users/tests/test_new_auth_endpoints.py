import pytest
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
import secrets

from apps.core.users.models import CustomUser

@pytest.mark.django_db
class TestNewAuthAPIs:
    def test_check_email_exists(self, api_client, user):
        url = reverse('check-email')
        response = api_client.post(url, {'email': user.email})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['exists'] is True

    def test_check_email_not_exists(self, api_client):
        url = reverse('check-email')
        response = api_client.post(url, {'email': 'nonexistent@example.com'})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['exists'] is False

    def test_forgot_password_success(self, api_client, user):
        url = reverse('forgot-password')
        response = api_client.post(url, {'email': user.email})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == "Email đã được gửi"
        
        user.refresh_from_db()
        assert user.password_reset_token is not None
        assert user.password_reset_expires > timezone.now()

    def test_reset_password_success(self, api_client, user):
        # Setup reset token
        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expires = timezone.now() + timedelta(minutes=5)
        user.save()

        url = reverse('reset-password')
        data = {
            'token': token,
            'new_password': 'newpassword123',
            'new_password_confirm': 'newpassword123'
        }
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == "Mật khẩu đã được đổi"

        user.refresh_from_db()
        assert user.check_password('newpassword123')
        assert user.password_reset_token is None

    def test_verify_email_success(self, api_client, user):
        # Setup verify token
        token = secrets.token_urlsafe(32)
        user.email_verification_token = token
        user.email_verified = False
        user.save()

        url = reverse('verify-email')
        response = api_client.post(url, {'email_verification_token': token})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == "Email đã được xác minh"

        user.refresh_from_db()
        assert user.email_verified is True
        assert user.email_verification_token is None

    def test_resend_verification_success(self, api_client, user):
        user.email_verified = False
        user.save()

        url = reverse('resend-verification')
        response = api_client.post(url, {'email': user.email})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == "Email xác minh đã được gửi lại"

        user.refresh_from_db()
        assert user.email_verification_token is not None

    def test_change_password_success(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse('change-password')
        data = {
            'old_password': 'password123', # Default password in factory/fixture usually
            'new_password': 'newsecretpwd123',
            'new_password_confirm': 'newsecretpwd123'
        }
        # Note: 'user' fixture in conftest.py usually has password 'password123' 
        # but I should check if it's set correctly.
        
        # Let's set it explicitly to be sure
        user.set_password('oldpassword123')
        user.save()
        
        data['old_password'] = 'oldpassword123'
        
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == "Mật khẩu đã được đổi"

        user.refresh_from_db()
        assert user.check_password('newsecretpwd123')
