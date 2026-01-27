from django.db.models import QuerySet
from apps.core.users.models import CustomUser
from .models import AnalyticsReport

class AnalyticsReportPolicy:
    """Policy for Analytics Reports access control"""
    
    @staticmethod
    def scope(user: CustomUser, queryset: QuerySet) -> QuerySet:
        """
        Filter queryset based on user permissions.
        - Superuser/Staff: Can see all (or filter further by request)
        - Company: Can only see reports belonging to their company
        - Others (Recruiter/Guest): See nothing
        """
        if not user.is_authenticated:
            return queryset.none()
            
        if user.is_superuser or user.is_staff:
            return queryset
            
        # Check if user has company profile
        company_profile = getattr(user, 'company_profile', None)
        if company_profile:
            return queryset.filter(company=company_profile)
            
        # Default: No access
        return queryset.none()

    @staticmethod
    def can_view(user: CustomUser, report: AnalyticsReport) -> bool:
        """Check if user can view a specific report"""
        if user.is_superuser or user.is_staff:
            return True
            
        company_profile = getattr(user, 'company_profile', None)
        if company_profile and report.company == company_profile:
            return True
            
        return False
