# Notifications ViewSet Tests

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.communication.notifications.models import Notification
from apps.communication.notification_types.models import NotificationType

User = get_user_model()


@pytest.fixture
def api_client():
    """Create API client."""
    return APIClient()


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
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def notification_type(db):
    """Create a notification type."""
    return NotificationType.objects.create(
        type_name='system',
        template='System notification',
        is_active=True
    )


@pytest.fixture
def notification(db, user, notification_type):
    """Create a test notification."""
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title='Test Notification',
        content='This is a test notification',
        link='https://example.com/test',
        is_read=False
    )


@pytest.fixture
def read_notification(db, user, notification_type):
    """Create a read notification."""
    from django.utils import timezone
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title='Read Notification',
        content='This notification has been read',
        is_read=True,
        read_at=timezone.now()
    )


@pytest.fixture
def other_user_notification(db, other_user, notification_type):
    """Create a notification for another user."""
    return Notification.objects.create(
        user=other_user,
        notification_type=notification_type,
        title='Other User Notification',
        content='This belongs to another user'
    )


@pytest.mark.django_db
class TestNotificationList:
    """Tests for listing notifications."""
    
    def test_list_notifications_success(self, authenticated_client, notification):
        """Test listing notifications returns user's notifications."""
        url = '/api/notifications/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        assert len(data) >= 1
    
    def test_list_notifications_unauthenticated(self, api_client):
        """Test listing notifications requires authentication."""
        url = '/api/notifications/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_notifications_only_own(
        self, authenticated_client, notification, other_user_notification
    ):
        """Test user only sees their own notifications."""
        url = '/api/notifications/'
        response = authenticated_client.get(url)
        
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        notification_ids = [n['id'] for n in data]
        assert notification.id in notification_ids
        assert other_user_notification.id not in notification_ids
    
    def test_list_notifications_filter_by_read_status(
        self, authenticated_client, notification, read_notification
    ):
        """Test filtering notifications by read status."""
        url = '/api/notifications/'
        
        # Filter unread
        response = authenticated_client.get(url, {'is_read': 'false'})
        assert response.status_code == status.HTTP_200_OK
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for n in data:
            assert n['is_read'] is False
        
        # Filter read
        response = authenticated_client.get(url, {'is_read': 'true'})
        assert response.status_code == status.HTTP_200_OK
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for n in data:
            assert n['is_read'] is True


@pytest.mark.django_db
class TestNotificationUnread:
    """Tests for unread notifications endpoint."""
    
    def test_list_unread_success(
        self, authenticated_client, notification, read_notification
    ):
        """Test listing unread notifications."""
        url = '/api/notifications/unread/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data or isinstance(response.data, list)
        
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        for n in data:
            assert n['is_read'] is False
    
    def test_unread_empty_list(self, authenticated_client, read_notification):
        """Test empty unread list when all are read."""
        url = '/api/notifications/unread/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestNotificationDetail:
    """Tests for notification detail endpoint."""
    
    def test_retrieve_notification_success(self, authenticated_client, notification):
        """Test retrieving notification detail."""
        url = f'/api/notifications/{notification.id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == notification.id
        assert response.data['title'] == notification.title
    
    def test_retrieve_notification_not_found(self, authenticated_client):
        """Test retrieving non-existent notification."""
        url = '/api/notifications/99999/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_retrieve_other_user_notification_forbidden(
        self, authenticated_client, other_user_notification
    ):
        """Test cannot retrieve other user's notification."""
        url = f'/api/notifications/{other_user_notification.id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestMarkNotificationRead:
    """Tests for marking notification as read."""
    
    def test_mark_as_read_success(self, authenticated_client, notification):
        """Test marking notification as read."""
        url = f'/api/notifications/{notification.id}/read/'
        response = authenticated_client.patch(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] is True
        assert response.data['read_at'] is not None
        
        notification.refresh_from_db()
        assert notification.is_read is True
    
    def test_mark_already_read(self, authenticated_client, read_notification):
        """Test marking already read notification."""
        url = f'/api/notifications/{read_notification.id}/read/'
        response = authenticated_client.patch(url)
        
        # Should still succeed
        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_read'] is True
    
    def test_mark_other_user_notification(
        self, authenticated_client, other_user_notification
    ):
        """Test cannot mark other user's notification."""
        url = f'/api/notifications/{other_user_notification.id}/read/'
        response = authenticated_client.patch(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMarkAllNotificationsRead:
    """Tests for marking all notifications as read."""
    
    def test_mark_all_as_read_success(
        self, authenticated_client, notification, user, notification_type
    ):
        """Test marking all notifications as read."""
        # Create multiple unread notifications
        Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title='Another notification',
            content='Another content'
        )
        
        url = '/api/notifications/read-all/'
        response = authenticated_client.patch(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'updated_count' in response.data
        
        # Verify all are marked read
        unread_count = Notification.objects.filter(
            user=user, is_read=False
        ).count()
        assert unread_count == 0


@pytest.mark.django_db
class TestDeleteNotification:
    """Tests for deleting notifications."""
    
    def test_delete_notification_success(self, authenticated_client, notification):
        """Test deleting a notification."""
        url = f'/api/notifications/{notification.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Notification.objects.filter(id=notification.id).exists()
    
    def test_delete_other_user_notification(
        self, authenticated_client, other_user_notification
    ):
        """Test cannot delete other user's notification."""
        url = f'/api/notifications/{other_user_notification.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestClearAllNotifications:
    """Tests for clearing all notifications."""
    
    def test_clear_all_success(
        self, authenticated_client, notification, read_notification, user
    ):
        """Test clearing all notifications."""
        url = '/api/notifications/clear-all/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'deleted_count' in response.data
        
        # Verify all are deleted
        count = Notification.objects.filter(user=user).count()
        assert count == 0
    
    def test_clear_all_does_not_affect_others(
        self, authenticated_client, notification, other_user_notification
    ):
        """Test clearing does not affect other users."""
        url = '/api/notifications/clear-all/'
        authenticated_client.delete(url)
        
        # Other user's notification should still exist
        assert Notification.objects.filter(id=other_user_notification.id).exists()


@pytest.mark.django_db
class TestNotificationSettings:
    """Tests for notification settings endpoint."""
    
    def test_get_settings_success(self, authenticated_client):
        """Test getting notification settings."""
        url = '/api/notifications/settings/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'email_notifications' in response.data
        assert 'push_notifications' in response.data


@pytest.mark.django_db
class TestNotificationCount:
    """Tests for notification count endpoint."""
    
    def test_get_unread_count(
        self, authenticated_client, notification, read_notification
    ):
        """Test getting unread notification count."""
        url = '/api/notifications/count/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'unread_count' in response.data
        assert response.data['unread_count'] >= 1
