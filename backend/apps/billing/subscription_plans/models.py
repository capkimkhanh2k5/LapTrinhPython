from django.db import models


class SubscriptionPlan(models.Model):
    """Bảng Subscription_Plans - Gói đăng ký cho công ty"""
    
    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', 'Hàng tháng'
        QUARTERLY = 'quarterly', 'Hàng quý'
        YEARLY = 'yearly', 'Hàng năm'
    
    class Currency(models.TextChoices):
        VND = 'VND', 'VND'
        USD = 'USD', 'USD'
    
    plan_name = models.CharField(
        max_length=100,
        verbose_name='Tên gói'
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
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='Giá'
    )
    currency = models.CharField(
        max_length=10,
        choices=Currency.choices,
        verbose_name='Đơn vị tiền tệ'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BillingCycle.choices,
        verbose_name='Chu kỳ thanh toán'
    )
    duration_days = models.IntegerField(
        verbose_name='Thời hạn (ngày)'
    )
    max_job_posts = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Số tin tuyển dụng tối đa'
    )
    max_featured_jobs = models.IntegerField(
        default=0,
        verbose_name='Số tin nổi bật tối đa'
    )
    max_urgent_jobs = models.IntegerField(
        default=0,
        verbose_name='Số tin gấp tối đa'
    )
    can_view_candidate_contact = models.BooleanField(
        default=False,
        verbose_name='Xem liên hệ ứng viên'
    )
    can_use_ai_matching = models.BooleanField(
        default=False,
        verbose_name='Sử dụng AI matching'
    )
    priority_support = models.BooleanField(
        default=False,
        verbose_name='Hỗ trợ ưu tiên'
    )
    features = models.JSONField(
        null=True,
        blank=True,
        verbose_name='Tính năng'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name='Đang hoạt động'
    )
    is_popular = models.BooleanField(
        default=False,
        verbose_name='Phổ biến'
    )
    display_order = models.IntegerField(
        default=0,
        verbose_name='Thứ tự hiển thị'
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
        db_table = 'subscription_plans'
        verbose_name = 'Gói đăng ký'
        verbose_name_plural = 'Gói đăng ký'
        ordering = ['display_order']
    
    def __str__(self):
        return self.plan_name
