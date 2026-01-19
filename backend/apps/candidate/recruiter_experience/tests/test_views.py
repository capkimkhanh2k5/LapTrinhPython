from rest_framework.test import APITestCase
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.recruiter_experience.models import RecruiterExperience


class RecruiterExperienceViewTest(APITestCase):
    """Test cases for Experience APIs"""
    
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
        
        # Authenticate as user 1
        self.client.force_authenticate(user=self.user)
        
        # Create sample experience
        self.experience = RecruiterExperience.objects.create(
            recruiter=self.recruiter,
            company_name="Google",
            job_title="Software Engineer",
            start_date="2020-01-01",
            display_order=1
        )
    
    # ========== LIST Tests ==========
    
    def test_list_experience_success(self):
        """Test GET /api/recruiters/:id/experience/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/experience/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['company_name'], "Google")
    
    def test_list_experience_recruiter_not_found(self):
        """Test GET with non-existent recruiter returns 404"""
        url = '/api/recruiters/99999/experience/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== CREATE Tests ==========
    
    def test_create_experience_success(self):
        """Test POST /api/recruiters/:id/experience/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/experience/'
        data = {
            "company_name": "Microsoft",
            "job_title": "Senior Engineer",
            "start_date": "2023-01-01"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], "Microsoft")
        self.assertEqual(RecruiterExperience.objects.count(), 2)
        # Check auto display_order
        self.assertEqual(response.data['display_order'], 2)
    
    def test_create_experience_not_owner(self):
        """Test POST by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/experience/'
        data = {
            "company_name": "Hacker Corp", 
            "job_title": "Hacker",
            "start_date": "2023-01-01"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_experience_invalid_dates(self):
        """Test POST with end_date < start_date returns 400"""
        url = f'/api/recruiters/{self.recruiter.id}/experience/'
        data = {
            "company_name": "Test Company",
            "job_title": "Test",
            "start_date": "2024-01-01",
            "end_date": "2023-01-01"  # Before start_date
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_experience_unauthenticated(self):
        """Test POST without auth returns 401"""
        self.client.logout()
        url = f'/api/recruiters/{self.recruiter.id}/experience/'
        data = {
            "company_name": "Test",
            "job_title": "Test",
            "start_date": "2023-01-01"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== UPDATE Tests ==========
    
    def test_update_experience_success(self):
        """Test PUT /api/recruiters/:id/experience/:expId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/experience/{self.experience.id}/'
        data = {"company_name": "Updated Company", "job_title": "CTO"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], "Updated Company")
        
        # Verify DB update
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.company_name, "Updated Company")
    
    def test_update_experience_not_owner(self):
        """Test PUT by non-owner returns 403"""
        exp2 = RecruiterExperience.objects.create(
            recruiter=self.recruiter2,
            company_name="Other Company",
            job_title="Other",
            start_date="2020-01-01"
        )
        url = f'/api/recruiters/{self.recruiter2.id}/experience/{exp2.id}/'
        data = {"company_name": "Hacked"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_experience_not_found(self):
        """Test PUT with non-existent experience returns 404"""
        url = f'/api/recruiters/{self.recruiter.id}/experience/99999/'
        data = {"company_name": "Test"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== DELETE Tests ==========
    
    def test_delete_experience_success(self):
        """Test DELETE /api/recruiters/:id/experience/:expId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/experience/{self.experience.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RecruiterExperience.objects.count(), 0)
    
    def test_delete_experience_not_owner(self):
        """Test DELETE by non-owner returns 403"""
        exp2 = RecruiterExperience.objects.create(
            recruiter=self.recruiter2,
            company_name="Other Company",
            job_title="Other",
            start_date="2020-01-01"
        )
        url = f'/api/recruiters/{self.recruiter2.id}/experience/{exp2.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(RecruiterExperience.objects.count(), 2)
    
    # ========== REORDER Tests ==========
    
    def test_reorder_experience_success(self):
        """Test PATCH /api/recruiters/:id/experience/reorder/ - success"""
        # Create more experience records
        exp2 = RecruiterExperience.objects.create(
            recruiter=self.recruiter,
            company_name="Company 2",
            job_title="Job 2",
            start_date="2021-01-01",
            display_order=2
        )
        exp3 = RecruiterExperience.objects.create(
            recruiter=self.recruiter,
            company_name="Company 3",
            job_title="Job 3",
            start_date="2022-01-01",
            display_order=3
        )
        
        url = f'/api/recruiters/{self.recruiter.id}/experience/reorder/'
        data = {
            "order": [
                {"id": exp3.id, "display_order": 1},
                {"id": exp2.id, "display_order": 2},
                {"id": self.experience.id, "display_order": 3}
            ]
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify reorder
        exp3.refresh_from_db()
        self.assertEqual(exp3.display_order, 1)
    
    def test_reorder_experience_not_owner(self):
        """Test PATCH reorder by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/experience/reorder/'
        data = {"order": []}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_reorder_experience_invalid_id(self):
        """Test PATCH reorder with id not belonging to recruiter returns 400"""
        exp_other = RecruiterExperience.objects.create(
            recruiter=self.recruiter2,
            company_name="Other Company",
            job_title="Other",
            start_date="2020-01-01"
        )
        
        url = f'/api/recruiters/{self.recruiter.id}/experience/reorder/'
        data = {
            "order": [
                {"id": exp_other.id, "display_order": 1}
            ]
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
