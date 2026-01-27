import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

"""Lưu tin nhắn vào database."""
from apps.communication.message_threads.models import MessageThread
from apps.communication.message_participants.models import MessageParticipant
from apps.communication.messages.services.mongo_service import MongoChatService
from apps.communication.messages.tasks import persist_chat_message_task
from bson import ObjectId


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket Consumer cho real-time chat.
    
    Kết nối: ws://domain/ws/chat/<thread_id>/
    """
    
    async def connect(self):
        """Xử lý khi client kết nối WebSocket."""
        self.thread_id = self.scope['url_route']['kwargs']['thread_id']
        self.room_group_name = f'chat_{self.thread_id}'
        self.user = self.scope.get('user')
        
        # Kiểm tra user đã authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # Kiểm tra user có quyền truy cập thread này không
        if not await self.check_thread_access():
            await self.close(code=4003)
            return
        
        # Tham gia room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Thông báo user đã online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'status': 'online',
                'timestamp': timezone.now().isoformat()
            }
        )
    
    async def disconnect(self, close_code):
        """Xử lý khi client ngắt kết nối."""
        if hasattr(self, 'room_group_name'):
            # Thông báo user đã offline
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'status': 'offline',
                    'timestamp': timezone.now().isoformat()
                }
            )
            
            # Rời khỏi room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Xử lý khi nhận tin nhắn từ client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read':
                await self.handle_read(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
    
    async def handle_chat_message(self, data):
        """Xử lý gửi tin nhắn chat."""
        content = data.get('content', '').strip()
        
        if not content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message content cannot be empty'
            }))
            return
        
        # Generate message ID immediately for fast UI feedback
        message_id = str(ObjectId())
        created_at = timezone.now().isoformat()
        
        # Update thread metadata in SQL (keep this fast)
        await self.update_thread_metadata()
        
        # Offload Storage to background worker
        persist_chat_message_task.delay(
            thread_id=self.thread_id,
            sender_id=self.user.id,
            sender_name=self.user.full_name,
            sender_avatar=getattr(self.user, 'avatar_url', None),
            content=content,
            message_id=message_id
        )
        
        # Gửi tin nhắn đến tất cả users trong room ngay lập tức
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message_id': message_id,
                'content': content,
                'sender_id': self.user.id,
                'sender_name': self.user.full_name,
                'created_at': created_at,
            }
        )
    
    async def handle_typing(self, data):
        """Xử lý thông báo đang gõ."""
        is_typing = data.get('is_typing', False)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_typing',
                'user_id': self.user.id,
                'user_name': self.user.full_name,
                'is_typing': is_typing,
            }
        )
    
    async def handle_read(self, data):
        """Xử lý đánh dấu đã đọc."""
        await self.mark_thread_as_read()
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'message_read',
                'user_id': self.user.id,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def chat_message(self, event):
        """Gửi tin nhắn chat đến WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message_id': event['message_id'],
            'content': event['content'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'created_at': event['created_at'],
        }))
    
    async def user_typing(self, event):
        """Gửi thông báo đang gõ đến WebSocket."""
        # Không gửi cho chính user đang gõ
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing'],
            }))
    
    async def user_status(self, event):
        """Gửi thông báo trạng thái user đến WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'status': event['status'],
            'timestamp': event['timestamp'],
        }))
    
    async def message_read(self, event):
        """Gửi thông báo đã đọc đến WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message_read',
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        }))
    
    @database_sync_to_async
    def check_thread_access(self):
        """Kiểm tra user có quyền truy cập thread không."""
        
        return MessageParticipant.objects.filter(
            thread_id=self.thread_id,
            user_id=self.user.id,
            is_active=True
        ).exists()
    
    @database_sync_to_async
    def update_thread_metadata(self):
        """Cập nhật thời gian update của thread trong DB chính."""
        try:
            thread = MessageThread.objects.get(id=self.thread_id)
            thread.save() # Triggers auto_now update
            return True
        except MessageThread.DoesNotExist:
            return False
    
    @database_sync_to_async
    def mark_thread_as_read(self):
        """Đánh dấu thread là đã đọc."""
        
        MessageParticipant.objects.filter(
            thread_id=self.thread_id,
            user_id=self.user.id
        ).update(last_read_at=timezone.now())
