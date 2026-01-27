"""
Unit tests for Social Auth Adapter.
Tests verify token validation, error handling, and user creation/linking.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from apps.core.users.models import CustomUser
from apps.core.users.services.social_auth import (
    SocialAdapterFactory,
    GoogleAdapter,
    LinkedInAdapter,
    SocialProfile
)
from apps.core.users.services.auth import social_login, verify_social_token
from apps.core.users.exceptions import (
    TokenInvalidError,
    ProviderUnavailableError,
    EmailNotProvidedError,
    UnsupportedProviderError
)


class SocialAdapterFactoryTest(TestCase):
    """Test the adapter factory."""
    
    def test_get_google_adapter(self):
        adapter = SocialAdapterFactory.get_adapter('google')
        self.assertIsInstance(adapter, GoogleAdapter)
    
    def test_get_linkedin_adapter(self):
        adapter = SocialAdapterFactory.get_adapter('linkedin')
        self.assertIsInstance(adapter, LinkedInAdapter)
    
    def test_unsupported_provider_raises_error(self):
        with self.assertRaises(UnsupportedProviderError):
            SocialAdapterFactory.get_adapter('twitter')
    
    def test_supported_providers_list(self):
        providers = SocialAdapterFactory.supported_providers()
        self.assertIn('google', providers)
        self.assertIn('facebook', providers)
        self.assertIn('linkedin', providers)


class GoogleAdapterTest(TestCase):
    """Test Google OAuth adapter."""
    
    @patch('apps.core.users.services.social_auth.requests.Session.get')
    def test_verify_token_success(self, mock_get):
        """Test successful token verification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'sub': 'google-123',
            'email': 'test@gmail.com',
            'name': 'Test User',
            'picture': 'https://example.com/photo.jpg'
        }
        mock_get.return_value = mock_response
        
        adapter = GoogleAdapter()
        profile = adapter.verify_token('valid_token')
        
        self.assertIsInstance(profile, SocialProfile)
        self.assertEqual(profile.provider, 'google')
        self.assertEqual(profile.email, 'test@gmail.com')
        self.assertEqual(profile.provider_id, 'google-123')
    
    @patch('apps.core.users.services.social_auth.requests.Session.get')
    def test_verify_token_invalid(self, mock_get):
        """Test invalid token raises error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {'error': 'invalid_token'}
        mock_get.return_value = mock_response
        
        adapter = GoogleAdapter()
        with self.assertRaises(TokenInvalidError):
            adapter.verify_token('invalid_token')
    
    @patch('apps.core.users.services.social_auth.requests.Session.get')
    def test_verify_token_no_email(self, mock_get):
        """Test missing email raises error."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'sub': 'google-123',
            'name': 'Test User',
            # No email
        }
        mock_get.return_value = mock_response
        
        adapter = GoogleAdapter()
        with self.assertRaises(EmailNotProvidedError):
            adapter.verify_token('token_without_email')


class SocialLoginTest(TestCase):
    """Test the social_login service function."""
    
    def test_social_login_creates_new_user(self):
        """Test that social_login creates a new user if not exists."""
        with patch('apps.core.users.services.social_auth.SocialAdapterFactory') as MockFactory:
            mock_adapter = MagicMock()
            mock_adapter.verify_token.return_value = SocialProfile(
                provider='google',
                provider_id='new-google-id',
                email='newuser@gmail.com',
                name='New User',
                picture='https://example.com/avatar.jpg'
            )
            MockFactory.get_adapter.return_value = mock_adapter
            
            result = social_login('google', 'valid_token')
            
            self.assertIn('access_token', result)
            self.assertIn('refresh_token', result)
            self.assertTrue(result['is_new_user'])
            
            # Verify user was created
            user = CustomUser.objects.get(email='newuser@gmail.com')
            self.assertEqual(user.social_provider, 'google')
            self.assertEqual(user.social_id, 'new-google-id')
            self.assertTrue(user.email_verified)
    
    def test_social_login_links_existing_user(self):
        """Test that social_login links existing user by email."""
        # Create existing user without social linking
        existing_user = CustomUser.objects.create_user(
            email='existing@gmail.com',
            password='password123',
            full_name='Existing User'
        )
        
        with patch('apps.core.users.services.social_auth.SocialAdapterFactory') as MockFactory:
            mock_adapter = MagicMock()
            mock_adapter.verify_token.return_value = SocialProfile(
                provider='google',
                provider_id='google-link-id',
                email='existing@gmail.com',
                name='Existing User',
                picture=None
            )
            MockFactory.get_adapter.return_value = mock_adapter
            
            result = social_login('google', 'valid_token')
            
            self.assertFalse(result['is_new_user'])
            
            # Verify social linking was added
            existing_user.refresh_from_db()
            self.assertEqual(existing_user.social_provider, 'google')
            self.assertEqual(existing_user.social_id, 'google-link-id')
