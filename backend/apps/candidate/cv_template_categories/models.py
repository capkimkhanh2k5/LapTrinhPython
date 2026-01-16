from django.db import models


class CVTemplateCategory(models.Model):
    """Bảng CV_Template_Categories - Phân loại mẫu CV"""
    
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
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
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
        db_table = 'cv_template_categories'
        verbose_name = 'Danh mục mẫu CV'
        verbose_name_plural = 'Danh mục mẫu CV'
    
    def __str__(self):
        return self.name
