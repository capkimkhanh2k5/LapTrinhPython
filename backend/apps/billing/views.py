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
        
        # Payment Logic Simulation
        # TODO: Cần xem lại logic này, tích hợp thanh toán bằng VN PAY hoặc các gateway khác
        
        
        try:
            subscription = SubscriptionService.subscribe(company_profile, plan)
            return Response(self.get_serializer(subscription).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
