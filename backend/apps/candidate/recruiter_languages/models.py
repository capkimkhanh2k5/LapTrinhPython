from django.db import models


class RecruiterLanguage(models.Model):
    """Bảng Recruiter_Languages - Ngôn ngữ của ứng viên"""
    
    class ProficiencyLevel(models.TextChoices):
        BASIC = 'basic', 'Cơ bản'
        INTERMEDIATE = 'intermediate', 'Trung bình'
        ADVANCED = 'advanced', 'Khá'
        FLUENT = 'fluent', 'Thành thạo'
        NATIVE = 'native', 'Bản xứ'
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='languages',
        db_index=True,
        verbose_name='Ứng viên'
    )
    language = models.ForeignKey(
        'candidate_languages.Language',
        on_delete=models.CASCADE,
        related_name='recruiter_languages',
        verbose_name='Ngôn ngữ'
    )
    proficiency_level = models.CharField(
        max_length=20,
        choices=ProficiencyLevel.choices,
        verbose_name='Trình độ'
    )
    is_native = models.BooleanField(
        default=False,
        verbose_name='Ngôn ngữ mẹ đẻ'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'recruiter_languages'
        verbose_name = 'Ngôn ngữ ứng viên'
        verbose_name_plural = 'Ngôn ngữ ứng viên'
        unique_together = ['recruiter', 'language']
    
    def __str__(self):
        return f"{self.recruiter.user.full_name} - {self.language.language_name}"
