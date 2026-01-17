from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomUserViewSet, LoginView, LogoutView, RegisterView, 
    ForgotPasswordView, ResetPasswordView, VerifyEmailView, 
    ResendVerificationView, ChangePasswordView, CheckEmailView, 
    AuthMeView, SocialLoginView, Verify2FAView
)

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    
    # Auth endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/refresh-token/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('auth/resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('auth/check-email/', CheckEmailView.as_view(), name='check-email'),
    path('auth/me/', AuthMeView.as_view(), name='auth-me'),
    path('auth/social/<str:provider>/', SocialLoginView.as_view(), name='social-login'),
    path('auth/verify-2fa/', Verify2FAView.as_view(), name='verify-2fa'),
]
