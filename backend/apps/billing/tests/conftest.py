import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.company.companies.models import Company
from apps.billing.models import SubscriptionPlan

from apps.company.industries.models import Industry

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return User.objects.create_user(
        email="company@test.com",
        password="password123",
        first_name="Test",
        last_name="Owner",
        role='employer'
    )

@pytest.fixture
def industry():
    return Industry.objects.create(name="Tech", slug="tech")

@pytest.fixture
def company(user, industry):
    company = Company.objects.create(
        user=user,
        company_name="Test Company",
        slug="test-company",
        industry=industry,
        description="A test company"
    )
    return company

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def plan():
    return SubscriptionPlan.objects.create(
        name="Pro Plan",
        slug="pro",
        price=1000000,
        currency="VND",
        duration_days=30
    )
