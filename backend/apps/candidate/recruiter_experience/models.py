from django.db import models


class RecruiterExperience(models.Model):
    """Bảng Recruiter_Experience - Kinh nghiệm làm việc"""
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='experiences',
        db_index=True,
        verbose_name='Ứng viên'
    )
    company_name = models.CharField(
        max_length=255,
        verbose_name='Tên công ty'
    )
    job_title = models.CharField(
        max_length=100,
        verbose_name='Chức danh'
    )
    industry = models.ForeignKey(
        'company_industries.Industry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recruiter_experiences',
        verbose_name='Ngành nghề'
    )
    start_date = models.DateField(
        db_index=True,
        verbose_name='Ngày bắt đầu'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày kết thúc'
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name='Công việc hiện tại'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả công việc'
    )
    address = models.ForeignKey(
        'geography_addresses.Address',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recruiter_experiences',
        verbose_name='Địa chỉ'
    )
    achievements = models.TextField(
        null=True,
        blank=True,
        verbose_name='Thành tựu'
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name='Thứ tự hiển thị'
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
        db_table = 'recruiter_experience'
        verbose_name = 'Kinh nghiệm làm việc'
        verbose_name_plural = 'Kinh nghiệm làm việc'
        ordering = ['-start_date', 'display_order']
    
    def __str__(self):
        return f"{self.job_title} tại {self.company_name}"
