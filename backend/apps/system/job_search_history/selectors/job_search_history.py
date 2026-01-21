from django.db.models import QuerySet
from ..models import JobSearchHistory


def list_search_history(user, limit=10) -> QuerySet[JobSearchHistory]:
    """
        List search history for a user
    """
    if not user.is_authenticated:
        return JobSearchHistory.objects.none()
        
    return JobSearchHistory.objects.filter(user=user)[:limit]
