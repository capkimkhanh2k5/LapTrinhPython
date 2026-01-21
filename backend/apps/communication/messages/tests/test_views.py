# MessageThread ViewSet Tests

import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.communication.message_threads.models import MessageThread
from apps.communication.messages.models import Message
from apps.communication.message_participants.models import MessageParticipant

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
def third_user(db):
    """Create a third test user."""
    return User.objects.create_user(
        email='thirduser@example.com',
        password='testpass123',
        full_name='Third User'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Create authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


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


@pytest.fixture
def other_thread(db, other_user, third_user):
    """Create a thread user is not part of."""
    thread = MessageThread.objects.create(
        subject='Other Thread'
    )
    MessageParticipant.objects.create(thread=thread, user=other_user)
    MessageParticipant.objects.create(thread=thread, user=third_user)
    return thread


@pytest.mark.django_db
class TestMessageThreadList:
    """Tests for listing message threads."""
    
    def test_list_threads_success(self, authenticated_client, message_thread):
        """Test listing threads returns user's threads."""
        url = '/api/messages/threads/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_threads_unauthenticated(self, api_client):
        """Test listing threads requires authentication."""
        url = '/api/messages/threads/'
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_list_threads_only_participating(
        self, authenticated_client, message_thread, other_thread
    ):
        """Test user only sees threads they participate in."""
        url = '/api/messages/threads/'
        response = authenticated_client.get(url)
        
        # Handle both paginated and non-paginated responses
        data = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        thread_ids = [t['id'] for t in data]
        assert message_thread.id in thread_ids
        assert other_thread.id not in thread_ids


@pytest.mark.django_db
class TestMessageThreadCreate:
    """Tests for creating message threads."""
    
    def test_create_thread_success(self, authenticated_client, other_user):
        """Test creating a new thread."""
        url = '/api/messages/threads/'
        data = {
            'participant_ids': [other_user.id],
            'subject': 'New Conversation',
            'initial_message': 'Hello!'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['subject'] == 'New Conversation'
        assert len(response.data['participants']) == 2  # Creator + other_user
    
    def test_create_thread_without_subject(self, authenticated_client, other_user):
        """Test creating thread without subject."""
        url = '/api/messages/threads/'
        data = {
            'participant_ids': [other_user.id]
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_create_thread_invalid_participant(self, authenticated_client):
        """Test creating thread with invalid participant."""
        url = '/api/messages/threads/'
        data = {
            'participant_ids': [99999],
            'subject': 'Invalid'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_thread_empty_participants(self, authenticated_client):
        """Test creating thread with empty participants."""
        url = '/api/messages/threads/'
        data = {
            'participant_ids': [],
            'subject': 'Empty'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMessageThreadDetail:
    """Tests for thread detail endpoint."""
    
    def test_retrieve_thread_success(self, authenticated_client, message_thread):
        """Test retrieving thread detail."""
        url = f'/api/messages/threads/{message_thread.id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == message_thread.id
        assert 'participants' in response.data
    
    def test_retrieve_thread_not_participant(
        self, authenticated_client, other_thread
    ):
        """Test cannot retrieve thread not participating in."""
        url = f'/api/messages/threads/{other_thread.id}/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_retrieve_thread_not_found(self, authenticated_client):
        """Test retrieving non-existent thread."""
        url = '/api/messages/threads/99999/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestMessageThreadDelete:
    """Tests for deleting/leaving threads."""
    
    def test_leave_thread_success(self, authenticated_client, message_thread, user):
        """Test leaving a thread."""
        url = f'/api/messages/threads/{message_thread.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Check user is marked as inactive in thread
        participant = MessageParticipant.objects.get(
            thread=message_thread, user=user
        )
        assert participant.is_active is False
    
    def test_leave_thread_not_participant(
        self, authenticated_client, other_thread
    ):
        """Test cannot leave thread not participating in."""
        url = f'/api/messages/threads/{other_thread.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestThreadMessages:
    """Tests for messages in thread endpoint."""
    
    def test_list_messages_success(
        self, authenticated_client, message_thread, message_in_thread
    ):
        """Test listing messages in thread."""
        url = f'/api/messages/threads/{message_thread.id}/messages/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
    
    def test_send_message_success(self, authenticated_client, message_thread):
        """Test sending a message to thread."""
        url = f'/api/messages/threads/{message_thread.id}/messages/'
        data = {
            'content': 'Hello, this is a new message!'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Hello, this is a new message!'
    
    def test_send_message_empty_content(self, authenticated_client, message_thread):
        """Test sending message with empty content."""
        url = f'/api/messages/threads/{message_thread.id}/messages/'
        data = {
            'content': ''
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_send_message_not_participant(
        self, authenticated_client, other_thread
    ):
        """Test cannot send message to thread not participating in."""
        url = f'/api/messages/threads/{other_thread.id}/messages/'
        data = {
            'content': 'Unauthorized message'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMarkThreadRead:
    """Tests for marking thread as read."""
    
    def test_mark_read_success(self, authenticated_client, message_thread, user):
        """Test marking thread as read."""
        url = f'/api/messages/threads/{message_thread.id}/read/'
        response = authenticated_client.patch(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        participant = MessageParticipant.objects.get(
            thread=message_thread, user=user
        )
        assert participant.last_read_at is not None
    
    def test_mark_read_not_participant(
        self, authenticated_client, other_thread
    ):
        """Test cannot mark thread not participating in."""
        url = f'/api/messages/threads/{other_thread.id}/read/'
        response = authenticated_client.patch(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAddParticipant:
    """Tests for adding participant to thread."""
    
    def test_add_participant_success(
        self, authenticated_client, message_thread, third_user
    ):
        """Test adding a new participant."""
        url = f'/api/messages/threads/{message_thread.id}/participants/'
        data = {'user_id': third_user.id}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # Verify participant was added
        assert MessageParticipant.objects.filter(
            thread=message_thread, user=third_user, is_active=True
        ).exists()
    
    def test_add_participant_already_exists(
        self, authenticated_client, message_thread, other_user
    ):
        """Test adding participant who is already in thread."""
        url = f'/api/messages/threads/{message_thread.id}/participants/'
        data = {'user_id': other_user.id}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_add_participant_invalid_user(
        self, authenticated_client, message_thread
    ):
        """Test adding non-existent user."""
        url = f'/api/messages/threads/{message_thread.id}/participants/'
        data = {'user_id': 99999}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRemoveParticipant:
    """Tests for removing participant from thread."""
    
    def test_remove_participant_success(
        self, authenticated_client, message_thread, other_user
    ):
        """Test removing a participant."""
        url = f'/api/messages/threads/{message_thread.id}/participants/{other_user.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify participant was deactivated
        participant = MessageParticipant.objects.get(
            thread=message_thread, user=other_user
        )
        assert participant.is_active is False
    
    def test_remove_self_from_thread(
        self, authenticated_client, message_thread, user
    ):
        """Test user can remove themselves."""
        url = f'/api/messages/threads/{message_thread.id}/participants/{user.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestMessageDelete:
    """Tests for deleting messages."""
    
    def test_delete_own_message_success(
        self, authenticated_client, message_in_thread
    ):
        """Test deleting own message."""
        url = f'/api/messages/{message_in_thread.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Message.objects.filter(id=message_in_thread.id).exists()
    
    def test_delete_other_message_forbidden(
        self, authenticated_client, message_thread, other_user
    ):
        """Test cannot delete other user's message."""
        other_message = Message.objects.create(
            thread=message_thread,
            sender=other_user,
            content='Other user message'
        )
        
        url = f'/api/messages/{other_message.id}/'
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUnreadCount:
    """Tests for unread message count endpoint."""
    
    def test_get_unread_count(self, authenticated_client):
        """Test getting unread message count."""
        url = '/api/messages/unread-count/'
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'unread_count' in response.data
