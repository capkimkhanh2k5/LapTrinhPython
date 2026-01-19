from typing import Optional
from django.db.models import QuerySet
from apps.candidate.recruiter_experience.models import RecruiterExperience


def list_experience_by_recruiter(recruiter_id: int) -> QuerySet[RecruiterExperience]:
    """
    Lấy danh sách tất cả kinh nghiệm làm việc của một ứng viên.
    Ordering: display_order, -start_date
    """
    return RecruiterExperience.objects.filter(
        recruiter_id=recruiter_id
    ).select_related('industry', 'address').order_by('display_order', '-start_date')


def get_experience_by_id(experience_id: int) -> Optional[RecruiterExperience]:
    """
    Lấy thông tin chi tiết của một kinh nghiệm cụ thể.
    Trả về None nếu không tìm thấy.
    """
    try:
        return RecruiterExperience.objects.select_related(
            'recruiter', 'industry', 'address'
        ).get(id=experience_id)
    except RecruiterExperience.DoesNotExist:
        return None
