from django.db import models


class Province(models.Model):
    """Bảng Provinces - Tỉnh/Thành phố (28 tỉnh + 6 thành phố trực thuộc Trung ương)"""
    
    class ProvinceType(models.TextChoices):
        PROVINCE = 'province', 'Tỉnh'
        MUNICIPALITY = 'municipality', 'Thành phố trực thuộc Trung ương'
    
    class Region(models.TextChoices):
        NORTH = 'north', 'Miền Bắc'
        CENTRAL = 'central', 'Miền Trung'
        SOUTH = 'south', 'Miền Nam'
    
    province_code = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name='Mã tỉnh'
    )
    province_name = models.CharField(
        max_length=100,
        verbose_name='Tên tỉnh/thành phố'
    )
    province_type = models.CharField(
        max_length=20,
        choices=ProvinceType.choices,
        verbose_name='Loại'
    )
    region = models.CharField(
        max_length=10,
        choices=Region.choices,
        db_index=True,
        verbose_name='Vùng miền'
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
        db_table = 'provinces'
        verbose_name = 'Tỉnh/Thành phố'
        verbose_name_plural = 'Tỉnh/Thành phố'
        ordering = ['province_name']
    
    def __str__(self):
        return self.province_name