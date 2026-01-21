from rest_framework import serializers
from .models import Message
from apps.core.users.models import CustomUser


class MessageSenderSerializer(serializers.ModelSerializer):
    """Serializer cho thông tin người gửi."""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'avatar_url']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer cho đọc dữ liệu tin nhắn."""
    
    sender = MessageSenderSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id',
            'thread_id',
            'sender',
            'content',
            'attachment_url',
            'is_system_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'thread_id', 'sender', 'created_at', 'updated_at']


class MessageCreateSerializer(serializers.Serializer):
    """Serializer cho tạo tin nhắn mới."""
    
    content = serializers.CharField(max_length=5000)
    attachment_url = serializers.URLField(required=False, allow_blank=True)
    
    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty")
        return value.strip()


class AttachmentUploadSerializer(serializers.Serializer):
    """Serializer cho upload file đính kèm."""
    
    file = serializers.FileField()
    
    def validate_file(self, value):
        # 10MB limit
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Allowed extensions
        allowed_extensions = [
            'jpg', 'jpeg', 'png', 'gif', 'webp',  # Images
            'pdf', 'doc', 'docx', 'xls', 'xlsx',  # Documents
            'zip', 'rar',  # Archives
        ]
        
        ext = value.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value
