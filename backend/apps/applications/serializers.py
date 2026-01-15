from rest_framework import serializers
from .models import Application
from apps.jobs.serializers import JobSerializer
from apps.users.serializers import CustomUserSerializer

class ApplicationSerializer(serializers.ModelSerializer):
    job_detail = JobSerializer(source='job', read_only=True)
    candidate_detail = CustomUserSerializer(source='candidate', read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job', 'candidate', 'cover_letter', 'status', 'applied_at', 'job_detail', 'candidate_detail']
        read_only_fields = ['candidate', 'status', 'applied_at']
