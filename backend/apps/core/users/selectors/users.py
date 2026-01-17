from typing import Iterable
from ..models import CustomUser


def list_users() -> Iterable[CustomUser]:
    """Lấy toàn bộ users"""
    return CustomUser.objects.all()


def get_user_by_email(*, email: str) -> CustomUser | None:
    """Lấy user theo email để authenticate"""
    return CustomUser.objects.filter(email=email).first()
