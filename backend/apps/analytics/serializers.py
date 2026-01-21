from rest_framework import serializers
from apps.analytics.models import GeneratedReport

class GeneratedReportSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = GeneratedReport
        fields = ['id', 'name', 'report_type', 'type_display', 'file', 'filters', 'created_by_name', 'created_at']
        read_only_fields = ['name', 'file', 'created_by']
