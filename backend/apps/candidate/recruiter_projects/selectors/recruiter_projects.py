from typing import Optional
from django.db.models import QuerySet
from apps.candidate.recruiter_projects.models import RecruiterProject


def list_projects_by_recruiter(recruiter_id: int) -> QuerySet[RecruiterProject]:
    """
    Lấy danh sách dự án của recruiter.
    Ordering: display_order, -start_date
    """
    return RecruiterProject.objects.filter(
        recruiter_id=recruiter_id
    ).order_by('display_order', '-start_date')


def get_project_by_id(project_id: int) -> Optional[RecruiterProject]:
    """
    Lấy chi tiết một dự án.
    Trả về None nếu không tìm thấy.
    """
    try:
        return RecruiterProject.objects.select_related(
            'recruiter'
        ).get(id=project_id)
    except RecruiterProject.DoesNotExist:
        return None
