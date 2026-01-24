from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from django.test import override_settings
from apps.communication.message_threads.models import MessageThread
from apps.communication.message_participants.models import MessageParticipant
from apps.communication.messages.services.messages import send_message, ThreadCreateInput, MessageCreateInput
from apps.communication.messages.services.mongo_service import MongoChatService
import pymongo

User = get_user_model()

@override_settings(MONGO_DB_NAME='test_chat_integration_db')
class TestChatIntegration(APITestCase):
    
    def setUp(self):
        # Create Users
        self.user1 = User.objects.create_user(email="user1@test.com", password="password123", full_name="User One")
        self.user2 = User.objects.create_user(email="user2@test.com", password="password123", full_name="User Two")
        
        # Create Thread (SQL) manually or via service
        self.thread = MessageThread.objects.create(subject="Test Thread")
        MessageParticipant.objects.create(thread=self.thread, user=self.user1)
        MessageParticipant.objects.create(thread=self.thread, user=self.user2)
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)
        
        # Clean Mongo Test DB
        MongoChatService._client = None
        MongoChatService._db = None
        self._clean_mongo()

    def tearDown(self):
        self._clean_mongo()

    def _clean_mongo(self):
        from django.conf import settings
        client = pymongo.MongoClient(settings.MONGO_URI)
        client.drop_database('test_chat_integration_db')

    def test_send_message_updates_sql_metadata(self):
        """Test that sending a message updates SQL Thread's last_message fields."""
        
        # Check initial state
        self.thread.refresh_from_db()
        self.assertIsNone(self.thread.last_message_at)
        self.assertIsNone(self.thread.last_message_content)
        
        # Actions: Send Message via Service
        msg_input = MessageCreateInput(content="Hello Integration")
        send_message(self.thread.id, self.user1, msg_input)
        
        # Verify SQL Update
        self.thread.refresh_from_db()
        self.assertIsNotNone(self.thread.last_message_at)
        self.assertEqual(self.thread.last_message_content, "Hello Integration")
        
        # Verify Mongo Storage
        messages = MongoChatService.get_messages(self.thread.id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['content'], "Hello Integration")
        self.assertEqual(messages[0]['sender_id'], self.user1.id)

    def test_api_list_threads_order(self):
        """Test API lists threads ordered by last_message_at."""
        
        # Create another thread
        thread2 = MessageThread.objects.create(subject="Thread 2")
        MessageParticipant.objects.create(thread=thread2, user=self.user1)
        
        # Send message to Thread 1 (Old)
        send_message(self.thread.id, self.user1, MessageCreateInput(content="Msg 1"))
        
        # Send message to Thread 2 (New)
        send_message(thread2.id, self.user1, MessageCreateInput(content="Msg 2"))
        
        # Call API
        # Router basename is 'message-thread', app_name is 'message_threads'
        url = reverse('message_threads:message-thread-list')
        
        # If reverse fails, we debug. For now, try standard router name.
        # Check views.py -> MessageThreadViewSet
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data['results'] if 'results' in response.data else response.data
        
        self.assertEqual(len(data), 2)
        # Thread 2 should be first because it has newer message
        self.assertEqual(data[0]['id'], thread2.id)
        self.assertEqual(data[1]['id'], self.thread.id)
        
        # Verify last_message content in response
        self.assertEqual(data[0]['last_message']['content'], "Msg 2")

    def test_mongo_delete_message(self):
        """Test deleting a message via Service."""
        
        # Create message
        msg_data = MongoChatService.save_message(
            thread_id=self.thread.id,
            sender_id=self.user1.id,
            sender_name="User 1",
            sender_avatar="",
            content="To be deleted"
        )
        msg_id = msg_data['id']
        
        # Verify exists
        msgs = MongoChatService.get_messages(self.thread.id)
        self.assertEqual(len(msgs), 1)
        
        # Delete
        success = MongoChatService.delete_message(msg_id, self.user1.id)
        self.assertTrue(success)
        
        # Verify gone
        msgs = MongoChatService.get_messages(self.thread.id)
        self.assertEqual(len(msgs), 0)
