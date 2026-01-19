from rest_framework import serializers
from .models import RecruiterEducation


class EducationSerializer(serializers.ModelSerializer):
    """Serializer cho đọc dữ liệu (List/Detail)"""
    
    class Meta:
        model = RecruiterEducation
        fields = [
            'id', 'school_name', 'degree', 'field_of_study',
            'start_date', 'end_date', 'is_current', 'gpa',
            'description', 'display_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EducationCreateSerializer(serializers.Serializer):
    """Serializer cho tạo mới education"""
    
    school_name = serializers.CharField(max_length=255, required=True)
    degree = serializers.CharField(max_length=100, required=False, allow_blank=True)
    field_of_study = serializers.CharField(max_length=100, required=False, allow_blank=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    is_current = serializers.BooleanField(required=False, default=False)
    gpa = serializers.DecimalField(max_digits=3, decimal_places=2, required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
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
                "end_date": "End date should be empty when currently studying"
            })
        
        return attrs


class EducationUpdateSerializer(serializers.Serializer):
    """Serializer cho cập nhật education (partial update)"""
    
    school_name = serializers.CharField(max_length=255, required=False)
    degree = serializers.CharField(max_length=100, required=False, allow_blank=True)
    field_of_study = serializers.CharField(max_length=100, required=False, allow_blank=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    is_current = serializers.BooleanField(required=False)
    gpa = serializers.DecimalField(max_digits=3, decimal_places=2, required=False, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    
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
                "end_date": "End date should be empty when currently studying"
            })
        
        return attrs


class EducationReorderSerializer(serializers.Serializer):
    """Serializer cho reorder education"""
    
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
