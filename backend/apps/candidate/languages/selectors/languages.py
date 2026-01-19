from django.db.models import QuerySet
from apps.candidate.languages.models import Language


def list_all_languages() -> QuerySet[Language]:
    """
    Lấy danh sách tất cả ngôn ngữ đang active.
    """
    return Language.objects.filter(is_active=True).order_by('language_name')
