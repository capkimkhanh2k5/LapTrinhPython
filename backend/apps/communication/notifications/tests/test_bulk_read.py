from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.communication.notifications.models import Notification
from apps.communication.notification_types.models import NotificationType

class NotificationBulkReadTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create(email='test@example.com', full_name='Test User')
        self.client.force_authenticate(user=self.user)
        
        self.type = NotificationType.objects.create(type_name='General', is_active=True)
        
        # Create 5 unread notifications
        self.notifs = [
            Notification.objects.create(
                user=self.user,
                notification_type=self.type,
                title=f'Notif {i}',
                content='Test content',
                is_read=False
            ) for i in range(5)
        ]

    def test_mark_all_read(self):
        """Test marking all as read via bulk API."""
        response = self.client.patch('/api/notifications/mark-read/', {'read_all': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 5)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_mark_specific_ids_read(self):
        """Test marking specific IDs as read."""
        ids_to_read = [self.notifs[0].id, self.notifs[1].id]
        response = self.client.patch('/api/notifications/mark-read/', {'notification_ids': ids_to_read})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['updated_count'], 2)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=True).count(), 2)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 3)

    def test_empty_request_fails(self):
        """Test that empty request returns validation error."""
        response = self.client.patch('/api/notifications/mark-read/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
