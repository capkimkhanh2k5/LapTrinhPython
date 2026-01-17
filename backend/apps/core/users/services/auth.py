from pydantic import BaseModel, EmailStr
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone

from ..selectors.users import get_user_by_email
from ..models import CustomUser


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
        raise AuthenticationError("Email không tồn tại!")
    
    if not user.check_password(data.password):
        raise AuthenticationError("Mật khẩu không đúng!")

    if user.status != 'active':
        raise AuthenticationError("Tài khoản đã bị khóa!")

    # Cập nhật last_login
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])

    # Tạo JWT tokens
    refresh = RefreshToken.for_user(user)
    
    return {
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': user
    }


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
        raise AuthenticationError(f"Không thể logout: {str(e)}")

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
        raise AuthenticationError("Email đã được sử dụng!")
    
    #Tạo user mới
    user = CustomUser.objects.create_user(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        role=data.role
    )
    
    #Tạo JWT tokens
    refresh_token = RefreshToken.for_user(user)
    
    #Return kết quả
    return {    
        'access_token': str(refresh_token.access_token),
        'refresh_token': str(refresh_token),
        'user': user
    }