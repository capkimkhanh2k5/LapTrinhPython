from rest_framework import serializers
from .models import Recruiter
from apps.core.users.serializers import CustomUserSerializer


class RecruiterSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Recruiter
        fields = [
            'id', 'user', 'current_company', 'current_position', 
            'date_of_birth', 'gender', 'address', 'bio', 
            'linkedin_url', 'facebook_url', 'github_url', 'portfolio_url',
            'job_search_status', 'desired_salary_min', 'desired_salary_max', 'salary_currency',
            'available_from_date', 'years_of_experience', 'highest_education_level',
            'profile_completeness_score', 'is_profile_public', 'profile_views_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 
            'profile_completeness_score', 'profile_views_count'
        ]

class RecruiterCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruiter
        fields = [
            'current_company', 'current_position', 
            'date_of_birth', 'gender', 'address', 'bio', 
            'linkedin_url', 'facebook_url', 'github_url', 'portfolio_url',
            'job_search_status', 'desired_salary_min', 'desired_salary_max', 'salary_currency',
            'available_from_date', 'years_of_experience', 'highest_education_level',
            'is_profile_public'
        ]

class RecruiterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruiter
        fields = [
            'current_company', 'current_position', 
            'date_of_birth', 'gender', 'address', 'bio', 
            'linkedin_url', 'facebook_url', 'github_url', 'portfolio_url',
            'job_search_status', 'desired_salary_min', 'desired_salary_max', 'salary_currency',
            'available_from_date', 'years_of_experience', 'highest_education_level',
            'is_profile_public'
        ]

class JobSearchStatusSerializer(serializers.Serializer):
    job_search_status = serializers.ChoiceField(choices=Recruiter.JobSearchStatus.choices)

class ProfileCompletenessSerializer(serializers.Serializer):
    score = serializers.IntegerField(read_only=True)
    missing_fields = serializers.ListField(child=serializers.CharField(), read_only=True)

class RecruiterAvatarSerializer(serializers.Serializer):
    avatar = serializers.ImageField(max_length=None, use_url=True)
    
class RecruiterPublicProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Recruiter
        fields = [
            'id', 'user', 'current_company', 'current_position', 
            'bio', 'linkedin_url', 'github_url', 'portfolio_url',
            'years_of_experience', 'highest_education_level',
        ]
        read_only_fields = ['id']

class RecruiterPrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Recruiter
        fields = ['is_profile_public']

class RecruiterStatsSerializer(serializers.Serializer):
    profile_views = serializers.IntegerField(read_only=True)
    following_companies = serializers.IntegerField(read_only=True)

class RecruiterSearchFilterSerializer(serializers.Serializer):
    skills = serializers.ListField(child=serializers.CharField())
    location = serializers.CharField()
    min_experience = serializers.IntegerField()
    job_status = serializers.CharField()

class MatchingJobSerializer(serializers.Serializer):
    job_id = serializers.IntegerField()
    job_title = serializers.CharField()
    company_name = serializers.CharField()
    match_score = serializers.IntegerField()

class RecruiterApplicationSerializer(serializers.Serializer):
    """Placeholder cho danh sách đơn ứng tuyển"""
    id = serializers.IntegerField()
    job_title = serializers.CharField()
    company_name = serializers.CharField()
    status = serializers.CharField()
    applied_at = serializers.DateTimeField()

class SavedJobSerializer(serializers.Serializer):
    """Serializer cho danh sách việc làm đã lưu"""
    id = serializers.SerializerMethodField()
    job_title = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    saved_at = serializers.SerializerMethodField()
    
    def get_id(self, obj):
        return obj.id
    
    def get_job_title(self, obj):
        return obj.job.title if obj.job else None
    
    def get_company_name(self, obj):
        return obj.job.company.company_name if obj.job and obj.job.company else None
    
    def get_saved_at(self, obj):
        return obj.created_at