import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.email.models import EmailTemplate, EmailTemplateCategory

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        email="admin@test.com",
        password="password123",
        first_name="Admin",
        last_name="User"
    )

@pytest.fixture
def regular_user():
    return User.objects.create_user(
        email="user@test.com",
        password="password123",
        first_name="Test",
        last_name="User"
    )

@pytest.fixture
def category():
    return EmailTemplateCategory.objects.create(
        name="Notifications",
        slug="notifications"
    )

@pytest.fixture
def email_template(category):
    return EmailTemplate.objects.create(
        name="Welcome Email",
        slug="welcome-email",
        category=category,
        subject="Welcome {{ name }}",
        body="Hello {{ name }}, welcome to our platform!",
        variables={"name": "User Name"}
    )
