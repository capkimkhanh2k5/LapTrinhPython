from django.db import models


class BenefitCategory(models.Model):
    """Bảng Benefit_Categories - Phân loại phúc lợi"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Tên danh mục'
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='Slug'
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
    display_order = models.IntegerField(
        default=0,
        verbose_name='Thứ tự hiển thị'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo'
    )
    
    class Meta:
        db_table = 'benefit_categories'
        verbose_name = 'Danh mục phúc lợi'
        verbose_name_plural = 'Danh mục phúc lợi'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
