from django.db import models


class JobLocation(models.Model):
    """Bảng Job_Locations - Địa điểm làm việc (1 job có thể nhiều địa điểm)"""
    
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='locations',
        db_index=True,
        verbose_name='Công việc'
    )
    address = models.ForeignKey(
        'geography_addresses.Address',
        on_delete=models.CASCADE,
        related_name='job_locations',
        db_index=True,
        verbose_name='Địa chỉ'
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='Địa điểm chính'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'job_locations'
        verbose_name = 'Địa điểm công việc'
        verbose_name_plural = 'Địa điểm công việc'
    
    def __str__(self):
        return f"{self.job.title} - {self.address}"
