from rest_framework import serializers
from .models import JobAlert, JobAlertMatch
from apps.geography.provinces.models import Province
from apps.geography.provinces.serializers import ProvinceListSerializer
from apps.candidate.skills.models import Skill
from apps.candidate.skills.serializers import SkillListSerializer
from apps.recruitment.jobs.serializers import JobListSerializer

class JobAlertSerializer(serializers.ModelSerializer):
    locations_detail = ProvinceListSerializer(source='locations', many=True, read_only=True)
    skills_detail = SkillListSerializer(source='skills', many=True, read_only=True)
    
    location_ids = serializers.PrimaryKeyRelatedField(
        queryset=Province.objects.all(), source='locations', many=True, write_only=True, required=False
    )
    skill_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(), source='skills', many=True, write_only=True, required=False
    )

    class Meta:
        model = JobAlert
        fields = [
            'id', 'alert_name', 'keywords', 'category',
            'locations_detail', 'location_ids',
            'skills_detail', 'skill_ids',
            'job_type', 'level', 'salary_min',
            'frequency', 'email_notification', 'use_ai_matching', 'is_active',
            'last_sent_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['last_sent_at', 'created_at', 'updated_at']

    def validate_salary_min(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Mức lương tối thiểu không được âm.")
        return value

    def create(self, validated_data):
        # Recruiter (Candidate) will be assigned in ViewSet
        return super().create(validated_data)


class JobAlertMatchSerializer(serializers.ModelSerializer):
    job_detail = JobListSerializer(source='job', read_only=True)
    
    class Meta:
        model = JobAlertMatch
        fields = ['id', 'job', 'job_detail', 'is_sent', 'is_viewed', 'matched_at', 'score']
