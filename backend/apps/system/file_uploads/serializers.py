from rest_framework import serializers
from .models import FileUpload

class FileUploadSerializer(serializers.ModelSerializer):
    """
        Serializer for File Uploads
    """
    file = serializers.FileField(write_only=True, required=True)
    
    class Meta:
        model = FileUpload
        fields = [
            'id', 'user', 'file_name', 'original_name', 'file_path',
            'file_type', 'file_size', 'mime_type',
            'entity_type', 'entity_id', 'is_public', 'created_at',
            'file' # write only
        ]
        read_only_fields = [
            'id', 'user', 'file_name', 'original_name', 'file_path',
            'file_type', 'file_size', 'mime_type', 'created_at'
        ]

    def create(self, validated_data):
        """
            Xóa 'file' khỏi validated_data trước khi tạo
        """
        validated_data.pop('file', None)
        return super().create(validated_data)
