from rest_framework import serializers
from apps.recruitment.campaigns.models import Campaign
from apps.recruitment.jobs.serializers import JobListSerializer as JobSerializer  # Alias for consistency
from apps.recruitment.jobs.validators import JobOwnershipValidator

class CampaignSerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(source='jobs.count', read_only=True)
    
    class Meta:
        model = Campaign
        fields = [
            'id', 'title', 'slug', 'description', 
            'start_date', 'end_date', 'status', 'budget',
            'job_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'job_count']

class CampaignDetailSerializer(CampaignSerializer):
    jobs = JobSerializer(many=True, read_only=True)
    
    class Meta(CampaignSerializer.Meta):
        fields = CampaignSerializer.Meta.fields + ['jobs']

class CampaignJobAddSerializer(serializers.Serializer):
    job_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        validators=[JobOwnershipValidator()]
    )

class CampaignStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Campaign.Status.choices)
