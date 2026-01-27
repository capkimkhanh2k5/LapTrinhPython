# Job Alerts ViewSet Tests

from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.communication.job_alerts.models import JobAlert
from apps.recruitment.job_categories.models import JobCategory
from apps.geography.provinces.models import Province
from apps.candidate.recruiters.models import Recruiter

User = get_user_model()


class JobAlertViewTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.user = User.objects.create_user(
            email='user@test.com',
            password='password123',
            full_name='Test User',
        )
        cls.recruiter_profile = Recruiter.objects.create(user=cls.user)
        
        # Create categories and locations
        cls.category = JobCategory.objects.create(name="IT Software", slug="it-software")
        cls.province = Province.objects.create(province_name="Ho Chi Minh", province_code="79")
        
        # Create Initial Alert
        cls.job_alert = JobAlert.objects.create(
            recruiter=cls.recruiter_profile,
            alert_name="React Dev",
            category=cls.category,
            salary_min=10000000,
            job_type=JobAlert.JobType.FULL_TIME
        )
        cls.job_alert.locations.add(cls.province)

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_list_alerts(self):
        url = '/api/job-alerts/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            results = response.data['results']
        else:
            results = response.data
            
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], self.job_alert.id)

    def test_create_alert(self):
        url = '/api/job-alerts/'
        data = {
            'alert_name': 'New Python Job',
            'category': self.category.id,
            'location_ids': [self.province.id],
            'salary_min': 15000000,
            'frequency': 'daily'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(JobAlert.objects.count(), 2) # 1 initial + 1 created
        self.assertEqual(response.data['alert_name'], 'New Python Job')

    def test_toggle_alert(self):
        url = f'/api/job-alerts/{self.job_alert.id}/toggle/'
        
        # Turn OFF
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_active'])
        self.job_alert.refresh_from_db()
        self.assertFalse(self.job_alert.is_active)
        
        # Turn ON
        response = self.client.patch(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_active'])

    def test_update_alert(self):
        url = f'/api/job-alerts/{self.job_alert.id}/'
        data = {'alert_name': 'Updated Name', 'salary_min': 20000000}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['alert_name'], 'Updated Name')
        self.assertEqual(float(response.data['salary_min']), 20000000)

    def test_delete_alert(self):
        url = f'/api/job-alerts/{self.job_alert.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(JobAlert.objects.filter(id=self.job_alert.id).count(), 0)

    def test_get_detail(self):
        url = f'/api/job-alerts/{self.job_alert.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.job_alert.id)

    def test_create_invalid_salary(self):
        url = '/api/job-alerts/'
        data = {
            'alert_name': 'Invalid Salary',
            'category': self.category.id,
            'location_ids': [self.province.id],
            'salary_min': -5000000, # Invalid
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('salary_min', response.data)

    def test_create_invalid_frequency(self):
        url = '/api/job-alerts/'
        data = {
            'alert_name': 'Invalid Freq',
            'category': self.category.id,
            'frequency': 'yearly' # Invalid choice
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('frequency', response.data)

    def test_access_other_user_alert(self):
        # Create another user and client (authenticating as other user via separate login/force_auth in test context if needed, but here we switch client auth)
        other_user = User.objects.create_user(email='other@test.com', password='password')
        Recruiter.objects.create(user=other_user)
        
        self.client.force_authenticate(user=other_user)
        
        url = f'/api/job-alerts/{self.job_alert.id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) # Should not find other's alert

    def test_unauthenticated_access(self):
        self.client.logout()
        url = '/api/job-alerts/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
