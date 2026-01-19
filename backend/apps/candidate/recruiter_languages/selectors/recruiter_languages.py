from typing import Optional
from django.db.models import QuerySet
from apps.candidate.recruiter_languages.models import RecruiterLanguage


def list_languages_by_recruiter(recruiter_id: int) -> QuerySet[RecruiterLanguage]:
    """
    Lấy danh sách ngôn ngữ của recruiter.
    """
    return RecruiterLanguage.objects.filter(
        recruiter_id=recruiter_id
    ).select_related('language').order_by('-is_native', 'language__language_name')


def get_language_by_id(language_id: int) -> Optional[RecruiterLanguage]:
    """
    Lấy chi tiết một ngôn ngữ của recruiter.
    """
    try:
        return RecruiterLanguage.objects.select_related(
            'language', 'recruiter'
        ).get(id=language_id)
    except RecruiterLanguage.DoesNotExist:
        return None
