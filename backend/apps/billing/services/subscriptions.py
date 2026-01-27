from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.billing.models import CompanySubscription, SubscriptionPlan, Transaction
from apps.billing.services.payments import PaymentService


class SubscriptionService:
    """
    Subscription Service với Hybrid Logic:
    - Cancellation: Passive (giữ end_date, tắt auto_renew).
    - New Subscription: Aggressive (xoá gói cũ ngay, tạo gói mới).
    """

    @staticmethod
    @transaction.atomic
    def subscribe(company, plan: SubscriptionPlan) -> CompanySubscription:
        """
        Đăng ký hoặc đổi gói mới.
        
        Logic Hybrid:
        1. Nếu có gói ACTIVE -> Hủy ngay lập tức (không hoàn tiền, không proration).
        2. Tạo gói mới ACTIVE từ hôm nay.
        3. Charge full giá gói mới.
        """
        # 1. Cancel any active subscription IMMEDIATELY
        current_sub = CompanySubscription.objects.filter(
            company=company, 
            status=CompanySubscription.Status.ACTIVE
        ).first()
        
        if current_sub:
            current_sub.status = CompanySubscription.Status.CANCELLED
            current_sub.auto_renew = False
            current_sub.save()
            
        # Also cancel any PENDING subscriptions (scheduled downgrades)
        CompanySubscription.objects.filter(
            company=company,
            status=CompanySubscription.Status.PENDING
        ).update(status=CompanySubscription.Status.CANCELLED)
            
        # 2. Create new subscription starting TODAY
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=plan.duration_days)
        
        subscription = CompanySubscription.objects.create(
            company=company,
            plan=plan,
            start_date=start_date,
            end_date=end_date,
            status=CompanySubscription.Status.ACTIVE,
            auto_renew=True
        )
        
        # 3. Record Transaction (Full Price)
        if plan.price == 0:
            Transaction.objects.create(
                company=company,
                amount=0,
                status=Transaction.Status.COMPLETED,
                description=f"Free Plan Subscription: {plan.name}"
            )
        else:
            Transaction.objects.create(
                company=company,
                amount=plan.price,
                status=Transaction.Status.PENDING,  # Needs Payment Gateway
                description=f"Subscription: {plan.name}"
            )
            
        return subscription

    @staticmethod
    @transaction.atomic
    def change_subscription(company, new_plan: SubscriptionPlan) -> CompanySubscription:
        """
        Thay đổi gói cước (Upgrade/Downgrade).
        
        Logic:
        1. Upgrade (Giá cao hơn): Huỷ gói cũ ngay, đăng ký gói mới ngay (Full giá).
        2. Downgrade (Giá thấp hơn hoặc bằng): Chờ gói cũ hết hạn, gói mới ở trạng thái PENDING.
        """
        current_sub = SubscriptionService.get_active_subscription(company)
        
        # Case 1: No active sub -> Subscribe immediately
        if not current_sub:
            return SubscriptionService.subscribe(company, new_plan)
            
        # Case 2: Upgrade -> Aggressive Replace
        if new_plan.price > current_sub.plan.price:
            return SubscriptionService.subscribe(company, new_plan)
            
        # Case 3: Downgrade -> Schedule for future
        # 3.1 Turn off auto_renew for current
        current_sub.auto_renew = False
        current_sub.save()
        
        # 3.2 Cancel any existing PENDING subs
        CompanySubscription.objects.filter(
            company=company,
            status=CompanySubscription.Status.PENDING
        ).update(status=CompanySubscription.Status.CANCELLED)
        
        # 3.3 Create PENDING subscription
        start_date = current_sub.end_date + timedelta(days=1)
        end_date = start_date + timedelta(days=new_plan.duration_days)
        
        new_sub = CompanySubscription.objects.create(
            company=company,
            plan=new_plan,
            start_date=start_date,
            end_date=end_date,
            status=CompanySubscription.Status.PENDING,
            auto_renew=True
        )
        
        return new_sub

    @staticmethod
    def cancel_subscription(company) -> CompanySubscription:
        """
        Hủy gói cước (Passive).
        
        Logic:
        1. Tắt `auto_renew` để không gia hạn tự động.
        2. Giữ nguyên `status=ACTIVE` cho đến khi hết hạn (`end_date`).
        3. User vẫn được hưởng quyền lợi đến hết ngày đã trả tiền.
        
        NOTE: Cần có Celery task/cronjob để quét và chuyển ACTIVE -> EXPIRED khi quá end_date.
        """
        sub = CompanySubscription.objects.filter(
            company=company,
            status=CompanySubscription.Status.ACTIVE
        ).first()
        
        if not sub:
            raise ValidationError("No active subscription found.")
            
        sub.auto_renew = False
        sub.save()
        
        return sub

    @staticmethod
    def get_active_subscription(company) -> CompanySubscription:
        """Lấy gói cước đang hoạt động."""
        return CompanySubscription.objects.filter(
            company=company,
            status=CompanySubscription.Status.ACTIVE
        ).first()

    @staticmethod
    @transaction.atomic
    def renew_subscription(subscription: CompanySubscription) -> CompanySubscription:
        """
        Gia hạn gói cước (Được gọi bởi Celery task).
        
        Logic:
        1. Kiểm tra `auto_renew=True` và gói sắp hết hạn.
        2. Extend `end_date` thêm `duration_days`.
        3. Tạo Transaction cho kỳ mới.
        """
        if not subscription.auto_renew:
            raise ValidationError("Subscription is not set to auto-renew.")
            
        plan = subscription.plan
        
        # Extend end_date
        subscription.end_date = subscription.end_date + timedelta(days=plan.duration_days)
        subscription.save()
        
        # Record Transaction for renewal
        Transaction.objects.create(
            company=subscription.company,
            amount=plan.price,
            status=Transaction.Status.PENDING,  # Needs Payment
            description=f"Subscription Renewal: {plan.name}"
        )
        
        return subscription
