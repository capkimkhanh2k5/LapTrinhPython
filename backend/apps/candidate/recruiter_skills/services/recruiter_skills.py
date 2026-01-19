from typing import Optional
from datetime import date

from pydantic import BaseModel
from django.db import transaction

from apps.candidate.recruiters.models import Recruiter
from apps.candidate.skills.models import Skill
from apps.candidate.recruiter_skills.models import RecruiterSkill


class SkillInput(BaseModel):
    """Input để tạo/update skill cho recruiter"""
    skill_id: Optional[int] = None
    proficiency_level: Optional[str] = None
    years_of_experience: Optional[int] = None
    last_used_date: Optional[date] = None
    
    class Config:
        arbitrary_types_allowed = True


@transaction.atomic
def create_skill(recruiter: Recruiter, data: SkillInput) -> RecruiterSkill:
    """
    Tạo skill mới cho recruiter.
    
    Returns:
        RecruiterSkill: Skill vừa tạo
    
    Raises:
        ValueError: Nếu skill_id không tồn tại hoặc đã được thêm
    """
    # Kiểm tra skill tồn tại
    skill = Skill.objects.filter(id=data.skill_id).first()
    if not skill:
        raise ValueError("Skill không tồn tại!")
    
    # Kiểm tra đã thêm skill này chưa
    if RecruiterSkill.objects.filter(recruiter=recruiter, skill=skill).exists():
        raise ValueError("Skill này đã được thêm!")
    
    # Tạo RecruiterSkill
    recruiter_skill = RecruiterSkill.objects.create(
        recruiter=recruiter,
        skill=skill,
        proficiency_level=data.proficiency_level or 'intermediate',
        years_of_experience=data.years_of_experience,
        last_used_date=data.last_used_date,
    )
    
    return recruiter_skill


@transaction.atomic
def update_skill(recruiter_skill: RecruiterSkill, data: SkillInput) -> RecruiterSkill:
    """
    Cập nhật thông tin skill của recruiter.
    Không cho phép update skill_id.
    
    Returns:
        RecruiterSkill: Skill đã cập nhật
    """
    fields = data.dict(exclude_unset=True)
    
    # xoá skill_id nếu có (không cho update)
    fields.pop('skill_id', None)
    
    for field, value in fields.items():
        if value is not None:
            setattr(recruiter_skill, field, value)
    
    recruiter_skill.save()
    return recruiter_skill


@transaction.atomic
def delete_skill(recruiter_skill: RecruiterSkill) -> None:
    """Xóa skill của recruiter (Hard delete)"""
    recruiter_skill.delete()


@transaction.atomic
def bulk_add_skills(recruiter: Recruiter, skills_data: list[SkillInput]) -> list[RecruiterSkill]:
    """
    Thêm nhiều skill cùng lúc cho recruiter.
    Skip duplicate skills without raising error.
    
    Returns:
        list[RecruiterSkill]: Danh sách skill vừa thêm
    """
    created_skills = []
    
    # Lấy skill_ids đã tồn tại của recruiter
    existing_skill_ids = set(
        RecruiterSkill.objects.filter(recruiter=recruiter).values_list('skill_id', flat=True)
    )
    
    for skill_data in skills_data:
        # Bỏ qua nếu skill đã tồn tại
        if skill_data.skill_id in existing_skill_ids:
            continue
        
        # Kiểm tra skill tồn tại
        skill = Skill.objects.filter(id=skill_data.skill_id).first()
        if not skill:
            continue
        
        # Tạo RecruiterSkill mới
        recruiter_skill = RecruiterSkill.objects.create(
            recruiter=recruiter,
            skill=skill,
            proficiency_level=skill_data.proficiency_level or 'intermediate',
            years_of_experience=skill_data.years_of_experience,
            last_used_date=skill_data.last_used_date,
        )
        created_skills.append(recruiter_skill)
        existing_skill_ids.add(skill_data.skill_id)
    
    return created_skills