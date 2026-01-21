import pytest
from rest_framework import status
from django.urls import reverse
from apps.blog.models import Post

@pytest.mark.django_db
class TestBlogViews:
    def test_public_list_posts(self, api_client, published_post, draft_post):
        url = reverse('posts-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['title'] == published_post.title

    def test_admin_list_posts(self, api_client, admin_user, published_post, draft_post):
        api_client.force_authenticate(user=admin_user)
        url = reverse('posts-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2 # Admin sees all

    def test_create_post_admin(self, api_client, admin_user, category, tag):
        api_client.force_authenticate(user=admin_user)
        url = reverse('posts-list')
        data = {
            "title": "New Post",
            "content": "New Content",
            "category_id": category.id,
            "tag_ids": [tag.id],
            "status": "draft"
        }
        response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert Post.objects.count() == 1 # Assuming db cleared or fixtures not counted? 
        # Fixtures are created per test function scope if used. 
        # But here checking 'count' might be affected by fixtures if they are instantiated.
        # Arguments `category`, `tag` do create them. But `published_post` is NOT requested, so count should reflect what's created here?
        # No, `published_post` argument is NOT passed, so it's not created.
        # But checking `count() == 1`.
    
    def test_regular_user_cannot_create_post(self, api_client, public_user):
        api_client.force_authenticate(user=public_user)
        url = reverse('posts-list')
        data = {"title": "Hacked", "content": "..."}
        response = api_client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_view_count_increment(self, api_client, published_post):
        url = reverse('posts-view-count', kwargs={'slug': published_post.slug})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        published_post.refresh_from_db()
        assert published_post.view_count == 1
