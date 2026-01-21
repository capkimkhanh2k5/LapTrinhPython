from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.billing.views import SubscriptionPlanViewSet, CompanySubscriptionViewSet, TransactionViewSet

router = DefaultRouter()
router.register(r'subscription-plans', SubscriptionPlanViewSet, basename='subscription-plans')
router.register(r'company-subscriptions', CompanySubscriptionViewSet, basename='company-subscriptions')
router.register(r'transactions', TransactionViewSet, basename='transactions')

urlpatterns = [
    path('', include(router.urls)),
]
