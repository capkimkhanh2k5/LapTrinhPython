from rest_framework import serializers
from .models import RecruiterCertification


class CertificationSerializer(serializers.ModelSerializer):
    """
    Serializer cho đọc dữ liệu (List/Detail)
    """
    
    class Meta:
        model = RecruiterCertification
        fields = [
            'id', 'certification_name', 'issuing_organization', 
            'issue_date', 'expiry_date', 'credential_id', 
            'credential_url', 'does_not_expire', 'display_order',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CertificationCreateSerializer(serializers.Serializer):
    """
    Serializer cho tạo mới certification
    """
    
    certification_name = serializers.CharField(max_length=255, required=True)
    issuing_organization = serializers.CharField(max_length=255, required=False, allow_blank=True)
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    credential_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    credential_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    does_not_expire = serializers.BooleanField(required=False, default=False)
    
    def validate(self, attrs):
        issue_date = attrs.get('issue_date')
        expiry_date = attrs.get('expiry_date')
        does_not_expire = attrs.get('does_not_expire', False)
        
        if expiry_date and issue_date and expiry_date < issue_date:
            raise serializers.ValidationError({
                "expiry_date": "Expiry date must be after issue date"
            })
        
        if does_not_expire and expiry_date:
            raise serializers.ValidationError({
                "expiry_date": "Expiry date should be empty when does_not_expire=True"
            })
        
        return attrs


class CertificationUpdateSerializer(serializers.Serializer):
    """
    Serializer cho cập nhật certification (partial update)
    """
    
    certification_name = serializers.CharField(max_length=255, required=False)
    issuing_organization = serializers.CharField(max_length=255, required=False, allow_blank=True)
    issue_date = serializers.DateField(required=False, allow_null=True)
    expiry_date = serializers.DateField(required=False, allow_null=True)
    credential_id = serializers.CharField(max_length=100, required=False, allow_blank=True)
    credential_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    does_not_expire = serializers.BooleanField(required=False)
    
    def validate(self, attrs):
        issue_date = attrs.get('issue_date')
        expiry_date = attrs.get('expiry_date')
        does_not_expire = attrs.get('does_not_expire')
        
        if expiry_date and issue_date and expiry_date < issue_date:
            raise serializers.ValidationError({
                "expiry_date": "Expiry date must be after issue date"
            })
        
        if does_not_expire and expiry_date:
            raise serializers.ValidationError({
                "expiry_date": "Expiry date should be empty when does_not_expire=True"
            })
        
        return attrs


class CertificationReorderSerializer(serializers.Serializer):
    """
    Serializer cho reorder certifications
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