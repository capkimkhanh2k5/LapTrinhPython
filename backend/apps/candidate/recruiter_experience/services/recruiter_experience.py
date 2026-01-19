from typing import Optional
from datetime import date
from pydantic import BaseModel
from django.db import transaction
from django.db.models import Max

from apps.candidate.recruiter_experience.models import RecruiterExperience
from apps.candidate.recruiters.models import Recruiter


class ExperienceInput(BaseModel):
    """Pydantic input model cho create/update experience"""
    
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    industry_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    address_id: Optional[int] = None
    achievements: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


@transaction.atomic
def create_experience_service(recruiter: Recruiter, data: ExperienceInput) -> RecruiterExperience:
    """
    Tạo một kinh nghiệm làm việc mới cho ứng viên.
    
    Business rule:
    - Tự động set display_order = max hiện tại + 1
    """
    # Get max display_order
    max_order = RecruiterExperience.objects.filter(
        recruiter=recruiter
    ).aggregate(Max('display_order'))['display_order__max']
    
    next_order = (max_order or 0) + 1
    
    fields = data.dict(exclude_unset=True)
    
    # Handle FK fields
    industry_id = fields.pop('industry_id', None)
    address_id = fields.pop('address_id', None)
    
    experience = RecruiterExperience.objects.create(
        recruiter=recruiter,
        display_order=next_order,
        industry_id=industry_id,
        address_id=address_id,
        **fields
    )
    return experience


@transaction.atomic
def update_experience_service(experience: RecruiterExperience, data: ExperienceInput) -> RecruiterExperience:
    """
    Cập nhật thông tin kinh nghiệm làm việc.
    Chỉ update các fields có trong data.
    """
    fields = data.dict(exclude_unset=True)
    
    # Handle FK fields
    if 'industry_id' in fields:
        experience.industry_id = fields.pop('industry_id')
    if 'address_id' in fields:
        experience.address_id = fields.pop('address_id')
    
    for field, value in fields.items():
        setattr(experience, field, value)
    
    experience.save()
    return experience


@transaction.atomic
def delete_experience_service(experience: RecruiterExperience) -> None:
    """
    Xóa một kinh nghiệm làm việc.
    """
    experience.delete()


@transaction.atomic
def reorder_experience_service(recruiter: Recruiter, order_data: list) -> None:
    """
    Sắp xếp lại thứ tự hiển thị của các kinh nghiệm.
    
    Input: [{'id': 1, 'display_order': 0}, {'id': 2, 'display_order': 1}]
    
    Business rule:
    - Tất cả id phải thuộc về recruiter
    """
    # Get all experience ids belonging to recruiter
    valid_ids = set(
        RecruiterExperience.objects.filter(recruiter=recruiter).values_list('id', flat=True)
    )
    
    # Validate all ids belong to recruiter
    for item in order_data:
        if item['id'] not in valid_ids:
            raise ValueError(f"Experience id {item['id']} does not belong to this recruiter")
    
    # Build list of experience objects to update
    experience_updates = []
    for item in order_data:
        experience = RecruiterExperience.objects.get(id=item['id'])
        experience.display_order = item['display_order']
        experience_updates.append(experience)
    
    # Bulk update for performance
    RecruiterExperience.objects.bulk_update(experience_updates, ['display_order'])
