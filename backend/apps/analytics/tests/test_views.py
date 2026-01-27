from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch
from apps.core.users.models import CustomUser
from apps.analytics.models import GeneratedReport


class TestAnalyticsViews(APITestCase):
    
    def setUp(self):
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@test.com', 
            password='pwd'
        )
        self.generated_report = GeneratedReport.objects.create(
            name="Test Report",
            report_type=GeneratedReport.Type.REVENUE,
            created_by=self.admin_user,
            file="https://res.cloudinary.com/test/raw/upload/reports/test.csv"
        )
    
    def test_admin_stats_access(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/dashboard/stats/admin/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('users', response.data)
        self.assertIn('revenue', response.data)

    @patch('apps.analytics.services.save_raw_file')
    def test_generate_report(self, mock_save_raw_file):
        # Note: Depending on where save_raw_file is imported in views/services, 
        # the patch path might need adjustment. Assuming 'apps.analytics.services.reports' or similar.
        # If the original test used 'apps.analytics.services.save_raw_file', I'llstick to that but check imports.
        # The original code patched 'apps.analytics.services.save_raw_file'.
        mock_save_raw_file.return_value = 'https://res.cloudinary.com/test/raw/upload/reports/report_revenue_123.csv'
        
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            'type': GeneratedReport.Type.REVENUE,
            'filters': {}
        }
        response = self.client.post('/api/dashboard/reports/generate/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['report_type'], GeneratedReport.Type.REVENUE)
        self.assertIn('cloudinary', response.data['file'])
        self.assertEqual(GeneratedReport.objects.count(), 2) # 1 from setUp + 1 new

    def test_list_reports(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/dashboard/reports/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

