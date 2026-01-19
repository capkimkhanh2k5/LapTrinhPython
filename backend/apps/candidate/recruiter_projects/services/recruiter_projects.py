from typing import Optional
from datetime import date

from pydantic import BaseModel
from django.db import transaction
from django.db.models import Max

from apps.candidate.recruiter_projects.models import RecruiterProject
from apps.candidate.recruiters.models import Recruiter


class ProjectInput(BaseModel):
    """
    Pydantic input model cho create/update project
    """
    project_name: Optional[str] = None
    description: Optional[str] = None
    project_url: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_ongoing: Optional[bool] = None
    technologies_used: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


@transaction.atomic
def create_project(recruiter: Recruiter, data: ProjectInput) -> RecruiterProject:
    """
    Tạo dự án mới cho recruiter.
    Auto set display_order = max + 1
    """
    # Get max display_order
    max_order = RecruiterProject.objects.filter(
        recruiter=recruiter
    ).aggregate(Max('display_order'))['display_order__max']
    
    next_order = (max_order or 0) + 1
    
    fields = data.dict(exclude_unset=True)
    
    project = RecruiterProject.objects.create(
        recruiter=recruiter,
        display_order=next_order,
        **fields
    )
    return project


@transaction.atomic
def update_project(project: RecruiterProject, data: ProjectInput) -> RecruiterProject:
    """
    Cập nhật thông tin dự án.
    """
    fields = data.dict(exclude_unset=True)
    
    for field, value in fields.items():
        setattr(project, field, value)
    
    project.save()
    return project


@transaction.atomic
def delete_project(project: RecruiterProject) -> None:
    """
    Xóa dự án.
    """
    project.delete()


@transaction.atomic
def reorder_project(recruiter: Recruiter, order_data: list) -> None:
    """
    Sắp xếp lại thứ tự hiển thị.
    Input: [{'id': 1, 'display_order': 0}, ...]
    """
    # Lấy tất cả project ids thuộc recruiter
    valid_ids = set(
        RecruiterProject.objects.filter(recruiter=recruiter).values_list('id', flat=True)
    )
    
    # Validate tất cả ids thuộc recruiter
    for item in order_data:
        if item['id'] not in valid_ids:
            raise ValueError(f"Project id {item['id']} does not belong to this recruiter")
    
    # Build list để update
    project_updates = []
    for item in order_data:
        proj = RecruiterProject.objects.get(id=item['id'])
        proj.display_order = item['display_order']
        project_updates.append(proj)
    
    # Bulk update
    RecruiterProject.objects.bulk_update(project_updates, ['display_order'])
