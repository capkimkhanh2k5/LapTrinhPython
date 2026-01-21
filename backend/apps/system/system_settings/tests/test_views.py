from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import SystemSetting

User = get_user_model()

class SystemSettingViewSetTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='password123',
            first_name='Admin',
            last_name='User'
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            password='password123',
            first_name='Normal',
            last_name='User'
        )
        
        self.public_setting = SystemSetting.objects.create(
            setting_key='site_name',
            setting_value='My Job Board',
            setting_type=SystemSetting.SettingType.STRING,
            is_public=True
        )
        self.private_setting = SystemSetting.objects.create(
            setting_key='api_secret',
            setting_value='secret123',
            setting_type=SystemSetting.SettingType.STRING,
            is_public=False
        )
        
        self.list_url = reverse('system-settings-list')
        self.public_url = reverse('system-settings-public')

    def test_list_settings_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Admin sees all (implementation detail might vary, but assuming admin sees all)
        self.assertTrue(len(response.data) >= 2)

    def test_list_settings_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming user sees filtered list or we have a policy. 
        # Based on view implementation: `if not request.user.is_staff: filters['is_public'] = True`
        # So user should see public only
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['setting_key'], 'site_name')

    def test_update_setting_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('system-settings-detail', args=[self.public_setting.id])
        data = {'setting_value': 'New Site Name'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.public_setting.refresh_from_db()
        self.assertEqual(self.public_setting.setting_value, 'New Site Name')

    def test_update_setting_user_forbidden(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('system-settings-detail', args=[self.public_setting.id])
        data = {'setting_value': 'Hacked Name'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_public_endpoint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.public_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['setting_key'], 'site_name')
