import os
import uuid

from typing import Optional

from django.utils import timezone
from django.db import transaction
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings

from pydantic import BaseModel
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.communication.message_threads.models import MessageThread
from apps.communication.message_participants.models import MessageParticipant
from apps.communication.messages.services.mongo_service import MongoChatService
from apps.core.users.models import CustomUser


class ThreadCreateInput(BaseModel):
    """Input model for creating a thread."""
    
    participant_ids: list[int]
    subject: Optional[str] = None
    job_id: Optional[int] = None
    application_id: Optional[int] = None
    initial_message: Optional[str] = None
    
    class Config:
        extra = 'forbid'


class MessageCreateInput(BaseModel):
    """Input model for creating a message."""
    
    content: str
    attachment_url: Optional[str] = None
    
    class Config:
        extra = 'forbid'


@transaction.atomic
def create_thread(
    creator: CustomUser,
    data: ThreadCreateInput
) -> MessageThread:
    """
    Create a new message thread.
    
    Args:
        creator: User creating the thread
        data: Thread data
    
    Returns:
        Created MessageThread object
    
    Raises:
        ValueError: If participants are invalid
    """
    # Ensure creator is in participant list
    all_participant_ids = list(set(data.participant_ids + [creator.id]))
    
    # Validate all participants exist
    existing_users = CustomUser.objects.filter(id__in=all_participant_ids)
    if existing_users.count() != len(all_participant_ids):
        raise ValueError("One or more participants do not exist")
    
    # Create thread
    thread = MessageThread.objects.create(
        subject=data.subject or '',
        job_id=data.job_id,
        application_id=data.application_id
    )
    
    # Add participants
    for user_id in all_participant_ids:
        MessageParticipant.objects.create(
            thread=thread,
            user_id=user_id
        )
    
    # Send initial message if provided
    if data.initial_message:
        send_message(
            thread_id=thread.id,
            sender=creator,
            data=MessageCreateInput(content=data.initial_message)
        )
    
    return thread


def delete_thread(thread_id: int, user_id: int) -> bool:
    """
    Delete a thread (soft delete - remove user from participants).
    
    Args:
        thread_id: ID of the thread
        user_id: ID of the user
    
    Returns:
        True if deleted successfully
    
    Raises:
        ValueError: If thread not found or user is not a participant
    """
    try:
        participant = MessageParticipant.objects.get(
            thread_id=thread_id,
            user_id=user_id
        )
    except MessageParticipant.DoesNotExist:
        raise ValueError("Thread not found or you are not a participant")
    
    # Soft delete - mark as inactive
    participant.is_active = False
    participant.save(update_fields=['is_active'])
    
    return True


def send_message(
    thread_id: int,
    sender: CustomUser,
    data: MessageCreateInput
) -> Message:
    """
    Send a message to a thread.
    
    Args:
        thread_id: ID of the thread
        sender: User sending the message
        data: Message data
    
    Returns:
        Created Message object
    
    Raises:
        ValueError: If thread not found or sender is not a participant
    """
    # Check sender is a participant
    if not MessageParticipant.objects.filter(
        thread_id=thread_id,
        user_id=sender.id,
        is_active=True
    ).exists():
        raise ValueError("You are not a participant in this thread")
    
    # Create message (MongoDB)
    message_data = MongoChatService.save_message(
        thread_id=thread_id,
        sender_id=sender.id,
        sender_name=sender.full_name,
        sender_avatar=sender.avatar_url,
        content=data.content,
        attachments=data.attachment_url
    )
    message = message_data # It's a dict
    
    # Update thread updated_at AND last_message metadata
    MessageThread.objects.filter(id=thread_id).update(
        updated_at=timezone.now(),
        last_message_at=timezone.now(),
        last_message_content=data.content[:500] if data.content else "Attachment"
    )
    
    # Send real-time notification via WebSocket
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'chat_{thread_id}',
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'content': message.content,
                    'sender_id': sender.id,
                    'sender_name': sender.full_name,
                    'created_at': message.created_at.isoformat(),
                }
            )
    except Exception:
        # WebSocket notification failed, but message was saved
        pass
    
    return message


def delete_message(message_id: int, user_id: int) -> bool:
    """
    Delete a message.
    
    Args:
        message_id: ID of the message
        user_id: ID of the user (must be sender)
    
    Returns:
        True if deleted successfully
    
    Raises:
        ValueError: If message not found or user is not the sender
    """
    # MongoDB Delete
    return MongoChatService.delete_message(message_id, user_id)


