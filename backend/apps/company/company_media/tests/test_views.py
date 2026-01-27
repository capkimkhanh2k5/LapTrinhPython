"""
Tests cho Company Media API
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.users.models import CustomUser
from apps.company.companies.models import Company
from apps.company.media_types.models import MediaType
from apps.company.company_media.models import CompanyMedia


class CompanyMediaViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(email="test@example.com", password="password")
        self.client.force_authenticate(user=self.user)
        
        self.company = Company.objects.create(user=self.user, company_name="Test Company")
        self.media_type = MediaType.objects.create(type_name="Office Photo")

    def test_list_media(self):
        CompanyMedia.objects.create(company=self.company, media_type=self.media_type, media_url="u1")
        
        response = self.client.get(f'/api/companies/{self.company.id}/media')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    @patch('apps.company.company_media.services.company_media.save_company_file')
    def test_create_media(self, mock_save):
        mock_save.return_value = "http://url"
        file = SimpleUploadedFile("test.jpg", b"content", content_type="image/jpeg")
        
        data = {
            'media_file': file,
            'media_type_id': self.media_type.id,
            'title': 'Test'
        }
        
        response = self.client.post(f'/api/companies/{self.company.id}/media', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['media_url'], "http://url")

    def test_update_media(self):
        media = CompanyMedia.objects.create(company=self.company, media_type=self.media_type, media_url="u1")
        
        data = {'title': 'Updated Title'}
        response = self.client.put(f'/api/companies/{self.company.id}/media/{media.id}', data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    @patch('apps.company.company_media.services.company_media.delete_company_file')
    def test_delete_media(self, mock_delete):
        media = CompanyMedia.objects.create(company=self.company, media_type=self.media_type, media_url="u1")
        
        response = self.client.delete(f'/api/companies/{self.company.id}/media/{media.id}')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(CompanyMedia.objects.filter(id=media.id).exists())

    def test_reorder_media(self):
        m1 = CompanyMedia.objects.create(company=self.company, media_type=self.media_type, media_url="u1", display_order=1)
        
        data = {
            'reorders': [{'id': m1.id, 'display_order': 5}]
        }
        
        response = self.client.patch(f'/api/companies/{self.company.id}/media/reorder', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        m1.refresh_from_db()
        self.assertEqual(m1.display_order, 5)
