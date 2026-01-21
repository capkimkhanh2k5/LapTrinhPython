from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.recruitment.referrals.views import ReferralProgramViewSet, ReferralViewSet

router = DefaultRouter()
router.register(r'referral-programs', ReferralProgramViewSet, basename='referral-programs')
router.register(r'referrals', ReferralViewSet, basename='referrals')

urlpatterns = [
    path('', include(router.urls)),
]
