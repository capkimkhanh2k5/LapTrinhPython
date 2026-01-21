import shutil
import tempfile
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, override_settings
from rest_framework import status
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import FileUpload

User = get_user_model()
MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class FileUploadViewSetTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='password123',
            first_name='Normal',
            last_name='User'
        )
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        self.url = reverse('file-uploads-list')

    def test_upload_file(self):
        self.client.force_authenticate(user=self.user)
        file = SimpleUploadedFile("test_file.txt", b"file_content", content_type="text/plain")
        data = {
            'file': file,
            'is_public': 'false'
        }
        response = self.client.post(self.url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FileUpload.objects.count(), 1)
        self.assertEqual(FileUpload.objects.first().user, self.user)

    def test_list_files_user_scope(self):
        # Create a file for user
        FileUpload.objects.create(
            user=self.user,
            file_name='user_file.txt',
            original_name='user_file.txt',
            file_path='path/to/user_file.txt'
        )
        # Create a file for admin
        FileUpload.objects.create(
            user=self.admin,
            file_name='admin_file.txt',
            original_name='admin_file.txt',
            file_path='path/to/admin_file.txt'
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['original_name'], 'user_file.txt')

    def test_list_files_admin_scope(self):
        # Create a file for user
        FileUpload.objects.create(
            user=self.user,
            file_name='user_file.txt',
            original_name='user_file.txt',
            file_path='path/to/user_file.txt'
        )
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)
        # Admin sees their own (if created) + user's. 
        # In this setup only user created one.
        # But wait, did I create one for admin in setup? No.
        # Let's create one properly for admin test logic
        FileUpload.objects.create(
            user=self.admin,
            file_name='admin_file.txt',
            original_name='admin_file.txt',
            file_path='path/to/admin_file.txt'
        )
        
        response = self.client.get(self.url)
        # Admin sees all (2 files)
        self.assertEqual(len(response.data), 2)
