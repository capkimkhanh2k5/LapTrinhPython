"""
Tests for Media Types Views (ViewSet)
Module 22: Advanced Features - Media Types API

Test Coverage:
- GET /api/media-types/ (list)
- POST /api/media-types/ (create)
- PUT /api/media-types/:id/ (update)
- DELETE /api/media-types/:id/ (destroy)
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.company.media_types.models import MediaType

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    """Create admin user"""
    user = User.objects.create_user(
        email='admin@test.com',
        password='adminpass123',
        is_staff=True,
        is_superuser=True
    )
    return user


@pytest.fixture
def normal_user(db):
    """Create normal user"""
    user = User.objects.create_user(
        email='user@test.com',
        password='userpass123'
    )
    return user


@pytest.fixture
def media_type(db):
    """Create sample media type"""
    return MediaType.objects.create(
        type_name='Image',
        description='Image files (jpg, png, gif)',
        is_active=True
    )


@pytest.fixture
def media_types(db):
    """Create multiple media types"""
    types = [
        MediaType.objects.create(type_name='Image', description='Image files', is_active=True),
        MediaType.objects.create(type_name='Video', description='Video files', is_active=True),
        MediaType.objects.create(type_name='Document', description='Document files', is_active=False),
    ]
    return types


# ============================================
# LIST TESTS - GET /api/media-types/
# ============================================

@pytest.mark.django_db
class TestMediaTypeList:
    """Tests for listing media types"""
    
    def test_list_media_types_public_access(self, api_client, media_types):
        """List endpoint should be public (no auth required)"""
        url = reverse('media-types-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3
    
    def test_list_media_types_filter_active(self, api_client, media_types):
        """Should filter by is_active"""
        url = reverse('media-types-list')
        response = api_client.get(url, {'is_active': 'true'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        for item in response.data:
            assert item['is_active'] is True
    
    def test_list_media_types_filter_inactive(self, api_client, media_types):
        """Should filter inactive media types"""
        url = reverse('media-types-list')
        response = api_client.get(url, {'is_active': 'false'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['is_active'] is False
    
    def test_list_media_types_returns_expected_fields(self, api_client, media_type):
        """Response should contain all expected fields"""
        url = reverse('media-types-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        item = response.data[0]
        assert 'id' in item
        assert 'type_name' in item
        assert 'description' in item
        assert 'is_active' in item
        assert 'created_at' in item


# ============================================
# CREATE TESTS - POST /api/media-types/
# ============================================

@pytest.mark.django_db
class TestMediaTypeCreate:
    """Tests for creating media types"""
    
    def test_create_media_type_admin_success(self, api_client, admin_user):
        """Admin should be able to create media type"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('media-types-list')
        data = {
            'type_name': 'Audio',
            'description': 'Audio files (mp3, wav)',
            'is_active': True
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['type_name'] == 'Audio'
        assert response.data['description'] == 'Audio files (mp3, wav)'
        assert response.data['is_active'] is True
        assert MediaType.objects.filter(type_name='Audio').exists()
    
    def test_create_media_type_unauthenticated_fails(self, api_client):
        """Unauthenticated user should not create"""
        url = reverse('media-types-list')
        data = {'type_name': 'Audio', 'description': 'Audio files'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_media_type_normal_user_fails(self, api_client, normal_user):
        """Normal user (non-admin) should not create"""
        api_client.force_authenticate(user=normal_user)
        url = reverse('media-types-list')
        data = {'type_name': 'Audio', 'description': 'Audio files'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_media_type_duplicate_name_fails(self, api_client, admin_user, media_type):
        """Should reject duplicate type_name"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('media-types-list')
        data = {'type_name': 'Image', 'description': 'Another image type'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already exists' in str(response.data)
    
    def test_create_media_type_missing_name_fails(self, api_client, admin_user):
        """Should require type_name field"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('media-types-list')
        data = {'description': 'Some description'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================
# UPDATE TESTS - PUT /api/media-types/:id/
# ============================================

@pytest.mark.django_db
class TestMediaTypeUpdate:
    """Tests for updating media types"""
    
    def test_update_media_type_admin_success(self, api_client, admin_user, media_type):
        """Admin should be able to update media type"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('media-types-detail', kwargs={'pk': media_type.id})
        data = {
            'type_name': 'Updated Image',
            'description': 'Updated description',
            'is_active': False
        }
        
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['type_name'] == 'Updated Image'
        assert response.data['description'] == 'Updated description'
        assert response.data['is_active'] is False
    
    def test_update_media_type_partial(self, api_client, admin_user, media_type):
        """Should allow partial updates"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('media-types-detail', kwargs={'pk': media_type.id})
        data = {'description': 'Only description updated'}
        
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['description'] == 'Only description updated'
        assert response.data['type_name'] == media_type.type_name  # unchanged
    
    def test_update_media_type_normal_user_fails(self, api_client, normal_user, media_type):
        """Normal user should not update"""
        api_client.force_authenticate(user=normal_user)
        url = reverse('media-types-detail', kwargs={'pk': media_type.id})
        data = {'type_name': 'Hacked'}
        
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_update_media_type_not_found(self, api_client, admin_user):
        """Should return 404 for non-existent ID"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('media-types-detail', kwargs={'pk': 99999})
        data = {'type_name': 'Test'}
        
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_media_type_duplicate_name_fails(self, api_client, admin_user, media_types):
        """Should reject duplicate type_name on update"""
        api_client.force_authenticate(user=admin_user)
        first_type = media_types[0]
        second_type = media_types[1]
        
        url = reverse('media-types-detail', kwargs={'pk': second_type.id})
        data = {'type_name': first_type.type_name}  # Try to use existing name
        
        response = api_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================
# DELETE TESTS - DELETE /api/media-types/:id/
# ============================================

@pytest.mark.django_db
class TestMediaTypeDelete:
    """Tests for deleting media types"""
    
    def test_delete_media_type_admin_success(self, api_client, admin_user, media_type):
        """Admin should be able to delete media type"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('media-types-detail', kwargs={'pk': media_type.id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not MediaType.objects.filter(id=media_type.id).exists()
    
    def test_delete_media_type_normal_user_fails(self, api_client, normal_user, media_type):
        """Normal user should not delete"""
        api_client.force_authenticate(user=normal_user)
        url = reverse('media-types-detail', kwargs={'pk': media_type.id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert MediaType.objects.filter(id=media_type.id).exists()
    
    def test_delete_media_type_unauthenticated_fails(self, api_client, media_type):
        """Unauthenticated user should not delete"""
        url = reverse('media-types-detail', kwargs={'pk': media_type.id})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_delete_media_type_not_found(self, api_client, admin_user):
        """Should return 404 for non-existent ID"""
        api_client.force_authenticate(user=admin_user)
        url = reverse('media-types-detail', kwargs={'pk': 99999})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
