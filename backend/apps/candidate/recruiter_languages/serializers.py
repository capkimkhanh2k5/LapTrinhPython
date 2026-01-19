from rest_framework import serializers
from .models import RecruiterLanguage


class RecruiterLanguageSerializer(serializers.ModelSerializer):
    """
    Serializer cho đọc dữ liệu (List/Detail)
    """
    
    language_id = serializers.IntegerField(source='language.id', read_only=True)
    language_code = serializers.CharField(source='language.language_code', read_only=True)
    language_name = serializers.CharField(source='language.language_name', read_only=True)
    
    class Meta:
        model = RecruiterLanguage
        fields = [
            'id', 'language_id', 'language_code', 'language_name',
            'proficiency_level', 'is_native', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RecruiterLanguageCreateSerializer(serializers.Serializer):
    """
    Serializer cho tạo mới ngôn ngữ
    """
    
    language_id = serializers.IntegerField(required=True)
    proficiency_level = serializers.ChoiceField(
        choices=['basic', 'intermediate', 'advanced', 'fluent', 'native'],
        required=True
    )
    is_native = serializers.BooleanField(required=False, default=False)
    
    def validate(self, attrs):
        # Nếu proficiency_level = 'native' thì is_native = True
        if attrs.get('proficiency_level') == 'native':
            attrs['is_native'] = True
        return attrs


class RecruiterLanguageUpdateSerializer(serializers.Serializer):
    """
    Serializer cho cập nhật ngôn ngữ (không cho update language_id)
    """
    
    proficiency_level = serializers.ChoiceField(
        choices=['basic', 'intermediate', 'advanced', 'fluent', 'native'],
        required=False
    )
    is_native = serializers.BooleanField(required=False)
    
    def validate(self, attrs):
        if attrs.get('proficiency_level') == 'native':
            attrs['is_native'] = True
        return attrs
