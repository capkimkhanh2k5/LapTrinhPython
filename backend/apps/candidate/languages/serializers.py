from rest_framework import serializers
from .models import Language


class LanguageSerializer(serializers.ModelSerializer):
    """
    Serializer cho Language (read-only, public API)
    """
    
    class Meta:
        model = Language
        fields = ['id', 'language_code', 'language_name', 'native_name']
        read_only_fields = ['id', 'language_code', 'language_name', 'native_name']
