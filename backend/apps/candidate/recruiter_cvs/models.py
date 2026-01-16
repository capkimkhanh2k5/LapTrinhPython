from django.db import models


class RecruiterCV(models.Model):
    """Bảng Recruiter_CVs - CV được tạo bởi người tìm việc"""
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='cvs',
        db_index=True,
        verbose_name='Ứng viên'
    )
    template = models.ForeignKey(
        'candidate_cv_templates.CVTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recruiter_cvs',
        verbose_name='Mẫu CV'
    )
    cv_name = models.CharField(
        max_length=255,
        verbose_name='Tên CV'
    )
    cv_data = models.JSONField(
        verbose_name='Dữ liệu CV'
    )
    cv_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL CV'
    )
    is_default = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='CV mặc định'
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name='CV công khai'
    )
    view_count = models.IntegerField(
        default=0,
        verbose_name='Lượt xem'
    )
    download_count = models.IntegerField(
        default=0,
        verbose_name='Lượt tải'
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
        db_table = 'recruiter_cvs'
        verbose_name = 'CV ứng viên'
        verbose_name_plural = 'CV ứng viên'
    
    def __str__(self):
        return f"{self.cv_name} - {self.recruiter.user.full_name}"
