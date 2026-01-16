from django.db import models


class AssessmentCategory(models.Model):
    """Bảng Assessment_Categories - Phân loại bài test"""
    
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
        db_table = 'assessment_categories'
        verbose_name = 'Danh mục bài test'
        verbose_name_plural = 'Danh mục bài test'
    
    def __str__(self):
        return self.name
