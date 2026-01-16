from django.db import models


class AIMatchingScore(models.Model):
    """Bảng AI_Matching_Scores - Điểm match AI"""
    
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='ai_scores',
        db_index=True,
        verbose_name='Công việc'
    )
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='ai_scores',
        db_index=True,
        verbose_name='Ứng viên'
    )
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        db_index=True,
        verbose_name='Điểm tổng'
    )
    skill_match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Điểm kỹ năng'
    )
    experience_match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Điểm kinh nghiệm'
    )
    education_match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Điểm học vấn'
    )
    location_match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Điểm vị trí'
    )
    salary_match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Điểm lương'
    )
    matching_details = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Chi tiết matching'
    )
    calculated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tính toán'
    )
    is_valid = models.BooleanField(
        default=True,
        verbose_name='Còn hiệu lực'
    )
    
    class Meta:
        db_table = 'ai_matching_scores'
        verbose_name = 'Điểm AI matching'
        verbose_name_plural = 'Điểm AI matching'
        unique_together = ['job', 'recruiter']
        ordering = ['-overall_score']
    
    def __str__(self):
        return f"{self.recruiter.user.full_name} - {self.job.title} : {self.overall_score}"
