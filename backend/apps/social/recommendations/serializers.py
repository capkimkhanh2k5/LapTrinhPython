from rest_framework import serializers

from apps.social.recommendations.models import Recommendation

class RecommendationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a recommendation."""
    
    class Meta:
        model = Recommendation
        fields = [
            'relationship',
            'content',
        ]


class RecommendationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a recommendation."""
    
    class Meta:
        model = Recommendation
        fields = [
            'relationship',
            'content',
        ]


class VisibilitySerializer(serializers.Serializer):
    """Serializer for changing visibility."""
    is_visible = serializers.BooleanField()


class RecruiterBriefSerializer(serializers.Serializer):
    """Brief recruiter info."""
    id = serializers.IntegerField()
    full_name = serializers.CharField(source='user.full_name')
    avatar_url = serializers.CharField(source='user.avatar_url', allow_null=True)
    headline = serializers.CharField(allow_null=True)


class RecommenderSerializer(serializers.Serializer):
    """Recommender (user) info."""
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    avatar_url = serializers.CharField(allow_null=True)


class RecommendationListSerializer(serializers.ModelSerializer):
    """Serializer for listing recommendations."""
    recruiter = RecruiterBriefSerializer(read_only=True)
    recommender = RecommenderSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id',
            'recruiter',
            'recommender',
            'relationship',
            'content',
            'is_visible',
            'created_at',
        ]


class RecommendationDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer."""
    recruiter = RecruiterBriefSerializer(read_only=True)
    recommender = RecommenderSerializer(read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id',
            'recruiter',
            'recommender',
            'relationship',
            'content',
            'is_visible',
            'created_at',
            'updated_at',
        ]
