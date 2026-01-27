from rest_framework import serializers
from .models import Notification
from apps.communication.notification_types.models import NotificationType


class NotificationTypeSerializer(serializers.ModelSerializer):
    """Serializer cho loại thông báo."""
    
    class Meta:
        model = NotificationType
        fields = ['id', 'type_name', 'template']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer cho đọc dữ liệu thông báo (List/Detail)."""
    
    notification_type = NotificationTypeSerializer(read_only=True)
    notification_type_name = serializers.CharField(
        source='notification_type.type_name',
        read_only=True
    )
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'notification_type',
            'notification_type_name',
            'title',
            'content',
            'link',
            'entity_type',
            'entity_id',
            'is_read',
            'read_at',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class NotificationCreateSerializer(serializers.Serializer):
    """Serializer cho tạo thông báo mới."""
    
    notification_type_id = serializers.IntegerField()
    title = serializers.CharField(max_length=255)
    content = serializers.CharField()
    link = serializers.URLField(required=False, allow_blank=True)
    entity_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    entity_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_notification_type_id(self, value):
        if not NotificationType.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Notification type does not exist or is inactive")
        return value


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer cho đánh dấu đã đọc (Bulk)."""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of notification IDs to mark as read"
    )
    read_all = serializers.BooleanField(
        default=False,
        help_text="Set to true to mark all notifications as read"
    )

    def validate(self, data):
        if not data.get('read_all') and not data.get('notification_ids'):
            raise serializers.ValidationError("Either 'notification_ids' or 'read_all' must be provided.")
        return data


class NotificationSettingSerializer(serializers.Serializer):
    """Serializer cho cài đặt thông báo."""
    
    email_notifications = serializers.BooleanField(default=True)
    push_notifications = serializers.BooleanField(default=True)
    job_alerts = serializers.BooleanField(default=True)
    application_updates = serializers.BooleanField(default=True)
    message_notifications = serializers.BooleanField(default=True)
