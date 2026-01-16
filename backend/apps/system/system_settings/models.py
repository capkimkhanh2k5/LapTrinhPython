from django.db import models


class SystemSetting(models.Model):
    """Bảng System_Settings - Cài đặt hệ thống"""
    
    class SettingType(models.TextChoices):
        STRING = 'string', 'Chuỗi'
        NUMBER = 'number', 'Số'
        BOOLEAN = 'boolean', 'Boolean'
        JSON = 'json', 'JSON'
    
    setting_key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Khóa'
    )
    setting_value = models.TextField(
        null=True,
        blank=True,
        verbose_name='Giá trị'
    )
    setting_type = models.CharField(
        max_length=20,
        choices=SettingType.choices,
        default=SettingType.STRING,
        verbose_name='Loại'
    )
    category = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='Danh mục'
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name='Công khai'
    )
    updated_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_system_settings',
        verbose_name='Người cập nhật'
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
        db_table = 'system_settings'
        verbose_name = 'Cấu hình hệ thống'
        verbose_name_plural = 'Cấu hình hệ thống'
    
    def __str__(self):
        return self.setting_key
