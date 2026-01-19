from rest_framework import serializers
from .models import RecruiterSkill


class RecruiterSkillSerializer(serializers.ModelSerializer):
    """
        Serializer cho đọc dữ liệu (List/Detail)
    """
    
    skill_id = serializers.IntegerField(source='skill.id', read_only=True)
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    
    class Meta:
        model = RecruiterSkill
        fields = [
            'id', 'skill_id', 'skill_name', 'proficiency_level', 
            'years_of_experience', 'is_verified', 'endorsement_count', 
            'last_used_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified', 'endorsement_count', 'created_at', 'updated_at']


class RecruiterSkillCreateSerializer(serializers.Serializer):
    """
        Serializer cho tạo mới skill
    """
    
    skill_id = serializers.IntegerField(required=True)
    proficiency_level = serializers.ChoiceField(
        choices=['basic', 'intermediate', 'advanced', 'expert'],
        required=False,
        default='intermediate'
    )
    years_of_experience = serializers.IntegerField(required=False, allow_null=True)
    last_used_date = serializers.DateField(required=False, allow_null=True)


class RecruiterSkillUpdateSerializer(serializers.Serializer):
    """
        Serializer cho cập nhật skill (partial update)
    """
    
    proficiency_level = serializers.ChoiceField(
        choices=['basic', 'intermediate', 'advanced', 'expert'],
        required=False
    )
    years_of_experience = serializers.IntegerField(required=False, allow_null=True)
    last_used_date = serializers.DateField(required=False, allow_null=True)


class BulkAddSkillSerializer(serializers.Serializer):
    """
        Serializer cho bulk-add skills
    """
    
    skills = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    
    def validate_skills(self, value):
        """
            Validate each skill item has skill_id
        """
        for item in value:
            if 'skill_id' not in item:
                raise serializers.ValidationError(
                    "Each skill must have 'skill_id' field"
                )
        return value


class EndorseSkillSerializer(serializers.Serializer):
    """
        Serializer cho endorse skill
    """
    
    relationship = serializers.CharField(
        max_length=100, 
        required=False, 
        allow_blank=True,
        default=''
    )