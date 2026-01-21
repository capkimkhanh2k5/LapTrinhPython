from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import ActivityLog
from apps.system.activity_log_types.models import ActivityLogType

User = get_user_model()

class ActivityLogViewSetTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            password='password123',
            first_name='Normal',
            last_name='User'
        )
        
        self.log_type = ActivityLogType.objects.create(
            type_name='User Login',
            description='User logged in'
        )
        
        self.log1 = ActivityLog.objects.create(
            user=self.user,
            log_type=self.log_type,
            action='User logged in successfully',
            ip_address='127.0.0.1'
        )
        
        self.url = reverse('activity-logs-list')

    def test_list_logs_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see the log
        self.assertEqual(len(response.data), 1)

    def test_list_logs_user_forbidden(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_logs_by_user(self):
        self.client.force_authenticate(user=self.admin)
        # Filter by the specific user id
        response = self.client.get(self.url, {'user_id': self.user.id})
        self.assertEqual(len(response.data), 1)
        
        # Filter by non-existent user id
        response = self.client.get(self.url, {'user_id': 9999})
        self.assertEqual(len(response.data), 0)
