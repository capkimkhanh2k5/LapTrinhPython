import pytest
from apps.billing.models import SubscriptionPlan
from apps.billing.services.plans import PlanService
from apps.billing.services.subscriptions import SubscriptionService
from apps.billing.services.payments import PaymentService

@pytest.fixture
def plan():
    return SubscriptionPlan.objects.create(
        name="Pro Plan",
        slug="pro",
        price=1000000,
        currency="VND",
        duration_days=30
    )

@pytest.mark.django_db
class TestBillingServices:
    def test_create_plan_service(self):
        plan = PlanService.create_plan(
            name="Basic", slug="basic", price=0, duration_days=30, features={"limit": 10}
        )
        assert plan.price == 0
        assert plan.slug == "basic"

    def test_subscribe_service(self, company, plan):
        sub = SubscriptionService.subscribe(company, plan)
        assert sub.status == 'active'
        assert sub.plan == plan
        assert sub.auto_renew is True

    def test_cancel_subscription_service(self, company, plan):
        SubscriptionService.subscribe(company, plan)
        sub = SubscriptionService.cancel_subscription(company)
        assert sub.auto_renew is False
        
    def test_upgrade_subscription(self, company, plan):
        # First sub
        SubscriptionService.subscribe(company, plan)
        
        # Upgrade (change plan)
        new_plan = SubscriptionPlan.objects.create(name="Ent", slug="ent", price=2000, duration_days=30)
        new_sub = SubscriptionService.subscribe(company, new_plan)
        
        assert new_sub.plan == new_plan
        assert new_sub.status == 'active'
        # Old sub should be cancelled - accessing via manager
        old_sub = company.subscriptions.filter(plan=plan).first()
        assert old_sub.status == 'cancelled'
        # Model defines OneToOne related_name='subscription'.
        # If we create a new one, does it overwrite or error?
        # Service logic: current_sub.status = Cancelled. Then create NEW.
        # But OneToOneField limits to ONE record if strictly enforced unique?
        # Let's check model definition.
