import secrets
import requests
from datetime import timedelta

from pydantic import BaseModel, EmailStr
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from ..selectors.users import get_user_by_email, get_user_by_reset_token, get_user_by_verification_token
from ..models import CustomUser

import string
from apps.email.services import EmailService



# Input Models

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class LogoutInput(BaseModel):
    refresh_token: str


# Exception Class

class AuthenticationError(Exception):
    """Exception khi xác thực thất bại"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


# Helper Functions

def generate_tokens(user: CustomUser) -> dict:
    """Helper tạo JWT tokens cho user"""
    refresh = RefreshToken.for_user(user)
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': user
    }


def verify_social_token(provider: str, token: str) -> dict:
    """
    Xác thực token với Provider (Google/Facebook/LinkedIn)
    Returns: dict chứa thông tin user từ provider
    """

    #TODO: Nếu lỗi Social -> kiểm tra tại đây
    
    if provider == 'google':
        # URL xác thực token của Google
        response = requests.get(f'https://www.googleapis.com/oauth2/v3/userinfo?access_token={token}')
        if response.status_code != 200:
            raise AuthenticationError("Token Google is invalid or expired!")
        return response.json() # Chứa: email, name, picture, sub...
        
    elif provider == 'facebook':
        # URL xác thực token của Facebook
        response = requests.get(f'https://graph.facebook.com/me?fields=id,name,email,picture&access_token={token}')
        if response.status_code != 200:
            raise AuthenticationError("Token Facebook is invalid or expired!")
        return response.json()
        
    elif provider == 'linkedin':
        # URL xác thực token của LinkedIn
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get('https://api.linkedin.com/v2/userinfo', headers=headers)
        if response.status_code != 200:
            raise AuthenticationError("Token LinkedIn is invalid or expired!")
        return response.json()
        
    raise AuthenticationError(f"Provider {provider} is not supported!")


# Service Functions

def login_user(data: LoginInput) -> dict:
    """
    Xác thực user và trả về JWT tokens.
    
    Returns:
        dict với keys: access, refresh, user
    
    Raises:
        AuthenticationError nếu email/password sai
    """
    # Lấy user từ selector
    user = get_user_by_email(email=data.email)
    
    if not user:
        raise AuthenticationError("Email not found!")
    
    if not user.check_password(data.password):
        raise AuthenticationError("Password is incorrect!")

    if user.status != 'active':
        raise AuthenticationError("Account is inactive!")

    # Update last_login
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    return generate_tokens(user)


def logout_user(data: LogoutInput) -> bool:
    """
    Logout user bằng cách blacklist refresh token.

    Returns:
        bool: True nếu logout thành công
    
    Raises:
        AuthenticationError nếu token không hợp lệ
    """
    try:
        token = RefreshToken(data.refresh_token)
        token.blacklist()
        return True
    except Exception as e:
        raise AuthenticationError(f"Can't logout: {str(e)}")

class RegisterInput(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = 'recruiter'  # Mặc định là recruiter

def register_user(data: RegisterInput) -> dict:
    """
    Đăng ký user mới và trả về JWT tokens.
    
    Returns:
        dict với keys: access_token, refresh_token, user
    
    Raises:
        AuthenticationError nếu email đã tồn tại
    """
    
    #Check email tồn tại
    existing_user = get_user_by_email(email=data.email)
    if existing_user:
        raise AuthenticationError("Email is already in use!")
    
    #Create new user
    user = CustomUser.objects.create_user(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        role=data.role
    )
    
    user.email_verification_token = secrets.token_urlsafe(32)
    user.save(update_fields=["email_verification_token"])

    # Send Verification Email
    verification_link = f"http://localhost:3000/auth/verify-email?token={user.email_verification_token}"
    
    EmailService.send_email(
        recipient=user.email,
        subject="[JobPortal] Xác thực tài khoản của bạn",
        template_path="emails/auth/verify_email.html",
        context={
            "user_name": user.full_name,
            "verification_link": verification_link
        }
    )
    
    #Return kết quả
    return generate_tokens(user)

class ForgotPasswordInput(BaseModel):
    email: EmailStr

class ResetPasswordInput(BaseModel):
    reset_token: str
    new_password: str

def forgot_password(data: ForgotPasswordInput) -> bool:
    """
    Quên mật khẩu: Gửi mã OTP xác thực qua email
    Returns:
        bool: True nếu gửi thành công
    Raises:
        AuthenticationError nếu email không tồn tại
    """
    user = get_user_by_email(email=data.email)
    if not user:
        raise AuthenticationError("Email not found!")
    
    # Generate 6-digit OTP
    otp_code = ''.join(secrets.choice(string.digits) for _ in range(6))
    reset_expires = timezone.now() + timedelta(minutes=10)
    
    user.password_reset_token = otp_code
    user.password_reset_expires = reset_expires
    user.save(update_fields=["password_reset_token", "password_reset_expires"])
    
    # Send OTP Email
    EmailService.send_email(
        recipient=user.email,
        subject="[JobPortal] Mã xác thực đặt lại mật khẩu",
        template_path="emails/auth/otp.html",
        context={
            "user_name": user.full_name,
            "otp_code": otp_code,
            "expiry_minutes": 10
        }
    )
    
    return True
    
def reset_password(data: ResetPasswordInput) -> bool:
    """
    Reset mật khẩu

    Returns:
        bool: True nếu reset mật khẩu thành công
    
    Raises:
        AuthenticationError nếu token không hợp lệ hoặc hết hạn
    """

    user = get_user_by_reset_token(reset_token=data.reset_token)
    if not user:
        raise AuthenticationError("Token is invalid!")
    
    if user.password_reset_expires < timezone.now():
        raise AuthenticationError("Token has expired!")
    
    user.set_password(data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    user.save(update_fields=["password", "password_reset_token", "password_reset_expires"])
    
    return True


class VerifyEmailInput(BaseModel):
    token: str

class ResendVerificationInput(BaseModel):
    email: EmailStr

def verify_email(data: VerifyEmailInput) -> bool:
    """
    Verify email

    Returns:
        bool: True nếu verify email thành công
    
    Raises:
        AuthenticationError nếu token không hợp lệ
    """
    user = get_user_by_verification_token(token=data.token)
    if not user:
        raise AuthenticationError("Token is invalid!")
    
    user.email_verified = True
    user.email_verification_token = None
    user.save(update_fields=["email_verified", "email_verification_token"])
    
    return True

def resend_verification(data: ResendVerificationInput) -> bool:
    """
    Resend verification email

    Returns:
        bool: True nếu resend verification email thành công
    
    Raises:
        AuthenticationError nếu email không tồn tại hoặc email đã được xác minh
    """

    user = get_user_by_email(email=data.email)
    if not user:
        raise AuthenticationError("Email not found!")
    
    if user.email_verified:
        raise AuthenticationError("Email has been verified!")
    
    user.email_verification_token = secrets.token_urlsafe(32)
    user.save(update_fields=["email_verification_token"])

    # Send Verification Email
    verification_link = f"http://localhost:3000/auth/verify-email?token={user.email_verification_token}"
    
    EmailService.send_email(
        recipient=user.email,
        subject="[JobPortal] Gửi lại liên kết xác thực",
        template_path="emails/auth/verify_email.html",
        context={
            "user_name": user.full_name,
            "verification_link": verification_link
        }
    )
    
    return True

class ChangePasswordInput(BaseModel):
    user_id: int
    old_password: str
    new_password: str

class CheckEmailInput(BaseModel):
    email: EmailStr

def change_password(data: ChangePasswordInput) -> bool:
    """
    Thay đổi mật khẩu

    Returns:
        bool: True nếu thay đổi mật khẩu thành công
    
    Raises:
        AuthenticationError nếu mật khẩu cũ không đúng
    """
    user = CustomUser.objects.get(id=data.user_id)

    if not user.check_password(data.old_password):
        raise AuthenticationError("Old password is incorrect!")

    user.set_password(data.new_password)
    user.save(update_fields=["password"])

    return True

def check_email(data: CheckEmailInput) -> dict:
    """
    Kiểm tra email tồn tại

    Returns:
        dict: {"exists": True/False}
    """
    user = get_user_by_email(email=data.email)
    return {"exists": user is not None}

class SocialLoginInput(BaseModel):
    provider: str  # 'google', 'facebook', 'linkedin'
    access_token: str  # Token nhận từ frontend
    email: EmailStr  # Giả định frontend gửi kèm email
    full_name: str
    role: str = 'recruiter'

class Verify2FAInput(BaseModel):
    user_id: int
    code: str
    
def social_login(data: SocialLoginInput) -> dict:
    """
    Đăng nhập với tài khoản xã hội
    """
    # Xác thực token với Provider để lấy thông tin thực tế
    social_user_data = verify_social_token(data.provider, data.access_token)
    
    # Ưu tiên email từ provider để đảm bảo chính xác
    email = social_user_data.get('email') or data.email
    full_name = social_user_data.get('name') or social_user_data.get('full_name') or data.full_name
    
    user = get_user_by_email(email=email)
    
    # User không tồn tại thì tạo mới
    if not user:
        user = CustomUser.objects.create_user(
            email=email,
            password=None, # Social user không bắt buộc password
            full_name=full_name,
            role=data.role
        )
        # Tự động verify email cho social user
        user.email_verified = True
        user.save(update_fields=['email_verified'])
    
    return generate_tokens(user)
    
def verify_2fa(data: Verify2FAInput) -> bool:
    """
    Kiểm tra mã 2FA
    """
    user = CustomUser.objects.get(id=data.user_id)

    if not user.two_factor_enabled:
        raise AuthenticationError("Account is not enabled 2FA!")

    if not user.check_2fa_code(data.code):
        raise AuthenticationError("2FA code is incorrect!")
    
    return True
        