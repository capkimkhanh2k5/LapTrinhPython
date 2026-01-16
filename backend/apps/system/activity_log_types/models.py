from django.db import models


class ActivityLogType(models.Model):
    """Bảng Activity_Log_Types - Loại hoạt động"""
    
    class Severity(models.TextChoices):
        INFO = 'info', 'Thông tin'
        WARNING = 'warning', 'Cảnh báo'
        ERROR = 'error', 'Lỗi'
        CRITICAL = 'critical', 'Nghiêm trọng'
    
    type_name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Tên loại'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.INFO,
        verbose_name='Mức độ'
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
        db_table = 'activity_log_types'
        verbose_name = 'Loại hoạt động'
        verbose_name_plural = 'Loại hoạt động'
    
    def __str__(self):
        return self.type_name
