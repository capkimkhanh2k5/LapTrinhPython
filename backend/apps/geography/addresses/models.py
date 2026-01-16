from django.db import models


class Address(models.Model):
    """Bảng Addresses - Địa chỉ tổng hợp"""
    
    address_line = models.CharField(
        max_length=255,
        verbose_name='Số nhà, tên đường'
    )
    commune = models.ForeignKey(
        'geography_communes.Commune',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='addresses',
        db_index=True,
        verbose_name='Xã/Phường'
    )
    province = models.ForeignKey(
        'geography_provinces.Province',
        on_delete=models.CASCADE,
        related_name='addresses',
        db_index=True,
        verbose_name='Tỉnh/Thành phố'
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name='Vĩ độ'
    )
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        verbose_name='Kinh độ'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Đã xác minh'
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
        db_table = 'addresses'
        verbose_name = 'Địa chỉ'
        verbose_name_plural = 'Địa chỉ'
        indexes = [
            models.Index(fields=['latitude', 'longitude'], name='idx_location'),
        ]
    
    def __str__(self):
        return f"{self.address_line}, {self.province.province_name}"