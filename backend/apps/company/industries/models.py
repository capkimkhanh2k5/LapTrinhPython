from django.db import models


class Industry(models.Model):
    """Bảng Industries - Ngành nghề/Lĩnh vực kinh doanh"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='Tên ngành nghề'
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
    icon_url = models.URLField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='URL icon'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        verbose_name='Ngành cha'
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
        db_table = 'industries'
        verbose_name = 'Ngành nghề'
        verbose_name_plural = 'Ngành nghề'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name