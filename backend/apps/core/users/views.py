from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView

from .permissions import IsAdmin

from .models import CustomUser
from .services.auth import (
    login_user, logout_user, register_user, forgot_password, reset_password, 
    verify_email, resend_verification, change_password, check_email,
    social_login, verify_2fa,
    LoginInput, LogoutInput, RegisterInput, ForgotPasswordInput, 
    ResetPasswordInput, VerifyEmailInput, ResendVerificationInput, 
    ChangePasswordInput, CheckEmailInput, SocialLoginInput, Verify2FAInput, # New inputs
    AuthenticationError
)
from .services.users import create_user, UserCreateInput, bulk_user_action, upload_user_avatar, update_user_role, update_user_status, delete_user, update_user, UserUpdateInput
from .selectors.users import list_users, get_user_stats
from .serializers import (
    CustomUserSerializer, LoginSerializer, LogoutSerializer, 
    LoginResponseSerializer, RegisterSerializer, RegisterResponseSerializer, 
    ForgotPasswordSerializer, ResetPasswordSerializer, VerifyEmailSerializer, 
    ResendVerificationSerializer, ChangePasswordSerializer, CheckEmailSerializer,
    SocialAuthSerializer, Verify2FASerializer,
    UserUpdateSerializer, UserStatusSerializer, UserRoleSerializer, UserAvatarSerializer
)
from django.http import HttpResponse

from apps.system.activity_logs.models import ActivityLog
from apps.system.activity_logs.serializers import ActivityLogSerializer


class CustomUserViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Support filtering
        return list_users(filters=self.request.query_params)

    def get_permissions(self):
        if self.action in ['create']:
            return [AllowAny()]
        
        if self.action in ['destroy', 'update_status_action', 'update_role_action']:
            return [IsAuthenticated(), IsAdmin()]
            
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        # Validate Input via Serializer
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Call Service Layer
        try:
            user_input = UserCreateInput(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                role=serializer.validated_data.get('role', CustomUser.Role.RECRUITER)
            )
            user = create_user(data=user_input)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Return Response
        output_serializer = self.get_serializer(user)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        updated_user = update_user(
            user=user, 
            data=UserUpdateInput(**serializer.validated_data)
        )
        
        return Response(CustomUserSerializer(updated_user).data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
    
        delete_user(user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status_action(self, request, pk=None):
        user = self.get_object()
        serializer = UserStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_user = update_user_status(user, serializer.validated_data['status'])
            return Response(CustomUserSerializer(updated_user).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='role')
    def update_role_action(self, request, pk=None):
        user = self.get_object()
        serializer = UserRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_user = update_user_role(user, serializer.validated_data['role'])
            return Response(CustomUserSerializer(updated_user).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'delete'], url_path='avatar')
    def manage_avatar(self, request, pk=None):
        user = self.get_object()
        
        if request.method == 'POST':
            serializer = UserAvatarSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            try:
                updated_user = upload_user_avatar(user, serializer.validated_data['avatar'])
                return Response(CustomUserSerializer(updated_user).data)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                
        elif request.method == 'DELETE':
            user.avatar_url = None
            user.save(update_fields=['avatar_url'])
            return Response(CustomUserSerializer(user).data)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='activity-logs')
    def activity_logs(self, request, pk=None):
        user = self.get_object()
        # Lazy import to avoid circular dependency
        
        logs = ActivityLog.objects.filter(user=user)
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = ActivityLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        # Admin only
        if not request.user.role == CustomUser.Role.ADMIN:
             return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
             
        data = get_user_stats()
        return Response(data)

    @action(detail=False, methods=['get'], url_path='export')
    def export(self, request):
        # Admin only
        if not request.user.role == CustomUser.Role.ADMIN:
             return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
             
        try:
            csv_content = export_users_csv()

            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
            return response
        except Exception as e:
             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='bulk-action')
    def bulk_action(self, request):
        # Admin only
        if not request.user.role == CustomUser.Role.ADMIN:
             return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
             
        ids = request.data.get('ids', [])
        action_type = request.data.get('action') # 'delete', 'update_status'
        value = request.data.get('value') # e.g. 'active', 'banned'
        
        if not ids or not action_type:
            return Response({"detail": "Missing ids or action"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            result = bulk_user_action(ids, action_type, value)
            return Response(result)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/auth/login/
    Login user và trả về JWT tokens
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Validate input via serializer
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Gọi service layer
        try:
            result = login_user(data=LoginInput(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        # 3. Trả về response
        output_serializer = LoginResponseSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Logout user và blacklist refresh token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 1. Validate input via serializer
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Gọi service layer
        try:
            logout_user(data=LogoutInput(
                refresh_token=serializer.validated_data['refresh_token']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Trả về response
        return Response({"detail": "Đăng xuất thành công"}, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Đăng ký tài khoản mới
    """
    permission_classes = [AllowAny]  # Cho phép anonymous
    
    def post(self, request):
        # Validate input via serializer
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            result = register_user(data=RegisterInput(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
                full_name=serializer.validated_data['full_name'],
                role=serializer.validated_data.get('role', 'recruiter')
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        output_serializer = RegisterResponseSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

class ForgotPasswordView(APIView):
    """
    POST /api/auth/forgot-password/
    Quên mật khẩu
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate input via serializer
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            forgot_password(data=ForgotPasswordInput(
                email=serializer.validated_data['email']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        return Response({"detail": "Email đã được gửi"}, status=status.HTTP_200_OK)

class ResetPasswordView(APIView):
    """
    POST /api/auth/reset-password/
    Reset mật khẩu
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate input via serializer
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            reset_password(data=ResetPasswordInput(
                reset_token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        return Response({"detail": "Mật khẩu đã được đổi"}, status=status.HTTP_200_OK)

class VerifyEmailView(APIView):
    """
    POST /api/auth/verify-email/
    Verify email
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate input via serializer
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            verify_email(data=VerifyEmailInput(
                token=serializer.validated_data['email_verification_token']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        return Response({"detail": "Email đã được xác minh"}, status=status.HTTP_200_OK)

class ResendVerificationView(APIView):
    """
    POST /api/auth/resend-verification/
    Resend verification email
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Validate input via serializer
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            resend_verification(data=ResendVerificationInput(
                email=serializer.validated_data['email']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        return Response({"detail": "Email xác minh đã được gửi lại"}, status=status.HTTP_200_OK)

class ChangePasswordView(APIView):
    """
    POST /api/auth/change-password/
    Thay đổi mật khẩu
    """
    permission_classes = [IsAuthenticated] # Login mới đổi

    def post(self, request):
        # Validate input via serializer
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            change_password(data=ChangePasswordInput(
                user_id=request.user.id,
                old_password=serializer.validated_data['old_password'],
                new_password=serializer.validated_data['new_password']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        return Response({"detail": "Mật khẩu đã được đổi"}, status=status.HTTP_200_OK)

class CheckEmailView(APIView):
    """
    POST /api/auth/check-email/
    Kiểm tra email
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        # Validate input via serializer
        serializer = CheckEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            result = check_email(data=CheckEmailInput(email=serializer.validated_data['email']))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        return Response(result, status=status.HTTP_200_OK)

class SocialLoginView(APIView):
    """
    POST /api/auth/social/(google|facebook|linkedin)/
    Đăng nhập với tài khoản xã hội
    """
    permission_classes = [AllowAny]
    
    def post(self, request, provider):
        # Validate input via serializer
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            result = social_login(data=SocialLoginInput(
                provider=provider,
                access_token=serializer.validated_data['access_token'],
                email=serializer.validated_data['email'],
                full_name=serializer.validated_data['full_name'],
                role=serializer.validated_data.get('role', 'recruiter')
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        output_serializer = LoginResponseSerializer(result)
        return Response(output_serializer.data, status=status.HTTP_200_OK)

class Verify2FAView(APIView):
    """
    POST /api/auth/verify-2fa/
    Kiểm tra mã 2FA
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Validate input via serializer
        serializer = Verify2FASerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Gọi service layer
        try:
            result = verify_2fa(data=Verify2FAInput(
                user_id=request.user.id,
                code=serializer.validated_data['code']
            ))
        except AuthenticationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        # Trả về response
        return Response(result, status=status.HTTP_200_OK)

class AuthMeView(APIView):
    """
    GET /api/auth/me/
    Lấy thông tin người dùng
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Validate input via serializer
        serializer = CustomUserSerializer(request.user)
        
        # Trả về response
        return Response(serializer.data)