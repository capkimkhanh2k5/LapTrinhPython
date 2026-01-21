# Notifications Services Tests

import pytest
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


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        email='testuser@example.com',
        password='testpass123',
        full_name='Test User'
    )


@pytest.fixture
def other_user(db):
    """Create another test user."""
    return User.objects.create_user(
        email='otheruser@example.com',
        password='testpass123',
        full_name='Other User'
    )


@pytest.fixture
def notification_type(db):
    """Create a notification type."""
    return NotificationType.objects.create(
        type_name='system',
        template='System notification',
        is_active=True
    )


@pytest.fixture
def inactive_notification_type(db):
    """Create an inactive notification type."""
    return NotificationType.objects.create(
        type_name='deprecated',
        template='Deprecated notification',
        is_active=False
    )


@pytest.fixture
def notification(db, user, notification_type):
    """Create a test notification."""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title='Test Notification',
        content='This is a test notification',
        is_read=False
    )


@pytest.mark.django_db
class TestCreateNotification:
    """Tests for create_notification service."""
    
    def test_create_notification_success(self, user, notification_type):
        """Test creating a notification successfully."""
        data = NotificationCreateInput(
            notification_type_id=notification_type.id,
            title='New Notification',
            content='This is the content',
            link='https://example.com',
            entity_type='job',
            entity_id=123
        )
        
        notification = create_notification(user, data)
        
        assert notification.id is not None
        assert notification.user == user
        assert notification.title == 'New Notification'
        assert notification.content == 'This is the content'
        assert notification.link == 'https://example.com'
        assert notification.entity_type == 'job'
        assert notification.entity_id == 123
        assert notification.is_read is False
    
    def test_create_notification_minimal(self, user, notification_type):
        """Test creating notification with minimal data."""
        data = NotificationCreateInput(
            notification_type_id=notification_type.id,
            title='Minimal',
            content='Content only'
        )
        
        notification = create_notification(user, data)
        
        assert notification.id is not None
        assert notification.link == ''
        assert notification.entity_type == ''
        assert notification.entity_id is None
    
    def test_create_notification_invalid_type(self, user):
        """Test creating notification with invalid type."""
        data = NotificationCreateInput(
            notification_type_id=99999,
            title='Test',
            content='Content'
        )
        
        with pytest.raises(ValueError, match="does not exist"):
            create_notification(user, data)
    
    def test_create_notification_inactive_type(self, user, inactive_notification_type):
        """Test creating notification with inactive type."""
        data = NotificationCreateInput(
            notification_type_id=inactive_notification_type.id,
            title='Test',
            content='Content'
        )
        
        with pytest.raises(ValueError, match="does not exist or is inactive"):
            create_notification(user, data)


@pytest.mark.django_db
class TestMarkAsRead:
    """Tests for mark_as_read service."""
    
    def test_mark_as_read_success(self, notification, user):
        """Test marking notification as read."""
        result = mark_as_read(notification.id, user.id)
        
        assert result.is_read is True
        assert result.read_at is not None
    
    def test_mark_as_read_already_read(self, user, notification_type):
        """Test marking already read notification."""
        read_notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title='Already Read',
            content='Content',
            is_read=True,
            read_at=timezone.now()
        )
        original_read_at = read_notification.read_at
        
        result = mark_as_read(read_notification.id, user.id)
        
        # Should keep original read_at
        assert result.is_read is True
        assert result.read_at == original_read_at
    
    def test_mark_as_read_not_found(self, user):
        """Test marking non-existent notification."""
        with pytest.raises(ValueError, match="not found"):
            mark_as_read(99999, user.id)
    
    def test_mark_as_read_wrong_user(self, notification, other_user):
        """Test marking other user's notification."""
        with pytest.raises(ValueError, match="not found"):
            mark_as_read(notification.id, other_user.id)


