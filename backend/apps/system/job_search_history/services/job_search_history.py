from ..models import JobSearchHistory

def add_history(
    user,
    query: str,
    filters: dict = None,
    results_count: int = 0,
    ip_address: str = None
) -> JobSearchHistory:
    """
        Add a search history record
    """
    if not user.is_authenticated:
        return None

    return JobSearchHistory.objects.create(
        user=user,
        search_query=query,
        filters=filters or {},
        results_count=results_count,
        ip_address=ip_address
    )


def clear_history(user):
    """
        Clear all search history for a user
    """
    if user.is_authenticated:
        JobSearchHistory.objects.filter(user=user).delete()
