import pytest
from rest_framework import status
from apps.recruitment.campaigns.models import Campaign
from apps.recruitment.jobs.models import Job
from apps.company.companies.models import Company
from django.utils import timezone
from datetime import timedelta

@pytest.mark.django_db
class TestCampaignViewSet:
    def test_create_campaign(self, authenticated_client, company):
        url = '/api/campaigns/'
        data = {
            'title': 'Test Campaign',
            'slug': 'test-campaign',
            'status': 'active',
            'budget': 1000
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'Test Campaign'
        assert Campaign.objects.count() == 1

    def test_create_campaign_invalid_dates(self, authenticated_client, company):
        url = '/api/campaigns/'
        data = {
            'title': 'Invalid Date Campaign',
            'slug': 'invalid-date-campaign',
            'start_date': (timezone.now() + timedelta(days=5)).date(),
            'end_date': (timezone.now() + timedelta(days=1)).date(), # End before start
            'budget': 1000
        }
        # Assuming model/serializer validation catches this, or service
        # Currently service doesn't have explicit date validation, waiting to see if DRF or logic handles it.
        # If not implemented, this test might fail (pass as 201).
        # Let's check serializer/model first. Model doesn't enforce it by default.
        # I should probably add validation to service/serializer if it's missing.
        # For now, let's write the test expecting 400.
        response = authenticated_client.post(url, data, format='json')
        # If failure, I will need to implement validation.
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_campaign_negative_budget(self, authenticated_client, company):
        url = '/api/campaigns/'
        data = {
            'title': 'Negative Budget',
            'slug': 'neg-budget',
            'budget': -100
        }
        # DecimalField usually allows negative unless validators are set. 
        # I should check if I set validators.
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_campaigns(self, authenticated_client, company):
        Campaign.objects.create(company=company, title="C1", slug="c1")
        Campaign.objects.create(company=company, title="C2", slug="c2")
        
        url = '/api/campaigns/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        if 'results' in response.data:
            assert len(response.data['results']) == 2
        else:
            assert len(response.data) == 2

    def test_add_jobs(self, authenticated_client, category, company, user, address_hcm):
        campaign = Campaign.objects.create(company=company, title="Jobs Camp", slug="jobs-camp")
        job1 = Job.objects.create(title="J1", slug="j1", company=company, category=category, address=address_hcm, created_by=user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        job2 = Job.objects.create(title="J2", slug="j2", company=company, category=category, address=address_hcm, created_by=user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        
        url = f'/api/campaigns/{campaign.id}/jobs/'
        data = {'job_ids': [job1.id, job2.id]}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert campaign.jobs.count() == 2

    def test_add_other_company_jobs(self, authenticated_client, company, category, user, address_hcm):
        # Create another user and company
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_user = User.objects.create_user(email='other_co@test.com', password='password', role='company')
        other_company = Company.objects.create(user=other_user, company_name="Other Co", slug="other-co")
        
        job_other = Job.objects.create(title="Other J", slug="other-j", company=other_company, category=category, address=address_hcm, created_by=other_user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        
        campaign = Campaign.objects.create(company=company, title="My Camp", slug="my-camp")
        
        url = f'/api/campaigns/{campaign.id}/jobs/'
        data = {'job_ids': [job_other.id]}
        response = authenticated_client.post(url, data, format='json')
        
        # Service should filter it out, resulting in 0 jobs added
        assert response.status_code == status.HTTP_200_OK
        assert campaign.jobs.count() == 0

    def test_remove_job(self, authenticated_client, category, company, user, address_hcm):
        campaign = Campaign.objects.create(company=company, title="Rem Job", slug="rem-job")
        job = Job.objects.create(title="J1", slug="j1", company=company, category=category, address=address_hcm, created_by=user, status=Job.Status.PUBLISHED, description="d", requirements="r")
        campaign.jobs.add(job)
        
        url = f'/api/campaigns/{campaign.id}/jobs/{job.id}/'
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert campaign.jobs.count() == 0

    def test_update_status(self, authenticated_client, company):
        campaign = Campaign.objects.create(company=company, title="Status Test", slug="status-test", status='draft')
        url = f'/api/campaigns/{campaign.id}/status/'
        data = {'status': 'active'}
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'active'
        campaign.refresh_from_db()
        assert campaign.status == 'active'

    def test_analytics(self, authenticated_client, company, category, user, address_hcm):
        campaign = Campaign.objects.create(company=company, title="Ana Test", slug="ana-test")
        job = Job.objects.create(title="J1", slug="j1", company=company, category=category, address=address_hcm, created_by=user, status=Job.Status.PUBLISHED, description="d", requirements="r", view_count=100)
        campaign.jobs.add(job)
        
        url = f'/api/campaigns/{campaign.id}/analytics/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_views'] == 100
        assert response.data['total_jobs'] == 1

    def test_permissions(self, api_client, company):
        # Unauthenticated
        url = '/api/campaigns/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_access_other_company_campaign(self, api_client, company):
        # Create another user and company
        from django.contrib.auth import get_user_model
        User = get_user_model()
        other_user = User.objects.create_user(email='other@test.com', password='password', role='company')
        other_company = Company.objects.create(user=other_user, company_name="Other", slug="other")
        
        # Campaign belongs to 'company' (fixture)
        campaign_owned_by_company = Campaign.objects.create(company=company, title="Owned", slug="owned")
        
        # Authenticate as other_user
        api_client.force_authenticate(user=other_user)
        
        url = f'/api/campaigns/{campaign_owned_by_company.id}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND # Selector filters by company, so it should be 404
