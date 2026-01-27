from typing import Optional
from django.db.models import QuerySet
from apps.candidate.recruiters.models import Recruiter
from apps.assessment.ai_matching_scores.models import AIMatchingScore
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from django.db.models import F

def get_recruiter_by_user(user) -> Optional[Recruiter]:
    """
    Lấy hồ sơ ứng viên theo user.
    """
    if not hasattr(user, 'recruiter_profile'):
        return None
    return user.recruiter_profile

def get_recruiter_by_id(pk: int) -> Optional[Recruiter]:
    """
    Lấy hồ sơ ứng viên theo ID.
    """
    try:
        return Recruiter.objects.get(pk=pk)
    except Recruiter.DoesNotExist:
        return None

def get_recruiter_stats(recruiter: Recruiter) -> dict:
    """
    Lấy thống kê hồ sơ ứng viên.
    """
    # following_companies là reverse relation từ CompanyFollower model
    following_count = recruiter.following_companies.count() if hasattr(recruiter, 'following_companies') else 0
    
    return {
        'profile_views': recruiter.profile_views_count,
        'following_companies': following_count,
    }

def search_recruiters(filters: dict) -> QuerySet:
    """
    Advanced recruiter search using Postgres Full Text Search.
    
    filters can contain:
    - q: Search query (searches position, bio, skills)
    - skills: List of skill names or IDs
    - location: Province/City name
    - min_experience: Minimum years of experience
    - max_experience: Maximum years of experience
    - job_status: Job search status
    - education_level: Highest education level
    """
    queryset = Recruiter.objects.filter(is_profile_public=True).select_related('user', 'address')
    
    # Full Text Search (q parameter)
    search_query = filters.get('q') or filters.get('search')
    if search_query:
        # Build search vector from multiple fields
        search_vector = SearchVector(
            'current_position', weight='A',
            config='english'
        ) + SearchVector(
            'bio', weight='B',
            config='english'
        )
        
        # Create query
        query = SearchQuery(search_query, config='english')
        
        # Annotate with search rank and filter
        queryset = queryset.annotate(
            search=search_vector,
            rank=SearchRank(search_vector, query)
        ).filter(search=query).order_by('-rank')
    
    # Filter by job_status
    if filters.get('job_status'):
        queryset = queryset.filter(job_search_status=filters['job_status'])
    
    # Filter by experience range
    if filters.get('min_experience'):
        queryset = queryset.filter(years_of_experience__gte=int(filters['min_experience']))
    if filters.get('max_experience'):
        queryset = queryset.filter(years_of_experience__lte=int(filters['max_experience']))
    
    # Filter by education level
    if filters.get('education_level'):
        queryset = queryset.filter(highest_education_level=filters['education_level'])
    
    # Filter by location (province via address)
    if filters.get('location'):
        location = filters['location']
        queryset = queryset.filter(
            address__commune__province__name__icontains=location
        )
    
    # Filter by skills (exact or list)
    if filters.get('skills'):
        skills = filters['skills']
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(',')]
        # Filter recruiters who have at least one of the skills
        queryset = queryset.filter(skills__skill__name__in=skills).distinct()
    
    return queryset

def get_matching_jobs(recruiter: Recruiter) -> list:
    """
    Tìm kiếm công việc phù hợp với hồ sơ ứng viên.
    Sử dụng kết quả matching AI đã tính toán sẵn.
    """
    # Get top 10 jobs with highest overall score
    matches = AIMatchingScore.objects.filter(
        recruiter=recruiter,
        is_valid=True
    ).select_related('job', 'job__company', 'job__address').order_by('-overall_score')[:10]
    
    return [match.job for match in matches]

def get_recruiter_applications(recruiter: Recruiter) -> QuerySet:
    """
    Lấy các CV đã ứng tuyển của hồ sơ ứng viên.
    """
    return recruiter.applications.all()

def get_saved_jobs(recruiter: Recruiter) -> QuerySet:
    """
    Lấy các công việc đã lưu của hồ sơ ứng viên.
    """
    return recruiter.saved_jobs.all()
