from typing import Optional
from django.db.models import QuerySet
from apps.candidate.recruiter_certifications.models import RecruiterCertification


def list_certifications_by_recruiter(recruiter_id: int) -> QuerySet[RecruiterCertification]:
    """
    Lấy danh sách chứng chỉ của recruiter.
    Ordering: display_order, -issue_date
    """
    return RecruiterCertification.objects.filter(
        recruiter_id=recruiter_id
    ).order_by('display_order', '-issue_date')


def get_certification_by_id(certification_id: int) -> Optional[RecruiterCertification]:
    """
    Lấy chi tiết một chứng chỉ.
    Trả về None nếu không tìm thấy.
    """
    try:
        return RecruiterCertification.objects.select_related(
            'recruiter'
        ).get(id=certification_id)
    except RecruiterCertification.DoesNotExist:
        return None
