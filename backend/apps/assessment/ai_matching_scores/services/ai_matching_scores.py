from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from django.db import transaction
from django.db.models import Q
from django.db.models import Avg, Count, Max, Min

from apps.assessment.ai_matching_scores.models import AIMatchingScore
from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter
from apps.assessment.ai_matching_scores.calculators import (
    calculate_skill_score,
    calculate_experience_score,
    calculate_education_score,
    calculate_location_score,
    calculate_salary_score,
    calculate_semantic_score,
    is_semantic_enabled,
)



# Matching weights configuration (without semantic)
MATCHING_WEIGHTS_BASIC = {
    'skill': Decimal('0.35'),       # 35%
    'experience': Decimal('0.25'),  # 25%
    'education': Decimal('0.15'),   # 15%
    'location': Decimal('0.10'),    # 10%
    'salary': Decimal('0.15'),      # 15%
}

# Matching weights with semantic (when OpenAI enabled)
MATCHING_WEIGHTS_SEMANTIC = {
    'skill': Decimal('0.25'),       # 25% (reduced)
    'experience': Decimal('0.20'),  # 20% (reduced)
    'education': Decimal('0.10'),   # 10% (reduced)
    'location': Decimal('0.10'),    # 10%
    'salary': Decimal('0.10'),      # 10% (reduced)
    'semantic': Decimal('0.25'),    # 25% (new)
}


class CalculateMatchInput(BaseModel):
    """Input for calculating a single match."""
    job_id: int
    recruiter_id: int


class BatchCalculateInput(BaseModel):
    """Input for batch calculating matches."""
    job_id: int
    recruiter_ids: list[int] = Field(max_length=100)
    
    @field_validator('recruiter_ids')
    @classmethod
    def validate_recruiter_ids(cls, v):
        if len(v) > 100:
            raise ValueError('Maximum 100 recruiters per batch')
        if len(v) == 0:
            raise ValueError('At least one recruiter required')
        return v


class RefreshMatchInput(BaseModel):
    """Input for refreshing match scores."""
    job_id: Optional[int] = None
    recruiter_id: Optional[int] = None
    
    @field_validator('recruiter_id')
    @classmethod
    def validate_at_least_one(cls, v, info):
        job_id = info.data.get('job_id')
        if not job_id and not v:
            raise ValueError('At least one of job_id or recruiter_id is required')
        return v


def calculate_single_match(input_data: CalculateMatchInput) -> AIMatchingScore:
    """
    Calculate and save match score for a single job-recruiter pair.
    
    Args:
        input_data: CalculateMatchInput with job_id and recruiter_id
        
    Returns:
        AIMatchingScore instance (created or updated)
        
    Raises:
        Job.DoesNotExist: If job not found
        Recruiter.DoesNotExist: If recruiter not found
    """
    job = Job.objects.select_related('address__commune__province').get(
        id=input_data.job_id
    )
    recruiter = Recruiter.objects.select_related('address__commune__province').get(
        id=input_data.recruiter_id
    )
    
    # Calculate individual scores
    skill_result = calculate_skill_score(job, recruiter)
    experience_result = calculate_experience_score(job, recruiter)
    education_result = calculate_education_score(job, recruiter)
    location_result = calculate_location_score(job, recruiter)
    salary_result = calculate_salary_score(job, recruiter)
    
    # Calculate semantic score if OpenAI is enabled
    semantic_result = None
    use_semantic = is_semantic_enabled()
    
    if use_semantic:
        semantic_result = calculate_semantic_score(job, recruiter)
        use_semantic = semantic_result.get('is_semantic', False)
    
    # Select weights based on semantic availability
    if use_semantic:
        weights = MATCHING_WEIGHTS_SEMANTIC
        overall_score = (
            weights['skill'] * skill_result['score'] +
            weights['experience'] * experience_result['score'] +
            weights['education'] * education_result['score'] +
            weights['location'] * location_result['score'] +
            weights['salary'] * salary_result['score'] +
            weights['semantic'] * semantic_result['score']
        ).quantize(Decimal('0.01'))
    else:
        weights = MATCHING_WEIGHTS_BASIC
        overall_score = (
            weights['skill'] * skill_result['score'] +
            weights['experience'] * experience_result['score'] +
            weights['education'] * education_result['score'] +
            weights['location'] * location_result['score'] +
            weights['salary'] * salary_result['score']
        ).quantize(Decimal('0.01'))
    
    # Prepare matching details
    matching_details = {
        'skill': skill_result,
        'experience': experience_result,
        'education': education_result,
        'location': location_result,
        'salary': salary_result,
        'weights': {k: float(v) for k, v in weights.items()},
        'semantic_enabled': use_semantic,
    }
    
    if semantic_result:
        matching_details['semantic'] = semantic_result
    
    # Serialize Decimal to float for JSON storage
    for key in matching_details:
        if isinstance(matching_details[key], dict) and 'score' in matching_details[key]:
            matching_details[key]['score'] = float(matching_details[key]['score'])
    
    # Create or update score
    score, created = AIMatchingScore.objects.update_or_create(
        job=job,
        recruiter=recruiter,
        defaults={
            'overall_score': overall_score,
            'skill_match_score': skill_result['score'],
            'experience_match_score': experience_result['score'],
            'education_match_score': education_result['score'],
            'location_match_score': location_result['score'],
            'salary_match_score': salary_result['score'],
            'matching_details': matching_details,
            'is_valid': True,
        }
    )
    
    return score


