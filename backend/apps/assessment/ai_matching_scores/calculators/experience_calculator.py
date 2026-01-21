from decimal import Decimal

from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter


def calculate_experience_score(job: Job, recruiter: Recruiter) -> dict:
    """
    Calculate experience match score between Job and Recruiter.
    
    Algorithm:
    1. Get min/max experience years from Job
    2. Get years_of_experience from Recruiter
    3. Score based on how well recruiter fits the range:
       - Within range: 100 points
       - Slightly under (1-2 years): 70-90 points
       - Significantly under: 30-60 points
       - Over-qualified (reasonably): 90 points
       - Way over-qualified: 70 points (may not be interested)
    
    Args:
        job: Job instance
        recruiter: Recruiter instance
        
    Returns:
        dict with score (0-100), details
    """
    min_exp = job.experience_years_min or 0
    max_exp = job.experience_years_max
    recruiter_exp = recruiter.years_of_experience or 0
    
    # Determine score based on experience fit
    if max_exp is None:
        # No upper limit
        if recruiter_exp >= min_exp:
            score = Decimal('100.00')
            status = 'meets_requirement'
        elif recruiter_exp >= min_exp - 1:
            score = Decimal('85.00')
            status = 'slightly_under'
        elif recruiter_exp >= min_exp - 2:
            score = Decimal('70.00')
            status = 'under_requirement'
        else:
            # Calculate proportional score
            if min_exp > 0:
                ratio = recruiter_exp / min_exp
                score = Decimal(str(max(30, ratio * 60)))
            else:
                score = Decimal('30.00')
            status = 'significantly_under'
    else:
        # Has both min and max
        if min_exp <= recruiter_exp <= max_exp:
            # Perfect fit within range
            score = Decimal('100.00')
            status = 'perfect_fit'
        elif recruiter_exp < min_exp:
            # Under-qualified
            gap = min_exp - recruiter_exp
            if gap <= 1:
                score = Decimal('85.00')
                status = 'slightly_under'
            elif gap <= 2:
                score = Decimal('70.00')
                status = 'under_requirement'
            else:
                # Significant gap
                if min_exp > 0:
                    ratio = recruiter_exp / min_exp
                    score = Decimal(str(max(20, ratio * 50)))
                else:
                    score = Decimal('20.00')
                status = 'significantly_under'
        else:
            # Over-qualified
            overage = recruiter_exp - max_exp
            if overage <= 2:
                score = Decimal('90.00')
                status = 'slightly_over'
            elif overage <= 5:
                score = Decimal('75.00')
                status = 'over_qualified'
            else:
                # May not be interested in the role
                score = Decimal('60.00')
                status = 'significantly_over'
    
    # Round to 2 decimal places
    score = score.quantize(Decimal('0.01'))
    
    return {
        'score': score,
        'details': {
            'job_min_experience': min_exp,
            'job_max_experience': max_exp,
            'recruiter_experience': recruiter_exp,
            'status': status,
            'gap': recruiter_exp - min_exp if recruiter_exp < min_exp else 0,
        }
    }
