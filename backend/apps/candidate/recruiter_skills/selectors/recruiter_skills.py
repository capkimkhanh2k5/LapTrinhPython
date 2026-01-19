from typing import Optional
from django.db.models import QuerySet
from apps.candidate.recruiter_skills.models import RecruiterSkill


def list_skills_by_recruiter(recruiter_id: int) -> QuerySet[RecruiterSkill]:
    """
    List all skills of a recruiter
    """
    return RecruiterSkill.objects.filter(
        recruiter_id=recruiter_id
    ).select_related('skill').order_by('-endorsement_count', 'skill__name')


def get_skill_by_id(skill_id: int) -> Optional[RecruiterSkill]:
    """
    Get a skill by ID
    """
    try:
        return RecruiterSkill.objects.select_related(
            'skill', 'recruiter'
        ).get(id=skill_id)
    except RecruiterSkill.DoesNotExist:
        return None


def get_skill_by_recruiter_and_skill_id(recruiter_id: int, skill_id: int) -> Optional[RecruiterSkill]:
    """
    Get a skill by recruiter ID and skill ID (FK)
    """
    try:
        return RecruiterSkill.objects.select_related(
            'skill', 'recruiter'
        ).get(recruiter_id=recruiter_id, skill_id=skill_id)
    except RecruiterSkill.DoesNotExist:
        return None