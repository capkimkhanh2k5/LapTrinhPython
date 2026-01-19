from typing import Optional
from django.db.models import QuerySet
from apps.candidate.recruiter_education.models import RecruiterEducation


def list_education_by_recruiter(recruiter_id: int) -> QuerySet[RecruiterEducation]:
    """
    Lấy danh sách tất cả các học vấn của một ứng viên cụ thể.
    Ordering: display_order, -start_date
    """
    return RecruiterEducation.objects.filter(
        recruiter_id=recruiter_id
    ).order_by('display_order', '-start_date')


def get_education_by_id(education_id: int) -> Optional[RecruiterEducation]:
    """
    Lấy thông tin chi tiết của một học vấn cụ thể.
    Trả về None nếu không tìm thấy.
    """
    try:
        return RecruiterEducation.objects.select_related('recruiter').get(id=education_id)
    except RecruiterEducation.DoesNotExist:
        return None