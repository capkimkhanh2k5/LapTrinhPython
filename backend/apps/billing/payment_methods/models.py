from django.db import models


class PaymentMethod(models.Model):
    """Bảng Payment_Methods - Phương thức thanh toán"""
    
    method_name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Tên phương thức'
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
        db_table = 'payment_methods'
        verbose_name = 'Phương thức thanh toán'
        verbose_name_plural = 'Phương thức thanh toán'
        ordering = ['display_order']
    
    def __str__(self):
        return self.method_name
