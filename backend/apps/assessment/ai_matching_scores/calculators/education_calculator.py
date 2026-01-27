from decimal import Decimal
from typing import Optional

from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter


# Education level hierarchy (higher = more advanced)
EDUCATION_LEVELS = {
    'thpt': 1,       # High School
    'trung_cap': 2,  # Vocational
    'cao_dang': 3,   # College
    'dai_hoc': 4,    # Bachelor's
    'thac_si': 5,    # Master's
    'tien_si': 6,    # PhD
    'khac': 2,       # Other (treated as vocational level)
}


def get_education_level_value(level: Optional[str]) -> int:
    """Get numeric value for education level."""
    if not level:
        return 0
    return EDUCATION_LEVELS.get(level, 2)


def calculate_education_score(job: Job, recruiter: Recruiter) -> dict:
    """
    Calculate education match score between Job and Recruiter.
    
    Algorithm:
    1. Get job's required education level (from job.level or category settings)
    2. Get recruiter's highest_education_level
    3. Score based on comparison:
       - Meets or exceeds requirement: 100 points
       - 1 level below: 70 points
       - 2 levels below: 40 points
       - More than 2 levels below: 20 points
    
    Note: Currently job model doesn't have explicit education requirement field,
    so we infer from job level (intern/fresher = lower requirement, senior+ = higher)
    
    Args:
        job: Job instance
        recruiter: Recruiter instance
        
    Returns:
        dict with score (0-100), details
    """
    # Infer required education from job level
    job_level = job.level
    required_education = _infer_required_education(job_level)
    required_value = get_education_level_value(required_education)
    
    # Get recruiter's education
    recruiter_education = recruiter.highest_education_level
    recruiter_value = get_education_level_value(recruiter_education)
    
    # Handle case where recruiter has no education info
    if not recruiter_education:
        return {
            'score': Decimal('50.00'),
            'details': {
                'required_education': required_education,
                'required_value': required_value,
                'recruiter_education': None,
                'recruiter_value': 0,
                'status': 'unknown',
                'message': 'Recruiter education level not specified',
            }
        }
    
    # Calculate score based on education gap
    education_gap = required_value - recruiter_value
    
    if education_gap <= 0:
        # Meets or exceeds requirement
        score = Decimal('100.00')
        status = 'meets_or_exceeds'
    elif education_gap == 1:
        # UPDATED: 1 level below - experience often compensates for education
        score = Decimal('85.00')
        status = 'slightly_below'
    elif education_gap == 2:
        # UPDATED: 2 levels below - still consider if experience is strong
        score = Decimal('60.00')
        status = 'below_requirement'
    else:
        # More than 2 levels below
        score = Decimal('30.00')
        status = 'significantly_below'
    
    return {
        'score': score,
        'details': {
            'required_education': required_education,
            'required_value': required_value,
            'recruiter_education': recruiter_education,
            'recruiter_value': recruiter_value,
            'education_gap': education_gap,
            'status': status,
        }
    }


def _infer_required_education(job_level: str) -> str:
    """
    Infer required education level from job level.
    
    This is a heuristic since jobs don't have explicit education requirements.
    """
    level_to_education = {
        'intern': 'cao_dang',      # Internship: College or higher
        'fresher': 'dai_hoc',      # Fresher: Bachelor's
        'junior': 'dai_hoc',       # Junior: Bachelor's
        'middle': 'dai_hoc',       # Middle: Bachelor's
        'senior': 'dai_hoc',       # Senior: Bachelor's
        'lead': 'dai_hoc',         # Team Lead: Bachelor's
        'manager': 'dai_hoc',      # Manager: Bachelor's (prefer Master's)
        'director': 'thac_si',     # Director: Master's preferred
    }
    return level_to_education.get(job_level, 'dai_hoc')
