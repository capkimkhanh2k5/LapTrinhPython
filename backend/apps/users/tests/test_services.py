import pytest
from apps.users.services.users import create_user, UserCreateInput
from apps.users.models import CustomUser

@pytest.mark.django_db
def test_create_user_service():
    """Test creating user via service layer standard."""
    user_input = UserCreateInput(
        email="test@example.com",
        password="strongpassword123",
        is_employer=True
    )
    user = create_user(data=user_input)
    
    assert user.email == "test@example.com"
    assert user.check_password("strongpassword123")
    assert user.is_employer is True
    assert CustomUser.objects.count() == 1
