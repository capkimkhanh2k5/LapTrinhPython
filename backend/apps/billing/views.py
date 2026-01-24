from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from apps.billing.models import SubscriptionPlan, CompanySubscription, PaymentMethod, Transaction
from apps.billing.serializers import (
    SubscriptionPlanSerializer, 
    CompanySubscriptionSerializer, 
    PaymentMethodSerializer, 
    TransactionSerializer,
    SubscribeInputSerializer
)
from apps.billing.services.subscriptions import SubscriptionService
from apps.billing.services.payments import PaymentService
from apps.billing.services.plans import PlanService
from apps.core.permissions import IsCompanyOwner
from apps.billing.services.vnpay import VNPayService

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

class CompanySubscriptionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, IsCompanyOwner]
    serializer_class = CompanySubscriptionSerializer
    
    def get_queryset(self):
        return CompanySubscription.objects.filter(company__user=self.request.user)

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        company_profile = getattr(request.user, 'company_profile', None)
        if not company_profile:
            return Response({"error": "User is not a company"}, status=status.HTTP_403_FORBIDDEN)
            
        sub = CompanySubscription.objects.filter(company=company_profile, status=CompanySubscription.Status.ACTIVE).first()
        if not sub:
            return Response({"detail": "No active subscription"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = self.get_serializer(sub)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='subscribe')
    def subscribe(self, request):
        input_ser = SubscribeInputSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        
        company_profile = getattr(request.user, 'company_profile', None)
        plan = SubscriptionPlan.objects.get(id=input_ser.validated_data['plan_id'])
        
        # Get IP Address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
            
        try:
            # Default to VNPay, auto-create if missing (Robustness)
            pm, created = PaymentMethod.objects.get_or_create(
                code='vnpay',
                defaults={
                    'name': 'VNPay Gateway',
                    'is_active': True,
                    'config': {} 
                }
            )
            
            # Calculate Amount (Check Plan Logic)
            amount = plan.price # Simplification
            
            txn, payment_url = PaymentService.process_payment(
                company=company_profile,
                amount=amount,
                payment_method=pm, 
                description=f"Subscribe to {plan.name}",
                ip_addr=ip
            )
            
            # Store Plan ID in Transaction for callback processing? 
            # Or better: Create Inactive Subscription first?
            # Creating Inactive Subscription is safer:
            sub = SubscriptionService.subscribe(company_profile, plan)
            # Override to inactive
            sub.status = CompanySubscription.Status.EXPIRED # Pending/Inactive
            sub.save()
            
            # Link TXN to Sub? (Using description or Reference Code hack for now as Models don't have direct link)
            txn.description = f"PLAN_ID:{plan.id}|SUB_ID:{sub.id}"
            txn.save()

            return Response({
                "payment_url": payment_url, 
                "transaction_ref": txn.reference_code
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='payment-return', permission_classes=[AllowAny])
    def payment_return(self, request):
        """
        Handle VNPay Return URL (Callback from User Browser).
        """
        
        # 1. Validate Checksum
        if not VNPayService.validate_payment(request.GET):
            return Response({"error": "Invalid Checksum"}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. Get Transaction
        txn_ref = request.GET.get('vnp_TxnRef')
        response_code = request.GET.get('vnp_ResponseCode')
        
        try:
            txn = Transaction.objects.get(reference_code=txn_ref)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)
            
        if txn.status == Transaction.Status.COMPLETED:
             return Response({"message": "Transaction already completed"})

        # 3. Update Transaction
        txn.vnp_TransactionNo = request.GET.get('vnp_TransactionNo')
        txn.vnp_BankCode = request.GET.get('vnp_BankCode')
        txn.vnp_CardType = request.GET.get('vnp_CardType')
        txn.vnp_OrderInfo = request.GET.get('vnp_OrderInfo')
        
        if response_code == '00':
            txn.status = Transaction.Status.COMPLETED
            txn.save()
            
            # 4. Activate Subscription (Parse from description)
            # Format: PLAN_ID:1|SUB_ID:5
            try:
                parts = txn.description.split('|')
                sub_id = parts[1].split(':')[1]
                sub = CompanySubscription.objects.get(id=sub_id)
                sub.status = CompanySubscription.Status.ACTIVE
                sub.save()
            except:
                pass # Handle manually
                
            return Response({"message": "Payment Successful", "data": request.GET})
        else:
            txn.status = Transaction.Status.FAILED
            txn.save()
            return Response({"message": "Payment Failed", "code": response_code}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='cancel')
    def cancel(self, request):
        company_profile = getattr(request.user, 'company_profile', None)
        try:
            sub = SubscriptionService.cancel_subscription(company_profile)
            return Response({"status": "cancelled", "end_date": sub.end_date})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated, IsCompanyOwner]
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        if hasattr(self.request.user, 'company_profile'):
            return Transaction.objects.filter(company=self.request.user.company_profile).order_by('-created_at')
        return Transaction.objects.none()
