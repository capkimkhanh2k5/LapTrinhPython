from typing import Optional

from pydantic import BaseModel
from django.db import transaction

from apps.candidate.recruiter_languages.models import RecruiterLanguage
from apps.candidate.recruiters.models import Recruiter
from apps.candidate.languages.models import Language


class LanguageInput(BaseModel):
    """
    Pydantic input model cho create/update recruiter language
    """
    language_id: Optional[int] = None
    proficiency_level: Optional[str] = None
    is_native: Optional[bool] = None
    
    class Config:
        arbitrary_types_allowed = True


@transaction.atomic
def create_language(recruiter: Recruiter, data: LanguageInput) -> RecruiterLanguage:
    """
    Thêm ngôn ngữ mới cho recruiter.
    
    Raises:
        ValueError: Nếu language_id không tồn tại hoặc đã được thêm
    """
    # Kiểm tra language tồn tại
    language = Language.objects.filter(id=data.language_id, is_active=True).first()
    if not language:
        raise ValueError("Ngôn ngữ không tồn tại!")
    
    # Kiểm tra đã thêm language này chưa
    if RecruiterLanguage.objects.filter(recruiter=recruiter, language=language).exists():
        raise ValueError("Ngôn ngữ này đã được thêm!")
    
    # Tạo RecruiterLanguage
    recruiter_language = RecruiterLanguage.objects.create(
        recruiter=recruiter,
        language=language,
        proficiency_level=data.proficiency_level,
        is_native=data.is_native or False,
    )
    
    return recruiter_language


@transaction.atomic
def update_language(recruiter_language: RecruiterLanguage, data: LanguageInput) -> RecruiterLanguage:
    """
    Cập nhật thông tin ngôn ngữ.
    Không cho phép update language_id.
    """
    fields = data.dict(exclude_unset=True)
    
    # Không cho update language_id
    fields.pop('language_id', None)
    
    for field, value in fields.items():
        if value is not None:
            setattr(recruiter_language, field, value)
    
    recruiter_language.save()
    return recruiter_language


@transaction.atomic
def delete_language(recruiter_language: RecruiterLanguage) -> None:
    """
    Xóa ngôn ngữ của recruiter.
    """
    recruiter_language.delete()
