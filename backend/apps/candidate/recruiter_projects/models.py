from django.db import models


class RecruiterProject(models.Model):
    """Bảng Recruiter_Projects - Dự án cá nhân"""
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='projects',
        db_index=True,
        verbose_name='Ứng viên'
    )
    project_name = models.CharField(
        max_length=255,
        verbose_name='Tên dự án'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    project_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL dự án'
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày bắt đầu'
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Ngày kết thúc'
    )
    is_ongoing = models.BooleanField(
        default=False,
        verbose_name='Đang thực hiện'
    )
    technologies_used = models.TextField(
        null=True,
        blank=True,
        verbose_name='Công nghệ sử dụng'
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
        db_table = 'recruiter_projects'
        verbose_name = 'Dự án cá nhân'
        verbose_name_plural = 'Dự án cá nhân'
        ordering = ['-start_date', 'display_order']
    
    def __str__(self):
        return self.project_name
