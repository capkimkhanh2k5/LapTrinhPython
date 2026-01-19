from rest_framework.test import APITestCase
from rest_framework import status
from apps.candidate.languages.models import Language


class LanguageViewTest(APITestCase):
    """Test cases for Language Public API"""
    
    def setUp(self):
        # Create sample languages
        self.lang1 = Language.objects.create(
            language_code="en",
            language_name="English",
            native_name="English",
            is_active=True
        )
        self.lang2 = Language.objects.create(
            language_code="vi",
            language_name="Vietnamese",
            native_name="Tiếng Việt",
            is_active=True
        )
        self.lang_inactive = Language.objects.create(
            language_code="xx",
            language_name="Inactive Lang",
            is_active=False
        )
    
    def test_list_languages_success(self):
        """Test GET /api/languages/ - success (AllowAny)"""
        url = '/api/languages/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only active languages (2)
        self.assertEqual(len(response.data), 2)
    
    def test_list_languages_no_auth_required(self):
        """Test GET /api/languages/ works without authentication"""
        # Not authenticated
        url = '/api/languages/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
