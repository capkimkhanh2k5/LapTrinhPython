from rest_framework import serializers

from apps.assessment.ai_matching_scores.models import AIMatchingScore

class CalculateMatchRequestSerializer(serializers.Serializer):
    """Request serializer for calculating a single match."""
    job_id = serializers.IntegerField(
        help_text='ID of the job'
    )
    recruiter_id = serializers.IntegerField(
        help_text='ID of the recruiter (candidate)'
    )


class BatchCalculateRequestSerializer(serializers.Serializer):
    """Request serializer for batch calculating matches."""
    job_id = serializers.IntegerField(
        help_text='ID of the job'
    )
    recruiter_ids = serializers.ListField(
        child=serializers.IntegerField(),
        max_length=100,
        help_text='List of recruiter IDs (max 100)'
    )


class RefreshMatchRequestSerializer(serializers.Serializer):
    """Request serializer for refreshing match scores."""
    job_id = serializers.IntegerField(
        required=False,
        help_text='Job ID to refresh scores for'
    )
    recruiter_id = serializers.IntegerField(
        required=False,
        help_text='Recruiter ID to refresh scores for'
    )
    
    def validate(self, data):
        if not data.get('job_id') and not data.get('recruiter_id'):
            raise serializers.ValidationError(
                'At least one of job_id or recruiter_id is required'
            )
        return data

class RecruiterBriefSerializer(serializers.Serializer):
    """Brief recruiter info for matching results."""
    id = serializers.IntegerField()
    full_name = serializers.CharField(source='user.full_name')
    avatar = serializers.ImageField(source='user.avatar', required=False)
    current_position = serializers.CharField(required=False)
    years_of_experience = serializers.IntegerField()
    job_search_status = serializers.CharField()


class JobBriefSerializer(serializers.Serializer):
    """Brief job info for matching results."""
    id = serializers.IntegerField()
    title = serializers.CharField()
    slug = serializers.CharField()
    company_name = serializers.CharField(source='company.company_name')
    company_logo = serializers.URLField(source='company.logo_url', required=False)
    job_type = serializers.CharField()
    level = serializers.CharField()
    salary_min = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    salary_max = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    is_remote = serializers.BooleanField()


class MatchingScoreListSerializer(serializers.ModelSerializer):
    """Serializer for listing matching scores (lightweight)."""
    recruiter = RecruiterBriefSerializer(read_only=True)
    job = JobBriefSerializer(read_only=True)
    
    class Meta:
        model = AIMatchingScore
        fields = [
            'id',
            'job',
            'recruiter',
            'overall_score',
            'skill_match_score',
            'experience_match_score',
            'education_match_score',
            'location_match_score',
            'salary_match_score',
            'calculated_at',
            'is_valid',
        ]


class MatchingScoreDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed matching score with breakdown."""
    recruiter = RecruiterBriefSerializer(read_only=True)
    job = JobBriefSerializer(read_only=True)
    
    class Meta:
        model = AIMatchingScore
        fields = [
            'id',
            'job',
            'recruiter',
            'overall_score',
            'skill_match_score',
            'experience_match_score',
            'education_match_score',
            'location_match_score',
            'salary_match_score',
            'matching_details',
            'calculated_at',
            'is_valid',
        ]


class MatchingCandidateSerializer(serializers.ModelSerializer):
    """Serializer for matching candidates (recruiter-focused)."""
    recruiter = RecruiterBriefSerializer(read_only=True)
    
    class Meta:
        model = AIMatchingScore
        fields = [
            'id',
            'recruiter',
            'overall_score',
            'skill_match_score',
            'experience_match_score',
            'education_match_score',
            'location_match_score',
            'salary_match_score',
            'calculated_at',
        ]


class MatchingJobSerializer(serializers.ModelSerializer):
    """Serializer for matching jobs (job-focused)."""
    job = JobBriefSerializer(read_only=True)
    
    class Meta:
        model = AIMatchingScore
        fields = [
            'id',
            'job',
            'overall_score',
            'skill_match_score',
            'experience_match_score',
            'education_match_score',
            'location_match_score',
            'salary_match_score',
            'calculated_at',
        ]


class MatchingInsightsSerializer(serializers.Serializer):
    """Serializer for matching insights response."""
    summary = serializers.DictField()
    score_distribution = serializers.DictField()
    component_averages = serializers.DictField()
    filters_applied = serializers.DictField()


class BatchCalculateResponseSerializer(serializers.Serializer):
    """Response serializer for batch calculate."""
    total_requested = serializers.IntegerField()
    total_calculated = serializers.IntegerField()
    scores = MatchingScoreListSerializer(many=True)


class RefreshMatchResponseSerializer(serializers.Serializer):
    """Response serializer for refresh matches."""
    total_refreshed = serializers.IntegerField()
    message = serializers.CharField()
