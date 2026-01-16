from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Application(models.Model):
    """Bảng Applications - Đơn ứng tuyển"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ xử lý'
        REVIEWING = 'reviewing', 'Đang xem xét'
        SHORTLISTED = 'shortlisted', 'Vào vòng tiếp'
        INTERVIEW = 'interview', 'Phỏng vấn'
        OFFERED = 'offered', 'Đề xuất offer'
        REJECTED = 'rejected', 'Từ chối'
        WITHDRAWN = 'withdrawn', 'Đã rút'
        ACCEPTED = 'accepted', 'Đã nhận việc'
    
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='applications',
        db_index=True,
        verbose_name='Công việc'
    )
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='applications',
        db_index=True,
        verbose_name='Ứng viên'
    )
    cv = models.ForeignKey(
        'candidate_recruiter_cvs.RecruiterCV',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        verbose_name='CV'
    )
    cover_letter = models.TextField(
        null=True,
        blank=True,
        verbose_name='Thư xin việc'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name='Trạng thái'
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Đánh giá'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ghi chú'
    )
    applied_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày ứng tuyển'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    reviewed_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
        verbose_name='Người xem xét'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Ngày xem xét'
    )
    
    class Meta:
        db_table = 'applications'
        verbose_name = 'Đơn ứng tuyển'
        verbose_name_plural = 'Đơn ứng tuyển'
        unique_together = ['job', 'recruiter']
        indexes = [
            models.Index(fields=['recruiter', 'status'], name='idx_app_recruiter_status'),
            models.Index(fields=['job', 'status'], name='idx_app_job_status'),
        ]
    
    def __str__(self):
        return f"{self.recruiter.user.full_name} - {self.job.title}"
