"""
Blog Views Tests - Django TestCase Version
"""
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.blog.models import Category, Tag, Post

User = get_user_model()


class TestBlogViews(APITestCase):
    """Tests for Blog ViewSet"""
    
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = User.objects.create_superuser(
            email="admin@blog-test.com",
            password="password123",
            first_name="Admin",
            last_name="User"
        )
        cls.public_user = User.objects.create_user(
            email="user@blog-test.com",
            password="password123",
            first_name="Public",
            last_name="User"
        )
        cls.category = Category.objects.create(name="Tech", slug="tech")
        cls.tag = Tag.objects.create(name="Python", slug="python")
        
        # Published post
        cls.published_post = Post.objects.create(
            title="Published Post",
            slug="published-post",
            author=cls.admin_user,
            category=cls.category,
            content="Content",
            status=Post.Status.PUBLISHED,
            published_at="2023-01-01T00:00:00Z"
        )
        cls.published_post.tags.add(cls.tag)
        
        # Draft post
        cls.draft_post = Post.objects.create(
            title="Draft Post",
            slug="draft-post",
            author=cls.admin_user,
            category=cls.category,
            content="Draft Content",
            status=Post.Status.DRAFT
        )
    
    def test_public_list_posts(self):
        """Authenticated users see published posts (API requires auth)"""
        self.client.force_authenticate(user=self.public_user)
        url = reverse('posts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Public user sees only published posts
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], self.published_post.title)
    
    def test_admin_list_posts(self):
        """Admin users see all posts (published and draft)"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('posts-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Admin sees all
    
    def test_create_post_admin(self):
        """Admin can create posts"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('posts-list')
        data = {
            "title": "New Post",
            "content": "New Content",
            "category_id": self.category.id,
            "tag_ids": [self.tag.id],
            "status": "draft"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_regular_user_can_create_draft_post(self):
        """Regular users can create posts (as draft for review)"""
        self.client.force_authenticate(user=self.public_user)
        url = reverse('posts-list')
        data = {"title": "User Post", "content": "User content", "category_id": self.category.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Verify it's created as draft
        created_post = Post.objects.get(title="User Post")
        self.assertEqual(created_post.status, Post.Status.DRAFT)
    
    def test_view_count_increment(self):
        """View count increments when action is called"""
        url = reverse('posts-view-count', kwargs={'slug': self.published_post.slug})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.published_post.refresh_from_db()
        self.assertEqual(self.published_post.view_count, 1)
