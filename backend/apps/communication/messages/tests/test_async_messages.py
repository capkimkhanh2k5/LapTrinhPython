from django.test import TransactionTestCase
from unittest.mock import patch
from channels.testing import WebsocketCommunicator
from apps.core.users.models import CustomUser
from apps.communication.message_threads.models import MessageThread
from apps.communication.message_participants.models import MessageParticipant
from apps.communication.messages.consumers import ChatConsumer
from asgiref.sync import async_to_sync
from django.utils import timezone

class ChatAsyncPersistenceTest(TransactionTestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(email='chat@example.com', full_name='Chat User')
        self.thread = MessageThread.objects.create()
        self.participant = MessageParticipant.objects.create(
            thread=self.thread,
            user=self.user,
            is_active=True
        )

    @patch('apps.communication.messages.consumers.persist_chat_message_task.delay')
    def test_chat_message_triggers_task(self, mock_task):
        """Test that sending a message via WebSocket triggers the Celery task."""
        
        async def run_test():
            communicator = WebsocketCommunicator(
                ChatConsumer.as_asgi(), 
                f'/ws/chat/{self.thread.id}/'
            )
            communicator.scope['user'] = self.user
            communicator.scope['url_route'] = {'kwargs': {'thread_id': str(self.thread.id)}}
            
            connected, _ = await communicator.connect()
            if not connected:
                return False
            
            # Receive initial user_status message (self online)
            await communicator.receive_json_from()
            
            # Send message
            await communicator.send_json_to({
                'type': 'chat_message',
                'content': 'Hello Async World'
            })
            
            # Receive broadcast
            response = await communicator.receive_json_from()
            
            await communicator.disconnect()
            return response

        response = async_to_sync(run_test)()
        
        self.assertNotEqual(response, False, "Failed to connect to WebSocket")
        self.assertEqual(response['type'], 'chat_message')
        self.assertEqual(response['content'], 'Hello Async World')
        self.assertIn('message_id', response)
        
        # Verify Celery task was called
        mock_task.assert_called_once()
        args, kwargs = mock_task.call_args
        self.assertEqual(kwargs['content'], 'Hello Async World')
        self.assertEqual(kwargs['thread_id'], str(self.thread.id))
        self.assertEqual(kwargs['sender_id'], self.user.id)


