from backend.apps.users.models import CustomUser
from typing import Iterable

def get_user(*, email: str) -> CustomUser | None:
    return CustomUser.objects.filter(email=email).first()

def list_users() -> Iterable[CustomUser]:
    return CustomUser.objects.all()
