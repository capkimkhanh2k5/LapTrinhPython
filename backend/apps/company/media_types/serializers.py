from rest_framework import serializers
from .models import MediaType


class MediaTypeSerializer(serializers.ModelSerializer):
    """Serializer cho MediaType - hiển thị đầy đủ"""
    
    class Meta:
        model = MediaType
        fields = ['id', 'type_name', 'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class MediaTypeCreateSerializer(serializers.Serializer):
    """Serializer cho tạo MediaType"""
    
    type_name = serializers.CharField(max_length=50)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)


class MediaTypeUpdateSerializer(serializers.Serializer):
    """Serializer cho cập nhật MediaType"""
    
    type_name = serializers.CharField(max_length=50, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
