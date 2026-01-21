from django.db.models import QuerySet
from ..models import AnalyticsReport


def list_reports(user, filters: dict = None) -> QuerySet[AnalyticsReport]:
    """List analytics reports"""
    queryset = AnalyticsReport.objects.select_related('report_type', 'generated_by').all()
    
    # Logic cho phép admin xem tất cả báo cáo, còn người dùng chỉ thấy các báo cáo của mình
    #TODO: Check lại

    if not user.is_staff:
        if not hasattr(user, 'company_profile'):
             return AnalyticsReport.objects.none()
        queryset = queryset.filter(company=user.company_profile)
             
    if filters:
        if filters.get('type'):
            queryset = queryset.filter(report_type__code=filters['type'])
        if filters.get('date_from'):
            queryset = queryset.filter(generated_at__gte=filters['date_from'])
            
    return queryset.order_by('-generated_at')