def mark_thread_as_read(thread_id: int, user_id: int) -> bool:
    """
    Mark a thread as read for a user.
    
    Args:
        thread_id: ID of the thread
        user_id: ID of the user
    
    Returns:
        True if marked successfully
    
    Raises:
        ValueError: If thread not found or user is not a participant
    """
    try:
        participant = MessageParticipant.objects.get(
            thread_id=thread_id,
            user_id=user_id,
            is_active=True
        )
    except MessageParticipant.DoesNotExist:
        raise ValueError("Thread not found or you are not a participant")
    
    participant.last_read_at = timezone.now()
    participant.save(update_fields=['last_read_at'])
    
    return True


def add_participant(
    thread_id: int,
    user_id: int,
    adder_id: int
) -> MessageParticipant:
    """
    Add a participant to a thread.
    
    Args:
        thread_id: ID of the thread
        user_id: ID of user to add
        adder_id: ID of user adding (must be existing participant)
    
    Returns:
        Created MessageParticipant object
    
    Raises:
        ValueError: If thread not found, adder is not participant, or user doesn't exist
    """
    # Check adder is a participant
    if not MessageParticipant.objects.filter(
        thread_id=thread_id,
        user_id=adder_id,
        is_active=True
    ).exists():
        raise ValueError("You are not a participant in this thread")
    
    # Check user exists
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        raise ValueError("User does not exist")
    
    # Check if already a participant
    existing = MessageParticipant.objects.filter(
        thread_id=thread_id,
        user_id=user_id
    ).first()
    
    if existing:
        if existing.is_active:
            raise ValueError("User is already a participant")
        # Re-activate
        existing.is_active = True
        existing.save(update_fields=['is_active'])
        return existing
    
    # Create new participant
    participant = MessageParticipant.objects.create(
        thread_id=thread_id,
        user_id=user_id
    )
    
    # Send system message
    thread = MessageThread.objects.get(id=thread_id)
    adder = CustomUser.objects.get(id=adder_id)
    # Send system message (MongoDB)
    MongoChatService.save_message(
        thread_id=thread_id,
        sender_id=adder_id,
        sender_name=adder.full_name,
        sender_avatar=adder.avatar_url,
        content=f"{adder.full_name} added {user.full_name} to the conversation"
    )
    
    return participant


def remove_participant(
    thread_id: int,
    user_id: int,
    remover_id: int
) -> bool:
    """
    Remove a participant from a thread.
    
    Args:
        thread_id: ID of the thread
        user_id: ID of user to remove
        remover_id: ID of user removing (must be existing participant)
    
    Returns:
        True if removed successfully
    
    Raises:
        ValueError: If thread not found or user is not a participant
    """
    # Check remover is a participant
    if not MessageParticipant.objects.filter(
        thread_id=thread_id,
        user_id=remover_id,
        is_active=True
    ).exists():
        raise ValueError("You are not a participant in this thread")
    
    try:
        participant = MessageParticipant.objects.get(
            thread_id=thread_id,
            user_id=user_id,
            is_active=True
        )
    except MessageParticipant.DoesNotExist:
        raise ValueError("User is not a participant in this thread")
    
    # Soft delete
    participant.is_active = False
    participant.save(update_fields=['is_active'])
    
    # Send system message
    thread = MessageThread.objects.get(id=thread_id)
    remover = CustomUser.objects.get(id=remover_id)
    removed_user = CustomUser.objects.get(id=user_id)
    
    if remover_id == user_id:
        content = f"{remover.full_name} left the conversation"
    else:
        content = f"{remover.full_name} removed {removed_user.full_name} from the conversation"
    
    # Send system message (MongoDB)
    MongoChatService.save_message(
        thread_id=thread_id,
        sender_id=remover_id,
        sender_name=remover.full_name,
        sender_avatar=remover.avatar_url,
        content=content
    )
    
    return True


def upload_attachment(file: UploadedFile, user: CustomUser) -> str:
    """
    Upload a file attachment.
    
    Args:
        file: Uploaded file
        user: User uploading
    
    Returns:
        URL of the uploaded file
    
    Note: This is a placeholder - actual implementation depends on
    your file storage backend (local, S3, Cloudinary, etc.)
    """
    
    # Generate unique filename
    ext = file.name.split('.')[-1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    
    # Save to media directory
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'message_attachments')
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    # Return URL
    return f"{settings.MEDIA_URL}message_attachments/{filename}"
