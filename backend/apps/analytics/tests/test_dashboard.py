from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.company.companies.models import Company
from apps.recruitment.jobs.models import Job

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # 1. Company Owner
        self.owner = CustomUser.objects.create(email='owner@test.com')
        self.company = Company.objects.create(user=self.owner, company_name='Owner Co', slug='owner-co')
        
        # 2. Freelancer / No Company
        self.freelancer = CustomUser.objects.create(email='free@test.com')

        # Dummy Data
        Job.objects.create(company=self.company, title="J1", status='published', created_by=self.owner)

    def test_company_stats_access_owner(self):
        """Company Owner should access stats"""
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/dashboard/stats/company/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('jobs', response.data)
        self.assertEqual(response.data['jobs']['active'], 1)

    def test_company_stats_no_access(self):
        """User without company should get 403"""
        self.client.force_authenticate(user=self.freelancer)
        response = self.client.get('/api/dashboard/stats/company/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated(self):
        """Guest should be blocked"""
        response = self.client.get('/api/dashboard/stats/company/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
