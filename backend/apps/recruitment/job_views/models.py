from django.db import models


class JobView(models.Model):
    """Bảng Job_Views - Lượt xem công việc"""
    
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='views',
        db_index=True,
        verbose_name='Công việc'
    )
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_views',
        db_index=True,
        verbose_name='Người xem'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Địa chỉ IP'
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name='User Agent'
    )
    referrer = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Nguồn truy cập'
    )
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Thời gian xem'
    )
    
    class Meta:
        db_table = 'job_views'
        verbose_name = 'Lượt xem công việc'
        verbose_name_plural = 'Lượt xem công việc'
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.job.title} - {self.viewed_at}"
