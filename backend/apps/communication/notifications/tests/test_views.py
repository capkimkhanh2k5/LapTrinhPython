# Notifications ViewSet Tests

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.communication.notifications.models import Notification
from apps.communication.notification_types.models import NotificationType

User = get_user_model()


class NotificationViewTests(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        # Create users
        cls.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            full_name='Test User'
        )
        cls.other_user = User.objects.create_user(
            email='otheruser@example.com',
            password='testpass123',
            full_name='Other User'
        )
        
        # Create notification type
        cls.notification_type = NotificationType.objects.create(
            type_name='system',
            template='System notification',
            is_active=True
        )
        
        # Create notifications
        cls.notification = Notification.objects.create(
            user=cls.user,
            notification_type=cls.notification_type,
            title='Test Notification',
            content='This is a test notification',
            link='https://example.com/test',
            is_read=False
        )
        
        cls.read_notification = Notification.objects.create(
            user=cls.user,
            notification_type=cls.notification_type,
            title='Read Notification',
            content='This notification has been read',
            is_read=True,
            read_at=timezone.now()
        )
        
        cls.other_user_notification = Notification.objects.create(
            user=cls.other_user,
            notification_type=cls.notification_type,
            title='Other User Notification',
            content='This belongs to another user'
        )

    def setUp(self):
        self.client.force_authenticate(user=self.user)

    def test_list_notifications_success(self):
        """Test listing notifications returns user's notifications."""
        url = '/api/notifications/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertGreaterEqual(len(data), 1)

    def test_list_notifications_unauthenticated(self):
        """Test listing notifications requires authentication."""
        self.client.logout()
        url = '/api/notifications/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_notifications_only_own(self):
        """Test user only sees their own notifications."""
        url = '/api/notifications/'
        response = self.client.get(url)
        
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        notification_ids = [n['id'] for n in data]
        self.assertIn(self.notification.id, notification_ids)
        self.assertNotIn(self.other_user_notification.id, notification_ids)

    def test_list_notifications_filter_by_read_status(self):
        """Test filtering notifications by read status."""
        url = '/api/notifications/'
        
        # Filter unread
        response = self.client.get(url, {'is_read': 'false'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for n in data:
            self.assertFalse(n['is_read'])
        
        # Filter read
        response = self.client.get(url, {'is_read': 'true'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for n in data:
            self.assertTrue(n['is_read'])

    def test_list_unread_success(self):
        """Test listing unread notifications."""
        url = '/api/notifications/unread/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for n in data:
            self.assertFalse(n['is_read'])

    def test_unread_empty_list(self):
        """Test empty unread list when all are read."""
        # Mark all as read first to test empty state if needed, 
        # but here we rely on existing data. 
        # setUpTestData creates one unread notification, so this test as written in pytest 
        # (which asserted success) was just checking the endpoint works.
        # But to test empty list, we need to mark the unread one as read.
        self.notification.is_read = True
        self.notification.save()
        
        url = '/api/notifications/unread/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(data), 0)
        
        # Restore for other tests
        self.notification.is_read = False
        self.notification.save()

    def test_retrieve_notification_success(self):
        """Test retrieving notification detail."""
        url = f'/api/notifications/{self.notification.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.notification.id)
        self.assertEqual(response.data['title'], self.notification.title)

    def test_retrieve_notification_not_found(self):
        """Test retrieving non-existent notification."""
        url = '/api/notifications/99999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_other_user_notification_forbidden(self):
        """Test cannot retrieve other user's notification."""
        url = f'/api/notifications/{self.other_user_notification.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_mark_as_read_success(self):
        """Test marking notification as read."""
        url = f'/api/notifications/{self.notification.id}/read/'
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])
        self.assertIsNotNone(response.data['read_at'])
        
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_mark_already_read(self):
        """Test marking already read notification."""
        url = f'/api/notifications/{self.read_notification.id}/read/'
        response = self.client.patch(url)
        
        # Should still succeed
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_read'])

    def test_mark_other_user_notification(self):
        """Test cannot mark other user's notification."""
        url = f'/api/notifications/{self.other_user_notification.id}/read/'
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_all_as_read_success(self):
        """Test marking all notifications as read."""
        # Create multiple unread notifications
        Notification.objects.create(
            user=self.user,
            notification_type=self.notification_type,
            title='Another notification',
            content='Another content'
        )
        
        url = '/api/notifications/read-all/'
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('updated_count', response.data)
        
        # Verify all are marked read
        unread_count = Notification.objects.filter(
            user=self.user, is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_delete_notification_success(self):
        """Test deleting a notification."""
        url = f'/api/notifications/{self.notification.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notification.objects.filter(id=self.notification.id).exists())

    def test_delete_other_user_notification(self):
        """Test cannot delete other user's notification."""
        url = f'/api/notifications/{self.other_user_notification.id}/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_clear_all_success(self):
        """Test clearing all notifications."""
        url = '/api/notifications/clear-all/'
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('deleted_count', response.data)
        
        # Verify all are deleted
        count = Notification.objects.filter(user=self.user).count()
        self.assertEqual(count, 0)

    def test_clear_all_does_not_affect_others(self):
        """Test clearing does not affect other users."""
        url = '/api/notifications/clear-all/'
        self.client.delete(url)
        
        # Other user's notification should still exist
        self.assertTrue(Notification.objects.filter(id=self.other_user_notification.id).exists())

    def test_get_settings_success(self):
        """Test getting notification settings."""
        url = '/api/notifications/settings/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email_notifications', response.data)
        self.assertIn('push_notifications', response.data)

    def test_get_unread_count(self):
        """Test getting unread notification count."""
        url = '/api/notifications/count/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('unread_count', response.data)
        self.assertGreaterEqual(response.data['unread_count'], 1)
