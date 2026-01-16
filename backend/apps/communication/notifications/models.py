from django.db import models


class Notification(models.Model):
    """Bảng Notifications - Thông báo"""
    
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='notifications',
        db_index=True,
        verbose_name='Người dùng'
    )
    notification_type = models.ForeignKey(
        'communication_notification_types.NotificationType',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Loại thông báo'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Tiêu đề'
    )
    content = models.TextField(
        verbose_name='Nội dung'
    )
    link = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='Link'
    )
    entity_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Loại đối tượng'
    )
    entity_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID đối tượng'
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Đã đọc'
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Đọc lúc'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at'], name='idx_notif_user_read'),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.title}"
