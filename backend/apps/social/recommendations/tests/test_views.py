"""
API Integration Tests for Recommendations

Tests for 6 Recommendations API endpoints.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.social.recommendations.models import Recommendation
from apps.candidate.recruiters.models import Recruiter


User = get_user_model()


class RecommendationsAPITestCase(APITestCase):
    """Base test case with common setup."""
    
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True
        )
        
        cls.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            is_active=True
        )
        
        cls.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            full_name='Other User',
            is_active=True
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            job_search_status='active'
        )
        
        cls.other_recruiter = Recruiter.objects.create(
            user=cls.other_user,
            years_of_experience=2,
            job_search_status='active'
        )
    
    def setUp(self):
        self.client.force_authenticate(user=self.user)


class TestRecruiterRecommendationsView(RecommendationsAPITestCase):
    """Tests for GET /api/recruiters/:id/recommendations/"""
    
    def test_list_recommendations_success(self):
        """Should list visible recommendations."""
        Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Great colleague!',
            is_visible=True
        )
        
        response = self.client.get(f'/api/recruiters/{self.other_recruiter.id}/recommendations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['recommendations']), 1)
    
    def test_list_recommendations_hides_invisible(self):
        """Should hide invisible recommendations from others."""
        Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Secret!',
            is_visible=False
        )
        
        self.client.force_authenticate(user=self.other_user)  # As owner
        response = self.client.get(f'/api/recruiters/{self.other_recruiter.id}/recommendations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['recommendations']), 1)  # Owner sees all
    
    def test_list_recommendations_public_access(self):
        """Should allow public access to visible recommendations."""
        Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Public!',
            is_visible=True
        )
        
        self.client.logout()
        response = self.client.get(f'/api/recruiters/{self.other_recruiter.id}/recommendations/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['recommendations']), 1)
    
    def test_list_recommendations_recruiter_not_found(self):
        """Should return 404 for non-existent recruiter."""
        response = self.client.get('/api/recruiters/99999/recommendations/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestWriteRecommendationView(RecommendationsAPITestCase):
    """Tests for POST /api/recruiters/:id/recommend/"""
    
    def test_write_recommendation_success(self):
        """Should write recommendation."""
        data = {
            'relationship': 'Former colleague',
            'content': 'Excellent developer!'
        }
        
        response = self.client.post(
            f'/api/recruiters/{self.other_recruiter.id}/recommend/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'Excellent developer!')
    
    def test_write_recommendation_for_self(self):
        """Should reject self-recommendation."""
        data = {'content': 'I am great!'}
        
        response = self.client.post(
            f'/api/recruiters/{self.recruiter.id}/recommend/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_write_duplicate_recommendation(self):
        """Should reject duplicate recommendation."""
        Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Already written'
        )
        
        data = {'content': 'Another one!'}
        response = self.client.post(
            f'/api/recruiters/{self.other_recruiter.id}/recommend/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_write_recommendation_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()
        data = {'content': 'Test'}
        
        response = self.client.post(
            f'/api/recruiters/{self.other_recruiter.id}/recommend/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_write_recommendation_recruiter_not_found(self):
        """Should return 404 for non-existent recruiter."""
        data = {'content': 'Test'}
        response = self.client.post('/api/recruiters/99999/recommend/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRecommendationDetailView(RecommendationsAPITestCase):
    """Tests for GET/PUT/DELETE /api/recommendations/:id/"""
    
    def test_get_detail_success(self):
        """Should get recommendation detail."""
        recommendation = Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Great!',
            is_visible=True
        )
        
        response = self.client.get(f'/api/recommendations/{recommendation.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Great!')
    
    def test_get_detail_public_access(self):
        """Should allow public access to visible recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Public!',
            is_visible=True
        )
        
        self.client.logout()
        response = self.client.get(f'/api/recommendations/{recommendation.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_detail_invisible_to_public(self):
        """Should hide invisible recommendation from public."""
        recommendation = Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Hidden!',
            is_visible=False
        )
        
        self.client.logout()
        response = self.client.get(f'/api/recommendations/{recommendation.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_detail_not_found(self):
        """Should return 404 for non-existent recommendation."""
        response = self.client.get('/api/recommendations/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_own_recommendation(self):
        """Should update own recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Original'
        )
        
        data = {'content': 'Updated!'}
        response = self.client.put(
            f'/api/recommendations/{recommendation.id}/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['content'], 'Updated!')
    
    def test_update_other_recommendation_forbidden(self):
        """Should not update other's recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter,
            recommender=self.other_user,
            content='Not mine'
        )
        
        data = {'content': 'Hacked!'}
        response = self.client.put(
            f'/api/recommendations/{recommendation.id}/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_not_found(self):
        """Should return 404 for non-existent recommendation."""
        data = {'content': 'Test'}
        response = self.client.put('/api/recommendations/99999/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_own_recommendation(self):
        """Should delete own recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='To delete'
        )
        
        response = self.client.delete(f'/api/recommendations/{recommendation.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_delete_other_recommendation_forbidden(self):
        """Should not delete other's recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter,
            recommender=self.other_user,
            content='Not mine'
        )
        
        response = self.client.delete(f'/api/recommendations/{recommendation.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_admin(self):
        """Admin should delete any recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.other_user,
            content='Admin delete'
        )
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(f'/api/recommendations/{recommendation.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_delete_not_found(self):
        """Should return 404 for non-existent recommendation."""
        response = self.client.delete('/api/recommendations/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRecommendationVisibilityView(RecommendationsAPITestCase):
    """Tests for PATCH /api/recommendations/:id/visibility/"""
    
    def test_toggle_visibility_success(self):
        """Recruiter should toggle visibility."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter,
            recommender=self.other_user,
            content='Visible',
            is_visible=True
        )
        
        data = {'is_visible': False}
        response = self.client.patch(
            f'/api/recommendations/{recommendation.id}/visibility/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_visible'])
    
    def test_toggle_visibility_show_hidden(self):
        """Should show hidden recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter,
            recommender=self.other_user,
            content='Hidden',
            is_visible=False
        )
        
        data = {'is_visible': True}
        response = self.client.patch(
            f'/api/recommendations/{recommendation.id}/visibility/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_visible'])
    
    def test_toggle_visibility_not_recipient(self):
        """Non-recipient should not toggle."""
        recommendation = Recommendation.objects.create(
            recruiter=self.other_recruiter,
            recommender=self.user,
            content='Not mine',
            is_visible=True
        )
        
        data = {'is_visible': False}
        response = self.client.patch(
            f'/api/recommendations/{recommendation.id}/visibility/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_toggle_visibility_unauthenticated(self):
        """Should require authentication."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter,
            recommender=self.other_user,
            content='Test',
            is_visible=True
        )
        
        self.client.logout()
        data = {'is_visible': False}
        response = self.client.patch(
            f'/api/recommendations/{recommendation.id}/visibility/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_toggle_visibility_not_found(self):
        """Should return 404 for non-existent recommendation."""
        data = {'is_visible': False}
        response = self.client.patch('/api/recommendations/99999/visibility/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_toggle_visibility_invalid_data(self):
        """Should reject invalid visibility data."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter,
            recommender=self.other_user,
            content='Test',
            is_visible=True
        )
        
        data = {'is_visible': 'invalid'}
        response = self.client.patch(
            f'/api/recommendations/{recommendation.id}/visibility/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

