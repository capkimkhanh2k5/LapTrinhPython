from django.db import models


class JobSkill(models.Model):
    """Bảng Job_Skills - Kỹ năng yêu cầu cho công việc"""
    
    class ProficiencyLevel(models.TextChoices):
        BASIC = 'basic', 'Cơ bản'
        INTERMEDIATE = 'intermediate', 'Trung bình'
        ADVANCED = 'advanced', 'Nâng cao'
        EXPERT = 'expert', 'Chuyên gia'
    
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='required_skills',
        db_index=True,
        verbose_name='Công việc'
    )
    skill = models.ForeignKey(
        'candidate_skills.Skill',
        on_delete=models.CASCADE,
        related_name='job_skills',
        db_index=True,
        verbose_name='Kỹ năng'
    )
    is_required = models.BooleanField(
        default=True,
        verbose_name='Bắt buộc'
    )
    proficiency_level = models.CharField(
        max_length=20,
        choices=ProficiencyLevel.choices,
        null=True,
        blank=True,
        verbose_name='Mức độ yêu cầu'
    )
    years_required = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Số năm yêu cầu'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'job_skills'
        verbose_name = 'Kỹ năng công việc'
        verbose_name_plural = 'Kỹ năng công việc'
        unique_together = ['job', 'skill']
    
    def __str__(self):
        return f"{self.job.title} - {self.skill.name}"