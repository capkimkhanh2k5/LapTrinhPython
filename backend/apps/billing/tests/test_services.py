"""
Billing Services Tests - Django TestCase Version
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.billing.models import SubscriptionPlan
from apps.billing.services.plans import PlanService
from apps.billing.services.subscriptions import SubscriptionService
from apps.company.companies.models import Company
from apps.company.industries.models import Industry

User = get_user_model()


class TestBillingServices(TestCase):
    """Tests for Billing Services"""
    
    @classmethod
    def setUpTestData(cls):
        cls.industry = Industry.objects.create(name="Tech", slug="tech-svc")
        cls.user = User.objects.create_user(
            email="billing_svc@test.com",
            password="password123",
            first_name="Service",
            last_name="Test",
            role='employer'
        )
        cls.company = Company.objects.create(
            user=cls.user,
            company_name="Service Test Company",
            slug="service-test-company",
            industry=cls.industry,
            description="A service test company"
        )
        cls.plan = SubscriptionPlan.objects.create(
            name="Pro Plan",
            slug="pro-svc",
            price=1000000,
            currency="VND",
            duration_days=30
        )
    
    def test_create_plan_service(self):
        """PlanService can create a new subscription plan"""
        plan = PlanService.create_plan(
            name="Basic", 
            slug="basic-test", 
            price=0, 
            duration_days=30, 
            features={"limit": 10}
        )
        self.assertEqual(plan.price, 0)
        self.assertEqual(plan.slug, "basic-test")
    
    def test_subscribe_service(self):
        """SubscriptionService can subscribe a company to a plan"""
        sub = SubscriptionService.subscribe(self.company, self.plan)
        self.assertEqual(sub.status, 'active')
        self.assertEqual(sub.plan, self.plan)
        self.assertTrue(sub.auto_renew)
    
    def test_cancel_subscription_service(self):
        """SubscriptionService can cancel a subscription"""
        SubscriptionService.subscribe(self.company, self.plan)
        sub = SubscriptionService.cancel_subscription(self.company)
        self.assertFalse(sub.auto_renew)
    
    def test_upgrade_subscription(self):
        """SubscriptionService handles plan upgrades correctly"""
        # First subscribe
        SubscriptionService.subscribe(self.company, self.plan)
        
        # Upgrade (change plan)
        new_plan = SubscriptionPlan.objects.create(
            name="Enterprise", 
            slug="ent-test", 
            price=2000, 
            duration_days=30
        )
        new_sub = SubscriptionService.subscribe(self.company, new_plan)
        
        self.assertEqual(new_sub.plan, new_plan)
        self.assertEqual(new_sub.status, 'active')
        
        # Old sub should be cancelled
        old_sub = self.company.subscriptions.filter(plan=self.plan).first()
        self.assertEqual(old_sub.status, 'cancelled')
