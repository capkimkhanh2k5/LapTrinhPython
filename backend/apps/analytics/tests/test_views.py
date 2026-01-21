import pytest
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIClient
from apps.core.users.models import CustomUser
from apps.analytics.models import GeneratedReport

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_superuser(email='admin@test.com', password='pwd')

@pytest.fixture
def generated_report(db, admin_user):
    return GeneratedReport.objects.create(
        name="Test Report",
        report_type=GeneratedReport.Type.REVENUE,
        created_by=admin_user,
        file="https://res.cloudinary.com/test/raw/upload/reports/test.csv"
    )

@pytest.mark.django_db
class TestAnalyticsViews:
    def test_admin_stats_access(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/dashboard/stats/admin/')
        assert response.status_code == status.HTTP_200_OK
        assert 'users' in response.data
        assert 'revenue' in response.data

    @patch('apps.analytics.services.save_raw_file')
    def test_generate_report(self, mock_save_raw_file, api_client, admin_user):
        mock_save_raw_file.return_value = 'https://res.cloudinary.com/test/raw/upload/reports/report_revenue_123.csv'
        
        api_client.force_authenticate(user=admin_user)
        payload = {
            'type': GeneratedReport.Type.REVENUE,
            'filters': {}
        }
        response = api_client.post('/api/dashboard/reports/generate/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['report_type'] == GeneratedReport.Type.REVENUE
        assert 'cloudinary' in response.data['file']
        assert GeneratedReport.objects.count() == 1

    def test_list_reports(self, api_client, admin_user, generated_report):
        api_client.force_authenticate(user=admin_user)
        response = api_client.get('/api/dashboard/reports/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
