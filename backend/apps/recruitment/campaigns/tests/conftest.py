import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.company.companies.models import Company
from apps.recruitment.job_categories.models import JobCategory
from apps.geography.provinces.models import Province
from apps.geography.addresses.models import Address

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    # Create a user with role='company'
    return User.objects.create_user(
        email='company@test.com',
        password='password123',
        full_name='Test Company',
        role='company'
    )

@pytest.fixture
def company(user):
    return Company.objects.create(
        user=user,
        company_name="Test Company",
        slug="test-company"
    )

@pytest.fixture
def authenticated_client(api_client, user, company):
    # Ensure company profile exists via company fixture
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def category():
    return JobCategory.objects.create(name="IT Software", slug="it-software")

@pytest.fixture
def province():
    return Province.objects.create(province_name="Ho Chi Minh", province_code="79")

@pytest.fixture
def address_hcm(province):
    return Address.objects.create(address_line="123 Street", province=province)
