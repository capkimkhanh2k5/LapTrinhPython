"""
User Management Edge Cases Tests - Django TestCase Version
"""
import io
from PIL import Image
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.users.models import CustomUser


# ============================================================================
# URL PATHS
# ============================================================================
USER_LIST = '/api/users/'
USER_STATS = '/api/users/stats/'
USER_EXPORT = '/api/users/export/'
USER_BULK_ACTION = '/api/users/bulk-action/'


def user_detail(user_id): 
    return f'/api/users/{user_id}/'


def user_status(user_id): 
    return f'/api/users/{user_id}/status/'


def user_role(user_id): 
    return f'/api/users/{user_id}/role/'


def user_avatar(user_id): 
    return f'/api/users/{user_id}/avatar/'


def user_activity_logs(user_id): 
    return f'/api/users/{user_id}/activity-logs/'


# ============================================================================
# TEST: GET USER DETAIL API
# ============================================================================

class TestGetUserDetail(APITestCase):
    """Test cases for user detail API"""
    
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.normal_user = CustomUser.objects.create_user(
            email="normal@example.com",
            password="password123",
            full_name="Normal User",
            role="recruiter"
        )
        self.target_user = CustomUser.objects.create_user(
            email="target@example.com",
            password="password123",
            full_name="Target User",
            role="recruiter"
        )
    
    def test_get_user_detail_as_admin(self):
        """Admin views user detail → 200"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(user_detail(self.target_user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.target_user.email)
        self.assertEqual(response.data['full_name'], self.target_user.full_name)
    
    def test_get_user_detail_as_authenticated_user(self):
        """Normal user views other user's detail → 200"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(user_detail(self.target_user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_user_detail_self(self):
        """User views own detail → 200"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(user_detail(self.normal_user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.normal_user.email)
    
    def test_get_user_detail_not_found(self):
        """View non-existent user → 404"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(user_detail(99999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_user_detail_without_authentication(self):
        """View user detail without login → 401"""
        response = self.client.get(user_detail(self.target_user.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================================
# TEST: LIST USERS API - Edge Cases
# ============================================================================

class TestListUsersEdgeCases(APITestCase):
    """Test cases for list users edge cases"""
    
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.normal_user = CustomUser.objects.create_user(
            email="normal@example.com",
            password="password123",
            full_name="Normal User",
            role="recruiter"
        )
    
    def test_list_users_without_authentication(self):
        """List users without login → 401"""
        response = self.client.get(USER_LIST)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_users_as_normal_user(self):
        """Normal user lists users → 200 or 403 depending on permission"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(USER_LIST)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
    
    def test_list_users_with_pagination(self):
        """Test pagination when listing users"""
        # Create many users
        for i in range(15):
            CustomUser.objects.create_user(
                email=f"user{i}@example.com",
                password="password123",
                full_name=f"User {i}"
            )
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(USER_LIST, {'page': 1, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# TEST: UPDATE USER API - Edge Cases
# ============================================================================

class TestUpdateUserEdgeCases(APITestCase):
    """Test cases for update user edge cases"""
    
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.normal_user = CustomUser.objects.create_user(
            email="normal@example.com",
            password="password123",
            full_name="Normal User",
            role="recruiter"
        )
        self.target_user = CustomUser.objects.create_user(
            email="target@example.com",
            password="password123",
            full_name="Target User",
            role="recruiter"
        )
    
    def test_update_self_as_normal_user(self):
        """User updates own info → 200 or 403 depending on permission"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.put(user_detail(self.normal_user.id), {
            'full_name': 'Updated Name'
        })
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
    
    def test_update_other_user_as_normal_user(self):
        """Normal user updates other user → 403"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.put(user_detail(self.target_user.id), {
            'full_name': 'Hacked Name'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
    
    def test_update_user_not_found(self):
        """Update non-existent user → 404"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(user_detail(99999), {
            'full_name': 'New Name'
        })
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================================
# TEST: UPDATE STATUS API - Edge Cases
# ============================================================================

class TestUpdateStatusEdgeCases(APITestCase):
    """Test cases for update status edge cases"""
    
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.target_user = CustomUser.objects.create_user(
            email="target@example.com",
            password="password123",
            full_name="Target User",
            role="recruiter",
            status="active"
        )
    
    def test_update_status_to_inactive(self):
        """Admin changes user to inactive → 200"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(user_status(self.target_user.id), {'status': 'inactive'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.status, 'inactive')
    
    def test_update_status_to_active(self):
        """Admin changes user to active → 200"""
        self.target_user.status = 'banned'
        self.target_user.save()
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(user_status(self.target_user.id), {'status': 'active'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.status, 'active')
    
    def test_update_status_invalid_value(self):
        """Admin sends invalid status → 400"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(user_status(self.target_user.id), {'status': 'invalid_status'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TEST: UPDATE ROLE API - Edge Cases
# ============================================================================

class TestUpdateRoleEdgeCases(APITestCase):
    """Test cases for update role edge cases"""
    
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.target_user = CustomUser.objects.create_user(
            email="target@example.com",
            password="password123",
            full_name="Target User",
            role="recruiter"
        )
    
    def test_update_role_to_company(self):
        """Admin changes role to company → 200"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(user_role(self.target_user.id), {'role': 'company'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.role, 'company')
    
    def test_update_role_invalid_value(self):
        """Admin sends invalid role → 400"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(user_role(self.target_user.id), {'role': 'superadmin'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================================
# TEST: AVATAR API - Edge Cases
# ============================================================================