@pytest.mark.django_db
class TestMarkAllAsRead:
    """Tests for mark_all_as_read service."""
    
    def test_mark_all_as_read_success(self, user, notification_type):
        """Test marking all notifications as read."""
        # Create multiple unread notifications
        for i in range(3):
            Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=f'Notification {i}',
                content='Content',
                is_read=False
            )
        
        updated_count = mark_all_as_read(user.id)
        
        assert updated_count == 3
        
        unread = Notification.objects.filter(user=user, is_read=False).count()
        assert unread == 0
    
    def test_mark_all_as_read_no_unread(self, user, notification_type):
        """Test marking all when all are already read."""
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title='Already Read',
            content='Content',
            is_read=True,
            read_at=timezone.now()
        )
        
        updated_count = mark_all_as_read(user.id)
        
        assert updated_count == 0


@pytest.mark.django_db
class TestDeleteNotification:
    """Tests for delete_notification service."""
    
    def test_delete_notification_success(self, notification, user):
        """Test deleting a notification."""
        notification_id = notification.id
        
        result = delete_notification(notification_id, user.id)
        
        assert result is True
        assert not Notification.objects.filter(id=notification_id).exists()
    
    def test_delete_notification_not_found(self, user):
        """Test deleting non-existent notification."""
        with pytest.raises(ValueError, match="not found"):
            delete_notification(99999, user.id)
    
    def test_delete_notification_wrong_user(self, notification, other_user):
        """Test deleting other user's notification."""
        with pytest.raises(ValueError, match="not found"):
            delete_notification(notification.id, other_user.id)


@pytest.mark.django_db
class TestClearAllNotifications:
    """Tests for clear_all_notifications service."""
    
    def test_clear_all_success(self, user, notification_type):
        """Test clearing all notifications."""
        # Create notifications
        for i in range(5):
            Notification.objects.create(
                user=user,
                notification_type=notification_type,
                title=f'Notification {i}',
                content='Content'
            )
        
        deleted_count = clear_all_notifications(user.id)
        
        assert deleted_count == 5
        assert Notification.objects.filter(user=user).count() == 0
    
    def test_clear_all_empty(self, user):
        """Test clearing when no notifications exist."""
        deleted_count = clear_all_notifications(user.id)
        
        assert deleted_count == 0


@pytest.mark.django_db
class TestSendNotification:
    """Tests for send_notification convenience function."""
    
    def test_send_notification_success(self, user, notification_type):
        """Test sending notification by type name."""
        notification = send_notification(
            user_id=user.id,
            notification_type_name='system',
            title='Welcome',
            content='Welcome to the platform',
            link='https://example.com',
            entity_type='user',
            entity_id=user.id
        )
        
        assert notification is not None
        assert notification.title == 'Welcome'
        assert notification.notification_type.type_name == 'system'
    
    def test_send_notification_invalid_type(self, user):
        """Test sending with invalid type name."""
        notification = send_notification(
            user_id=user.id,
            notification_type_name='nonexistent',
            title='Test',
            content='Content'
        )
        
        assert notification is None
    
    def test_send_notification_invalid_user(self, notification_type):
        """Test sending to invalid user."""
        notification = send_notification(
            user_id=99999,
            notification_type_name='system',
            title='Test',
            content='Content'
        )
        
        assert notification is None


@pytest.mark.django_db
class TestSendBulkNotifications:
    """Tests for send_bulk_notifications function."""
    
    def test_send_bulk_success(self, user, other_user, notification_type):
        """Test sending bulk notifications."""
        notifications = send_bulk_notifications(
            user_ids=[user.id, other_user.id],
            notification_type_name='system',
            title='Announcement',
            content='Important announcement'
        )
        
        assert len(notifications) == 2
        
        user_notification = Notification.objects.filter(user=user).first()
        other_notification = Notification.objects.filter(user=other_user).first()
        
        assert user_notification is not None
        assert other_notification is not None
        assert user_notification.title == 'Announcement'
    
    def test_send_bulk_invalid_type(self, user, other_user):
        """Test bulk send with invalid type."""
        notifications = send_bulk_notifications(
            user_ids=[user.id, other_user.id],
            notification_type_name='nonexistent',
            title='Test',
            content='Content'
        )
        
        assert len(notifications) == 0
