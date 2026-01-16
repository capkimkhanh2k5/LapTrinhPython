from django.db import models


class EmailTemplate(models.Model):
    """Bảng Email_Templates - Mẫu email"""
    
    name = models.CharField(
        max_length=255,
        verbose_name='Tên mẫu'
    )
    category = models.ForeignKey(
        'email_email_template_categories.EmailTemplateCategory',
        on_delete=models.CASCADE,
        related_name='templates',
        db_index=True,
        verbose_name='Danh mục'
    )
    subject = models.CharField(
        max_length=255,
        verbose_name='Tiêu đề'
    )
    body = models.TextField(
        verbose_name='Nội dung'
    )
    variables = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Biến'
    )
    is_system = models.BooleanField(
        default=False,
        verbose_name='Mẫu hệ thống'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )
    created_by = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_email_templates',
        verbose_name='Người tạo'
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
        db_table = 'email_templates'
        verbose_name = 'Mẫu email'
        verbose_name_plural = 'Mẫu email'
    
    def __str__(self):
        return self.name
