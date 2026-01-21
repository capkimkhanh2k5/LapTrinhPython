from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.billing.models import CompanySubscription, SubscriptionPlan, Transaction
from apps.billing.services.payments import PaymentService

class SubscriptionService:
    @staticmethod
    @transaction.atomic
    def subscribe(company, plan: SubscriptionPlan) -> CompanySubscription:
        # Check active subscription
        current_sub = CompanySubscription.objects.filter(
            company=company, 
            status=CompanySubscription.Status.ACTIVE
        ).first()
        
        if current_sub:
            #TODO: Cần xem lại logic này, có thể cần handle proration hoặc schedule change
            
            # Simple logic: Cancel current and start new immediately (MVP)
            # In real world: Handle proration or schedule change
            current_sub.status = CompanySubscription.Status.CANCELLED
            current_sub.save()
            
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=plan.duration_days)
        
        # Create subscription
        subscription = CompanySubscription.objects.create(
            company=company,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status=CompanySubscription.Status.ACTIVE,
            auto_renew=True
        )
        
        # Record Free transaction if price is 0, else PaymentService handles it
        if plan.price == 0:
            Transaction.objects.create(
                company=company,
                amount=0,
                status=Transaction.Status.COMPLETED,
                description=f"Free Plan Subscription: {plan.name}"
            )
            
        return subscription
    
    @staticmethod
    def cancel_subscription(company) -> CompanySubscription:
        sub = CompanySubscription.objects.filter(
            company=company,
            status=CompanySubscription.Status.ACTIVE
        ).first()
        
        if not sub:
            raise ValidationError("No active subscription found.")
            
        sub.auto_renew = False
        sub.save()
        return sub
