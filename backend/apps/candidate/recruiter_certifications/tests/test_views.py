from rest_framework.test import APITestCase
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.recruiter_certifications.models import RecruiterCertification


class RecruiterCertificationViewTest(APITestCase):
    """Test cases for Certifications APIs"""
    
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
        
        # Create sample certification
        self.certification = RecruiterCertification.objects.create(
            recruiter=self.recruiter,
            certification_name="AWS Certified",
            issuing_organization="Amazon",
            issue_date="2023-01-01",
            display_order=1
        )
    
    # ========== LIST Tests ==========
    
    def test_list_certifications_success(self):
        """Test GET /api/recruiters/:id/certifications/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/certifications/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['certification_name'], "AWS Certified")
    
    def test_list_certifications_recruiter_not_found(self):
        """Test GET with non-existent recruiter returns 404"""
        url = '/api/recruiters/99999/certifications/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== CREATE Tests ==========
    
    def test_create_certification_success(self):
        """Test POST /api/recruiters/:id/certifications/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/certifications/'
        data = {
            "certification_name": "Google Cloud Professional",
            "issuing_organization": "Google",
            "issue_date": "2024-01-01"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['certification_name'], "Google Cloud Professional")
        self.assertEqual(RecruiterCertification.objects.count(), 2)
        # Check auto display_order
        self.assertEqual(response.data['display_order'], 2)
    
    def test_create_certification_not_owner(self):
        """Test POST by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/certifications/'
        data = {
            "certification_name": "Hacker Cert",
            "issuing_organization": "Hacker Corp"
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_certification_invalid_dates(self):
        """Test POST with expiry_date < issue_date returns 400"""
        url = f'/api/recruiters/{self.recruiter.id}/certifications/'
        data = {
            "certification_name": "Test Cert",
            "issue_date": "2024-01-01",
            "expiry_date": "2023-01-01"  # Before issue_date
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_certification_unauthenticated(self):
        """Test POST without auth returns 401"""
        self.client.logout()
        url = f'/api/recruiters/{self.recruiter.id}/certifications/'
        data = {"certification_name": "Test"}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========== UPDATE Tests ==========
    
    def test_update_certification_success(self):
        """Test PUT /api/recruiters/:id/certifications/:certId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/certifications/{self.certification.id}/'
        data = {"certification_name": "AWS Solutions Architect"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['certification_name'], "AWS Solutions Architect")
        
        # Verify DB update
        self.certification.refresh_from_db()
        self.assertEqual(self.certification.certification_name, "AWS Solutions Architect")
    
    def test_update_certification_not_owner(self):
        """Test PUT by non-owner returns 403"""
        cert2 = RecruiterCertification.objects.create(
            recruiter=self.recruiter2,
            certification_name="Other Cert",
            display_order=1
        )
        url = f'/api/recruiters/{self.recruiter2.id}/certifications/{cert2.id}/'
        data = {"certification_name": "Hacked"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_certification_not_found(self):
        """Test PUT with non-existent certification returns 404"""
        url = f'/api/recruiters/{self.recruiter.id}/certifications/99999/'
        data = {"certification_name": "Test"}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== DELETE Tests ==========
    
    def test_delete_certification_success(self):
        """Test DELETE /api/recruiters/:id/certifications/:certId/ - success"""
        url = f'/api/recruiters/{self.recruiter.id}/certifications/{self.certification.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(RecruiterCertification.objects.count(), 0)
    
    def test_delete_certification_not_owner(self):
        """Test DELETE by non-owner returns 403"""
        cert2 = RecruiterCertification.objects.create(
            recruiter=self.recruiter2,
            certification_name="Other Cert",
            display_order=1
        )
        url = f'/api/recruiters/{self.recruiter2.id}/certifications/{cert2.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(RecruiterCertification.objects.count(), 2)
    
    # ========== REORDER Tests ==========
    
    def test_reorder_certifications_success(self):
        """Test PATCH /api/recruiters/:id/certifications/reorder/ - success"""
        # Create more certifications
        cert2 = RecruiterCertification.objects.create(
            recruiter=self.recruiter,
            certification_name="Cert 2",
            display_order=2
        )
        cert3 = RecruiterCertification.objects.create(
            recruiter=self.recruiter,
            certification_name="Cert 3",
            display_order=3
        )
        
        url = f'/api/recruiters/{self.recruiter.id}/certifications/reorder/'
        data = {
            "order": [
                {"id": cert3.id, "display_order": 1},
                {"id": cert2.id, "display_order": 2},
                {"id": self.certification.id, "display_order": 3}
            ]
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify reorder
        cert3.refresh_from_db()
        self.assertEqual(cert3.display_order, 1)
    
    def test_reorder_certifications_not_owner(self):
        """Test PATCH reorder by non-owner returns 403"""
        url = f'/api/recruiters/{self.recruiter2.id}/certifications/reorder/'
        data = {"order": []}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_reorder_certifications_invalid_id(self):
        """Test PATCH reorder with id not belonging to recruiter returns 400"""
        cert_other = RecruiterCertification.objects.create(
            recruiter=self.recruiter2,
            certification_name="Other Cert",
            display_order=1
        )
        
        url = f'/api/recruiters/{self.recruiter.id}/certifications/reorder/'
        data = {
            "order": [
                {"id": cert_other.id, "display_order": 1}
            ]
        }
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
