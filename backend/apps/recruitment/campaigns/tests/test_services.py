from django.test import TestCase
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.recruitment.campaigns.services.campaigns import CampaignService, CampaignCreateInput, CampaignUpdateInput
from apps.recruitment.campaigns.models import Campaign
from apps.recruitment.jobs.models import Job
from apps.company.companies.models import Company
from apps.recruitment.job_categories.models import JobCategory
from apps.geography.provinces.models import Province
from apps.geography.addresses.models import Address

User = get_user_model()

class TestCampaignService(TestCase):
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

    def test_create_campaign_service(self):
        input_data = CampaignCreateInput(title="Serv Camp", slug="serv-camp", budget=Decimal('500.00'))
        campaign = CampaignService.create_campaign(self.company, input_data)
        self.assertIsNotNone(campaign.pk)
        self.assertEqual(campaign.title, "Serv Camp")
        self.assertEqual(campaign.budget, Decimal('500.00'))

    def test_create_campaign_slug_uniqueness(self):
        input_data = CampaignCreateInput(title="Unique", slug="unique")
        CampaignService.create_campaign(self.company, input_data)
        
        with self.assertRaises(ValidationError):
            CampaignService.create_campaign(self.company, input_data)

    def test_update_campaign_service(self):
        campaign = Campaign.objects.create(company=self.company, title="Old", slug="old")
        update_data = CampaignUpdateInput(title="New")
        updated = CampaignService.update_campaign(campaign, update_data)
        self.assertEqual(updated.title, "New")

    def test_add_remove_jobs_service(self):
        campaign = Campaign.objects.create(company=self.company, title="Jobs Svc", slug="jobs-svc")
        job = Job.objects.create(title="J1", slug="j1", company=self.company, category=self.category, address=self.address_hcm, created_by=self.user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        
        # Add
        CampaignService.add_jobs(campaign, [job.id])
        self.assertTrue(campaign.jobs.filter(id=job.id).exists())
        
        # Remove
        CampaignService.remove_job(campaign, job.id)
        self.assertFalse(campaign.jobs.filter(id=job.id).exists())

    def test_add_jobs_cross_company_check(self):
        campaign = Campaign.objects.create(company=self.company, title="My Camp", slug="my-camp")
        
        # Create other company job
        other_company = Company.objects.create(company_name="Other", slug="other")
        other_job = Job.objects.create(title="Other J", slug="other", company=other_company, category=self.category, address=self.address_hcm, created_by=self.user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        
        CampaignService.add_jobs(campaign, [other_job.id])
        self.assertEqual(campaign.jobs.count(), 0)

    def test_analytics_calculation(self):
        campaign = Campaign.objects.create(company=self.company, title="Ana Svc", slug="ana-svc")
        job1 = Job.objects.create(title="J1", slug="j1", company=self.company, category=self.category, address=self.address_hcm, created_by=self.user, status=Job.Status.PUBLISHED, description="d", requirements="r", view_count=50)
        job2 = Job.objects.create(title="J2", slug="j2", company=self.company, category=self.category, address=self.address_hcm, created_by=self.user, status=Job.Status.PUBLISHED, description="d", requirements="r", view_count=30)
        campaign.jobs.add(job1, job2)
        
        analytics = CampaignService.get_analytics(campaign)
        self.assertEqual(analytics.total_views, 80)
        self.assertEqual(analytics.total_jobs, 2)

    def test_analytics_empty_campaign(self):
        campaign = Campaign.objects.create(company=self.company, title="Empty", slug="empty")
        analytics = CampaignService.get_analytics(campaign)
        self.assertEqual(analytics.total_views, 0)
        self.assertEqual(analytics.total_applications, 0)
        self.assertEqual(analytics.total_jobs, 0)
