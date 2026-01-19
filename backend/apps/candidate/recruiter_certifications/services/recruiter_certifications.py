from typing import Optional
from datetime import date

from pydantic import BaseModel
from django.db import transaction
from django.db.models import Max

from apps.candidate.recruiter_certifications.models import RecruiterCertification
from apps.candidate.recruiters.models import Recruiter


class CertificationInput(BaseModel):
    """
    Input model cho Tạo và cập nhật chứng chỉ
    """
    certification_name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None
    does_not_expire: Optional[bool] = None
    
    class Config:
        arbitrary_types_allowed = True


@transaction.atomic
def create_certification_service(recruiter: Recruiter, data: CertificationInput) -> RecruiterCertification:
    """
    Tạo chứng chỉ mới cho recruiter.
    Auto set display_order = max + 1
    """
    # Get max display_order
    max_order = RecruiterCertification.objects.filter(
        recruiter=recruiter
    ).aggregate(Max('display_order'))['display_order__max']
    
    next_order = (max_order or 0) + 1
    
    fields = data.dict(exclude_unset=True)
    
    certification = RecruiterCertification.objects.create(
        recruiter=recruiter,
        display_order=next_order,
        **fields
    )
    return certification


@transaction.atomic
def update_certification_service(certification: RecruiterCertification, data: CertificationInput) -> RecruiterCertification:
    """
    Cập nhật thông tin chứng chỉ.
    """
    fields = data.dict(exclude_unset=True)
    
    for field, value in fields.items():
        setattr(certification, field, value)
    
    certification.save()
    return certification


@transaction.atomic
def delete_certification_service(certification: RecruiterCertification) -> None:
    """
    Xóa chứng chỉ.
    """
    certification.delete()


@transaction.atomic
def reorder_certification_service(recruiter: Recruiter, order_data: list) -> None:
    """
    Sắp xếp lại thứ tự hiển thị.
    Input: [{'id': 1, 'display_order': 0}, ...]
    """
    # Lấy tất cả certification ids thuộc recruiter
    valid_ids = set(
        RecruiterCertification.objects.filter(recruiter=recruiter).values_list('id', flat=True)
    )
    
    # Validate tất cả ids thuộc recruiter
    for item in order_data:
        if item['id'] not in valid_ids:
            raise ValueError(f"Certification id {item['id']} does not belong to this recruiter")
    
    # Build list để update
    certification_updates = []
    for item in order_data:
        cert = RecruiterCertification.objects.get(id=item['id'])
        cert.display_order = item['display_order']
        certification_updates.append(cert)
    
    # Bulk update
    RecruiterCertification.objects.bulk_update(certification_updates, ['display_order'])