class TestAvatarEdgeCases(APITestCase):
    """Test cases for avatar upload/delete edge cases"""
    
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="avatar@example.com",
            password="password123",
            full_name="Avatar User",
            role="recruiter"
        )
        self.other_user = CustomUser.objects.create_user(
            email="other@example.com",
            password="password123",
            full_name="Other User",
            role="recruiter"
        )
    
    def test_upload_avatar_other_user(self):
        """Upload avatar for other user → 403"""
        self.client.force_authenticate(user=self.user)
        
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'white')
        image.save(file, 'jpeg')
        file.seek(0)
        avatar = SimpleUploadedFile("avatar.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(user_avatar(self.other_user.id), {'avatar': avatar}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
    
    def test_upload_non_image_file(self):
        """Upload non-image file → 400"""
        self.client.force_authenticate(user=self.user)
        text_file = SimpleUploadedFile("document.txt", b"This is a text file", content_type="text/plain")
        
        response = self.client.post(user_avatar(self.user.id), {'avatar': text_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_delete_avatar_other_user(self):
        """Delete other user's avatar → 403"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(user_avatar(self.other_user.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('detail', response.data)
    
    def test_upload_avatar_self(self):
        """User uploads own avatar → 200"""
        self.client.force_authenticate(user=self.user)
        
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'blue')
        image.save(file, 'jpeg')
        file.seek(0)
        avatar = SimpleUploadedFile("my_avatar.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(user_avatar(self.user.id), {'avatar': avatar}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_avatar_self(self):
        """User deletes own avatar → 200"""
        self.user.avatar_url = "http://example.com/avatar.jpg"
        self.user.save()
        
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(user_avatar(self.user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# TEST: Permission Security
# ============================================================================

class TestPermissionSecurityFix(APITestCase):
    """Test cases verifying security fix: only self or admin can operate"""
    
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.target_user = CustomUser.objects.create_user(
            email="target@example.com",
            password="password123",
            full_name="Target User",
            role="recruiter"
        )
    
    def test_admin_can_update_other_user(self):
        """Admin can update other user → 200"""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.put(user_detail(self.target_user.id), {
            'full_name': 'Updated By Admin'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.full_name, 'Updated By Admin')
    
    def test_admin_can_upload_avatar_for_other_user(self):
        """Admin can upload avatar for other user → 200"""
        self.client.force_authenticate(user=self.admin)
        
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'green')
        image.save(file, 'jpeg')
        file.seek(0)
        avatar = SimpleUploadedFile("admin_avatar.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(user_avatar(self.target_user.id), {'avatar': avatar}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_can_delete_avatar_of_other_user(self):
        """Admin can delete other user's avatar → 200"""
        self.target_user.avatar_url = "http://example.com/old_avatar.jpg"
        self.target_user.save()
        
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.delete(user_avatar(self.target_user.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertIsNone(self.target_user.avatar_url)


# ============================================================================
# TEST: STATS API - Edge Cases
# ============================================================================

class TestStatsEdgeCases(APITestCase):
    """Test cases for stats API edge cases"""
    
    def setUp(self):
        self.normal_user = CustomUser.objects.create_user(
            email="normal@example.com",
            password="password123",
            full_name="Normal User",
            role="recruiter"
        )
    
    def test_stats_as_normal_user(self):
        """Normal user views stats → 403"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(USER_STATS)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_stats_without_authentication(self):
        """View stats without login → 401"""
        response = self.client.get(USER_STATS)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================================
# TEST: EXPORT API - Edge Cases
# ============================================================================

class TestExportEdgeCases(APITestCase):
    """Test cases for export API edge cases"""
    
    def setUp(self):
        self.normal_user = CustomUser.objects.create_user(
            email="normal@example.com",
            password="password123",
            full_name="Normal User",
            role="recruiter"
        )
    
    def test_export_as_normal_user(self):
        """Normal user exports users → 403"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(USER_EXPORT)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_export_without_authentication(self):
        """Export users without login → 401"""
        response = self.client.get(USER_EXPORT)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================================================
# TEST: BULK ACTION API - Edge Cases
# ============================================================================

class TestBulkActionEdgeCases(APITestCase):
    """Test cases for bulk action API edge cases"""
    
    def setUp(self):
        self.admin = CustomUser.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123"
        )
        self.normal_user = CustomUser.objects.create_user(
            email="normal@example.com",
            password="password123",
            full_name="Normal User",
            role="recruiter"
        )
    
    def test_bulk_action_as_normal_user(self):
        """Normal user performs bulk action → 403"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post(USER_BULK_ACTION, {
            'ids': [1, 2],
            'action': 'update_status',
            'value': 'banned'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_bulk_action_missing_ids(self):
        """Bulk action without ids → 400"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(USER_BULK_ACTION, {
            'action': 'update_status',
            'value': 'banned'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_bulk_action_missing_action(self):
        """Bulk action without action → 400"""
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(USER_BULK_ACTION, {
            'ids': [1, 2],
            'value': 'banned'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_bulk_action_invalid_action(self):
        """Bulk action with invalid action → 400"""
        u1 = CustomUser.objects.create_user(email="u1@example.com", password="pass")
        
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(USER_BULK_ACTION, {
            'ids': [u1.id],
            'action': 'invalid_action',
            'value': 'some_value'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_bulk_action_without_authentication(self):
        """Bulk action without login → 401"""
        response = self.client.post(USER_BULK_ACTION, {
            'ids': [1, 2],
            'action': 'update_status',
            'value': 'banned'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
