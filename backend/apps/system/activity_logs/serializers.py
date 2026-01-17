from rest_framework import serializers
from .models import ActivityLog

class ActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    log_type_name = serializers.CharField(source='log_type.name', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = ['id', 'user_email', 'log_type_name', 'action', 'entity_type', 'entity_id', 'ip_address', 'details', 'created_at']
