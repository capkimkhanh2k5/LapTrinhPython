import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.communication.job_alerts.models import JobAlert
from apps.recruitment.jobs.models import Job
from apps.company.companies.models import Company
from apps.recruitment.job_categories.models import JobCategory
from apps.geography.provinces.models import Province
from apps.geography.addresses.models import Address

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(
        email='user@test.com',
        password='password123',
        full_name='Test User',
    )

@pytest.fixture
def recruiter_profile(user):
    from apps.candidate.recruiters.models import Recruiter
    return Recruiter.objects.create(user=user)

@pytest.fixture
def authenticated_client(api_client, user, recruiter_profile):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def category():
    return JobCategory.objects.create(name="IT Software", slug="it-software")

@pytest.fixture
def province():
    return Province.objects.create(province_name="Ho Chi Minh", province_code="79")

@pytest.fixture
def job_alert(recruiter_profile, category, province):
    alert = JobAlert.objects.create(
        recruiter=recruiter_profile,
        alert_name="React Dev",
        category=category,
        salary_min=10000000,
        job_type=JobAlert.JobType.FULL_TIME
    )
    alert.locations.add(province)
    return alert

@pytest.mark.django_db
class TestJobAlertViewSet:
    
    def test_list_alerts(self, authenticated_client, job_alert):
        url = '/api/job-alerts/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
            
        assert len(results) == 1
        assert results[0]['id'] == job_alert.id

    def test_create_alert(self, authenticated_client, category, province):
        url = '/api/job-alerts/'
        data = {
            'alert_name': 'New Python Job',
            'category': category.id,
            'location_ids': [province.id],
            'salary_min': 15000000,
            'frequency': 'daily'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert JobAlert.objects.count() == 1 # + fixture alert? No, logic depends if fixture is used
        assert response.data['alert_name'] == 'New Python Job'

    def test_toggle_alert(self, authenticated_client, job_alert):
        url = f'/api/job-alerts/{job_alert.id}/toggle/'
        
        # Turn OFF
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is False
        job_alert.refresh_from_db()
        assert job_alert.is_active is False
        
        # Turn ON
        response = authenticated_client.patch(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_active'] is True

    def test_update_alert(self, authenticated_client, job_alert):
        url = f'/api/job-alerts/{job_alert.id}/'
        data = {'alert_name': 'Updated Name', 'salary_min': 20000000}
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['alert_name'] == 'Updated Name'
        assert float(response.data['salary_min']) == 20000000

    def test_delete_alert(self, authenticated_client, job_alert):
        url = f'/api/job-alerts/{job_alert.id}/'
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert JobAlert.objects.count() == 0

    def test_get_detail(self, authenticated_client, job_alert):
        url = f'/api/job-alerts/{job_alert.id}/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == job_alert.id

    def test_create_invalid_salary(self, authenticated_client, category, province):
        url = '/api/job-alerts/'
        data = {
            'alert_name': 'Invalid Salary',
            'category': category.id,
            'location_ids': [province.id],
            'salary_min': -5000000, # Invalid
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'salary_min' in response.data

    def test_create_invalid_frequency(self, authenticated_client, category, province):
        url = '/api/job-alerts/'
        data = {
            'alert_name': 'Invalid Freq',
            'category': category.id,
            'frequency': 'yearly' # Invalid choice
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'frequency' in response.data

    def test_access_other_user_alert(self, api_client, job_alert):
        # Create another user and client
        other_user = User.objects.create_user(email='other@test.com', password='password')
        from apps.candidate.recruiters.models import Recruiter
        Recruiter.objects.create(user=other_user)
        
        api_client.force_authenticate(user=other_user)
        
        url = f'/api/job-alerts/{job_alert.id}/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND # Should not find other's alert

    def test_unauthenticated_access(self, api_client):
        url = '/api/job-alerts/'
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
