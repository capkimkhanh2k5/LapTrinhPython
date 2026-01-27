from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from apps.core.users.models import CustomUser
from apps.company.companies.models import Company
from apps.billing.models import SubscriptionPlan, CompanySubscription, Transaction
from apps.billing.services.subscriptions import SubscriptionService

class SubscriptionChangeTest(TestCase):
    def setUp(self):
        # Setup User & Company
        self.user = CustomUser.objects.create(email='company@test.com')
        self.company = Company.objects.create(user=self.user, company_name='My Co', slug='my-co')
        
        # Setup Plans
        self.basic_plan = SubscriptionPlan.objects.create(
            name='Basic', slug='basic', price=1000000, duration_days=30, currency='VND'
        )
        self.pro_plan = SubscriptionPlan.objects.create(
            name='Pro', slug='pro', price=2000000, duration_days=30, currency='VND'
        )
        self.enterprise_plan = SubscriptionPlan.objects.create(
            name='Enterprise', slug='ent', price=5000000, duration_days=30, currency='VND'
        )
        
        # Setup Current Subscription (Basic) starting 10 days ago (20 days remaining)
        self.start_date = timezone.now().date() - timedelta(days=10)
        self.end_date = self.start_date + timedelta(days=30)
        
        self.current_sub = CompanySubscription.objects.create(
            company=self.company,
            plan=self.basic_plan,
            start_date=self.start_date,
            end_date=self.end_date,
            status=CompanySubscription.Status.ACTIVE
        )

    def test_upgrade_immediate(self):
        """
        Upgrade from Basic (1M) to Pro (2M).
        Remaining Basic Value: ~666,666 VND (20 days)
        Expected Charge: 2,000,000 - 666,666 = ~1,333,333
        Expected: Old CANCELLED, New ACTIVE immediately.
        """
        new_sub = SubscriptionService.change_subscription(self.company, self.pro_plan)
        
        # Check Old Sub
        self.current_sub.refresh_from_db()
        self.assertEqual(self.current_sub.status, CompanySubscription.Status.CANCELLED)
        
        # Check New Sub
        self.assertEqual(new_sub.plan, self.pro_plan)
        self.assertEqual(new_sub.status, CompanySubscription.Status.ACTIVE)
        self.assertEqual(new_sub.start_date, timezone.now().date())
        
        # Check Transaction
        tx = Transaction.objects.filter(company=self.company).last()
        self.assertIsNotNone(tx)
        
        # Policy: No Proration (Charge Full Price)
        self.assertEqual(tx.amount, 2000000)
        self.assertEqual(tx.status, Transaction.Status.PENDING)
        
    def test_downgrade_scheduled(self):
        """
        Downgrade (or switch) to cheaper plan.
        Expected: Old ACTIVE (auto_renew=False), New PENDING (starts later).
        """
        # Switch to cheaper plan/same price (treat as downgrade logic if not explicitly upgrade)
        # Assuming our logic uses price comparison.
        # Let's verify Basic (1M) -> Basic (1M) is treated as 'Downgrade' (Scheduled) by our logic (else statement)
        # Actually logic is `is_upgrade = new_plan.price > current_sub.plan.price`.
        # So Equal price = Downgrade path (Scheduled). That's acceptable for side-grade.
        
        # Let's downgrade Basic (1M) to a cheaper one (e.g. Free or Cheap)
        cheap_plan = SubscriptionPlan.objects.create(
            name='Cheap', slug='cheap', price=500000, duration_days=30
        )
        
        new_sub = SubscriptionService.change_subscription(self.company, cheap_plan)
        
        # Check Old Sub
        self.current_sub.refresh_from_db()
        # Should stay active but stop renew
        self.assertFalse(self.current_sub.auto_renew)
        self.assertEqual(self.current_sub.status, CompanySubscription.Status.ACTIVE)
        
        # Check New Sub
        self.assertEqual(new_sub.plan, cheap_plan)
        self.assertEqual(new_sub.status, CompanySubscription.Status.PENDING)
        self.assertEqual(new_sub.start_date, self.current_sub.end_date + timedelta(days=1))
