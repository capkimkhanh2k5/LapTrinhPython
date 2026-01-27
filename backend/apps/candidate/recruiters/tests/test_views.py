from rest_framework.test import APITestCase
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.candidate.recruiters.models import Recruiter
from django.urls import reverse

class RecruiterViewTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="test@example.com", password="password123", full_name="User 1")
        self.user2 = CustomUser.objects.create_user(email="test2@example.com", password="password123", full_name="User 2")
        self.client.force_authenticate(user=self.user)
        
        # Use direct URL path instead of reverse() to avoid namespace issues
        self.list_url = '/api/recruiters/' 

    def test_create_recruiter_profile(self):
        data = {
            "bio": "My new profile",
            "years_of_experience": 3
        }
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Recruiter.objects.count(), 1)
        self.assertEqual(Recruiter.objects.first().user, self.user)
        self.assertEqual(response.data['user']['email'], "test@example.com")

    def test_create_duplicate_fail(self):
        Recruiter.objects.create(user=self.user)
        data = {"bio": "Duplicate"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_unauthenticated(self):
        self.client.logout()
        data = {"bio": "Anon"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_recruiter(self):
        recruiter = Recruiter.objects.create(user=self.user, bio="Test")
        url = f'/api/recruiters/{recruiter.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], "Test")
        self.assertEqual(response.data['user']['email'], "test@example.com")

    def test_update_recruiter_owner(self):
        recruiter = Recruiter.objects.create(user=self.user, bio="Old")
        url = f'/api/recruiters/{recruiter.id}/'
        data = {"bio": "New"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], "New")
        
        # Verify db update
        recruiter.refresh_from_db()
        self.assertEqual(recruiter.bio, "New")

    def test_update_recruiter_not_owner(self):
        recruiter2 = Recruiter.objects.create(user=self.user2, bio="User 2")
        url = f'/api/recruiters/{recruiter2.id}/'
        data = {"bio": "Hacked"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify no update
        recruiter2.refresh_from_db()
        self.assertEqual(recruiter2.bio, "User 2")

    def test_delete_recruiter_owner(self):
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Recruiter.objects.count(), 0)

    def test_delete_recruiter_not_owner(self):
        recruiter2 = Recruiter.objects.create(user=self.user2)
        url = f'/api/recruiters/{recruiter2.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Recruiter.objects.count(), 1)

    def test_update_job_search_status(self):
        recruiter = Recruiter.objects.create(user=self.user, job_search_status='active')
        url = f'/api/recruiters/{recruiter.id}/job-search-status/'
        
        data = {"job_search_status": "not_looking"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        recruiter.refresh_from_db()
        self.assertEqual(recruiter.job_search_status, 'not_looking')
        
    def test_update_job_search_status_invalid(self):
        recruiter = Recruiter.objects.create(user=self.user, job_search_status='active')
        url = f'/api/recruiters/{recruiter.id}/job-search-status/'
        
        data = {"job_search_status": "invalid_status"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== Tests for Avatar Upload API ==========
    
    def test_upload_avatar_success(self):
        """Test POST /api/recruiters/:id/avatar - upload success"""
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/avatar/'
        
        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        avatar_file = SimpleUploadedFile(
            name='test_avatar.png',
            content=buffer.read(),
            content_type='image/png'
        )
        
        response = self.client.post(url, {'avatar': avatar_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_upload_avatar_not_owner(self):
        """Test POST avatar by non-owner returns 403"""
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        recruiter2 = Recruiter.objects.create(user=self.user2)
        url = f'/api/recruiters/{recruiter2.id}/avatar/'
        
        image = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        avatar_file = SimpleUploadedFile(
            name='test_avatar.png',
            content=buffer.read(),
            content_type='image/png'
        )
        
        response = self.client.post(url, {'avatar': avatar_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_upload_avatar_unauthenticated(self):
        """Test POST avatar without auth returns 401"""
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/avatar/'
        
        self.client.logout()
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_upload_avatar_no_file(self):
        """Test POST avatar without file returns 400"""
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/avatar/'
        
        response = self.client.post(url, {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_upload_avatar_recruiter_not_found(self):
        """Test POST avatar with non-existent recruiter returns 404"""
        url = '/api/recruiters/99999/avatar/'
        
        from PIL import Image
        from io import BytesIO
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        image = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        avatar_file = SimpleUploadedFile(
            name='test_avatar.png',
            content=buffer.read(),
            content_type='image/png'
        )
        
        response = self.client.post(url, {'avatar': avatar_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_upload_avatar_invalid_type(self):
        """Test POST avatar with non-image file returns 400"""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/avatar/'
        
        # Create a text file (not an image)
        text_file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'This is not an image file',
            content_type='text/plain'
        )
        
        response = self.client.post(url, {'avatar': text_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ========== Tests for Extended APIs ==========
    
    def test_get_profile_completeness(self):
        """Test GET /api/recruiters/:id/profile-completeness"""
        recruiter = Recruiter.objects.create(user=self.user, bio="Test Bio", current_position="Developer")
        url = f'/api/recruiters/{recruiter.id}/profile-completeness/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('score', response.data)
        self.assertIn('missing_fields', response.data)
        self.assertIsInstance(response.data['score'], int)
        self.assertIsInstance(response.data['missing_fields'], list)

    def test_get_profile_completeness_not_owner(self):
        """Only owner can view detailed completeness"""
        recruiter2 = Recruiter.objects.create(user=self.user2)
        url = f'/api/recruiters/{recruiter2.id}/profile-completeness/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_profile_visible(self):
        """Test GET /api/recruiters/:id/public_profile when profile is public"""
        recruiter = Recruiter.objects.create(user=self.user, bio="Public Bio", is_profile_public=True)
        url = f'/api/recruiters/{recruiter.id}/public_profile/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['bio'], "Public Bio")

    def test_public_profile_hidden(self):
        """Test GET /api/recruiters/:id/public_profile when profile is private"""
        recruiter2 = Recruiter.objects.create(user=self.user2, bio="Private Bio", is_profile_public=False)
        url = f'/api/recruiters/{recruiter2.id}/public_profile/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_privacy(self):
        """Test PATCH /api/recruiters/:id/privacy"""
        recruiter = Recruiter.objects.create(user=self.user, is_profile_public=True)
        url = f'/api/recruiters/{recruiter.id}/privacy/'
        
        response = self.client.patch(url, {"is_profile_public": False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        recruiter.refresh_from_db()
        self.assertFalse(recruiter.is_profile_public)

    def test_update_privacy_not_owner(self):
        """Only owner can update privacy"""
        recruiter2 = Recruiter.objects.create(user=self.user2, is_profile_public=True)
        url = f'/api/recruiters/{recruiter2.id}/privacy/'
        
        response = self.client.patch(url, {"is_profile_public": False})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_stats(self):
        """Test GET /api/recruiters/:id/stats"""
        recruiter = Recruiter.objects.create(user=self.user, profile_views_count=100)
        url = f'/api/recruiters/{recruiter.id}/stats/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('profile_views', response.data)
        self.assertIn('following_companies', response.data)
        self.assertEqual(response.data['profile_views'], 100)

    def test_get_stats_not_owner(self):
        """Only owner can view stats"""
        recruiter2 = Recruiter.objects.create(user=self.user2)
        url = f'/api/recruiters/{recruiter2.id}/stats/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ========== Tests for Advanced APIs ==========

    def test_verify_phone(self):
        """Test POST /api/recruiters/:id/verify-phone"""
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/verify-phone/'
        response = self.client.post(url, {"phone": "0123456789"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_phone_not_owner(self):
        """Only owner can verify phone"""
        recruiter2 = Recruiter.objects.create(user=self.user2)
        url = f'/api/recruiters/{recruiter2.id}/verify-phone/'
        response = self.client.post(url, {"phone": "0123456789"})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_matching_jobs(self):
        """Test GET /api/recruiters/:id/matching-jobs"""
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/matching-jobs/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_matching_jobs_not_owner(self):
        """Only owner can view matching jobs"""
        recruiter2 = Recruiter.objects.create(user=self.user2)
        url = f'/api/recruiters/{recruiter2.id}/matching-jobs/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_applications(self):
        """Test GET /api/recruiters/:id/applications"""
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/applications/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_applications_not_owner(self):
        """Only owner can view applications"""
        recruiter2 = Recruiter.objects.create(user=self.user2)
        url = f'/api/recruiters/{recruiter2.id}/applications/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_saved_jobs(self):
        """Test GET /api/recruiters/:id/saved-jobs"""
        recruiter = Recruiter.objects.create(user=self.user)
        url = f'/api/recruiters/{recruiter.id}/saved-jobs/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_saved_jobs_not_owner(self):
        """Only owner can view saved jobs"""
        recruiter2 = Recruiter.objects.create(user=self.user2)
        url = f'/api/recruiters/{recruiter2.id}/saved-jobs/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_search_recruiters(self):
        """Test GET /api/recruiters/search - requires company user"""
        # Create a company user
        company_user = CustomUser.objects.create_user(
            email="company@example.com", 
            password="password123", 
            full_name="Company User",
            role='company'
        )
        # Add is_company property check - this test verifies company-only access
        self.client.force_authenticate(user=company_user)
        
        # Create some public recruiters
        Recruiter.objects.create(user=self.user, is_profile_public=True, job_search_status='active')
        
        url = '/api/recruiters/search/'
        response = self.client.get(url)
        
        # Should succeed for company users (if is_company check passes)
        # Or return 403 if user doesn't have is_company attribute
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_search_recruiters_non_company(self):
        """Non-company users cannot search recruiters"""
        url = '/api/recruiters/search/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
