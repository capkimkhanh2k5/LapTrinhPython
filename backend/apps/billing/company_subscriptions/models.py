from django.db import models


class CompanySubscription(models.Model):
    """Bảng Company_Subscriptions - Đăng ký của công ty"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Đang hoạt động'
        EXPIRED = 'expired', 'Hết hạn'
        CANCELLED = 'cancelled', 'Đã hủy'
        SUSPENDED = 'suspended', 'Tạm dừng'
    
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        db_index=True,
        verbose_name='Công ty'
    )
    plan = models.ForeignKey(
        'billing_subscription_plans.SubscriptionPlan',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        db_index=True,
        verbose_name='Gói đăng ký'
    )
    start_date = models.DateField(
        verbose_name='Ngày bắt đầu'
    )
    end_date = models.DateField(
        db_index=True,
        verbose_name='Ngày kết thúc'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        verbose_name='Trạng thái'
    )
    auto_renew = models.BooleanField(
        default=True,
        verbose_name='Tự động gia hạn'
    )
    payment_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Số tiền thanh toán'
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name='Số tiền giảm giá'
    )
    final_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Số tiền cuối cùng'
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
        db_table = 'company_subscriptions'
        verbose_name = 'Đăng ký công ty'
        verbose_name_plural = 'Đăng ký công ty'
    
    def __str__(self):
        return f"{self.company.company_name} - {self.plan.plan_name}"
