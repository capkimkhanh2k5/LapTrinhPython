from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date
from apps.core.users.models import CustomUser
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.recruiter_projects.models import RecruiterProject


class RecruiterProjectViewTest(APITestCase):
    """Test cases for RecruiterProject APIs"""
    
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
        
        # Create sample project
        self.project = RecruiterProject.objects.create(
            recruiter=self.recruiter,
            project_name="Portfolio Website",
            description="Personal portfolio",
            project_url="https://example.com",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 1),
            technologies_used="Python, Django, React",
            display_order=0
        )
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
    
    # ========== LIST Tests ==========
    
    def test_list_projects_success(self):
        """Test GET /api/recruiters/:id/projects/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/projects/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['project_name'], "Portfolio Website")
    
    def test_list_projects_recruiter_not_found(self):
        """Test GET with non-existent recruiter returns 404"""
        url = '/api/recruiters/99999/projects/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== CREATE Tests ==========
    
    def test_create_project_success(self):
        """Test POST /api/recruiters/:id/projects/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/projects/'
        data = {
            "project_name": "E-commerce App",
            "description": "Online shopping platform",
            "project_url": "https://shop.example.com",
            "start_date": "2025-01-01",
            "is_ongoing": True,
            "technologies_used": "Node.js, React, MongoDB"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['project_name'], "E-commerce App")
        self.assertEqual(RecruiterProject.objects.filter(recruiter=self.recruiter).count(), 2)
    
    def test_create_project_not_owner(self):
        """Test POST by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/projects/'
        data = {"project_name": "Hacked project"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_project_invalid_dates(self):
        """Test POST with end_date < start_date returns 400"""
        url = f'/api/recruiters/{self.recruiter.id}/projects/'
        data = {
            "project_name": "Invalid project",
            "start_date": "2025-06-01",
            "end_date": "2025-01-01"  # End before start
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # ========== UPDATE Tests ==========
    
    def test_update_project_success(self):
        """Test PUT /api/recruiters/:id/projects/:pk/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/projects/{self.project.id}/'
        data = {
            "project_name": "Updated Portfolio",
            "is_ongoing": True
        }
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.project_name, "Updated Portfolio")
    
    def test_update_project_not_owner(self):
        """Test PUT by non-owner returns 403"""
        proj2 = RecruiterProject.objects.create(
            recruiter=self.recruiter2,
            project_name="Other project",
            display_order=0
        )
        url = f'/api/recruiters/{self.recruiter2.id}/projects/{proj2.id}/'
        data = {"project_name": "Hacked"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ========== DELETE Tests ==========
    
    def test_delete_project_success(self):
        """Test DELETE /api/recruiters/:id/projects/:pk/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/projects/{self.project.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RecruiterProject.objects.filter(recruiter=self.recruiter).count(), 0)
    
    def test_delete_project_not_owner(self):
        """Test DELETE by non-owner returns 403"""
        proj2 = RecruiterProject.objects.create(
            recruiter=self.recruiter2,
            project_name="Other project",
            display_order=0
        )
        url = f'/api/recruiters/{self.recruiter2.id}/projects/{proj2.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # ========== REORDER Tests ==========
    
    def test_reorder_projects_success(self):
        """Test PATCH /api/recruiters/:id/projects/reorder/ - success"""
        # Create another project
        proj2 = RecruiterProject.objects.create(
            recruiter=self.recruiter,
            project_name="Second project",
            display_order=1
        )
        
        url = f'/api/recruiters/{self.recruiter.id}/projects/reorder/'
        data = {
            "order": [
                {"id": proj2.id, "display_order": 0},
                {"id": self.project.id, "display_order": 1}
            ]
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify order changed
        self.project.refresh_from_db()
        proj2.refresh_from_db()
        self.assertEqual(proj2.display_order, 0)
        self.assertEqual(self.project.display_order, 1)
