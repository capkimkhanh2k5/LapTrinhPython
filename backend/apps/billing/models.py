from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel

class SubscriptionPlan(TimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='VND')
    duration_days = models.IntegerField(help_text="Duration in days (e.g. 30, 365)")
    features = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.price} {self.currency})"

class CompanySubscription(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        EXPIRED = 'expired', _('Expired')
        CANCELLED = 'cancelled', _('Cancelled')
        
    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='company_subscriptions'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.ACTIVE
    )
    auto_renew = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.company} - {self.plan}"

class PaymentMethod(TimeStampedModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    config = models.JSONField(default=dict, blank=True, help_text="Gateway configuration")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Transaction(TimeStampedModel):
    class Type(models.TextChoices):
        SUBSCRIPTION = 'subscription', _('Subscription')
        ADD_ON = 'add_on', _('Add On')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')

    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='VND')
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SUBSCRIPTION)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reference_code = models.CharField(max_length=100, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    
    # VN Pay Fields
    vnp_TransactionNo = models.CharField(max_length=100, blank=True, null=True, help_text="Transaction ID at VNPay System")
    vnp_BankCode = models.CharField(max_length=50, blank=True, null=True)
    vnp_CardType = models.CharField(max_length=50, blank=True, null=True)
    vnp_OrderInfo = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"TX-{self.id} ({self.status})"
