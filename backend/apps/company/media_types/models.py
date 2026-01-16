from django.db import models


class MediaType(models.Model):
    """Bảng Media_Types - Loại media"""
    
    type_name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Tên loại media'
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
        db_table = 'media_types'
        verbose_name = 'Loại media'
        verbose_name_plural = 'Loại media'
    
    def __str__(self):
        return self.type_name
