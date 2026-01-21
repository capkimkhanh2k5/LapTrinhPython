from rest_framework import serializers
from .models import ActivityLog


class ActivityLogSerializer(serializers.ModelSerializer):
    """Serializer for reading Activity Logs"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    log_type_name = serializers.CharField(source='log_type.type_name', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'user', 'user_email', 'log_type', 'log_type_name',
            'action', 'entity_type', 'entity_id', 
            'ip_address', 'user_agent', 'details', 'created_at'
        ]
        read_only_fields = fields
