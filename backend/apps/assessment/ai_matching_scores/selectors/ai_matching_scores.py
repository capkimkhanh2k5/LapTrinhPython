from typing import Optional

from django.db.models import QuerySet, F

from apps.assessment.ai_matching_scores.models import AIMatchingScore


def get_matching_candidates(
    job_id: int,
    min_score: float = 0,
    limit: int = 20,
    offset: int = 0
) -> QuerySet[AIMatchingScore]:
    """
    Get matching candidates for a job, sorted by overall score.
    
    Args:
        job_id: Job ID to find candidates for
        min_score: Minimum overall score filter (default 0)
        limit: Maximum number of results (default 20)
        offset: Pagination offset (default 0)
        
    Returns:
        QuerySet of AIMatchingScore with related recruiter and user data
    """
    return (
        AIMatchingScore.objects
        .filter(
            job_id=job_id,
            is_valid=True,
            overall_score__gte=min_score,
        )
        .select_related(
            'recruiter',
            'recruiter__user',
            'recruiter__current_company',
        )
        .order_by('-overall_score')
        [offset:offset + limit]
    )


def get_matching_jobs(
    recruiter_id: int,
    min_score: float = 0,
    limit: int = 20,
    offset: int = 0,
    job_status: str = 'published'
) -> QuerySet[AIMatchingScore]:
    """
    Get matching jobs for a recruiter, sorted by overall score.
    
    Args:
        recruiter_id: Recruiter ID to find jobs for
        min_score: Minimum overall score filter (default 0)
        limit: Maximum number of results (default 20)
        offset: Pagination offset (default 0)
        job_status: Filter by job status (default 'published')
        
    Returns:
        QuerySet of AIMatchingScore with related job and company data
    """
    queryset = (
        AIMatchingScore.objects
        .filter(
            recruiter_id=recruiter_id,
            is_valid=True,
            overall_score__gte=min_score,
        )
        .select_related(
            'job',
            'job__company',
            'job__category',
        )
    )
    
    if job_status:
        queryset = queryset.filter(job__status=job_status)
    
    return queryset.order_by('-overall_score')[offset:offset + limit]


def get_match_detail(job_id: int, recruiter_id: int) -> Optional[AIMatchingScore]:
    """
    Get detailed match score for a specific job-recruiter pair.
    
    Args:
        job_id: Job ID
        recruiter_id: Recruiter ID
        
    Returns:
        AIMatchingScore instance or None if not found
    """
    try:
        return (
            AIMatchingScore.objects
            .select_related(
                'job',
                'job__company',
                'recruiter',
                'recruiter__user',
            )
            .get(job_id=job_id, recruiter_id=recruiter_id)
        )
    except AIMatchingScore.DoesNotExist:
        return None


def get_top_matches(
    limit: int = 10,
    job_status: str = 'published',
    min_score: float = 70
) -> QuerySet[AIMatchingScore]:
    """
    Get top matches across the system.
    
    Args:
        limit: Maximum number of results (default 10)
        job_status: Filter by job status (default 'published')
        min_score: Minimum score to be considered top match (default 70)
        
    Returns:
        QuerySet of top AIMatchingScore records
    """
    queryset = (
        AIMatchingScore.objects
        .filter(
            is_valid=True,
            overall_score__gte=min_score,
        )
        .select_related(
            'job',
            'job__company',
            'recruiter',
            'recruiter__user',
        )
    )
    
    if job_status:
        queryset = queryset.filter(job__status=job_status)
    
    return queryset.order_by('-overall_score', '-calculated_at')[:limit]


def get_scores_count_by_job(job_id: int) -> int:
    """Get total number of calculated scores for a job."""
    return AIMatchingScore.objects.filter(
        job_id=job_id,
        is_valid=True
    ).count()


def get_scores_count_by_recruiter(recruiter_id: int) -> int:
    """Get total number of calculated scores for a recruiter."""
    return AIMatchingScore.objects.filter(
        recruiter_id=recruiter_id,
        is_valid=True
    ).count()
