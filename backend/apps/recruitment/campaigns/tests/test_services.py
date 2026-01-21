import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from apps.recruitment.campaigns.services.campaigns import CampaignService, CampaignCreateInput, CampaignUpdateInput
from apps.recruitment.campaigns.models import Campaign
from apps.recruitment.jobs.models import Job
from apps.company.companies.models import Company

@pytest.mark.django_db
class TestCampaignService:
    def test_create_campaign_service(self, company):
        input_data = CampaignCreateInput(title="Serv Camp", slug="serv-camp", budget=Decimal('500.00'))
        campaign = CampaignService.create_campaign(company, input_data)
        assert campaign.pk is not None
        assert campaign.title == "Serv Camp"
        assert campaign.budget == Decimal('500.00')

    def test_create_campaign_slug_uniqueness(self, company):
        input_data = CampaignCreateInput(title="Unique", slug="unique")
        CampaignService.create_campaign(company, input_data)
        
        with pytest.raises(ValidationError):
            CampaignService.create_campaign(company, input_data)

    def test_update_campaign_service(self, company):
        campaign = Campaign.objects.create(company=company, title="Old", slug="old")
        update_data = CampaignUpdateInput(title="New")
        updated = CampaignService.update_campaign(campaign, update_data)
        assert updated.title == "New"

    def test_add_remove_jobs_service(self, company, category, user, address_hcm):
        campaign = Campaign.objects.create(company=company, title="Jobs Svc", slug="jobs-svc")
        job = Job.objects.create(title="J1", slug="j1", company=company, category=category, address=address_hcm, created_by=user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        
        # Add
        CampaignService.add_jobs(campaign, [job.id])
        assert campaign.jobs.filter(id=job.id).exists()
        
        # Remove
        CampaignService.remove_job(campaign, job.id)
        assert not campaign.jobs.filter(id=job.id).exists()

    def test_add_jobs_cross_company_check(self, company, category, user, address_hcm):
        campaign = Campaign.objects.create(company=company, title="My Camp", slug="my-camp")
        
        # Create other company job
        other_company = Company.objects.create(company_name="Other", slug="other")
        other_job = Job.objects.create(title="Other J", slug="other", company=other_company, category=category, address=address_hcm, created_by=user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        
        CampaignService.add_jobs(campaign, [other_job.id])
        assert campaign.jobs.count() == 0

    def test_analytics_calculation(self, company, category, user, address_hcm):
        campaign = Campaign.objects.create(company=company, title="Ana Svc", slug="ana-svc")
        job1 = Job.objects.create(title="J1", slug="j1", company=company, category=category, address=address_hcm, created_by=user, status=Job.Status.PUBLISHED, description="d", requirements="r", view_count=50)
        job2 = Job.objects.create(title="J2", slug="j2", company=company, category=category, address=address_hcm, created_by=user, status=Job.Status.PUBLISHED, description="d", requirements="r", view_count=30)
        campaign.jobs.add(job1, job2)
        
        analytics = CampaignService.get_analytics(campaign)
        assert analytics.total_views == 80
        assert analytics.total_jobs == 2

    def test_analytics_empty_campaign(self, company):
        campaign = Campaign.objects.create(company=company, title="Empty", slug="empty")
        analytics = CampaignService.get_analytics(campaign)
        assert analytics.total_views == 0
        assert analytics.total_applications == 0
        assert analytics.total_jobs == 0
