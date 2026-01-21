# Notifications Selectors
# Query functions for notifications data access

from typing import Optional
from django.db.models import QuerySet
from apps.communication.notifications.models import Notification


def list_notifications(
    user_id: int,
    is_read: Optional[bool] = None,
    notification_type_id: Optional[int] = None
) -> QuerySet:
    """
    Get list of notifications for a user with optional filters.
    
    Args:
        user_id: ID of the user
        is_read: Filter by read status (optional)
        notification_type_id: Filter by notification type (optional)
    
    Returns:
        QuerySet of notifications ordered by created_at desc
    """
    queryset = Notification.objects.filter(
        user_id=user_id
    ).select_related('notification_type')
    
    if is_read is not None:
        queryset = queryset.filter(is_read=is_read)
    
    if notification_type_id:
        queryset = queryset.filter(notification_type_id=notification_type_id)
    
    return queryset.order_by('-created_at')


def list_unread_notifications(user_id: int) -> QuerySet:
    """
    Get list of unread notifications for a user.
    
    Args:
        user_id: ID of the user
    
    Returns:
        QuerySet of unread notifications
    """
    return list_notifications(user_id, is_read=False)


def get_notification_by_id(notification_id: int) -> Optional[Notification]:
    """
    Get a notification by its ID.
    
    Args:
        notification_id: ID of the notification
    
    Returns:
        Notification object or None if not found
    """
    try:
        return Notification.objects.select_related(
            'notification_type',
            'user'
        ).get(id=notification_id)
    except Notification.DoesNotExist:
        return None


def count_unread_notifications(user_id: int) -> int:
    """
    Count unread notifications for a user.
    
    Args:
        user_id: ID of the user
    
    Returns:
        Count of unread notifications
    """
    return Notification.objects.filter(
        user_id=user_id,
        is_read=False
    ).count()


def get_notifications_by_entity(
    user_id: int,
    entity_type: str,
    entity_id: int
) -> QuerySet:
    """
    Get notifications related to a specific entity.
    
    Args:
        user_id: ID of the user
        entity_type: Type of entity (e.g., 'job', 'application')
        entity_id: ID of the entity
    
    Returns:
        QuerySet of notifications
    """
    return Notification.objects.filter(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id
    ).select_related('notification_type').order_by('-created_at')
