from django.db.models import QuerySet, Count, Q
from apps.communication.message_threads.models import MessageThread
from apps.communication.message_participants.models import MessageParticipant
from apps.communication.messages.services.mongo_service import MongoChatService


def list_threads(user_id: int) -> QuerySet:
    """
    Get list of message threads for a user.
    
    Args:
        user_id: ID of the user
    
    Returns:
        QuerySet of threads the user participates in, ordered by updated_at
    """
    return MessageThread.objects.filter(
        participants__user_id=user_id,
        participants__is_active=True
    ).prefetch_related(
        'participants__user'
    ).order_by('-last_message_at', '-updated_at')


def get_thread_by_id(thread_id: int, user_id: int) -> Optional[MessageThread]:
    """
    Get a thread by ID, checking user access.
    
    Args:
        thread_id: ID of the thread
        user_id: ID of the user (for access check)
    
    Returns:
        MessageThread object or None if not found or no access
    """
    try:
        thread = MessageThread.objects.prefetch_related(
            'participants__user',
        ).get(id=thread_id)
        
        # Check user is a participant
        if not thread.participants.filter(user_id=user_id, is_active=True).exists():
            return None
        
        return thread
    except MessageThread.DoesNotExist:
        return None


def list_messages(thread_id: int, user_id: int) -> Optional[QuerySet]:
    """
    Get messages in a thread.
    
    Args:
        thread_id: ID of the thread
        user_id: ID of the user (for access check)
    
    Returns:
        QuerySet of messages or None if thread not found or no access
    """
    # Check access
    if not MessageParticipant.objects.filter(
        thread_id=thread_id,
        user_id=user_id,
        is_active=True
    ).exists():
        return None
    
    # MongoDB Logic
    return MongoChatService.get_messages(thread_id=thread_id)


# get_message_by_id removed (SQL)


def count_unread_messages(user_id: int) -> int:
    """
    Count total unread messages across all threads for a user.
    TODO: Implement MongoDB aggregation for unread count.
    """
    # Placeholder for Migration phase
    return 0


def get_thread_between_users(user_ids: list[int]) -> Optional[MessageThread]:
    """
    Find existing thread between a set of users (for 1-1 or group chats).
    
    Args:
        user_ids: List of user IDs
    
    Returns:
        Existing MessageThread if found, None otherwise
    """
    # Find threads where all users are participants
    threads = MessageThread.objects.annotate(
        participant_count=Count('participants', filter=Q(participants__is_active=True))
    ).filter(
        participant_count=len(user_ids)
    )
    
    for thread in threads:
        thread_user_ids = set(
            thread.participants.filter(is_active=True).values_list('user_id', flat=True)
        )
        if thread_user_ids == set(user_ids):
            return thread
    
    return None
