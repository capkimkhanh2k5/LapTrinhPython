from django.db import models


class RecruiterSkill(models.Model):
    """Bảng Recruiter_Skills - Kỹ năng của người tìm việc"""
    
    class ProficiencyLevel(models.TextChoices):
        BASIC = 'basic', 'Cơ bản'
        INTERMEDIATE = 'intermediate', 'Trung bình'
        ADVANCED = 'advanced', 'Nâng cao'
        EXPERT = 'expert', 'Chuyên gia'
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='skills',
        db_index=True,
        verbose_name='Ứng viên'
    )
    skill = models.ForeignKey(
        'candidate_skills.Skill',
        on_delete=models.CASCADE,
        related_name='recruiter_skills',
        db_index=True,
        verbose_name='Kỹ năng'
    )
    proficiency_level = models.CharField(
        max_length=20,
        choices=ProficiencyLevel.choices,
        default=ProficiencyLevel.INTERMEDIATE,
        verbose_name='Mức độ thành thạo'
    )
    years_of_experience = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Số năm kinh nghiệm'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Đã xác minh'
    )
    endorsement_count = models.IntegerField(
        default=0,
        verbose_name='Số lượt xác nhận'
    )
    last_used_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày sử dụng gần nhất'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        db_table = 'recruiter_skills'
        verbose_name = 'Kỹ năng ứng viên'
        verbose_name_plural = 'Kỹ năng ứng viên'
        unique_together = ['recruiter', 'skill']
    
    def __str__(self):
        return f"{self.recruiter.user.full_name} - {self.skill.name}"
