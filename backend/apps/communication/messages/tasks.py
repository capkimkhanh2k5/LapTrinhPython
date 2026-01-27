from celery import shared_task
from apps.communication.messages.services.mongo_service import MongoChatService
import logging

logger = logging.getLogger(__name__)

@shared_task(name="apps.communication.messages.persist_chat_message")
def persist_chat_message_task(
    thread_id: int, 
    sender_id: int, 
    sender_name: str, 
    sender_avatar: str, 
    content: str, 
    message_id: str = None,
    recipient_ids: list[int] = None
):
    """
    Task chạy background để lưu tin nhắn vào MongoDB.
    
    Args:
        thread_id: ID of the thread
        sender_id: ID of the sender
        sender_name: Name of the sender (cached)
        sender_avatar: Avatar URL of the sender (cached)
        content: Message content
        message_id: Optional message ID
        recipient_ids: List of user IDs to increment unread counters for
    """
    try:
        MongoChatService.save_message(
            thread_id=thread_id,
            sender_id=sender_id,
            sender_name=sender_name,
            sender_avatar=sender_avatar,
            content=content,
            message_id=message_id
        )
        
        # Increment unread counters if recipient_ids provided
        if recipient_ids:
            MongoChatService.increment_unread_counters(thread_id, recipient_ids)
        
        return f"Message {message_id} persisted for thread {thread_id}"
    except Exception as e:
        logger.error(f"Error persisting message: {str(e)}")
        raise e
