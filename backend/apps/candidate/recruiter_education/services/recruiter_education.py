from typing import Optional
from datetime import date
from decimal import Decimal
from pydantic import BaseModel
from django.db import transaction
from django.db.models import Max

from apps.candidate.recruiter_education.models import RecruiterEducation
from apps.candidate.recruiters.models import Recruiter


class EducationInput(BaseModel):
    """Pydantic input model cho create/update education"""
    
    school_name: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    gpa: Optional[Decimal] = None
    description: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


@transaction.atomic
def create_education_service(recruiter: Recruiter, data: EducationInput) -> RecruiterEducation:
    """
    Tạo một học vấn mới cho ứng viên.
    
    Business rule:
    - Tự động set display_order = max hiện tại + 1
    """
    # Get max display_order
    max_order = RecruiterEducation.objects.filter(
        recruiter=recruiter
    ).aggregate(Max('display_order'))['display_order__max']
    
    next_order = (max_order or 0) + 1
    
    fields = data.dict(exclude_unset=True)
    
    education = RecruiterEducation.objects.create(
        recruiter=recruiter,
        display_order=next_order,
        **fields
    )
    return education


@transaction.atomic
def update_education_service(education: RecruiterEducation, data: EducationInput) -> RecruiterEducation:
    """
    Cập nhật thông tin học vấn.
    Chỉ update các fields có trong data.
    """
    fields = data.dict(exclude_unset=True)
    
    for field, value in fields.items():
        setattr(education, field, value)
    
    education.save()
    return education


@transaction.atomic
def delete_education_service(education: RecruiterEducation) -> None:
    """
    Xóa một học vấn.
    """
    education.delete()


@transaction.atomic
def reorder_education_service(recruiter: Recruiter, order_data: list) -> None:
    """
    Sắp xếp lại thứ tự hiển thị của các học vấn.
    
    Input: [{'id': 1, 'display_order': 0}, {'id': 2, 'display_order': 1}]
    
    Business rule:
    - Tất cả id phải thuộc về recruiter
    """
    # Get all education ids belonging to recruiter
    valid_ids = set(
        RecruiterEducation.objects.filter(recruiter=recruiter).values_list('id', flat=True)
    )
    
    # Validate all ids belong to recruiter
    for item in order_data:
        if item['id'] not in valid_ids:
            raise ValueError(f"Education id {item['id']} does not belong to this recruiter")
    
    # Build list of education objects to update
    education_updates = []
    for item in order_data:
        education = RecruiterEducation.objects.get(id=item['id'])
        education.display_order = item['display_order']
        education_updates.append(education)
    
    # Bulk update for performance
    RecruiterEducation.objects.bulk_update(education_updates, ['display_order'])