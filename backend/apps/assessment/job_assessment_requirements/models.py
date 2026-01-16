from django.db import models


class JobAssessmentRequirement(models.Model):
    """Bảng Job_Assessment_Requirements - Yêu cầu test cho công việc"""
    
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='assessment_requirements',
        db_index=True,
        verbose_name='Công việc'
    )
    assessment_test = models.ForeignKey(
        'assessment_assessment_tests.AssessmentTest',
        on_delete=models.CASCADE,
        related_name='job_requirements',
        verbose_name='Bài test'
    )
    is_mandatory = models.BooleanField(
        default=True,
        verbose_name='Bắt buộc'
    )
    minimum_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Điểm tối thiểu'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'job_assessment_requirements'
        verbose_name = 'Yêu cầu test công việc'
        verbose_name_plural = 'Yêu cầu test công việc'
        unique_together = ['job', 'assessment_test']
    
    def __str__(self):
        return f"{self.job.title} - {self.assessment_test.title}"
