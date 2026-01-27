"""
Test cases cho Subscription Hybrid Logic.
- Cancellation: Passive (giữ end_date, tắt auto_renew).
- New Subscription: Aggressive (xoá gói cũ ngay, tạo gói mới).
"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.core.users.models import CustomUser
from apps.company.companies.models import Company
from apps.billing.models import CompanySubscription, SubscriptionPlan, Transaction
from apps.billing.services.subscriptions import SubscriptionService


class TestSubscriptionHybridLogic(TestCase):
    """Test Hybrid Subscription Logic"""

    def setUp(self):
        # Create User
        self.user = CustomUser.objects.create_user(
            email="test@example.com",
            password="password123"
        )
        # Create Company
        self.company = Company.objects.create(
            user=self.user,
            company_name="Test Corp",
            slug="test-corp"
        )
        # Create Plans
        self.free_plan = SubscriptionPlan.objects.create(
            name="Free",
            slug="free",
            price=0,
            duration_days=30
        )
        self.basic_plan = SubscriptionPlan.objects.create(
            name="Basic",
            slug="basic",
            price=100000,
            duration_days=30
        )
        self.premium_plan = SubscriptionPlan.objects.create(
            name="Premium",
            slug="premium",
            price=300000,
            duration_days=30
        )

    # ==========================================================================
    # Test: New Subscription (No existing)
    # ==========================================================================
    def test_subscribe_new_company(self):
        """Company không có gói cước -> Tạo mới thành công"""
        sub = SubscriptionService.subscribe(self.company, self.basic_plan)

        self.assertEqual(sub.status, CompanySubscription.Status.ACTIVE)
        self.assertEqual(sub.plan, self.basic_plan)
        self.assertTrue(sub.auto_renew)
        self.assertEqual(sub.start_date, timezone.now().date())
        self.assertEqual(sub.end_date, timezone.now().date() + timedelta(days=30))

    def test_subscribe_free_plan_creates_completed_transaction(self):
        """Free plan -> Transaction với status=COMPLETED"""
        SubscriptionService.subscribe(self.company, self.free_plan)

        tx = Transaction.objects.filter(company=self.company).first()
        self.assertEqual(tx.amount, 0)
        self.assertEqual(tx.status, Transaction.Status.COMPLETED)

    def test_subscribe_paid_plan_creates_pending_transaction(self):
        """Paid plan -> Transaction với status=PENDING"""
        SubscriptionService.subscribe(self.company, self.basic_plan)

        tx = Transaction.objects.filter(company=self.company).first()
        self.assertEqual(tx.amount, 100000)
        self.assertEqual(tx.status, Transaction.Status.PENDING)

    # ==========================================================================
    # Test: Replace Subscription (Upgrade/Change)
    # ==========================================================================
    def test_subscribe_replaces_old_subscription(self):
        """Đổi gói -> Gói cũ bị CANCELLED ngay lập tức"""
        # Subscribe to Basic first
        old_sub = SubscriptionService.subscribe(self.company, self.basic_plan)
        old_sub_id = old_sub.id

        # Upgrade to Premium
        new_sub = SubscriptionService.subscribe(self.company, self.premium_plan)

        # Old sub should be CANCELLED
        old_sub.refresh_from_db()
        self.assertEqual(old_sub.status, CompanySubscription.Status.CANCELLED)
        self.assertFalse(old_sub.auto_renew)

        # New sub should be ACTIVE
        self.assertEqual(new_sub.status, CompanySubscription.Status.ACTIVE)
        self.assertEqual(new_sub.plan, self.premium_plan)

    def test_subscribe_cancels_pending_downgrades(self):
        """Đổi gói -> Xoá cả các gói PENDING (scheduled downgrades)"""
        # Manually create a PENDING subscription (simulating scheduled downgrade)
        pending_sub = CompanySubscription.objects.create(
            company=self.company,
            plan=self.free_plan,
            start_date=timezone.now().date() + timedelta(days=31),
            end_date=timezone.now().date() + timedelta(days=61),
            status=CompanySubscription.Status.PENDING,
            auto_renew=True
        )

        # Now subscribe to a new plan
        SubscriptionService.subscribe(self.company, self.basic_plan)

        # PENDING sub should be CANCELLED
        pending_sub.refresh_from_db()
        self.assertEqual(pending_sub.status, CompanySubscription.Status.CANCELLED)

    # ==========================================================================
    # Test: Cancel Subscription (Passive)
    # ==========================================================================
    def test_cancel_subscription_keeps_end_date(self):
        """Hủy gói -> end_date không thay đổi"""
        sub = SubscriptionService.subscribe(self.company, self.basic_plan)
        original_end_date = sub.end_date

        cancelled_sub = SubscriptionService.cancel_subscription(self.company)

        self.assertEqual(cancelled_sub.status, CompanySubscription.Status.ACTIVE)  # Vẫn Active
        self.assertFalse(cancelled_sub.auto_renew)  # Tắt gia hạn
        self.assertEqual(cancelled_sub.end_date, original_end_date)  # Giữ nguyên end_date

    def test_cancel_subscription_no_active_raises_error(self):
        """Hủy khi không có gói -> Raise ValidationError"""
        with self.assertRaises(ValidationError):
            SubscriptionService.cancel_subscription(self.company)

    # ==========================================================================
    # Test: Renew Subscription
    # ==========================================================================
    def test_renew_subscription_extends_end_date(self):
        """Gia hạn -> end_date += duration_days"""
        sub = SubscriptionService.subscribe(self.company, self.basic_plan)
        original_end_date = sub.end_date

        renewed_sub = SubscriptionService.renew_subscription(sub)

        self.assertEqual(renewed_sub.end_date, original_end_date + timedelta(days=30))

    def test_renew_subscription_creates_transaction(self):
        """Gia hạn -> Tạo Transaction mới"""
        sub = SubscriptionService.subscribe(self.company, self.basic_plan)
        initial_tx_count = Transaction.objects.filter(company=self.company).count()

        SubscriptionService.renew_subscription(sub)

        new_tx_count = Transaction.objects.filter(company=self.company).count()
        self.assertEqual(new_tx_count, initial_tx_count + 1)

    def test_renew_subscription_fails_if_auto_renew_false(self):
        """Gia hạn khi auto_renew=False -> Raise ValidationError"""
        sub = SubscriptionService.subscribe(self.company, self.basic_plan)
        sub.auto_renew = False
        sub.save()

        with self.assertRaises(ValidationError):
            SubscriptionService.renew_subscription(sub)
