from decimal import Decimal
from typing import Optional

from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter


def calculate_salary_score(job: Job, recruiter: Recruiter) -> dict:
    """
    Calculate salary match score between Job and Recruiter.
    
    Algorithm:
    1. If job salary is negotiable: 80 points baseline
    2. Calculate overlap between job salary range and recruiter's desired salary:
       - Full overlap (job meets recruiter's expectations): 100 points
       - Partial overlap > 50%: 80 points
       - Partial overlap > 0%: 60 points
       - No overlap but close: 40 points
       - Far apart: 20 points
    
    Args:
        job: Job instance
        recruiter: Recruiter instance
        
    Returns:
        dict with score (0-100), details
    """
    # Get job salary range
    job_min = job.salary_min
    job_max = job.salary_max
    job_currency = job.salary_currency or 'VND'
    is_negotiable = job.is_salary_negotiable
    
    # Get recruiter's desired salary range
    recruiter_min = recruiter.desired_salary_min
    recruiter_max = recruiter.desired_salary_max
    recruiter_currency = recruiter.salary_currency or 'VND'
    
    # Handle negotiable salary
    if is_negotiable:
        return {
            'score': Decimal('80.00'),
            'details': {
                'is_negotiable': True,
                'status': 'negotiable',
                'message': 'Salary is negotiable',
            }
        }
    
    # Handle missing salary information
    if not job_min and not job_max:
        return {
            'score': Decimal('70.00'),
            'details': {
                'job_salary_min': None,
                'job_salary_max': None,
                'status': 'job_salary_unknown',
                'message': 'Job salary not specified',
            }
        }
    
    if not recruiter_min and not recruiter_max:
        return {
            'score': Decimal('70.00'),
            'details': {
                'recruiter_salary_min': None,
                'recruiter_salary_max': None,
                'status': 'recruiter_expectation_unknown',
                'message': 'Recruiter salary expectation not specified',
            }
        }
    
    # Check currency mismatch
    if job_currency != recruiter_currency:
        return {
            'score': Decimal('50.00'),
            'details': {
                'job_currency': job_currency,
                'recruiter_currency': recruiter_currency,
                'status': 'currency_mismatch',
                'message': 'Currency mismatch between job and recruiter',
            }
        }
    
    # Normalize ranges (use same value for min/max if only one is specified)
    j_min = float(job_min) if job_min else float(job_max or 0)
    j_max = float(job_max) if job_max else float(job_min or 0)
    r_min = float(recruiter_min) if recruiter_min else float(recruiter_max or 0)
    r_max = float(recruiter_max) if recruiter_max else float(recruiter_min or 0)
    
    # Calculate overlap
    overlap_start = max(j_min, r_min)
    overlap_end = min(j_max, r_max)
    
    if overlap_start <= overlap_end:
        # There is an overlap
        overlap_size = overlap_end - overlap_start
        recruiter_range = r_max - r_min if r_max > r_min else r_max * 0.1 or 1
        overlap_ratio = overlap_size / recruiter_range if recruiter_range > 0 else 1
        
        if j_min <= r_min and j_max >= r_max:
            # Job fully covers recruiter's expectation
            score = Decimal('100.00')
            status = 'full_match'
        elif overlap_ratio >= 0.5:
            score = Decimal('85.00')
            status = 'good_overlap'
        else:
            score = Decimal('70.00')
            status = 'partial_overlap'
    else:
        # No overlap
        if j_max < r_min:
            # Job pays less than recruiter expects
            gap_ratio = (r_min - j_max) / r_min if r_min > 0 else 1
            if gap_ratio <= 0.1:
                score = Decimal('60.00')
                status = 'slightly_below_expectation'
            elif gap_ratio <= 0.2:
                score = Decimal('40.00')
                status = 'below_expectation'
            else:
                score = Decimal('20.00')
                status = 'far_below_expectation'
        else:
            # Job pays more than recruiter expects (rare case)
            score = Decimal('100.00')
            status = 'above_expectation'
    
    return {
        'score': score,
        'details': {
            'job_salary_min': float(j_min),
            'job_salary_max': float(j_max),
            'recruiter_salary_min': float(r_min),
            'recruiter_salary_max': float(r_max),
            'currency': job_currency,
            'overlap_start': float(overlap_start) if overlap_start <= overlap_end else None,
            'overlap_end': float(overlap_end) if overlap_start <= overlap_end else None,
            'status': status,
        }
    }
