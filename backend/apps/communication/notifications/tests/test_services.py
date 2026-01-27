# Notifications Services Tests

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.communication.notifications.models import Notification
from apps.communication.notification_types.models import NotificationType
from apps.communication.notifications.services.notifications import (
    create_notification,
    mark_as_read,
    mark_all_as_read,
    delete_notification,
    clear_all_notifications,
    send_notification,
    send_bulk_notifications,
    NotificationCreateInput,
)

User = get_user_model()


class NotificationServicesTests(TestCase):
    
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
        
        # Create notification types
        cls.notification_type = NotificationType.objects.create(
            type_name='system',
            template='System notification',
            is_active=True
        )
        cls.inactive_notification_type = NotificationType.objects.create(
            type_name='deprecated',
            template='Deprecated notification',
            is_active=False
        )
        
        # Create initial notification
        cls.notification = Notification.objects.create(
            user=cls.user,
            notification_type=cls.notification_type,
            title='Test Notification',
            content='This is a test notification',
            is_read=False
        )

    def test_create_notification_success(self):
        """Test creating a notification successfully."""
        data = NotificationCreateInput(
            notification_type_id=self.notification_type.id,
            title='New Notification',
            content='This is the content',
            link='https://example.com',
            entity_type='job',
            entity_id=123
        )
        
        notification = create_notification(self.user, data)
        
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, 'New Notification')
        self.assertEqual(notification.content, 'This is the content')
        self.assertEqual(notification.link, 'https://example.com')
        self.assertEqual(notification.entity_type, 'job')
        self.assertEqual(notification.entity_id, 123)
        self.assertFalse(notification.is_read)

    def test_create_notification_minimal(self):
        """Test creating notification with minimal data."""
        data = NotificationCreateInput(
            notification_type_id=self.notification_type.id,
            title='Minimal',
            content='Content only'
        )
        
        notification = create_notification(self.user, data)
        
        self.assertIsNotNone(notification.id)
        self.assertEqual(notification.link, '')
        self.assertEqual(notification.entity_type, '')
        self.assertIsNone(notification.entity_id)

    def test_create_notification_invalid_type(self):
        """Test creating notification with invalid type."""
        data = NotificationCreateInput(
            notification_type_id=99999,
            title='Test',
            content='Content'
        )
        
        with self.assertRaisesRegex(ValueError, "does not exist"):
            create_notification(self.user, data)

    def test_create_notification_inactive_type(self):
        """Test creating notification with inactive type."""
        data = NotificationCreateInput(
            notification_type_id=self.inactive_notification_type.id,
            title='Test',
            content='Content'
        )
        
        with self.assertRaisesRegex(ValueError, "does not exist or is inactive"):
            create_notification(self.user, data)

    def test_mark_as_read_success(self):
        """Test marking notification as read."""
        result = mark_as_read(self.notification.id, self.user.id)
        
        self.assertTrue(result.is_read)
        self.assertIsNotNone(result.read_at)

    def test_mark_as_read_already_read(self):
        """Test marking already read notification."""
        read_notification = Notification.objects.create(
            user=self.user,
            notification_type=self.notification_type,
            title='Already Read',
            content='Content',
            is_read=True,
            read_at=timezone.now()
        )
        original_read_at = read_notification.read_at
        
        result = mark_as_read(read_notification.id, self.user.id)
        
        # Should keep original read_at
        self.assertTrue(result.is_read)
        self.assertEqual(result.read_at, original_read_at)

    def test_mark_as_read_not_found(self):
        """Test marking non-existent notification."""
        with self.assertRaisesRegex(ValueError, "not found"):
            mark_as_read(99999, self.user.id)

    def test_mark_as_read_wrong_user(self):
        """Test marking other user's notification."""
        with self.assertRaisesRegex(ValueError, "not found"):
            mark_as_read(self.notification.id, self.other_user.id)

    def test_mark_all_as_read_success(self):
        """Test marking all notifications as read."""
        # Create multiple unread notifications
        for i in range(3):
            Notification.objects.create(
                user=self.user,
                notification_type=self.notification_type,
                title=f'Notification {i}',
                content='Content',
                is_read=False
            )
        
        unread_before = Notification.objects.filter(user=self.user, is_read=False).count()
        updated_count = mark_all_as_read(self.user.id)
        
        self.assertEqual(updated_count, unread_before)
        
        unread = Notification.objects.filter(user=self.user, is_read=False).count()
        self.assertEqual(unread, 0)

    def test_mark_all_as_read_no_unread(self):
        """Test marking all when all are already read."""
        # Clean up first
        Notification.objects.filter(user=self.user).delete()
        
        Notification.objects.create(
            user=self.user,
            notification_type=self.notification_type,
            title='Already Read',
            content='Content',
            is_read=True,
            read_at=timezone.now()
        )
        
        updated_count = mark_all_as_read(self.user.id)
        
        self.assertEqual(updated_count, 0)

    def test_delete_notification_success(self):
        """Test deleting a notification."""
        notification_id = self.notification.id
        
        result = delete_notification(notification_id, self.user.id)
        
        self.assertTrue(result)
        self.assertFalse(Notification.objects.filter(id=notification_id).exists())

    def test_delete_notification_not_found(self):
        """Test deleting non-existent notification."""
        with self.assertRaisesRegex(ValueError, "not found"):
            delete_notification(99999, self.user.id)

    def test_delete_notification_wrong_user(self):
        """Test deleting other user's notification."""
        with self.assertRaisesRegex(ValueError, "not found"):
            delete_notification(self.notification.id, self.other_user.id)

    def test_clear_all_success(self):
        """Test clearing all notifications."""
        # Create notifications
        for i in range(5):
            Notification.objects.create(
                user=self.user,
                notification_type=self.notification_type,
                title=f'Notification {i}',
                content='Content'
            )
        
        existing_count = Notification.objects.filter(user=self.user).count()
        
        deleted_count = clear_all_notifications(self.user.id)
        
        self.assertEqual(deleted_count, existing_count)
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 0)

    def test_clear_all_empty(self):
        """Test clearing when no notifications exist."""
        Notification.objects.filter(user=self.user).delete()
        deleted_count = clear_all_notifications(self.user.id)
        
        self.assertEqual(deleted_count, 0)

    def test_send_notification_success(self):
        """Test sending notification by type name."""
        notification = send_notification(
            user_id=self.user.id,
            notification_type_name='system',
            title='Welcome',
            content='Welcome to the platform',
            link='https://example.com',
            entity_type='user',
            entity_id=self.user.id
        )
        
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, 'Welcome')
        self.assertEqual(notification.notification_type.type_name, 'system')

    def test_send_notification_invalid_type(self):
        """Test sending with invalid type name."""
        notification = send_notification(
            user_id=self.user.id,
            notification_type_name='nonexistent',
            title='Test',
            content='Content'
        )
        
        self.assertIsNone(notification)

    def test_send_notification_invalid_user(self):
        """Test sending to invalid user."""
        notification = send_notification(
            user_id=99999,
            notification_type_name='system',
            title='Test',
            content='Content'
        )
        
        self.assertIsNone(notification)

    def test_send_bulk_notifications_success(self):
        """Test sending bulk notifications."""
        notifications = send_bulk_notifications(
            user_ids=[self.user.id, self.other_user.id],
            notification_type_name='system',
            title='Announcement',
            content='Important announcement'
        )
        
        self.assertEqual(len(notifications), 2)
        
        user_notification = Notification.objects.filter(user=self.user, title='Announcement').first()
        other_notification = Notification.objects.filter(user=self.other_user, title='Announcement').first()
        
        self.assertIsNotNone(user_notification)
        self.assertIsNotNone(other_notification)
        self.assertEqual(user_notification.title, 'Announcement')

    def test_send_bulk_invalid_type(self):
        """Test bulk send with invalid type."""
        notifications = send_bulk_notifications(
            user_ids=[self.user.id, self.other_user.id],
            notification_type_name='nonexistent',
            title='Test',
            content='Content'
        )
        
        # Expect empty list if type not found (based on source code implied by previous tests)
        self.assertEqual(len(notifications), 0)
