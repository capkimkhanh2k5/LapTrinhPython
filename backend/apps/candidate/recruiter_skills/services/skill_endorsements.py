from django.db import transaction

from apps.candidate.recruiters.models import Recruiter
from apps.candidate.recruiter_skills.models import RecruiterSkill
from apps.social.skill_endorsements.models import SkillEndorsement


@transaction.atomic
def endorse_skill_service(recruiter_skill: RecruiterSkill, endorsed_by: Recruiter, relationship: str = '') -> SkillEndorsement:
    """
    Xác nhận kỹ năng cho recruiter.
    
    Args:
        recruiter_skill: RecruiterSkill object
        endorsed_by: Recruiter object who is endorsing the skill
        relationship: Relationship between the two recruiters
    
    Returns:
        SkillEndorsement: SkillEndorsement object
    
    Raises:
        ValueError: Nếu recruiter đang xác nhận cho skill của chính mình hoặc đã xác nhận kỹ năng này
    """
    # Không thể xác nhận cho skill của chính mình
    if recruiter_skill.recruiter == endorsed_by:
        raise ValueError("Cannot endorse your own skill")
    
    # Kiểm tra nếu đã xác nhận kỹ năng này
    if SkillEndorsement.objects.filter(recruiter_skill=recruiter_skill, endorsed_by=endorsed_by).exists():
        raise ValueError("You have already endorsed this skill")
    
    # Tăng endorsement count
    recruiter_skill.endorsement_count += 1
    recruiter_skill.save(update_fields=['endorsement_count'])
    
    # Tạo endorsement record
    return SkillEndorsement.objects.create(
        recruiter_skill=recruiter_skill,
        endorsed_by=endorsed_by,
        relationship=relationship,
    )


@transaction.atomic
def remove_endorsement_service(recruiter_skill: RecruiterSkill, endorsed_by: Recruiter) -> None:
    """
    Xóa xác nhận kỹ năng.
    
    Args:
        recruiter_skill: RecruiterSkill object
        endorsed_by: Recruiter object who is removing the endorsement
    
    Raises:
        ValueError: Nếu endorsement không tồn tại
    """
    endorsement = SkillEndorsement.objects.filter(
        recruiter_skill=recruiter_skill, 
        endorsed_by=endorsed_by
    ).first()
    
    if not endorsement:
        raise ValueError("Endorsement does not exist")
    
    # Giảm endorsement count
    recruiter_skill.endorsement_count = max(0, recruiter_skill.endorsement_count - 1)
    recruiter_skill.save(update_fields=['endorsement_count'])
    
    # Xóa endorsement record
    endorsement.delete()
