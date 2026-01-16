from django.db import models


class AuditLog(models.Model):
    """Bảng Audit_Logs - Nhật ký hoạt động"""
    
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        db_index=True,
        verbose_name='Người dùng'
    )
    action = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name='Hành động'
    )
    entity_type = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name='Loại đối tượng'
    )
    entity_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID đối tượng'
    )
    old_values = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Giá trị cũ'
    )
    new_values = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Giá trị mới'
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
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Nhật ký hoạt động'
        verbose_name_plural = 'Nhật ký hoạt động'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.entity_type}:{self.entity_id}"
