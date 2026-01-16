from django.db import models


class CVTemplate(models.Model):
    """Bảng CV_Templates - Mẫu CV"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Tên mẫu'
    )
    category = models.ForeignKey(
        'candidate_cv_template_categories.CVTemplateCategory',
        on_delete=models.CASCADE,
        related_name='templates',
        db_index=True,
        verbose_name='Danh mục'
    )
    thumbnail_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL ảnh thumbnail'
    )
    preview_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL xem trước'
    )
    template_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Dữ liệu mẫu'
    )
    is_premium = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='Mẫu cao cấp'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Giá'
    )
    usage_count = models.IntegerField(
        default=0,
        verbose_name='Số lần sử dụng'
    )
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        verbose_name='Đánh giá'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
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
        db_table = 'cv_templates'
        verbose_name = 'Mẫu CV'
        verbose_name_plural = 'Mẫu CV'
    
    def __str__(self):
        return self.name
