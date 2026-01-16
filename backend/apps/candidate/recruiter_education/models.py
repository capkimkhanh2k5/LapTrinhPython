from django.db import models


class RecruiterEducation(models.Model):
    """Bảng Recruiter_Education - Học vấn"""
    
    recruiter = models.ForeignKey(
        'candidate_recruiters.Recruiter',
        on_delete=models.CASCADE,
        related_name='education',
        db_index=True,
        verbose_name='Ứng viên'
    )
    school_name = models.CharField(
        max_length=255,
        verbose_name='Tên trường'
    )
    degree = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Bằng cấp'
    )
    field_of_study = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='Chuyên ngành'
    )
    start_date = models.DateField(
        null=True,
        blank=True,
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
        verbose_name='Đang học'
    )
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='GPA'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
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
        db_table = 'recruiter_education'
        verbose_name = 'Học vấn'
        verbose_name_plural = 'Học vấn'
        ordering = ['-start_date', 'display_order']
    
    def __str__(self):
        return f"{self.school_name} - {self.degree}"
