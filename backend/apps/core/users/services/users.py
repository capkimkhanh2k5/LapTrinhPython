from django.db import transaction
from pydantic import BaseModel, EmailStr
from apps.users.models import User

class UserCreateInput(BaseModel):
    email: EmailStr
    password: str
    role: str = 'recruiter'


def create_user(data: UserCreateInput) -> User:
    """
    Service to create a user with hashed password.
    """
    with transaction.atomic():
        user = User.objects.create_user(
            email=data.email,
            password=data.password,
            role=data.role
        )
        return user

