from rest_framework import serializers
from .models import AnalyticsReport

class AnalyticsReportSerializer(serializers.ModelSerializer):
    """Serializer for Analytics Reports"""
    report_type_name = serializers.CharField(source='report_type.type_name', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = AnalyticsReport
        fields = [
            'id', 'company', 'report_type', 'report_type_name',
            'report_period_start', 'report_period_end',
            'metrics', 'generated_by', 'generated_by_name', 'generated_at'
        ]
        read_only_fields = ['id', 'metrics', 'generated_by', 'generated_at']
