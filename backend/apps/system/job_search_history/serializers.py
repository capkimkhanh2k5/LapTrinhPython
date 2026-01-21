from rest_framework import serializers
from .models import JobSearchHistory

class JobSearchHistorySerializer(serializers.ModelSerializer):
    """Serializer for Job Search History"""
    class Meta:
        model = JobSearchHistory
        fields = [
            'id', 'user', 'search_query', 'filters', 
            'results_count', 'ip_address', 'searched_at'
        ]
        read_only_fields = ['id', 'user', 'searched_at']
