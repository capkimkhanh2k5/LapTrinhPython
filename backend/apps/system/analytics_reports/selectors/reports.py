from django.db.models import QuerySet
from ..models import AnalyticsReport


from ..policies import AnalyticsReportPolicy

def list_reports(user, filters: dict = None) -> QuerySet[AnalyticsReport]:
    """List analytics reports with policy-based access control"""
    queryset = AnalyticsReport.objects.select_related('report_type', 'generated_by').all()
    
    # Delegate permission logic to Policy
    queryset = AnalyticsReportPolicy.scope(user, queryset)
             
    if filters:
        if filters.get('type'):
            queryset = queryset.filter(report_type__code=filters['type'])
        if filters.get('date_from'):
            queryset = queryset.filter(generated_at__gte=filters['date_from'])
            
    return queryset.order_by('-generated_at')
