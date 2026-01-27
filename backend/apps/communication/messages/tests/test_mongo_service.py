from django.test import SimpleTestCase, override_settings
from unittest.mock import patch, MagicMock
from datetime import datetime
from apps.communication.messages.services.mongo_service import MongoChatService

@override_settings(MONGO_DB_NAME='test_chat_unit_db')
class TestMongoChatService(SimpleTestCase):
    
    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_save_message_structure(self, mock_client):
        """Test that save_message formats the document correctly."""
        # Setup Mock
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock Insert Result
        mock_result = MagicMock()
        mock_result.inserted_id = '123456789012'
        mock_collection.insert_one.return_value = mock_result
        
        # Reset singleton to ensure mock is used
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Execute
        result = MongoChatService.save_message(
            thread_id=1,
            sender_id=99,
            sender_name="Test User",
            sender_avatar="http://avatar.com",
            content="Hello World"
        )
        
        # Verify call arguments
        mock_collection.insert_one.assert_called_once()
        call_args = mock_collection.insert_one.call_args[0][0]
        
        self.assertEqual(call_args['thread_id'], 1)
        self.assertEqual(call_args['sender_id'], 99)
        self.assertEqual(call_args['content'], "Hello World")
        self.assertEqual(call_args['is_system_message'], False)
        self.assertIsInstance(call_args['created_at'], datetime)
        
        # Verify return value
        self.assertEqual(result['id'], '123456789012')
        self.assertIsInstance(result['created_at'], str) # Should be converted to ISO format

    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_get_messages_sorting(self, mock_client):
        """Test that get_messages sorts and formats correctly."""
        # Setup Mock
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Mock Find Cursor
        mock_cursor = MagicMock()
        # Chaining calls: find().sort().skip().limit()
        mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        
        # Mock Data from Mongo
        mock_docs = [
            {
                '_id': 'msg2',
                'content': 'Message 2',
                'created_at': datetime(2023, 1, 1, 10, 1)
            },
            {
                '_id': 'msg1',
                'content': 'Message 1',
                'created_at': datetime(2023, 1, 1, 10, 0)
            }
        ]
        # Iterate over cursor returns docs
        mock_cursor.__iter__.return_value = iter(mock_docs)
        
        # Reset singleton
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Execute
        messages = MongoChatService.get_messages(thread_id=1)
        
        # Verify Sort Call
        # Should sort by created_at DESC
        mock_cursor.sort.assert_called_with("created_at", -1) # pymongo.DESCENDING is -1
        
        # Verify Result Reversal (Ascending for UI)
        self.assertEqual(messages[0]['content'], 'Message 1') # Oldest first
        self.assertEqual(messages[1]['content'], 'Message 2') # Newest last

    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_delete_message_success(self, mock_client):
        """Test deleting a message successfully."""
        # Setup Mock
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Reset singleton
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Mock Find Result (Return a valid doc)
        mock_collection.find_one.return_value = {'_id': 'valid_id', 'sender_id': 1}
        
        # Execute
        # Note: We must mock ObjectId to verify it's called, but here we test logic flow
        # We pass sender_id=1 to match mock doc
        result = MongoChatService.delete_message('123456789012345678901234', 1) 
        
        # Verify
        self.assertTrue(result)
        mock_collection.delete_one.assert_called_once()
        
    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_delete_message_invalid_id(self, mock_client):
        """Test handling of invalid ObjectId in delete_message."""
        # Setup Mock
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection
        
        # Reset singleton
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Execute with invalid ID (length != 24)
        result = MongoChatService.delete_message('invalid-id', 1) 
        
        # Verify
        self.assertFalse(result)
        # Should NOT call find_one or delete_one because validation catches it first (if logic correct)
        # Wait, my logic is try ObjectId(), catch InvalidId -> return False.
        # So it shouldn't reach find_one if I passed a truly invalid ID string.
        mock_collection.find_one.assert_not_called()
        mock_collection.delete_one.assert_not_called()


@override_settings(MONGO_DB_NAME='test_chat_unit_db')
class TestUnreadCounters(SimpleTestCase):
    """Test cases for MongoDB Unread Counters feature."""
    
    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_increment_unread_counters(self, mock_client):
        """Test that increment_unread_counters calls bulk_write correctly."""
        # Setup Mock
        mock_db = MagicMock()
        mock_counters_col = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_counters_col
        
        # Reset singleton
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Execute
        MongoChatService.increment_unread_counters(
            thread_id=10,
            recipient_ids=[1, 2, 3]
        )
        
        # Verify bulk_write was called
        mock_counters_col.bulk_write.assert_called_once()
        
        # Verify operations structure
        call_args = mock_counters_col.bulk_write.call_args[0][0]
        self.assertEqual(len(call_args), 3)  # 3 recipients = 3 operations

    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_increment_unread_counters_empty_list(self, mock_client):
        """Test that increment_unread_counters does nothing for empty list."""
        # Setup Mock
        mock_db = MagicMock()
        mock_counters_col = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_counters_col
        
        # Reset singleton
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Execute with empty list
        MongoChatService.increment_unread_counters(
            thread_id=10,
            recipient_ids=[]
        )
        
        # bulk_write should NOT be called
        mock_counters_col.bulk_write.assert_not_called()

    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_mark_read_resets_count(self, mock_client):
        """Test that mark_read resets count to 0."""
        # Setup Mock
        mock_db = MagicMock()
        mock_counters_col = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_counters_col
        
        # Reset singleton
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Execute
        MongoChatService.mark_read(user_id=5, thread_id=10)
        
        # Verify update_one was called with correct filter and update
        mock_counters_col.update_one.assert_called_once()
        call_args = mock_counters_col.update_one.call_args
        
        # Check filter
        filter_arg = call_args[0][0]
        self.assertEqual(filter_arg['user_id'], 5)
        self.assertEqual(filter_arg['thread_id'], 10)
        
        # Check update
        update_arg = call_args[0][1]
        self.assertEqual(update_arg['$set']['count'], 0)

    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_get_total_unread_count(self, mock_client):
        """Test aggregation for total unread count."""
        # Setup Mock
        mock_db = MagicMock()
        mock_counters_col = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_counters_col
        
        # Mock aggregation result
        mock_counters_col.aggregate.return_value = [{'_id': None, 'total': 15}]
        
        # Reset singleton
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Execute
        result = MongoChatService.get_total_unread_count(user_id=5)
        
        # Verify result
        self.assertEqual(result, 15)
        
        # Verify aggregation pipeline
        mock_counters_col.aggregate.assert_called_once()
        pipeline = mock_counters_col.aggregate.call_args[0][0]
        self.assertEqual(pipeline[0]['$match']['user_id'], 5)
        self.assertEqual(pipeline[1]['$group']['_id'], None)

    @patch('apps.communication.messages.services.mongo_service.pymongo.MongoClient')
    def test_get_total_unread_count_no_data(self, mock_client):
        """Test aggregation returns 0 when no data."""
        # Setup Mock
        mock_db = MagicMock()
        mock_counters_col = MagicMock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_counters_col
        
        # Mock empty aggregation result
        mock_counters_col.aggregate.return_value = []
        
        # Reset singleton
        MongoChatService._client = None
        MongoChatService._db = None
        
        # Execute
        result = MongoChatService.get_total_unread_count(user_id=999)
        
        # Verify returns 0
        self.assertEqual(result, 0)