def batch_calculate_matches(input_data: BatchCalculateInput) -> list[AIMatchingScore]:
    """
    Calculate match scores for multiple recruiters against a single job.
    
    Uses transaction to ensure atomicity.
    
    Args:
        input_data: BatchCalculateInput with job_id and recruiter_ids
        
    Returns:
        List of AIMatchingScore instances
    """
    results = []
    
    with transaction.atomic():
        for recruiter_id in input_data.recruiter_ids:
            try:
                score = calculate_single_match(
                    CalculateMatchInput(
                        job_id=input_data.job_id,
                        recruiter_id=recruiter_id
                    )
                )
                results.append(score)
            except (Job.DoesNotExist, Recruiter.DoesNotExist):
                # Skip invalid IDs
                continue
    
    return results


def refresh_matches(input_data: RefreshMatchInput) -> int:
    """
    Refresh (recalculate) existing match scores.
    
    If job_id provided: refresh all scores for that job
    If recruiter_id provided: refresh all scores for that recruiter
    If both provided: refresh only that specific pair
    
    Args:
        input_data: RefreshMatchInput
        
    Returns:
        Number of scores refreshed
    """
    # Build query filter
    filters = Q()
    if input_data.job_id:
        filters &= Q(job_id=input_data.job_id)
    if input_data.recruiter_id:
        filters &= Q(recruiter_id=input_data.recruiter_id)
    
    # Get existing scores to refresh
    existing_scores = AIMatchingScore.objects.filter(filters)
    
    count = 0
    with transaction.atomic():
        for score in existing_scores:
            try:
                calculate_single_match(
                    CalculateMatchInput(
                        job_id=score.job_id,
                        recruiter_id=score.recruiter_id
                    )
                )
                count += 1
            except (Job.DoesNotExist, Recruiter.DoesNotExist):
                # Mark as invalid if entities no longer exist
                score.is_valid = False
                score.save(update_fields=['is_valid'])
    
    return count


def get_matching_insights(
    job_id: Optional[int] = None,
    recruiter_id: Optional[int] = None
) -> dict:
    """
    Generate insights about matching patterns.
    
    Args:
        job_id: Optional job ID to filter insights
        recruiter_id: Optional recruiter ID to filter insights
        
    Returns:
        Dictionary with insights data
    """
    
    # Build query filter
    filters = Q(is_valid=True)
    if job_id:
        filters &= Q(job_id=job_id)
    if recruiter_id:
        filters &= Q(recruiter_id=recruiter_id)
    
    queryset = AIMatchingScore.objects.filter(filters)
    
    # Calculate aggregations
    aggregations = queryset.aggregate(
        total_matches=Count('id'),
        avg_overall_score=Avg('overall_score'),
        max_overall_score=Max('overall_score'),
        min_overall_score=Min('overall_score'),
        avg_skill_score=Avg('skill_match_score'),
        avg_experience_score=Avg('experience_match_score'),
        avg_education_score=Avg('education_match_score'),
        avg_location_score=Avg('location_match_score'),
        avg_salary_score=Avg('salary_match_score'),
    )
    
    # Score distribution
    high_matches = queryset.filter(overall_score__gte=80).count()
    medium_matches = queryset.filter(overall_score__gte=50, overall_score__lt=80).count()
    low_matches = queryset.filter(overall_score__lt=50).count()
    
    return {
        'summary': {
            'total_matches': aggregations['total_matches'],
            'avg_overall_score': float(aggregations['avg_overall_score'] or 0),
            'max_overall_score': float(aggregations['max_overall_score'] or 0),
            'min_overall_score': float(aggregations['min_overall_score'] or 0),
        },
        'score_distribution': {
            'high': high_matches,      # >= 80
            'medium': medium_matches,  # 50-79
            'low': low_matches,        # < 50
        },
        'component_averages': {
            'skill': float(aggregations['avg_skill_score'] or 0),
            'experience': float(aggregations['avg_experience_score'] or 0),
            'education': float(aggregations['avg_education_score'] or 0),
            'location': float(aggregations['avg_location_score'] or 0),
            'salary': float(aggregations['avg_salary_score'] or 0),
        },
        'filters_applied': {
            'job_id': job_id,
            'recruiter_id': recruiter_id,
        }
    }
