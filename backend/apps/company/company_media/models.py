from django.db import models


class CompanyMedia(models.Model):
    """Bảng Company_Media - Ảnh/Video văn phóng công ty"""
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='media',
        db_index=True,
        verbose_name='Công ty'
    )
    media_type = models.ForeignKey(
        'company_media_types.MediaType',
        on_delete=models.CASCADE,
        related_name='company_media',
        db_index=True,
        verbose_name='Loại media'
    )
    media_url = models.URLField(
        max_length=500,
        verbose_name='URL media'
    )
    thumbnail_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='URL thumbnail'
    )
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Tiêu đề'
    )
    caption = models.TextField(
        null=True,
        blank=True,
        verbose_name='Mô tả'
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
        db_table = 'company_media'
        verbose_name = 'Media công ty'
        verbose_name_plural = 'Media công ty'
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.company.company_name} - {self.title or self.media_type.type_name}"
