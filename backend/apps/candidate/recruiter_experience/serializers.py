from rest_framework import serializers
from .models import RecruiterExperience


class ExperienceSerializer(serializers.ModelSerializer):
    """Serializer cho đọc dữ liệu (List/Detail)"""
    industry_name = serializers.CharField(source='industry.name', read_only=True, allow_null=True)
    
    class Meta:
        model = RecruiterExperience
        fields = [
            'id', 'company_name', 'job_title', 'industry', 'industry_name',
            'start_date', 'end_date', 'is_current', 'description',
            'address', 'achievements', 'display_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExperienceCreateSerializer(serializers.Serializer):
    """Serializer cho tạo mới experience"""
    
    company_name = serializers.CharField(max_length=255, required=True)
    job_title = serializers.CharField(max_length=100, required=True)
    industry_id = serializers.IntegerField(required=False, allow_null=True)
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    is_current = serializers.BooleanField(required=False, default=False)
    description = serializers.CharField(required=False, allow_blank=True)
    address_id = serializers.IntegerField(required=False, allow_null=True)
    achievements = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        is_current = attrs.get('is_current', False)

        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date"
            })
        
        if is_current and end_date:
            raise serializers.ValidationError({
                "end_date": "End date should be empty for current job"
            })
        
        return attrs


class ExperienceUpdateSerializer(serializers.Serializer):
    """Serializer cho cập nhật experience (partial update)"""
    
    company_name = serializers.CharField(max_length=255, required=False)
    job_title = serializers.CharField(max_length=100, required=False)
    industry_id = serializers.IntegerField(required=False, allow_null=True)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False, allow_null=True)
    is_current = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    address_id = serializers.IntegerField(required=False, allow_null=True)
    achievements = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        is_current = attrs.get('is_current')
        
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({
                "end_date": "End date must be after start date"
            })
        
        if is_current and end_date:
            raise serializers.ValidationError({
                "end_date": "End date should be empty for current job"
            })
        
        return attrs


class ExperienceReorderSerializer(serializers.Serializer):
    """Serializer cho reorder experience"""
    
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
