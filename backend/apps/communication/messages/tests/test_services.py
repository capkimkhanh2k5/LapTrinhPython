# Messages Services Tests

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.communication.message_threads.models import MessageThread
from apps.communication.messages.models import Message
from apps.communication.message_participants.models import MessageParticipant
from apps.communication.messages.services.messages import (
    create_thread,
    delete_thread,
    send_message,
    delete_message,
    mark_thread_as_read,
    add_participant,
    remove_participant,
    ThreadCreateInput,
    MessageCreateInput,
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
def third_user(db):
    """Create a third test user."""
    return User.objects.create_user(
        email='thirduser@example.com',
        password='testpass123',
        full_name='Third User'
    )


@pytest.fixture
def message_thread(db, user, other_user):
    """Create a message thread with participants."""
    thread = MessageThread.objects.create(
        subject='Test Thread'
    )
    MessageParticipant.objects.create(thread=thread, user=user)
    MessageParticipant.objects.create(thread=thread, user=other_user)
    return thread


@pytest.fixture
def message_in_thread(db, message_thread, user):
    """Create a message in the thread."""
    return Message.objects.create(
        thread=message_thread,
        sender=user,
        content='Hello, this is a test message!'
    )


@pytest.mark.django_db
class TestCreateThread:
    """Tests for create_thread service."""
    
    def test_create_thread_success(self, user, other_user):
        """Test creating a thread with participants."""
        data = ThreadCreateInput(
            participant_ids=[other_user.id],
            subject='New Thread',
            initial_message='Hello!'
        )
        
        thread = create_thread(user, data)
        
        assert thread.id is not None
        assert thread.subject == 'New Thread'
        
        # Check participants
        participants = thread.participants.all()
        assert participants.count() == 2
        
        participant_user_ids = [p.user_id for p in participants]
        assert user.id in participant_user_ids
        assert other_user.id in participant_user_ids
        
        # Check initial message
        assert thread.messages.count() == 1
        assert thread.messages.first().content == 'Hello!'
    
    def test_create_thread_without_initial_message(self, user, other_user):
        """Test creating thread without initial message."""
        data = ThreadCreateInput(
            participant_ids=[other_user.id],
            subject='Empty Thread'
        )
        
        thread = create_thread(user, data)
        
        assert thread.id is not None
        assert thread.messages.count() == 0
    
    def test_create_thread_creator_added(self, user, other_user):
        """Test creator is automatically added to participants."""
        data = ThreadCreateInput(
            participant_ids=[other_user.id]  # Only other_user
        )
        
        thread = create_thread(user, data)
        
        # Creator should be added automatically
        assert MessageParticipant.objects.filter(
            thread=thread, user=user
        ).exists()
    
    def test_create_thread_invalid_participant(self, user):
        """Test creating thread with invalid participant."""
        data = ThreadCreateInput(
            participant_ids=[99999]
        )
        
        with pytest.raises(ValueError, match="do not exist"):
            create_thread(user, data)


@pytest.mark.django_db
class TestDeleteThread:
    """Tests for delete_thread service (soft delete)."""
    
    def test_delete_thread_success(self, message_thread, user):
        """Test soft deleting/leaving a thread."""
        result = delete_thread(message_thread.id, user.id)
        
        assert result is True
        
        # Check user is inactive in thread
        participant = MessageParticipant.objects.get(
            thread=message_thread, user=user
        )
        assert participant.is_active is False
        
        # Thread and other participant still exist
        assert MessageThread.objects.filter(id=message_thread.id).exists()
        other_participant = MessageParticipant.objects.get(
            thread=message_thread,
            is_active=True
        )
        assert other_participant is not None
    
    def test_delete_thread_not_participant(self, message_thread, third_user):
        """Test cannot delete thread not participating in."""
        with pytest.raises(ValueError, match="not a participant"):
            delete_thread(message_thread.id, third_user.id)


@pytest.mark.django_db
class TestSendMessage:
    """Tests for send_message service."""
    
    def test_send_message_success(self, message_thread, user):
        """Test sending a message."""
        data = MessageCreateInput(content='Hello World!')
        
        message = send_message(message_thread.id, user, data)
        
        assert message.id is not None
        assert message.content == 'Hello World!'
        assert message.sender == user
        assert message.thread == message_thread
    
    def test_send_message_with_attachment(self, message_thread, user):
        """Test sending message with attachment URL."""
        data = MessageCreateInput(
            content='Check this out',
            attachment_url='https://example.com/file.pdf'
        )
        
        message = send_message(message_thread.id, user, data)
        
        assert message.attachment_url == 'https://example.com/file.pdf'
    
    def test_send_message_not_participant(self, message_thread, third_user):
        """Test cannot send message if not participant."""
        data = MessageCreateInput(content='Unauthorized')
        
        with pytest.raises(ValueError, match="not a participant"):
            send_message(message_thread.id, third_user, data)
    
    def test_send_message_updates_thread(self, message_thread, user):
        """Test sending message updates thread's updated_at."""
        original_updated = message_thread.updated_at
        
        data = MessageCreateInput(content='New message')
        send_message(message_thread.id, user, data)
        
        message_thread.refresh_from_db()
        assert message_thread.updated_at >= original_updated


@pytest.mark.django_db
class TestDeleteMessage:
    """Tests for delete_message service."""
    
    def test_delete_message_success(self, message_in_thread, user):
        """Test deleting own message."""
        message_id = message_in_thread.id
        
        result = delete_message(message_id, user.id)
        
        assert result is True
        assert not Message.objects.filter(id=message_id).exists()
    
    def test_delete_message_not_sender(self, message_in_thread, other_user):
        """Test cannot delete other's message."""
        with pytest.raises(ValueError, match="only delete your own"):
            delete_message(message_in_thread.id, other_user.id)
    
    def test_delete_message_not_found(self, user):
        """Test deleting non-existent message."""
        with pytest.raises(ValueError, match="not found"):
            delete_message(99999, user.id)


@pytest.mark.django_db
class TestMarkThreadAsRead:
    """Tests for mark_thread_as_read service."""
    
    def test_mark_as_read_success(self, message_thread, user):
        """Test marking thread as read."""
        result = mark_thread_as_read(message_thread.id, user.id)
        
        assert result is True
        
        participant = MessageParticipant.objects.get(
            thread=message_thread, user=user
        )
        assert participant.last_read_at is not None
    
    def test_mark_as_read_not_participant(self, message_thread, third_user):
        """Test cannot mark thread not participating in."""
        with pytest.raises(ValueError, match="not a participant"):
            mark_thread_as_read(message_thread.id, third_user.id)


@pytest.mark.django_db
class TestAddParticipant:
    """Tests for add_participant service."""
    
    def test_add_participant_success(self, message_thread, user, third_user):
        """Test adding a new participant."""
        participant = add_participant(
            thread_id=message_thread.id,
            user_id=third_user.id,
            adder_id=user.id
        )
        
        assert participant is not None
        assert participant.user == third_user
        assert participant.is_active is True
        
        # System message should be created
        system_messages = Message.objects.filter(
            thread=message_thread,
            is_system_message=True
        )
        assert system_messages.exists()
    
    def test_add_participant_already_exists(self, message_thread, user, other_user):
        """Test adding participant already in thread."""
        with pytest.raises(ValueError, match="already a participant"):
            add_participant(message_thread.id, other_user.id, user.id)
    
    def test_add_participant_reactivate(
        self, message_thread, user, other_user
    ):
        """Test re-adding inactive participant."""
        # First deactivate
        participant = MessageParticipant.objects.get(
            thread=message_thread, user=other_user
        )
        participant.is_active = False
        participant.save()
        
        # Re-add
        reactivated = add_participant(
            message_thread.id, other_user.id, user.id
        )
        
        assert reactivated.is_active is True
    
    def test_add_participant_not_participant(
        self, message_thread, third_user, other_user
    ):
        """Test non-participant cannot add others."""
        new_user = User.objects.create_user(
            email='newuser@example.com',
            password='testpass123',
            full_name='New User'
        )
        
        with pytest.raises(ValueError, match="not a participant"):
            add_participant(message_thread.id, new_user.id, third_user.id)
    
    def test_add_participant_invalid_user(self, message_thread, user):
        """Test adding non-existent user."""
        with pytest.raises(ValueError, match="does not exist"):
            add_participant(message_thread.id, 99999, user.id)


@pytest.mark.django_db
class TestRemoveParticipant:
    """Tests for remove_participant service."""
    
    def test_remove_participant_success(self, message_thread, user, other_user):
        """Test removing a participant."""
        result = remove_participant(
            thread_id=message_thread.id,
            user_id=other_user.id,
            remover_id=user.id
        )
        
        assert result is True
        
        participant = MessageParticipant.objects.get(
            thread=message_thread, user=other_user
        )
        assert participant.is_active is False
        
        # System message should be created
        system_messages = Message.objects.filter(
            thread=message_thread,
            is_system_message=True
        )
        assert system_messages.exists()
    
    def test_remove_self(self, message_thread, user):
        """Test user can remove themselves."""
        result = remove_participant(
            message_thread.id, user.id, user.id
        )
        
        assert result is True
        
        # Check system message says "left"
        system_message = Message.objects.filter(
            thread=message_thread,
            is_system_message=True
        ).first()
        assert "left" in system_message.content
    
    def test_remove_participant_not_participant(
        self, message_thread, third_user, other_user
    ):
        """Test non-participant cannot remove others."""
        with pytest.raises(ValueError, match="not a participant"):
            remove_participant(message_thread.id, other_user.id, third_user.id)
    
    def test_remove_nonexistent_participant(self, message_thread, user, third_user):
        """Test removing someone not in thread."""
        with pytest.raises(ValueError, match="not a participant"):
            remove_participant(message_thread.id, third_user.id, user.id)
