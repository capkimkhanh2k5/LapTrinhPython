from rest_framework import serializers

from apps.social.recruiter_connections.models import RecruiterConnection
from apps.candidate.recruiters.models import Recruiter

class ConnectionRequestSerializer(serializers.Serializer):
    """Serializer for sending connection request."""
    message = serializers.CharField(required=False, allow_blank=True, max_length=500)


class ConnectionActionSerializer(serializers.Serializer):
    """Serializer for accept/reject actions."""
    pass


class RecruiterConnectionBriefSerializer(serializers.Serializer):
    """Brief recruiter info for connection."""
    id = serializers.IntegerField()
    full_name = serializers.CharField(source='user.full_name')
    avatar_url = serializers.CharField(source='user.avatar_url', allow_null=True)
    headline = serializers.CharField(allow_null=True)
    job_search_status = serializers.CharField()


class ConnectionListSerializer(serializers.ModelSerializer):
    """Serializer for listing connections."""
    requester = RecruiterConnectionBriefSerializer(read_only=True)
    receiver = RecruiterConnectionBriefSerializer(read_only=True)
    
    class Meta:
        model = RecruiterConnection
        fields = [
            'id',
            'requester',
            'receiver',
            'status',
            'message',
            'created_at',
        ]


class ConnectionDetailSerializer(serializers.ModelSerializer):
    """Full detail serializer for a connection."""
    requester = RecruiterConnectionBriefSerializer(read_only=True)
    receiver = RecruiterConnectionBriefSerializer(read_only=True)
    
    class Meta:
        model = RecruiterConnection
        fields = [
            'id',
            'requester',
            'receiver',
            'status',
            'message',
            'created_at',
            'updated_at',
        ]


class SuggestionSerializer(serializers.Serializer):
    """Serializer for connection suggestions."""
    recruiter = RecruiterConnectionBriefSerializer()
    mutual_connections = serializers.IntegerField()
    common_skills = serializers.ListField(child=serializers.CharField())
    score = serializers.FloatField()
