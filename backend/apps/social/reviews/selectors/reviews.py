from typing import Optional

from django.db.models import QuerySet, Avg, Count

from apps.social.reviews.models import Review


def get_company_reviews(
    company_id: int,
    status: Optional[str] = 'approved',
    rating: Optional[int] = None,
) -> QuerySet[Review]:
    """
    Get reviews for a company.
    
    Args:
        company_id: Company ID
        status: Filter by status (default: approved)
        rating: Optional rating filter
        
    Returns:
        QuerySet of Review
    """
    queryset = (
        Review.objects
        .filter(company_id=company_id)
        .select_related('company', 'recruiter__user')
    )
    
    if status:
        queryset = queryset.filter(status=status)
    
    if rating:
        queryset = queryset.filter(rating=rating)
    
    return queryset.order_by('-created_at')


def get_review_by_id(review_id: int) -> Optional[Review]:
    """
    Get single review by ID.
    
    Args:
        review_id: Review ID
        
    Returns:
        Review or None
    """
    try:
        return (
            Review.objects
            .select_related('company', 'recruiter__user')
            .get(id=review_id)
        )
    except Review.DoesNotExist:
        return None


def get_recruiter_reviews(recruiter_id: int) -> QuerySet[Review]:
    """
    Get reviews written by a recruiter.
    
    Args:
        recruiter_id: Recruiter ID
        
    Returns:
        QuerySet of Review
    """
    return (
        Review.objects
        .filter(recruiter_id=recruiter_id)
        .select_related('company', 'recruiter__user')
        .order_by('-created_at')
    )


def get_pending_reviews() -> QuerySet[Review]:
    """
    Get all pending reviews for admin moderation.
    
    Returns:
        QuerySet of pending Reviews
    """
    return (
        Review.objects
        .filter(status=Review.Status.PENDING)
        .select_related('company', 'recruiter__user')
        .order_by('-created_at')
    )


def get_company_review_stats(company_id: int) -> dict:
    """
    Get review statistics for a company.
    
    Args:
        company_id: Company ID
        
    Returns:
        dict with stats (avg_rating, total_reviews, rating_distribution)
    """
    reviews = Review.objects.filter(
        company_id=company_id,
        status=Review.Status.APPROVED
    )
    
    stats = reviews.aggregate(
        avg_rating=Avg('rating'),
        total=Count('id'),
        avg_work_environment=Avg('work_environment_rating'),
        avg_salary_benefits=Avg('salary_benefits_rating'),
        avg_management=Avg('management_rating'),
        avg_career=Avg('career_development_rating'),
    )
    
    # Rating distribution
    distribution = {}
    for rating in range(1, 6):
        distribution[rating] = reviews.filter(rating=rating).count()
    
    return {
        'avg_rating': float(stats['avg_rating'] or 0),
        'total_reviews': stats['total'],
        'rating_distribution': distribution,
        'category_ratings': {
            'work_environment': float(stats['avg_work_environment'] or 0),
            'salary_benefits': float(stats['avg_salary_benefits'] or 0),
            'management': float(stats['avg_management'] or 0),
            'career_development': float(stats['avg_career'] or 0),
        }
    }


def check_user_can_review(company_id: int, recruiter_id: int) -> dict:
    """
    Check if user can write a review for a company.
    
    Args:
        company_id: Company ID
        recruiter_id: Recruiter ID
        
    Returns:
        dict with can_review and existing_review_id
    """
    existing = Review.objects.filter(
        company_id=company_id,
        recruiter_id=recruiter_id
    ).first()
    
    return {
        'can_review': existing is None,
        'existing_review_id': existing.id if existing else None,
    }
