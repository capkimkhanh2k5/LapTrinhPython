from django.core.exceptions import ValidationError
from django.db import transaction
from apps.billing.models import SubscriptionPlan

class PlanService:
    @staticmethod
    def create_plan(name: str, slug: str, price: float, duration_days: int, features: dict, currency: str = 'VND') -> SubscriptionPlan:
        if price < 0:
            raise ValidationError("Price cannot be negative")
            
        return SubscriptionPlan.objects.create(
            name=name,
            slug=slug,
            price=price,
            duration_days=duration_days,
            features=features,
            currency=currency
        )
    
    @staticmethod
    def update_plan(plan: SubscriptionPlan, **kwargs) -> SubscriptionPlan:
        for key, value in kwargs.items():
            setattr(plan, key, value)
        plan.save()
        return plan
