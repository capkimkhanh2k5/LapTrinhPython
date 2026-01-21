from typing import Optional
from decimal import Decimal

from apps.recruitment.jobs.models import Job
from apps.recruitment.job_skills.models import JobSkill
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.recruiter_skills.models import RecruiterSkill


# Proficiency level weights for scoring
PROFICIENCY_WEIGHTS = {
    'basic': 1,
    'intermediate': 2,
    'advanced': 3,
    'expert': 4,
}


def calculate_skill_score(job: Job, recruiter: Recruiter) -> dict:
    """
    Calculate skill match score between Job and Recruiter.
    
    Algorithm:
    1. Get all required skills for the job
    2. Get all skills of the recruiter
    3. For each job skill, check if recruiter has it:
       - Exact match with sufficient proficiency: full points
       - Exact match with lower proficiency: partial points
       - Missing required skill: penalty
    4. Bonus for extra relevant skills
    
    Args:
        job: Job instance
        recruiter: Recruiter instance
        
    Returns:
        dict with score (0-100), matched_skills, missing_skills, details
    """
    # Get job required skills
    job_skills = JobSkill.objects.filter(job=job).select_related('skill')
    
    # Get recruiter skills
    recruiter_skills = RecruiterSkill.objects.filter(
        recruiter=recruiter
    ).select_related('skill')
    
    # Create lookup for recruiter skills by skill_id
    recruiter_skill_map = {
        rs.skill_id: rs for rs in recruiter_skills
    }
    
    if not job_skills.exists():
        # No skills required, give 100% score
        return {
            'score': Decimal('100.00'),
            'matched_skills': [],
            'missing_skills': [],
            'details': {
                'message': 'Job has no skill requirements',
                'total_job_skills': 0,
                'total_matched': 0,
            }
        }
    
    matched_skills = []
    missing_skills = []
    total_points = Decimal('0')
    max_points = Decimal('0')
    
    for job_skill in job_skills:
        skill_id = job_skill.skill_id
        skill_name = job_skill.skill.name
        is_required = job_skill.is_required
        required_proficiency = job_skill.proficiency_level or 'intermediate'
        
        # Weight: required skills are worth more
        skill_weight = Decimal('2.0') if is_required else Decimal('1.0')
        max_skill_points = skill_weight * Decimal('100')
        max_points += max_skill_points
        
        if skill_id in recruiter_skill_map:
            recruiter_skill = recruiter_skill_map[skill_id]
            recruiter_proficiency = recruiter_skill.proficiency_level or 'intermediate'
            
            # Calculate proficiency match
            required_level = PROFICIENCY_WEIGHTS.get(required_proficiency, 2)
            recruiter_level = PROFICIENCY_WEIGHTS.get(recruiter_proficiency, 2)
            
            if recruiter_level >= required_level:
                # Full points for meeting or exceeding requirement
                points = max_skill_points
            else:
                # Partial points based on proficiency ratio
                ratio = Decimal(str(recruiter_level / required_level))
                points = max_skill_points * ratio
            
            total_points += points
            matched_skills.append({
                'skill_id': skill_id,
                'skill_name': skill_name,
                'required_proficiency': required_proficiency,
                'recruiter_proficiency': recruiter_proficiency,
                'is_required': is_required,
                'points_earned': float(points),
                'max_points': float(max_skill_points),
            })
        else:
            # Missing skill
            missing_skills.append({
                'skill_id': skill_id,
                'skill_name': skill_name,
                'required_proficiency': required_proficiency,
                'is_required': is_required,
            })
    
    # Calculate final score
    if max_points > 0:
        score = (total_points / max_points) * Decimal('100')
    else:
        score = Decimal('100.00')
    
    # Round to 2 decimal places
    score = score.quantize(Decimal('0.01'))
    
    return {
        'score': score,
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'details': {
            'total_job_skills': len(job_skills),
            'total_matched': len(matched_skills),
            'total_missing': len(missing_skills),
            'required_matched': sum(
                1 for s in matched_skills if s['is_required']
            ),
            'required_missing': sum(
                1 for s in missing_skills if s['is_required']
            ),
            'total_points': float(total_points),
            'max_points': float(max_points),
        }
    }
