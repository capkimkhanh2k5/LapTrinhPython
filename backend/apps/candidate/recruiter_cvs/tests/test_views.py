from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.recruiter_cvs.models import RecruiterCV
from apps.candidate.cv_templates.models import CVTemplate
from apps.candidate.cv_template_categories.models import CVTemplateCategory


class RecruiterCVViewSetTests(TestCase):
    """Tests cho Recruiter CVs API"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create users
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )
        self.other_user = CustomUser.objects.create_user(
            email='other@example.com',
            password='testpass123',
            full_name='Other User'
        )
        
        # Create recruiter (job seeker)
        self.recruiter = Recruiter.objects.create(
            user=self.user,
            current_position='Software Engineer'
        )
        
        # Create category and template
        self.category = CVTemplateCategory.objects.create(
            name='Modern',
            slug='modern'
        )
        self.template = CVTemplate.objects.create(
            name='Modern Template',
            category=self.category
        )
        
        # Create CV
        self.cv = RecruiterCV.objects.create(
            recruiter=self.recruiter,
            template=self.template,
            cv_name='My Main CV',
            cv_data={'personal': {'name': 'Test User'}},
            is_default=True,
            is_public=True
        )
    
    def test_list_cvs(self):
        """Test GET /api/recruiters/:id/cvs/ - List CVs"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/cvs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_list_cvs_forbidden(self):
        """Test GET /api/recruiters/:id/cvs/ - Other user cannot access"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/cvs/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_cv(self):
        """Test POST /api/recruiters/:id/cvs/ - Create CV"""
        self.client.force_authenticate(user=self.user)
        data = {
            'cv_name': 'New CV',
            'template_id': self.template.id,
            'cv_data': {'personal': {'name': 'Test'}},
            'is_public': True
        }
        response = self.client.post(
            f'/api/recruiters/{self.recruiter.id}/cvs/', 
            data, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_retrieve_cv(self):
        """Test GET /api/recruiters/:id/cvs/:cvId/ - Get CV detail"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cv_name'], 'My Main CV')
    
    def test_update_cv(self):
        """Test PUT /api/recruiters/:id/cvs/:cvId/ - Update CV"""
        self.client.force_authenticate(user=self.user)
        data = {
            'cv_name': 'Updated CV Name',
            'cv_data': {'personal': {'name': 'Updated'}},
            'is_public': False
        }
        response = self.client.put(
            f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/', 
            data, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cv_name'], 'Updated CV Name')
    
    def test_delete_cv(self):
        """Test DELETE /api/recruiters/:id/cvs/:cvId/ - Delete CV"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_set_default_cv(self):
        """Test PATCH /api/recruiters/:id/cvs/:cvId/default/ - Set default"""
        # Create another CV
        cv2 = RecruiterCV.objects.create(
            recruiter=self.recruiter,
            cv_name='Second CV',
            cv_data={},
            is_default=False
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(f'/api/recruiters/{self.recruiter.id}/cvs/{cv2.id}/default/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        cv2.refresh_from_db()
        self.assertTrue(cv2.is_default)
    
    def test_set_privacy(self):
        """Test PATCH /api/recruiters/:id/cvs/:cvId/privacy/ - Set privacy"""
        self.client.force_authenticate(user=self.user)
        data = {'is_public': False}
        response = self.client.patch(
            f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/privacy/', 
            data, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.cv.refresh_from_db()
        self.assertFalse(self.cv.is_public)
    
    def test_download_cv(self):
        """Test POST /api/recruiters/:id/cvs/:cvId/download/ - Download CV"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('download_url', response.data)
    
    def test_preview_cv(self):
        """Test POST /api/recruiters/:id/cvs/:cvId/preview/ - Preview CV"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/preview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # API returns html_content for preview rendering
        self.assertIn('html_content', response.data)
    
    def test_generate_cv(self):
        """Test POST /api/recruiters/:id/cvs/generate/ - Auto-generate CV"""
        self.client.force_authenticate(user=self.user)
        data = {'template_id': self.template.id}
        response = self.client.post(
            f'/api/recruiters/{self.recruiter.id}/cvs/generate/', 
            data, 
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('cv_data', response.data)
    
    # ========== Tests bổ sung ==========
    
    def test_list_cvs_unauthenticated(self):
        """Test GET /api/recruiters/:id/cvs/ - Unauthenticated → 401"""
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/cvs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_cv_unauthenticated(self):
        """Test POST /api/recruiters/:id/cvs/ - Unauthenticated → 401"""
        data = {'cv_name': 'Test', 'cv_data': {}}
        response = self.client.post(f'/api/recruiters/{self.recruiter.id}/cvs/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_retrieve_cv_not_found(self):
        """Test GET /api/recruiters/:id/cvs/:cvId/ - CV not found → 404"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/cvs/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_cv_forbidden(self):
        """Test PUT /api/recruiters/:id/cvs/:cvId/ - Other user → 403"""
        self.client.force_authenticate(user=self.other_user)
        data = {'cv_name': 'Hacked', 'cv_data': {}}
        response = self.client.put(
            f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/', 
            data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_cv_forbidden(self):
        """Test DELETE /api/recruiters/:id/cvs/:cvId/ - Other user → 403"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_download_cv_forbidden(self):
        """Test POST /api/recruiters/:id/cvs/:cvId/download/ - Other user → 403"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(f'/api/recruiters/{self.recruiter.id}/cvs/{self.cv.id}/download/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

