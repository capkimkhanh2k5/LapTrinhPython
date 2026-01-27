from typing import Optional
from django.utils import timezone
from django.db import transaction
from pydantic import BaseModel

from apps.communication.notifications.models import Notification
from apps.communication.notification_types.models import NotificationType
from apps.core.users.models import CustomUser


class NotificationCreateInput(BaseModel):
    """Input model for creating a notification."""
    
    notification_type_id: int
    title: str
    content: str
    link: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    
    class Config:
        extra = 'forbid'


def create_notification(
    user: CustomUser,
    data: NotificationCreateInput
) -> Notification:
    """
    Create a new notification for a user.
    
    Args:
        user: User to receive the notification
        data: Notification data
    
    Returns:
        Created Notification object
    
    Raises:
        ValueError: If notification type is invalid
    """
    try:
        notification_type = NotificationType.objects.get(
            id=data.notification_type_id,
            is_active=True
        )
    except NotificationType.DoesNotExist:
        raise ValueError("Notification type does not exist or is inactive")
    
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=data.title,
        content=data.content,
        link=data.link or '',
        entity_type=data.entity_type or '',
        entity_id=data.entity_id
    )
    
    return notification


def mark_as_read(notification_id: int, user_id: int) -> Notification:
    """
    Mark a notification as read.
    
    Args:
        notification_id: ID of the notification
        user_id: ID of the user (for ownership check)
    
    Returns:
        Updated Notification object
    
    Raises:
        ValueError: If notification not found or not owned by user
    """
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user_id=user_id
        )
    except Notification.DoesNotExist:
        raise ValueError("Notification not found")
    
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
    
    return notification


def mark_all_as_read(user_id: int) -> int:
    """
    Mark all notifications as read for a user.
    """
    updated_count = Notification.objects.filter(
        user_id=user_id,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return updated_count


def bulk_mark_as_read(notification_ids: list[int], user_id: int) -> int:
    """
    Mark multiple notifications as read for a user.
    """
    updated_count = Notification.objects.filter(
        id__in=notification_ids,
        user_id=user_id,
        is_read=False
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return updated_count


def delete_notification(notification_id: int, user_id: int) -> bool:
    """
    Delete a notification.
    
    Args:
        notification_id: ID of the notification
        user_id: ID of the user (for ownership check)
    
    Returns:
        True if deleted successfully
    
    Raises:
        ValueError: If notification not found or not owned by user
    """
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user_id=user_id
        )
    except Notification.DoesNotExist:
        raise ValueError("Notification not found")
    
    notification.delete()
    return True


def clear_all_notifications(user_id: int) -> int:
    """
    Delete all notifications for a user.
    
    Args:
        user_id: ID of the user
    
    Returns:
        Number of notifications deleted
    """
    deleted_count, _ = Notification.objects.filter(
        user_id=user_id
    ).delete()
    
    return deleted_count


def send_notification(
    user_id: int,
    notification_type_name: str,
    title: str,
    content: str,
    link: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None
) -> Optional[Notification]:
    """
    Convenience function to send a notification by type name.
    
    Args:
        user_id: ID of the user to receive notification
        notification_type_name: Name of the notification type
        title: Notification title
        content: Notification content
        link: Optional link
        entity_type: Optional entity type
        entity_id: Optional entity ID
    
    Returns:
        Created Notification or None if user/type not found
    """
    try:
        user = CustomUser.objects.get(id=user_id)
        notification_type = NotificationType.objects.get(
            type_name=notification_type_name,
            is_active=True
        )
    except (CustomUser.DoesNotExist, NotificationType.DoesNotExist):
        return None
    
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        content=content,
        link=link or '',
        entity_type=entity_type or '',
        entity_id=entity_id
    )


def send_bulk_notifications(
    user_ids: list[int],
    notification_type_name: str,
    title: str,
    content: str,
    link: Optional[str] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None
) -> list[Notification]:
    """
    Send notification to multiple users.
    
    Args:
        user_ids: List of user IDs
        notification_type_name: Name of the notification type
        title: Notification title
        content: Notification content
        link: Optional link
        entity_type: Optional entity type
        entity_id: Optional entity ID
    
    Returns:
        List of created Notifications
    """
    try:
        notification_type = NotificationType.objects.get(
            type_name=notification_type_name,
            is_active=True
        )
    except NotificationType.DoesNotExist:
        return []
    
    users = CustomUser.objects.filter(id__in=user_ids)
    
    notifications = [
        Notification(
            user=user,
            notification_type=notification_type,
            title=title,
            content=content,
            link=link or '',
            entity_type=entity_type or '',
            entity_id=entity_id
        )
        for user in users
    ]
    
    return Notification.objects.bulk_create(notifications)
