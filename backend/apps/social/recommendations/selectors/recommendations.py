from typing import Optional

from django.db.models import QuerySet

from apps.social.recommendations.models import Recommendation


def get_recruiter_recommendations(
    recruiter_id: int,
    visible_only: bool = True,
) -> QuerySet[Recommendation]:
    """
    Get recommendations for a recruiter.
    
    Args:
        recruiter_id: Recruiter ID
        visible_only: Only show visible recommendations
        
    Returns:
        QuerySet of Recommendation
    """
    queryset = (
        Recommendation.objects
        .filter(recruiter_id=recruiter_id)
        .select_related('recruiter__user', 'recommender')
    )
    
    if visible_only:
        queryset = queryset.filter(is_visible=True)
    
    return queryset.order_by('-created_at')


def get_recommendation_by_id(recommendation_id: int) -> Optional[Recommendation]:
    """
    Get single recommendation by ID.
    
    Args:
        recommendation_id: Recommendation ID
        
    Returns:
        Recommendation or None
    """
    try:
        return (
            Recommendation.objects
            .select_related('recruiter__user', 'recommender')
            .get(id=recommendation_id)
        )
    except Recommendation.DoesNotExist:
        return None


def get_given_recommendations(user_id: int) -> QuerySet[Recommendation]:
    """
    Get recommendations written by a user.
    
    Args:
        user_id: User ID (recommender)
        
    Returns:
        QuerySet of Recommendation
    """
    return (
        Recommendation.objects
        .filter(recommender_id=user_id)
        .select_related('recruiter__user', 'recommender')
        .order_by('-created_at')
    )


def get_recommendation_count(recruiter_id: int) -> int:
    """
    Get count of visible recommendations for a recruiter.
    
    Args:
        recruiter_id: Recruiter ID
        
    Returns:
        Count of recommendations
    """
    return Recommendation.objects.filter(
        recruiter_id=recruiter_id,
        is_visible=True
    ).count()
