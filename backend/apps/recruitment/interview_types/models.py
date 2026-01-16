from django.db import models


class InterviewType(models.Model):
    """Bảng Interview_Types - Loại phỏng vấn"""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Tên loại phỏng vấn'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    icon_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='URL icon'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'interview_types'
        verbose_name = 'Loại phỏng vấn'
        verbose_name_plural = 'Loại phỏng vấn'
    
    def __str__(self):
        return self.name
