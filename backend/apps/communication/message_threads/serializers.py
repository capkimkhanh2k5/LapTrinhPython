# Message Thread Serializers

from rest_framework import serializers
from .models import MessageThread
from apps.communication.messages.models import Message
from apps.communication.message_participants.models import MessageParticipant
from apps.core.users.models import CustomUser


class ParticipantUserSerializer(serializers.ModelSerializer):
    """Serializer cho thông tin user trong participant."""
    
    class Meta:
        model = CustomUser
        fields = ['id', 'full_name', 'email', 'avatar_url']


class MessageParticipantSerializer(serializers.ModelSerializer):
    """Serializer cho participant của thread."""
    
    user = ParticipantUserSerializer(read_only=True)
    
    class Meta:
        model = MessageParticipant
        fields = ['id', 'user', 'joined_at', 'last_read_at', 'is_active']


class LastMessageSerializer(serializers.ModelSerializer):
    """Serializer cho tin nhắn cuối cùng của thread."""
    
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender_id', 'sender_name', 'content', 'created_at']


class MessageThreadSerializer(serializers.ModelSerializer):
    """Serializer cho đọc dữ liệu thread (List)."""
    
    last_message = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageThread
        fields = [
            'id',
            'subject',
            'job',
            'application',
            'last_message',
            'participant_count',
            'unread_count',
            'created_at',
            'updated_at',
        ]
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return LastMessageSerializer(last_msg).data
        return None
    
    def get_participant_count(self, obj):
        return obj.participants.filter(is_active=True).count()
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        
        try:
            participant = obj.participants.get(
                user_id=request.user.id,
                is_active=True
            )
            if participant.last_read_at:
                return obj.messages.filter(
                    created_at__gt=participant.last_read_at
                ).exclude(sender_id=request.user.id).count()
            return obj.messages.exclude(sender_id=request.user.id).count()
        except MessageParticipant.DoesNotExist:
            return 0


class MessageThreadDetailSerializer(serializers.ModelSerializer):
    """Serializer cho chi tiết thread với participants."""
    
    participants = MessageParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = MessageThread
        fields = [
            'id',
            'subject',
            'job',
            'application',
            'participants',
            'last_message',
            'created_at',
            'updated_at',
        ]
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return LastMessageSerializer(last_msg).data
        return None


class MessageThreadCreateSerializer(serializers.Serializer):
    """Serializer cho tạo thread mới."""
    
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of user IDs to add to the thread"
    )
    subject = serializers.CharField(max_length=255, required=False, allow_blank=True)
    job_id = serializers.IntegerField(required=False, allow_null=True)
    application_id = serializers.IntegerField(required=False, allow_null=True)
    initial_message = serializers.CharField(required=False, allow_blank=True)
    
    def validate_participant_ids(self, value):
        # Check all users exist
        existing_ids = set(
            CustomUser.objects.filter(id__in=value).values_list('id', flat=True)
        )
        invalid_ids = set(value) - existing_ids
        if invalid_ids:
            raise serializers.ValidationError(
                f"Users with IDs {list(invalid_ids)} do not exist"
            )
        return value


class AddParticipantSerializer(serializers.Serializer):
    """Serializer cho thêm participant vào thread."""
    
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        if not CustomUser.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist")
        return value
