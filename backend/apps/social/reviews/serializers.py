from rest_framework import serializers

from apps.social.reviews.models import Review
from apps.company.companies.models import Company

class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a review."""
    
    class Meta:
        model = Review
        fields = [
            'rating',
            'title',
            'content',
            'pros',
            'cons',
            'work_environment_rating',
            'salary_benefits_rating',
            'management_rating',
            'career_development_rating',
            'employment_status',
            'position',
            'employment_duration',
            'is_anonymous',
        ]
    
    def validate_rating(self, value):
        if not 1 <= value <= 5:
            raise serializers.ValidationError('Rating must be between 1 and 5')
        return value


class ReviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a review."""
    
    class Meta:
        model = Review
        fields = [
            'rating',
            'title',
            'content',
            'pros',
            'cons',
            'work_environment_rating',
            'salary_benefits_rating',
            'management_rating',
            'career_development_rating',
            'employment_status',
            'position',
            'employment_duration',
        ]


class ReportReviewSerializer(serializers.Serializer):
    """Serializer for reporting a review."""
    reason = serializers.CharField(max_length=500)
    details = serializers.CharField(required=False, allow_blank=True)


class ApproveReviewSerializer(serializers.Serializer):
    """Serializer for approving/rejecting a review."""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)

class RecruiterBriefSerializer(serializers.Serializer):
    """Brief recruiter info for review."""
    id = serializers.IntegerField()
    full_name = serializers.CharField(source='user.full_name')
    avatar_url = serializers.CharField(source='user.avatar_url', allow_null=True)


class CompanyBriefSerializer(serializers.ModelSerializer):
    """Brief company info for review."""
    name = serializers.CharField(source='company_name')
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'slug', 'logo_url']


class ReviewListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing reviews."""
    company = CompanyBriefSerializer(read_only=True)
    recruiter = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id',
            'company',
            'recruiter',
            'rating',
            'title',
            'content',
            'pros',
            'cons',
            'employment_status',
            'position',
            'helpful_count',
            'status',
            'created_at',
        ]
    
    def get_recruiter(self, obj):
        if obj.is_anonymous:
            return {'id': None, 'full_name': 'Anonymous', 'avatar_url': None}
        return {
            'id': obj.recruiter.id,
            'full_name': obj.recruiter.user.full_name,
            'avatar_url': getattr(obj.recruiter.user, 'avatar_url', None),
        }


class ReviewDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for a review."""
    company = CompanyBriefSerializer(read_only=True)
    recruiter = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id',
            'company',
            'recruiter',
            'rating',
            'title',
            'content',
            'pros',
            'cons',
            'work_environment_rating',
            'salary_benefits_rating',
            'management_rating',
            'career_development_rating',
            'employment_status',
            'position',
            'employment_duration',
            'is_verified',
            'helpful_count',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def get_recruiter(self, obj):
        if obj.is_anonymous:
            return {'id': None, 'full_name': 'Anonymous', 'avatar_url': None}
        return {
            'id': obj.recruiter.id,
            'full_name': obj.recruiter.user.full_name,
            'avatar_url': getattr(obj.recruiter.user, 'avatar_url', None),
        }


class ReviewAdminSerializer(serializers.ModelSerializer):
    """Admin serializer showing all info including anonymous identity."""
    company = CompanyBriefSerializer(read_only=True)
    recruiter = RecruiterBriefSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
