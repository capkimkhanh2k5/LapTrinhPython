from django.db import models


class NotificationType(models.Model):
    """Bảng Notification_Types - Loại thông báo"""
    
    type_name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Tên loại thông báo'
    )
    template = models.TextField(
        null=True,
        blank=True,
        verbose_name='Template'
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
        db_table = 'notification_types'
        verbose_name = 'Loại thông báo'
        verbose_name_plural = 'Loại thông báo'
    
    def __str__(self):
        return self.type_name
