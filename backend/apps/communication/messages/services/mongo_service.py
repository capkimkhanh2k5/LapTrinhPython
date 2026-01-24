from datetime import datetime
from django.conf import settings
import pymongo
from bson import ObjectId
from bson.errors import InvalidId

class MongoChatService:
    _client = None
    _db = None

    @classmethod
    def _get_db(cls):
        if cls._db is None:
            if cls._client is None:
                cls._client = pymongo.MongoClient(settings.MONGO_URI)
            cls._db = cls._client[settings.MONGO_DB_NAME]
        return cls._db

    @classmethod
    def _get_collection(cls):
        db = cls._get_db()
        return db['messages']

    @classmethod
    def save_message(cls, thread_id: int, sender_id: int, sender_name: str, sender_avatar: str, content: str, attachments=None):
        """
        Lưu tin nhắn vào MongoDB.
        """
        collection = cls._get_collection()
        
        doc = {
            "thread_id": thread_id,  # Reference SQL ID
            "sender_id": sender_id,  # Reference SQL ID
            "sender_name": sender_name, # Cache name để đỡ query lại
            "sender_avatar": sender_avatar, # Cache avatar
            "content": content,
            "attachments": attachments or [],
            "is_system_message": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = collection.insert_one(doc)
        
        # Return dict giống format cũ để Consumer dễ xử lý
        # Create a copy to avoid mutating the doc passed to insert_one
        ret_doc = doc.copy()
        ret_doc['id'] = str(result.inserted_id)
        ret_doc['created_at'] = ret_doc['created_at'].isoformat()
        ret_doc['updated_at'] = ret_doc['updated_at'].isoformat()
        
        return ret_doc

    @classmethod
    def get_messages(cls, thread_id: int, limit=50, offset=0):
        """
        Lấy danh sách tin nhắn từ MongoDB (Pagination).
        """
        collection = cls._get_collection()
        
        cursor = collection.find({"thread_id": thread_id})\
                           .sort("created_at", pymongo.DESCENDING)\
                           .skip(offset)\
                           .limit(limit)
                           
        messages = []
        for doc in cursor:
            doc['id'] = str(doc['_id']) # Convert ObjectId to string
            del doc['_id']
            if isinstance(doc.get('created_at'), datetime):
                 doc['created_at'] = doc['created_at'].isoformat()
            if isinstance(doc.get('updated_at'), datetime):
                 doc['updated_at'] = doc['updated_at'].isoformat()
            messages.append(doc)
            
        return messages[::-1]
            
    @classmethod
    def delete_message(cls, message_id: str, user_id: int):
        """
        Xóa tin nhắn (Soft delete hoặc hard delete).
        Ở đây dùng hard delete cho đơn giản, hoặc check ownership trước.
        """
        collection = cls._get_collection()
        # Verify ownership needed? Usually service handles permission?
        # Assuming sender_id verification happens in service layer or here.
        
        try:
             obj_id = ObjectId(message_id)
        except InvalidId:
             return False # Invalid ID format treated as "Not Found"

        msg = collection.find_one({"_id": obj_id})
        if not msg:
            return False # Not found
            
        if msg.get('sender_id') != user_id:
             raise ValueError("You can only delete your own messages")

        collection.delete_one({"_id": obj_id})
        return True
