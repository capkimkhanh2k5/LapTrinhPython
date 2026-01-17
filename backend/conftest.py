import os
import pytest

# Cấu hình Django settings cho pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')

# Setup Django
import django
django.setup()


@pytest.fixture
def api_client():
    """Fixture tạo API client cho tất cả tests"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def user(db):
    """Fixture tạo một CustomUser cho tests"""
    from apps.core.users.models import CustomUser
    return CustomUser.objects.create_user(
        email="testuser@example.com",
        password="password123",
        full_name="Test User"
    )
