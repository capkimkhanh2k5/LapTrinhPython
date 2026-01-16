from django.db import transaction
from pydantic import BaseModel, EmailStr
from backend.apps.users.models import CustomUser

class UserCreateInput(BaseModel):
    email: EmailStr
    password: str
    is_employer: bool = False
    is_candidate: bool = False

def create_user(data: UserCreateInput) -> CustomUser:
    """
    Service to create a user with hashed password.
    """
    with transaction.atomic():
        user = CustomUser.objects.create_user(
            email=data.email,
            password=data.password,
            username=data.email,  # Username defaults to email
            is_employer=data.is_employer,
            is_candidate=data.is_candidate
        )
        return user
