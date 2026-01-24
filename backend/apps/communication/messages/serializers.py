from rest_framework import serializers
from apps.core.users.models import CustomUser


class MessageSenderSerializer(serializers.ModelSerializer):
    """Serializer cho thông tin người gửi."""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'avatar_url']



class MessageSerializer(serializers.Serializer):
    """Serializer cho đọc dữ liệu tin nhắn (Legacy/Mongo Compatible)."""
    id = serializers.CharField()
    thread_id = serializers.IntegerField()
    content = serializers.CharField()
    attachment_url = serializers.CharField(allow_null=True)
    is_system_message = serializers.BooleanField()
    created_at = serializers.CharField()
    updated_at = serializers.CharField()
    sender = MessageSenderSerializer(read_only=True)


class MongoMessageSerializer(serializers.Serializer):
    """
    Serializer specifically for MongoDB Message Dictionaries.
    Handles nested sender dict or flat fields if needed.
    """
    id = serializers.CharField()
    thread_id = serializers.IntegerField()
    content = serializers.CharField()
    attachment_url = serializers.CharField(allow_null=True, required=False)
    is_system_message = serializers.BooleanField(default=False)
    created_at = serializers.CharField()
    updated_at = serializers.CharField()
    
    # Mongo stores sender info directly in the document usually to avoid JOINs
    sender_id = serializers.IntegerField()
    sender_name = serializers.CharField()
    sender_avatar = serializers.CharField(allow_null=True, required=False)
    
    def to_representation(self, instance):
        """Custom representation to match frontend expected format (nested sender)."""
        ret = super().to_representation(instance)
        # Construct sender object from flat fields
        ret['sender'] = {
            'id': instance.get('sender_id'),
            'full_name': instance.get('sender_name'),
            'avatar_url': instance.get('sender_avatar')
        }
        return ret


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
