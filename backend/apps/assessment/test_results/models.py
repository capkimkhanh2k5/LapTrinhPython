from django.db import models


class TestResult(models.Model):
    """Bảng Test_Results - Kết quả kiểm tra"""
    
    assessment_test = models.ForeignKey(
        'assessment_assessment_tests.AssessmentTest',
        on_delete=models.CASCADE,
        related_name='results',
        db_index=True,
        verbose_name='Bài test'
    )
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='test_results',
        db_index=True,
        verbose_name='Ứng viên'
    )
    application = models.ForeignKey(
        'recruitment_applications.Application',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='test_results',
        db_index=True,
        verbose_name='Đơn ứng tuyển'
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Điểm'
    )
    percentage_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Điểm phần trăm'
    )
    time_taken_minutes = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Thời gian làm bài (phút)'
    )
    answers_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Dữ liệu câu trả lời'
    )
    passed = models.BooleanField(
        default=False,
        verbose_name='Đạt'
    )
    certificate_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL chứng chỉ'
    )
    started_at = models.DateTimeField(
        verbose_name='Bắt đầu lúc'
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Hoàn thành lúc'
    )
    
    class Meta:
        db_table = 'test_results'
        verbose_name = 'Kết quả test'
        verbose_name_plural = 'Kết quả test'
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.recruiter.user.full_name} - {self.assessment_test.title} : {self.score}"
