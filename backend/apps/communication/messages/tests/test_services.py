# Messages Services Tests

from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.communication.message_threads.models import MessageThread
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


class MessageServiceTests(TestCase):
    
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
        cls.third_user = User.objects.create_user(
            email='thirduser@example.com',
            password='testpass123',
            full_name='Third User'
        )
        
        # Create a thread
        cls.message_thread = MessageThread.objects.create(subject='Test Thread')
        MessageParticipant.objects.create(thread=cls.message_thread, user=cls.user)
        MessageParticipant.objects.create(thread=cls.message_thread, user=cls.other_user)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_create_thread_success(self, mock_mongo):
        """Test creating a thread with participants."""
        mock_mongo.save_message.return_value = {
            'id': 'mongo_id_123',
            'content': 'Hello!',
            'created_at': '2023-01-01T00:00:00'
        }
        
        data = ThreadCreateInput(
            participant_ids=[self.other_user.id],
            subject='New Thread',
            initial_message='Hello!'
        )
        
        thread = create_thread(self.user, data)
        
        self.assertIsNotNone(thread.id)
        self.assertEqual(thread.subject, 'New Thread')
        
        # Check participants
        participants = thread.participants.all()
        self.assertEqual(participants.count(), 2)
        
        participant_user_ids = [p.user_id for p in participants]
        self.assertIn(self.user.id, participant_user_ids)
        self.assertIn(self.other_user.id, participant_user_ids)
        
        # Initial message call check
        mock_mongo.save_message.assert_called_once()

    def test_create_thread_without_initial_message(self):
        """Test creating thread without initial message."""
        data = ThreadCreateInput(
            participant_ids=[self.other_user.id],
            subject='Empty Thread'
        )
        
        thread = create_thread(self.user, data)
        
        self.assertIsNotNone(thread.id)
        # No initial message, so no call to DB/Mongo for messages expected here

    def test_create_thread_creator_added(self):
        """Test creator is automatically added to participants."""
        data = ThreadCreateInput(
            participant_ids=[self.other_user.id]
        )
        
        thread = create_thread(self.user, data)
        
        # Creator should be added automatically
        self.assertTrue(MessageParticipant.objects.filter(
            thread=thread, user=self.user
        ).exists())

    def test_create_thread_invalid_participant(self):
        """Test creating thread with invalid participant."""
        data = ThreadCreateInput(
            participant_ids=[99999]
        )
        
        with self.assertRaisesRegex(ValueError, "do not exist"):
            create_thread(self.user, data)

    def test_delete_thread_success(self):
        """Test soft deleting/leaving a thread."""
        thread = MessageThread.objects.create(subject='To Delete')
        MessageParticipant.objects.create(thread=thread, user=self.user)
        MessageParticipant.objects.create(thread=thread, user=self.other_user)

        result = delete_thread(thread.id, self.user.id)
        
        self.assertTrue(result)
        
        # Check user is inactive in thread
        participant = MessageParticipant.objects.get(thread=thread, user=self.user)
        self.assertFalse(participant.is_active)
        
        # Thread and other participant still exist
        self.assertTrue(MessageThread.objects.filter(id=thread.id).exists())
        other_participant = MessageParticipant.objects.get(thread=thread, user=self.other_user)
        self.assertTrue(other_participant.is_active)

    def test_delete_thread_not_participant(self):
        """Test cannot delete thread not participating in."""
        with self.assertRaisesRegex(ValueError, "not a participant"):
            delete_thread(self.message_thread.id, self.third_user.id)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_send_message_success(self, mock_mongo):
        """Test sending a message."""
        mock_mongo.save_message.return_value = {
            'id': 'msg_123',
            'content': 'Hello World!',
            'sender_id': self.user.id,
            'thread_id': self.message_thread.id,
            'created_at': '2023-01-01'
        }
        
        data = MessageCreateInput(content='Hello World!')
        message = send_message(self.message_thread.id, self.user, data)
        
        self.assertIsNotNone(message['id'])
        self.assertEqual(message['content'], 'Hello World!')
        self.assertEqual(message['sender_id'], self.user.id)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_send_message_with_attachment(self, mock_mongo):
        """Test sending message with attachment URL."""
        mock_mongo.save_message.return_value = {
            'id': 'msg_attach',
            'content': 'Check this out',
            'attachments': 'https://example.com/file.pdf'
        }

        data = MessageCreateInput(
            content='Check this out',
            attachment_url='https://example.com/file.pdf'
        )
        
        message = send_message(self.message_thread.id, self.user, data)
        
        self.assertEqual(message['attachments'], 'https://example.com/file.pdf')

    def test_send_message_not_participant(self):
        """Test cannot send message if not participant."""
        data = MessageCreateInput(content='Unauthorized')
        
        with self.assertRaisesRegex(ValueError, "not a participant"):
            send_message(self.message_thread.id, self.third_user, data)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_send_message_updates_thread(self, mock_mongo):
        """Test sending message updates thread's updated_at."""
        mock_mongo.save_message.return_value = {'id': '1', 'content': 'New', 'created_at': 'now'}
        
        original_updated = self.message_thread.updated_at
        
        data = MessageCreateInput(content='New message')
        send_message(self.message_thread.id, self.user, data)
        
        self.message_thread.refresh_from_db()
        self.assertGreaterEqual(self.message_thread.updated_at, original_updated)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_delete_message_success(self, mock_mongo):
        """Test deleting own message."""
        mock_mongo.delete_message.return_value = True
        
        result = delete_message('msg_id_1', self.user.id)
        
        self.assertTrue(result)
        mock_mongo.delete_message.assert_called_with('msg_id_1', self.user.id)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_delete_message_not_found(self, mock_mongo):
        """Test deleting non-existent message."""
        mock_mongo.delete_message.return_value = False
        
        result = delete_message('99999', self.user.id)
        self.assertFalse(result)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_mark_thread_as_read_success(self, mock_mongo):
        """Test marking thread as read."""
        result = mark_thread_as_read(self.message_thread.id, self.user.id)
        
        self.assertTrue(result)
        
        participant = MessageParticipant.objects.get(thread=self.message_thread, user=self.user)
        self.assertIsNotNone(participant.last_read_at)
        mock_mongo.mark_read.assert_called_with(self.user.id, self.message_thread.id)

    def test_mark_thread_as_read_not_participant(self):
        """Test cannot mark thread not participating in."""
        with self.assertRaisesRegex(ValueError, "not a participant"):
            mark_thread_as_read(self.message_thread.id, self.third_user.id)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_add_participant_success(self, mock_mongo):
        """Test adding a new participant."""
        participant = add_participant(
            thread_id=self.message_thread.id,
            user_id=self.third_user.id,
            adder_id=self.user.id
        )
        
        self.assertIsNotNone(participant)
        self.assertEqual(participant.user, self.third_user)
        self.assertTrue(participant.is_active)
        
        # System message call check
        mock_mongo.save_message.assert_called()

    def test_add_participant_already_exists(self):
        """Test adding participant already in thread."""
        with self.assertRaisesRegex(ValueError, "already a participant"):
            add_participant(self.message_thread.id, self.other_user.id, self.user.id)

    def test_add_participant_reactivate(self):
        """Test re-adding inactive participant."""
        # First deactivate
        participant = MessageParticipant.objects.get(thread=self.message_thread, user=self.other_user)
        participant.is_active = False
        participant.save()
        
        # Re-add
        reactivated = add_participant(
            self.message_thread.id, self.other_user.id, self.user.id
        )
        
        self.assertTrue(reactivated.is_active)

    def test_add_participant_not_participant(self):
        """Test non-participant cannot add others."""
        new_user = User.objects.create_user(email='new@test.com', password='pw', full_name='New')
        
        with self.assertRaisesRegex(ValueError, "not a participant"):
            add_participant(self.message_thread.id, new_user.id, self.third_user.id)

    def test_add_participant_invalid_user(self):
        """Test adding non-existent user."""
        with self.assertRaisesRegex(ValueError, "does not exist"):
            add_participant(self.message_thread.id, 99999, self.user.id)

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_remove_participant_success(self, mock_mongo):
        """Test removing a participant."""
        result = remove_participant(
            thread_id=self.message_thread.id,
            user_id=self.other_user.id,
            remover_id=self.user.id
        )
        
        self.assertTrue(result)
        
        participant = MessageParticipant.objects.get(thread=self.message_thread, user=self.other_user)
        self.assertFalse(participant.is_active)
        
        # System message call check
        mock_mongo.save_message.assert_called()

    @patch('apps.communication.messages.services.messages.MongoChatService')
    def test_remove_self(self, mock_mongo):
        """Test user can remove themselves."""
        result = remove_participant(
            self.message_thread.id, self.user.id, self.user.id
        )
        
        self.assertTrue(result)
        # System message check
        mock_mongo.save_message.assert_called()

    def test_remove_participant_not_participant(self):
        """Test non-participant cannot remove others."""
        with self.assertRaisesRegex(ValueError, "not a participant"):
            remove_participant(self.message_thread.id, self.other_user.id, self.third_user.id)

    def test_remove_nonexistent_participant(self):
        """Test removing someone not in thread."""
        with self.assertRaisesRegex(ValueError, "not a participant"):
            remove_participant(self.message_thread.id, self.third_user.id, self.user.id)
