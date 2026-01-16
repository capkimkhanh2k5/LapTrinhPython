from django.db import models


class PaymentTransaction(models.Model):
    """Bảng Payment_Transactions - Giao dịch thanh toán"""
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', 'Chờ xử lý'
        PROCESSING = 'processing', 'Đang xử lý'
        COMPLETED = 'completed', 'Hoàn thành'
        FAILED = 'failed', 'Thất bại'
        REFUNDED = 'refunded', 'Đã hoàn tiền'
        CANCELLED = 'cancelled', 'Đã hủy'
    
    subscription = models.ForeignKey(
        'billing_company_subscriptions.CompanySubscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        db_index=True,
        verbose_name='Đăng ký'
    )
    user = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='payment_transactions',
        db_index=True,
        verbose_name='Người dùng'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Số tiền'
    )
    currency = models.CharField(
        max_length=10,
        default='VND',
        verbose_name='Đơn vị tiền tệ'
    )
    payment_method = models.ForeignKey(
        'billing_payment_methods.PaymentMethod',
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name='Phương thức thanh toán'
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Mã giao dịch'
    )
    transaction_status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True,
        verbose_name='Trạng thái'
    )
    payment_gateway = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name='Cổng thanh toán'
    )
    gateway_response = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Phản hồi từ cổng thanh toán'
    )
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Ghi chú'
    )
    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thanh toán lúc'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Ngày tạo'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật'
    )
    
    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Giao dịch thanh toán'
        verbose_name_plural = 'Giao dịch thanh toán'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id or self.id} - {self.amount} {self.currency}"
