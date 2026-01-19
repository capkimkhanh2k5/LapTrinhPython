from rest_framework.test import APITestCase
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.languages.models import Language
from apps.candidate.recruiter_languages.models import RecruiterLanguage


class RecruiterLanguageViewTest(APITestCase):
    """Test cases for RecruiterLanguage APIs"""
    
    def setUp(self):
        # Create test users
        self.user = CustomUser.objects.create_user(
            email="test@example.com", 
            password="password123", 
            full_name="User 1"
        )
        self.user2 = CustomUser.objects.create_user(
            email="test2@example.com", 
            password="password123", 
            full_name="User 2"
        )
        
        # Create recruiter profiles
        self.recruiter = Recruiter.objects.create(user=self.user, bio="Test recruiter")
        self.recruiter2 = Recruiter.objects.create(user=self.user2, bio="Test recruiter 2")
        
        # Create sample languages
        self.lang_en = Language.objects.create(
            language_code="en",
            language_name="English",
            is_active=True
        )
        self.lang_vi = Language.objects.create(
            language_code="vi",
            language_name="Vietnamese",
            is_active=True
        )
        self.lang_ja = Language.objects.create(
            language_code="ja",
            language_name="Japanese",
            is_active=True
        )
        
        # Create sample recruiter_language
        self.recruiter_lang = RecruiterLanguage.objects.create(
            recruiter=self.recruiter,
            language=self.lang_en,
            proficiency_level='advanced',
            is_native=False
        )
        
        # Authenticate as user 1
        self.client.force_authenticate(user=self.user)
    
    # ========== LIST Tests ==========
    
    def test_list_languages_success(self):
        """Test GET /api/recruiters/:id/languages/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/languages/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['language_name'], "English")
    
    def test_list_languages_recruiter_not_found(self):
        """Test GET with non-existent recruiter returns 404"""
        url = '/api/recruiters/99999/languages/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== CREATE Tests ==========
    
    def test_create_language_success(self):
        """Test POST /api/recruiters/:id/languages/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/languages/'
        data = {
            "language_id": self.lang_vi.id,
            "proficiency_level": "fluent",
            "is_native": True
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['language_name'], "Vietnamese")
        self.assertEqual(RecruiterLanguage.objects.filter(recruiter=self.recruiter).count(), 2)
    
    def test_create_language_not_owner(self):
        """Test POST by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/languages/'
        data = {
            "language_id": self.lang_vi.id,
            "proficiency_level": "basic"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_language_duplicate(self):
        """Test POST with already added language returns 400"""
        url = f'/api/recruiters/{self.recruiter.id}/languages/'
        data = {
            "language_id": self.lang_en.id,  # Already added
            "proficiency_level": "native"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_language_unauthenticated(self):
        """Test POST without auth returns 401"""
        self.client.logout()
        url = f'/api/recruiters/{self.recruiter.id}/languages/'
        data = {"language_id": self.lang_vi.id, "proficiency_level": "basic"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== UPDATE Tests ==========
    
    def test_update_language_success(self):
        """Test PUT /api/recruiters/:id/languages/:langId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/languages/{self.recruiter_lang.id}/'
        data = {"proficiency_level": "native", "is_native": True}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify DB update
        self.recruiter_lang.refresh_from_db()
        self.assertEqual(self.recruiter_lang.proficiency_level, "native")
        self.assertTrue(self.recruiter_lang.is_native)
    
    def test_update_language_not_owner(self):
        """Test PUT by non-owner returns 403"""
        lang2 = RecruiterLanguage.objects.create(
            recruiter=self.recruiter2,
            language=self.lang_vi,
            proficiency_level='basic'
        )
        url = f'/api/recruiters/{self.recruiter2.id}/languages/{lang2.id}/'
        data = {"proficiency_level": "hacked"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_language_not_found(self):
        """Test PUT with non-existent language returns 404"""
        url = f'/api/recruiters/{self.recruiter.id}/languages/99999/'
        data = {"proficiency_level": "native"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== DELETE Tests ==========
    
    def test_delete_language_success(self):
        """Test DELETE /api/recruiters/:id/languages/:langId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/languages/{self.recruiter_lang.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RecruiterLanguage.objects.filter(recruiter=self.recruiter).count(), 0)
    
    def test_delete_language_not_owner(self):
        """Test DELETE by non-owner returns 403"""
        lang2 = RecruiterLanguage.objects.create(
            recruiter=self.recruiter2,
            language=self.lang_vi,
            proficiency_level='basic'
        )
        url = f'/api/recruiters/{self.recruiter2.id}/languages/{lang2.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
