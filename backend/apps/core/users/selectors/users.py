from apps.users.models import User
from typing import Iterable

def get_user(*, email: str) -> User | None:
    return User.objects.filter(email=email).first()

def list_users() -> Iterable[User]:
    return User.objects.all()
