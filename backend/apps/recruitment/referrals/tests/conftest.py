import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.company.companies.models import Company
from apps.recruitment.job_categories.models import JobCategory
from apps.recruitment.jobs.models import Job

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    # Create a user with role='employer' (assuming role field logic)
    return User.objects.create_user(
        email='company@test.com',
        password='password123',
        full_name='Test Company',
        role='employer' 
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
    api_client.force_authenticate(user=user)
    return api_client

@pytest.fixture
def category():
    return JobCategory.objects.create(name="IT Software", slug="it-software")

@pytest.fixture
def job(company, category, user):
    return Job.objects.create(
        company=company,
        title="Python Developer",
        category=category,
        job_type="full-time",
        level="junior",
        description="Dev python",
        requirements="Python skills",
        status="published",
        created_by=user
    )
