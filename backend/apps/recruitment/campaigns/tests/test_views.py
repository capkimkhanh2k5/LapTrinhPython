from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.recruitment.campaigns.models import Campaign
from apps.recruitment.jobs.models import Job
from apps.company.companies.models import Company
from apps.recruitment.job_categories.models import JobCategory
from apps.geography.provinces.models import Province
from apps.geography.addresses.models import Address

User = get_user_model()

class TestCampaignViewSet(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='company@test.com',
            password='password123',
            full_name='Test Company',
            role='company'
        )
        self.company = Company.objects.create(
            user=self.user,
            company_name="Test Company",
            slug="test-company"
        )
        self.category = JobCategory.objects.create(name="IT Software", slug="it-software")
        self.province = Province.objects.create(province_name="Ho Chi Minh", province_code="79")
        self.address_hcm = Address.objects.create(address_line="123 Street", province=self.province)

        # Authenticate client for tests requiring auth
        self.client.force_authenticate(user=self.user)

    def test_create_campaign(self):
        url = '/api/campaigns/'
        data = {
            'title': 'Test Campaign',
            'slug': 'test-campaign',
            'status': 'active',
            'budget': 1000
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Campaign')
        self.assertEqual(Campaign.objects.count(), 1)

    def test_create_campaign_invalid_dates(self):
        url = '/api/campaigns/'
        data = {
            'title': 'Invalid Date Campaign',
            'slug': 'invalid-date-campaign',
            'start_date': (timezone.now() + timedelta(days=5)).date(),
            'end_date': (timezone.now() + timedelta(days=1)).date(), # End before start
            'budget': 1000
        }
        # Expecting 400 if validation exists, otherwise 201 if no validation. 
        # Refactoring note: keeping original assertion assumption.
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_campaign_negative_budget(self):
        url = '/api/campaigns/'
        data = {
            'title': 'Negative Budget',
            'slug': 'neg-budget',
            'budget': -100
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_campaigns(self):
        Campaign.objects.create(company=self.company, title="C1", slug="c1")
        Campaign.objects.create(company=self.company, title="C2", slug="c2")
        
        url = '/api/campaigns/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 2)
        else:
            self.assertEqual(len(response.data), 2)

    def test_add_jobs(self):
        campaign = Campaign.objects.create(company=self.company, title="Jobs Camp", slug="jobs-camp")
        job1 = Job.objects.create(title="J1", slug="j1", company=self.company, category=self.category, address=self.address_hcm, created_by=self.user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        job2 = Job.objects.create(title="J2", slug="j2", company=self.company, category=self.category, address=self.address_hcm, created_by=self.user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        
        url = f'/api/campaigns/{campaign.id}/jobs/'
        data = {'job_ids': [job1.id, job2.id]}
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(campaign.jobs.count(), 2)

    def test_add_other_company_jobs(self):
        # Create another user and company
        other_user = User.objects.create_user(email='other_co@test.com', password='password', role='company')
        other_company = Company.objects.create(user=other_user, company_name="Other Co", slug="other-co")
        
        job_other = Job.objects.create(title="Other J", slug="other-j", company=other_company, category=self.category, address=self.address_hcm, created_by=other_user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        
        campaign = Campaign.objects.create(company=self.company, title="My Camp", slug="my-camp")
        
        url = f'/api/campaigns/{campaign.id}/jobs/'
        data = {'job_ids': [job_other.id]}
        response = self.client.post(url, data, format='json')
        
        # Service should filter it out, resulting in 0 jobs added
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(campaign.jobs.count(), 0)

    def test_remove_job(self):
        campaign = Campaign.objects.create(company=self.company, title="Rem Job", slug="rem-job")
        job = Job.objects.create(title="J1", slug="j1", company=self.company, category=self.category, address=self.address_hcm, created_by=self.user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        campaign.jobs.add(job)
        
        url = f'/api/campaigns/{campaign.id}/jobs/{job.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(campaign.jobs.count(), 0)

    def test_update_status(self):
        campaign = Campaign.objects.create(company=self.company, title="Status Test", slug="status-test", status='draft')
        url = f'/api/campaigns/{campaign.id}/status/'
        data = {'status': 'active'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'active')
        campaign.refresh_from_db()
        self.assertEqual(campaign.status, 'active')

    def test_analytics(self):
        campaign = Campaign.objects.create(company=self.company, title="Ana Test", slug="ana-test")
        job = Job.objects.create(title="J1", slug="j1", company=self.company, category=self.category, address=self.address_hcm, created_by=self.user, status=Job.Status.PUBLISHED, description="d", requirements="r", view_count=100)
        campaign.jobs.add(job)
        
        url = f'/api/campaigns/{campaign.id}/analytics/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_views'], 100)
        self.assertEqual(response.data['total_jobs'], 1)

    def test_permissions(self):
        # Unauthenticated
        self.client.logout()
        url = '/api/campaigns/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_access_other_company_campaign(self):
        # Create another user and company
        other_user = User.objects.create_user(email='other@test.com', password='password', role='company')
        other_company = Company.objects.create(user=other_user, company_name="Other", slug="other")
        
        # Campaign belongs to 'company' (fixture)
        campaign_owned_by_company = Campaign.objects.create(company=self.company, title="Owned", slug="owned")
        
        # Authenticate as other_user
        self.client.force_authenticate(user=other_user)
        
        url = f'/api/campaigns/{campaign_owned_by_company.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Selector filters by company, so it should be 404
