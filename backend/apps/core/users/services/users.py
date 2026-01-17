from django.db import transaction
from pydantic import BaseModel, EmailStr
from ..models import CustomUser


class UserCreateInput(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ''
    role: str = 'recruiter'


def create_user(data: UserCreateInput) -> CustomUser:
    """
    Service to create a user with hashed password.
    Tuân thủ N-Tier: Services chứa logic WRITE (create, update, delete)
    """
    with transaction.atomic():
        user = CustomUser.objects.create_user(
            email=data.email,
            password=data.password,
            full_name=data.full_name,
            role=data.role
        )
        return user

