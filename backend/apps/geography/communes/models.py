from django.db import models


class Commune(models.Model):
    """Bảng Communes - Xã/Phường/Thị Trấn thuộc tỉnh"""
    
    class CommuneType(models.TextChoices):
        COMMUNE = 'commune', 'Xã'
        WARD = 'ward', 'Phường'
        TOWNSHIP = 'township', 'Thị trấn'
        SPECIAL_ZONE = 'special_zone', 'Đơn vị hành chính đặc biệt'
    
    province = models.ForeignKey(
        'geography_provinces.Province',
        on_delete=models.CASCADE,
        related_name='communes',
        db_index=True,
        verbose_name='Tỉnh/Thành phố'
    )
    commune_name = models.CharField(
        max_length=100,
        verbose_name='Tên xã/phường'
    )
    commune_type = models.CharField(
        max_length=20,
        choices=CommuneType.choices,
        verbose_name='Loại'
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
        db_table = 'communes'
        verbose_name = 'Xã/Phường/Thị trấn'
        verbose_name_plural = 'Xã/Phường/Thị trấn'
        ordering = ['commune_name']
    
    def __str__(self):
        return f"{self.commune_name} - {self.province.province_name}"