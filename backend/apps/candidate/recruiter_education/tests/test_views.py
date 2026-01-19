from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from apps.core.users.models import CustomUser
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.recruiter_education.models import RecruiterEducation


class RecruiterEducationViewTest(APITestCase):
    """Test cases for Education APIs"""
    
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
        
        # Create sample education
        self.education = RecruiterEducation.objects.create(
            recruiter=self.recruiter,
            school_name="DUT",
            degree="Bachelor",
            field_of_study="IT",
            display_order=1
        )
    
    # ========== LIST Tests ==========
    
    def test_list_education_success(self):
        """Test GET /api/recruiters/:id/education/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/education/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['school_name'], "DUT")
    
    def test_list_education_recruiter_not_found(self):
        """Test GET with non-existent recruiter returns 404"""
        url = '/api/recruiters/99999/education/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== CREATE Tests ==========
    
    def test_create_education_success(self):
        """Test POST /api/recruiters/:id/education/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/education/'
        data = {
            "school_name": "MIT",
            "degree": "Master",
            "field_of_study": "Computer Science"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['school_name'], "MIT")
        self.assertEqual(RecruiterEducation.objects.count(), 2)
        # Check auto display_order
        self.assertEqual(response.data['display_order'], 2)
    
    def test_create_education_not_owner(self):
        """Test POST by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/education/'
        data = {"school_name": "Hacker School"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_education_invalid_dates(self):
        """Test POST with end_date < start_date returns 400"""
        url = f'/api/recruiters/{self.recruiter.id}/education/'
        data = {
            "school_name": "Test School",
            "start_date": "2024-01-01",
            "end_date": "2023-01-01"  # Before start_date
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_education_unauthenticated(self):
        """Test POST without auth returns 401"""
        self.client.logout()
        url = f'/api/recruiters/{self.recruiter.id}/education/'
        data = {"school_name": "Test"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== UPDATE Tests ==========
    
    def test_update_education_success(self):
        """Test PUT /api/recruiters/:id/education/:eduId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/education/{self.education.id}/'
        data = {"school_name": "Updated School", "degree": "PhD"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['school_name'], "Updated School")
        
        # Verify DB update
        self.education.refresh_from_db()
        self.assertEqual(self.education.school_name, "Updated School")
    
    def test_update_education_not_owner(self):
        """Test PUT by non-owner returns 403"""
        # Create education for recruiter2
        edu2 = RecruiterEducation.objects.create(
            recruiter=self.recruiter2,
            school_name="Other School"
        )
        url = f'/api/recruiters/{self.recruiter2.id}/education/{edu2.id}/'
        data = {"school_name": "Hacked"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_education_not_found(self):
        """Test PUT with non-existent education returns 404"""
        url = f'/api/recruiters/{self.recruiter.id}/education/99999/'
        data = {"school_name": "Test"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== DELETE Tests ==========
    
    def test_delete_education_success(self):
        """Test DELETE /api/recruiters/:id/education/:eduId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/education/{self.education.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RecruiterEducation.objects.count(), 0)
    
    def test_delete_education_not_owner(self):
        """Test DELETE by non-owner returns 403"""
        edu2 = RecruiterEducation.objects.create(
            recruiter=self.recruiter2,
            school_name="Other School"
        )
        url = f'/api/recruiters/{self.recruiter2.id}/education/{edu2.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(RecruiterEducation.objects.count(), 2)
    
    # ========== REORDER Tests ==========
    
    def test_reorder_education_success(self):
        """Test PATCH /api/recruiters/:id/education/reorder/ - success"""
        # Create more education records
        edu2 = RecruiterEducation.objects.create(
            recruiter=self.recruiter,
            school_name="School 2",
            display_order=2
        )
        edu3 = RecruiterEducation.objects.create(
            recruiter=self.recruiter,
            school_name="School 3",
            display_order=3
        )
        
        url = f'/api/recruiters/{self.recruiter.id}/education/reorder/'
        data = {
            "order": [
                {"id": edu3.id, "display_order": 1},
                {"id": edu2.id, "display_order": 2},
                {"id": self.education.id, "display_order": 3}
            ]
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify reorder
        edu3.refresh_from_db()
        self.assertEqual(edu3.display_order, 1)
    
    def test_reorder_education_not_owner(self):
        """Test PATCH reorder by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/education/reorder/'
        data = {"order": []}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_reorder_education_invalid_id(self):
        """Test PATCH reorder with id not belonging to recruiter returns 400"""
        # Create education for recruiter2
        edu_other = RecruiterEducation.objects.create(
            recruiter=self.recruiter2,
            school_name="Other School"
        )
        
        url = f'/api/recruiters/{self.recruiter.id}/education/reorder/'
        data = {
            "order": [
                {"id": edu_other.id, "display_order": 1}  # Wrong recruiter
            ]
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
