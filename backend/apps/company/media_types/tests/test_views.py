"""
Tests for Media Types Views (ViewSet)
Module 22: Advanced Features - Media Types API

Test Coverage:
- GET /api/media-types/ (list)
- POST /api/media-types/ (create)
- PUT /api/media-types/:id/ (update)
- DELETE /api/media-types/:id/ (destroy)
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from apps.company.media_types.models import MediaType

User = get_user_model()


class MediaTypeViewSetTests(APITestCase):
    def setUp(self):
        # Create users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )
        self.normal_user = User.objects.create_user(
            email='user@test.com',
            password='userpass123',
            first_name='Normal',
            last_name='User'
        )
        
        # Create media types
        self.image = MediaType.objects.create(type_name='Image', description='Image files', is_active=True)
        self.video = MediaType.objects.create(type_name='Video', description='Video files', is_active=True)
        self.doc = MediaType.objects.create(type_name='Document', description='Document files', is_active=False)
        
        self.list_url = reverse('media-types-list')
        self.detail_url = lambda pk: reverse('media-types-detail', kwargs={'pk': pk})

    # ============================================
    # LIST TESTS - GET /api/media-types/
    # ============================================
    
    def test_list_media_types_public_access(self):
        """List endpoint should be public (no auth required)"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_list_media_types_filter_active(self):
        """Should filter by is_active"""
        response = self.client.get(self.list_url, {'is_active': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        for item in response.data:
            self.assertTrue(item['is_active'])
    
    def test_list_media_types_filter_inactive(self):
        """Should filter inactive media types"""
        response = self.client.get(self.list_url, {'is_active': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertFalse(response.data[0]['is_active'])
    
    def test_list_media_types_returns_expected_fields(self):
        """Response should contain all expected fields"""
        response = self.client.get(self.list_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.data[0]
        self.assertIn('id', item)
        self.assertIn('type_name', item)
        self.assertIn('description', item)
        self.assertIn('is_active', item)
        self.assertIn('created_at', item)

    # ============================================
    # CREATE TESTS - POST /api/media-types/
    # ============================================
    
    def test_create_media_type_admin_success(self):
        """Admin should be able to create media type"""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'type_name': 'Audio',
            'description': 'Audio files (mp3, wav)',
            'is_active': True
        }
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['type_name'], 'Audio')
        self.assertEqual(response.data['description'], 'Audio files (mp3, wav)')
        self.assertTrue(response.data['is_active'])
        self.assertTrue(MediaType.objects.filter(type_name='Audio').exists())
    
    def test_create_media_type_unauthenticated_fails(self):
        """Unauthenticated user should not create"""
        data = {'type_name': 'Audio', 'description': 'Audio files'}
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_media_type_normal_user_fails(self):
        """Normal user (non-admin) should not create"""
        self.client.force_authenticate(user=self.normal_user)
        data = {'type_name': 'Audio', 'description': 'Audio files'}
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_media_type_duplicate_name_fails(self):
        """Should reject duplicate type_name"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'type_name': 'Image', 'description': 'Another image type'}
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', str(response.data))
    
    def test_create_media_type_missing_name_fails(self):
        """Should require type_name field"""
        self.client.force_authenticate(user=self.admin_user)
        data = {'description': 'Some description'}
        
        response = self.client.post(self.list_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================
    # UPDATE TESTS - PUT /api/media-types/:id/
    # ============================================
    
    def test_update_media_type_admin_success(self):
        """Admin should be able to update media type"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.detail_url(self.image.id)
        data = {
            'type_name': 'Updated Image',
            'description': 'Updated description',
            'is_active': False
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['type_name'], 'Updated Image')
        self.assertEqual(response.data['description'], 'Updated description')
        self.assertFalse(response.data['is_active'])
    
    def test_update_media_type_partial(self):
        """Should allow partial updates"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.detail_url(self.image.id)
        data = {'description': 'Only description updated'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Only description updated')
        self.assertEqual(response.data['type_name'], self.image.type_name)
    
    def test_update_media_type_normal_user_fails(self):
        """Normal user should not update"""
        self.client.force_authenticate(user=self.normal_user)
        url = self.detail_url(self.image.id)
        data = {'type_name': 'Hacked'}
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_update_media_type_not_found(self):
        """Should return 404 for non-existent ID"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.detail_url(99999)
        data = {'type_name': 'Test'}
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_media_type_duplicate_name_fails(self):
        """Should reject duplicate type_name on update"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.detail_url(self.video.id)
        data = {'type_name': self.image.type_name}  # Try to use 'Image' which belongs to another object
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================
    # DELETE TESTS - DELETE /api/media-types/:id/
    # ============================================
    
    def test_delete_media_type_admin_success(self):
        """Admin should be able to delete media type"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.detail_url(self.image.id)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MediaType.objects.filter(id=self.image.id).exists())
    
    def test_delete_media_type_normal_user_fails(self):
        """Normal user should not delete"""
        self.client.force_authenticate(user=self.normal_user)
        url = self.detail_url(self.image.id)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MediaType.objects.filter(id=self.image.id).exists())
    
    def test_delete_media_type_unauthenticated_fails(self):
        """Unauthenticated user should not delete"""
        url = self.detail_url(self.image.id)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_delete_media_type_not_found(self):
        """Should return 404 for non-existent ID"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.detail_url(99999)
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
