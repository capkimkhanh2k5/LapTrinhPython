import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.blog.models import Category, Tag, Post

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
def public_user():
    return User.objects.create_user(
        email="user@test.com",
        password="password123",
        first_name="Public",
        last_name="User"
    )

@pytest.fixture
def category():
    return Category.objects.create(name="Tech", slug="tech")

@pytest.fixture
def tag():
    return Tag.objects.create(name="Python", slug="python")

@pytest.fixture
def published_post(admin_user, category, tag):
    post = Post.objects.create(
        title="Published Post",
        author=admin_user,
        category=category,
        content="Content",
        status=Post.Status.PUBLISHED,
        published_at="2023-01-01T00:00:00Z"
    )
    post.tags.add(tag)
    return post

@pytest.fixture
def draft_post(admin_user, category):
    return Post.objects.create(
        title="Draft Post",
        author=admin_user,
        category=category,
        content="Draft Content",
        status=Post.Status.DRAFT
    )
