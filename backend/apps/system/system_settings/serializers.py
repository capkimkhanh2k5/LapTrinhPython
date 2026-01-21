from rest_framework import serializers
from .models import SystemSetting


class SystemSettingSerializer(serializers.ModelSerializer):
    """
        Serializer for reading System Settings
    """
    class Meta:
        model = SystemSetting
        fields = [
            'id', 'setting_key', 'setting_value', 'setting_type',
            'category', 'description', 'is_public', 'updated_at'
        ]
        read_only_fields = ['id', 'setting_key', 'setting_type', 'updated_at']


class SystemSettingUpdateSerializer(serializers.ModelSerializer):
    """
        Serializer for updating System Settings
    """
    class Meta:
        model = SystemSetting
        fields = ['setting_value', 'is_public', 'description']
