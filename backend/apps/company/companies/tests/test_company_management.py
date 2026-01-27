from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
import unittest

CustomUser = get_user_model()


class TestCompanyManagement(APITestCase):
    """Test suite cho Company Management APIs"""
    
    def test_create_company_success(self):
        """Kiểm tra tạo công ty thành công qua API"""
        user = CustomUser.objects.create_user(
            email="company@example.com",
            password="password123",
            role='company'
        )
        self.client.force_authenticate(user=user)
        
        url = reverse('company-list')
        data = {
            "company_name": "Công ty ABC",
            "website": "https://abc.com",
            "description": "Mô tả công ty ABC"
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['company_name'], "Công ty ABC")
        self.assertIn('cong-ty-abc', response.data['slug'])
        self.assertEqual(response.data['user'], user.id)
    
    def test_create_company_duplicate_user(self):
        """Lỗi khi user đã có company (sử dụng API thay vì trực tiếp tạo)"""
        user = CustomUser.objects.create_user(
            email="company2@example.com",
            password="password123",
            role='company'
        )
        self.client.force_authenticate(user=user)
        
        url = reverse('company-list')
        
        # Tạo company đầu tiên qua API
        response1 = self.client.post(url, {"company_name": "Công ty 1"}, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Tạo công ty thứ 2 sẽ lỗi
        response2 = self.client.post(url, {"company_name": "Công ty 2"}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("đã có hồ sơ công ty", str(response2.data['detail']))
    
    def test_list_companies_public(self):
        """Danh sách công ty công khai (không cần auth)"""
        # Tạo company trước
        user = CustomUser.objects.create_user(
            email="company3@example.com",
            password="password123",
            role='company'
        )
        self.client.force_authenticate(user=user)
        self.client.post(reverse('company-list'), {"company_name": "Test Company"}, format='json')
        self.client.logout()
        
        # Truy cập list không cần auth
        url = reverse('company-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_company_by_slug(self):
        """Lấy chi tiết công ty theo slug"""
        user = CustomUser.objects.create_user(
            email="company4@example.com",
            password="password123",
            role='company'
        )
        self.client.force_authenticate(user=user)
        create_response = self.client.post(reverse('company-list'), {"company_name": "Slug Company"}, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        
        slug = create_response.data['slug']
        self.client.logout()
        
        url = reverse('company-retrieve-by-slug', kwargs={'slug': slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], slug)
    
    def test_update_company_owner_only(self):
        """Chỉ chủ sở hữu mới được cập nhật"""
        owner = CustomUser.objects.create_user(email="owner@example.com", password="password", role='company')
        other = CustomUser.objects.create_user(email="other@example.com", password="password", role='company')
        
        # Tạo company bằng owner
        self.client.force_authenticate(user=owner)
        create_response = self.client.post(reverse('company-list'), {"company_name": "Owner Company"}, format='json')
        company_id = create_response.data['id']
        
        # Thử update bằng other user
        self.client.force_authenticate(user=other)
        url = reverse('company-detail', kwargs={'pk': company_id})
        response = self.client.put(url, {"company_name": "Hacked"}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_company_owner_only(self):
        """Chỉ chủ sở hữu mới được xóa"""
        owner = CustomUser.objects.create_user(email="deleteowner@example.com", password="password", role='company')
        
        self.client.force_authenticate(user=owner)
        create_response = self.client.post(reverse('company-list'), {"company_name": "Delete Company"}, format='json')
        company_id = create_response.data['id']
        
        url = reverse('company-detail', kwargs={'pk': company_id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    # =========================================================================
    # Tests cho Company Stats API
    # =========================================================================
    @unittest.skip("Company stats API needs Job/Review/Follower models not available in test settings")
    def test_company_stats(self):
        """GET /api/companies/:id/stats - Lấy thống kê công ty"""
        user = CustomUser.objects.create_user(email="stats@example.com", password="password", role='company')
        self.client.force_authenticate(user=user)
        
        # Tạo company
        create_response = self.client.post(reverse('company-list'), {"company_name": "Stats Company"}, format='json')
        company_id = create_response.data['id']
        
        # Lấy stats
        url = f"/api/companies/{company_id}/stats/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('job_count', response.data)
        self.assertIn('follower_count', response.data)
        self.assertIn('review_count', response.data)
    
    # =========================================================================
    # Tests cho Request Verification API
    # =========================================================================
    def test_request_verification_success(self):
        """POST /api/companies/:id/verify - Yêu cầu xác thực thành công"""
        user = CustomUser.objects.create_user(email="verify@example.com", password="password", role='company')
        self.client.force_authenticate(user=user)
        
        # Tạo company
        create_response = self.client.post(reverse('company-list'), {"company_name": "Verify Company"}, format='json')
        company_id = create_response.data['id']
        
        # Yêu cầu xác thực
        url = f"/api/companies/{company_id}/verify/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("successfully", response.data['detail'])
    
    def test_request_verification_not_owner(self):
        """POST /api/companies/:id/verify - Không phải chủ sở hữu"""
        owner = CustomUser.objects.create_user(email="verifyowner@example.com", password="password", role='company')
        other = CustomUser.objects.create_user(email="verifyother@example.com", password="password", role='company')
        
        self.client.force_authenticate(user=owner)
        create_response = self.client.post(reverse('company-list'), {"company_name": "Other Verify Company"}, format='json')
        company_id = create_response.data['id']
        
        # Other user cố yêu cầu xác thực
        self.client.force_authenticate(user=other)
        url = f"/api/companies/{company_id}/verify/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # =========================================================================
    # Tests cho Admin Verification API
    # =========================================================================
    def test_admin_verification_success(self):
        """PATCH /api/companies/:id/verification - Admin duyệt thành công"""
        owner = CustomUser.objects.create_user(email="adminverifyowner@example.com", password="password", role='company')
        admin = CustomUser.objects.create_user(email="admin@example.com", password="password", is_staff=True)
        
        # Tạo company
        self.client.force_authenticate(user=owner)
        create_response = self.client.post(reverse('company-list'), {"company_name": "Admin Verify Company"}, format='json')
        company_id = create_response.data['id']
        
        # Admin duyệt
        self.client.force_authenticate(user=admin)
        url = f"/api/companies/{company_id}/verification/"
        response = self.client.patch(url, {"status": "verified"}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_admin_verification_not_admin(self):
        """PATCH /api/companies/:id/verification - User thường không được duyệt"""
        owner = CustomUser.objects.create_user(email="notadminowner@example.com", password="password", role='company')
        
        self.client.force_authenticate(user=owner)
        create_response = self.client.post(reverse('company-list'), {"company_name": "Not Admin Company"}, format='json')
        company_id = create_response.data['id']
        
        url = f"/api/companies/{company_id}/verification/"
        response = self.client.patch(url, {"status": "verified"}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # =========================================================================
    # Tests cho Search Companies API
    # =========================================================================
    def test_search_companies(self):
        """GET /api/companies/search - Tìm kiếm công ty"""
        user = CustomUser.objects.create_user(email="searchtest@example.com", password="password", role='company')
        self.client.force_authenticate(user=user)
        self.client.post(reverse('company-list'), {"company_name": "Tech ABC Company"}, format='json')
        self.client.logout()
        
        # Tìm kiếm
        url = "/api/companies/search/?q=Tech"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    # =========================================================================
    # Tests cho Featured Companies API
    # =========================================================================
    def test_featured_companies(self):
        """GET /api/companies/featured - Công ty nổi bật"""
        url = "/api/companies/featured/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    # =========================================================================
    # Tests cho Company Suggestions API
    # =========================================================================
    def test_company_suggestions_anonymous(self):
        """GET /api/companies/suggestions - Gợi ý cho anonymous user"""
        url = "/api/companies/suggestions/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_company_suggestions_authenticated(self):
        """GET /api/companies/suggestions - Gợi ý cho authenticated user"""
        user = CustomUser.objects.create_user(email="suggestions@example.com", password="password")
        self.client.force_authenticate(user=user)
        
        url = "/api/companies/suggestions/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    # =========================================================================
    # Tests cho Claim Company API
    # =========================================================================
    def test_claim_company_already_claimed(self):
        """POST /api/companies/:id/claim - Công ty đã có chủ sở hữu"""
        owner = CustomUser.objects.create_user(email="claimowner@example.com", password="password", role='company')
        other = CustomUser.objects.create_user(email="claimother@example.com", password="password", role='company')
        
        # Tạo company có owner
        self.client.force_authenticate(user=owner)
        create_response = self.client.post(reverse('company-list'), {"company_name": "Claimed Company"}, format='json')
        company_id = create_response.data['id']
        
        # Other user cố claim
        self.client.force_authenticate(user=other)
        url = f"/api/companies/{company_id}/claim/"
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already claimed", str(response.data['detail']))
