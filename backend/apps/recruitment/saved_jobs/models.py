from django.db import models


class SavedJob(models.Model):
    """Bảng Saved_Jobs - Công việc đã lưu"""
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='saved_jobs',
        db_index=True,
        verbose_name='Ứng viên'
    )
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='saved_by',
        db_index=True,
        verbose_name='Công việc'
    )
    folder_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Tên thư mục'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ghi chú'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày lưu'
    )
    
    class Meta:
        db_table = 'saved_jobs'
        verbose_name = 'Công việc đã lưu'
        verbose_name_plural = 'Công việc đã lưu'
        unique_together = ['recruiter', 'job']
    
    def __str__(self):
        return f"{self.recruiter.user.full_name} - {self.job.title}"
