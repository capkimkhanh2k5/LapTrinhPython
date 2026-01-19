from rest_framework import serializers
from .models import RecruiterProject


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer cho đọc dữ liệu (List/Detail)
    """
    
    class Meta:
        model = RecruiterProject
        fields = [
            'id', 'project_name', 'description', 'project_url',
            'start_date', 'end_date', 'is_ongoing', 'technologies_used',
            'display_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectCreateSerializer(serializers.Serializer):
    """
    Serializer cho tạo mới project
    """
    
    project_name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    project_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    is_ongoing = serializers.BooleanField(required=False, default=False)
    technologies_used = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        is_ongoing = attrs.get('is_ongoing', False)
        
        # Validation: end_date >= start_date
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date"
            })
        
        # Validation: is_ongoing=True thì end_date=None
        if is_ongoing and end_date:
            raise serializers.ValidationError({
                "end_date": "End date should be empty when is_ongoing=True"
            })
        
        return attrs


class ProjectUpdateSerializer(serializers.Serializer):
    """
    Serializer cho cập nhật project (partial update)
    """
    
    project_name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    project_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    is_ongoing = serializers.BooleanField(required=False)
    technologies_used = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        is_ongoing = attrs.get('is_ongoing')
        
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date"
            })
        
        if is_ongoing and end_date:
            raise serializers.ValidationError({
                "end_date": "End date should be empty when is_ongoing=True"
            })
        
        return attrs


class ProjectReorderSerializer(serializers.Serializer):
    """
    Serializer cho reorder projects
    """
    
    order = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        required=True
    )
    
    def validate_order(self, value):
        for item in value:
            if 'id' not in item or 'display_order' not in item:
                raise serializers.ValidationError(
                    "Each item must have 'id' and 'display_order' fields"
                )
        return value
