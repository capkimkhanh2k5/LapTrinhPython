from django.db import models


class Language(models.Model):
    """Bảng Languages - Danh sách ngôn ngữ"""
    
    language_code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        verbose_name='Mã ngôn ngữ'
    )
    language_name = models.CharField(
        max_length=50,
        verbose_name='Tên ngôn ngữ'
    )
    native_name = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Tên bản địa'
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
        db_table = 'languages'
        verbose_name = 'Ngôn ngữ'
        verbose_name_plural = 'Ngôn ngữ'
        ordering = ['language_name']
    
    def __str__(self):
        return self.language_name
