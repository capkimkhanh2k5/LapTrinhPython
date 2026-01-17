from typing import Iterable
from ..models import CustomUser


def list_users() -> Iterable[CustomUser]:
    """Lấy toàn bộ users"""
    return CustomUser.objects.all()


def get_user_by_email(*, email: str) -> CustomUser | None:
    """Lấy user theo email để authenticate"""
    return CustomUser.objects.filter(email=email).first()

def get_user_by_reset_token(*, reset_token: str) -> CustomUser | None:
    """
    Tìm user theo reset_token để reset password
    """
    return CustomUser.objects.filter(password_reset_token=reset_token).first()

def get_user_by_verification_token(*, token: str) -> CustomUser | None:
    """
    Tìm user theo email_verification_token để chức năng xác minh email
    """
    return CustomUser.objects.filter(email_verification_token=token).first()