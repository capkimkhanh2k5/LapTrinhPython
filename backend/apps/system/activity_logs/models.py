from django.db import models


class ActivityLog(models.Model):
    """Bảng Activity_Logs - Nhật ký hoạt động"""
    
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        db_index=True,
        verbose_name='Người dùng'
    )
    log_type = models.ForeignKey(
        'system_activity_log_types.ActivityLogType',
        on_delete=models.CASCADE,
        related_name='logs',
        db_index=True,
        verbose_name='Loại hoạt động'
    )
    action = models.CharField(
        max_length=100,
        verbose_name='Hành động'
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
    details = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Chi tiết'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = 'Nhật ký hoạt động'
        verbose_name_plural = 'Nhật ký hoạt động'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id'], name='idx_activity_entity'),
        ]
    
    def __str__(self):
        return f"{self.action} - {self.entity_type}"
