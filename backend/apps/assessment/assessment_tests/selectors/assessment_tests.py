from typing import Optional

from django.db.models import QuerySet, Count, Avg
from django.db.models import Q

from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.assessment_categories.models import AssessmentCategory
from apps.assessment.test_results.models import TestResult

def get_tests_list(
    category_id: Optional[int] = None,
    test_type: Optional[str] = None,
    difficulty_level: Optional[str] = None,
    is_active: bool = True,
    is_public: bool = True,
) -> QuerySet[AssessmentTest]:
    """
    Get list of assessment tests with optional filters.
    
    Args:
        category_id: Filter by category
        test_type: Filter by test type
        difficulty_level: Filter by difficulty
        is_active: Filter active tests only
        is_public: Filter public tests only
        
    Returns:
        QuerySet of AssessmentTest
    """
    queryset = AssessmentTest.objects.select_related('category')
    
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    
    if is_public is not None:
        queryset = queryset.filter(is_public=is_public)
    
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    if test_type:
        queryset = queryset.filter(test_type=test_type)
    
    if difficulty_level:
        queryset = queryset.filter(difficulty_level=difficulty_level)
    
    return queryset.order_by('-created_at')


def get_test_by_id(test_id: int) -> Optional[AssessmentTest]:
    """
    Get single test by ID.
    
    Args:
        test_id: Test ID
        
    Returns:
        AssessmentTest or None
    """
    try:
        return AssessmentTest.objects.select_related('category', 'created_by').get(id=test_id)
    except AssessmentTest.DoesNotExist:
        return None


def get_test_by_slug(slug: str) -> Optional[AssessmentTest]:
    """
    Get single test by slug.
    
    Args:
        slug: Test slug
        
    Returns:
        AssessmentTest or None
    """
    try:
        return AssessmentTest.objects.select_related('category', 'created_by').get(slug=slug)
    except AssessmentTest.DoesNotExist:
        return None


def get_tests_by_type(test_type: str) -> QuerySet[AssessmentTest]:
    """
    Get tests filtered by type.
    
    Args:
        test_type: One of skill, personality, aptitude, language, technical
        
    Returns:
        QuerySet of AssessmentTest
    """
    return (
        AssessmentTest.objects
        .filter(test_type=test_type, is_active=True, is_public=True)
        .select_related('category')
        .order_by('-created_at')
    )


def get_all_categories() -> QuerySet[AssessmentCategory]:
    """
    Get all active assessment categories.
    
    Returns:
        QuerySet of AssessmentCategory
    """
    return (
        AssessmentCategory.objects
        .filter(is_active=True)
        .annotate(test_count=Count('tests'))
        .order_by('name')
    )


def get_test_statistics(test_id: int) -> dict:
    """
    Get statistics for a test.
    
    Args:
        test_id: Test ID
        
    Returns:
        dict with stats (total_attempts, avg_score, pass_rate)
    """
    
    results = TestResult.objects.filter(assessment_test_id=test_id)
    
    total_attempts = results.count()
    
    if total_attempts == 0:
        return {
            'total_attempts': 0,
            'avg_score': 0,
            'avg_percentage': 0,
            'pass_rate': 0,
        }
    
    stats = results.aggregate(
        avg_score=Avg('score'),
        avg_percentage=Avg('percentage_score'),
    )
    
    passed_count = results.filter(passed=True).count()
    pass_rate = (passed_count / total_attempts) * 100
    
    return {
        'total_attempts': total_attempts,
        'avg_score': float(stats['avg_score'] or 0),
        'avg_percentage': float(stats['avg_percentage'] or 0),
        'pass_rate': round(pass_rate, 2),
    }


def search_tests(query: str) -> QuerySet[AssessmentTest]:
    """
    Search tests by title or description.
    
    Args:
        query: Search query
        
    Returns:
        QuerySet of AssessmentTest
    """
    
    return (
        AssessmentTest.objects
        .filter(
            Q(title__icontains=query) | Q(description__icontains=query),
            is_active=True,
            is_public=True
        )
        .select_related('category')
        .order_by('-created_at')
    )
