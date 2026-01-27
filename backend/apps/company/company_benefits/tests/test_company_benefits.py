from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.company.companies.models import Company
from apps.company.company_benefits.models import CompanyBenefit
from apps.company.benefit_categories.models import BenefitCategory

CustomUser = get_user_model()

# ============================================================================
# URL PATHS (Nested under companies)
# ============================================================================
def benefits_list(company_id): 
    return f'/api/companies/{company_id}/benefits/'

def benefit_detail(company_id, benefit_id): 
    return f'/api/companies/{company_id}/benefits/{benefit_id}/'

def benefits_reorder(company_id): 
    return f'/api/companies/{company_id}/benefits/reorder/'


class TestCompanyBenefitsAPIs(APITestCase):
    
    def setUp(self):
        # Create users
        self.company_owner = CustomUser.objects.create_user(
            email="owner@example.com",
            password="password123",
            full_name="Company Owner",
            role="company"
        )
        self.other_user = CustomUser.objects.create_user(
            email="other@example.com",
            password="password123",
            full_name="Other User"
        )
        
        # Create company
        self.company = Company.objects.create(
            user=self.company_owner,
            company_name="Test Company",
            slug="test-company"
        )
        
        # Create category
        self.category = BenefitCategory.objects.create(
            name="Bảo hiểm",
            slug="bao-hiem",
            icon_url="https://example.com/icon.png",
            is_active=True,
            display_order=1
        )
        
        # Create benefit
        self.benefit = CompanyBenefit.objects.create(
            company=self.company,
            category=self.category,
            benefit_name="Bảo hiểm sức khỏe",
            description="Bảo hiểm toàn diện",
            display_order=1
        )

    # --- LIST BENEFITS ---
    
    def test_list_benefits_success(self):
        """GET /api/companies/:id/benefits/ - Thành công"""
        response = self.client.get(benefits_list(self.company.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['benefit_name'], 'Bảo hiểm sức khỏe')
    
    def test_list_benefits_invalid_company(self):
        """GET /api/companies/9999/benefits/ - Company không tồn tại"""
        response = self.client.get(benefits_list(9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # --- CREATE BENEFIT ---
    
    def test_create_benefit_success(self):
        """POST /api/companies/:id/benefits/ - Thành công"""
        self.client.force_authenticate(user=self.company_owner)
        data = {
            'category_id': self.category.id,
            'benefit_name': 'Thưởng Tết',
            'description': 'Thưởng 13 tháng lương'
        }
        response = self.client.post(benefits_list(self.company.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['benefit_name'], 'Thưởng Tết')
        self.assertEqual(CompanyBenefit.objects.count(), 2) # 1 from setUp + 1 new
    
    def test_create_benefit_not_owner(self):
        """POST /api/companies/:id/benefits/ - Không phải owner -> 403"""
        self.client.force_authenticate(user=self.other_user)
        data = {
            'category_id': self.category.id,
            'benefit_name': 'Test'
        }
        # Thử tạo cho company không thuộc sở hữu
        response = self.client.post(benefits_list(self.company.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_benefit_unauthenticated(self):
        """POST /api/companies/:id/benefits/ - Chưa login -> 401"""
        data = {
            'category_id': self.category.id,
            'benefit_name': 'Test'
        }
        response = self.client.post(benefits_list(self.company.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_benefit_invalid_category(self):
        """POST /api/companies/:id/benefits/ - Category không hợp lệ"""
        self.client.force_authenticate(user=self.company_owner)
        data = {
            'category_id': 9999,
            'benefit_name': 'Test'
        }
        response = self.client.post(benefits_list(self.company.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # --- RETRIEVE BENEFIT ---
    
    def test_retrieve_benefit_success(self):
        """GET /api/companies/:id/benefits/:pk/ - Thành công"""
        response = self.client.get(benefit_detail(self.company.id, self.benefit.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['benefit_name'], 'Bảo hiểm sức khỏe')
    
    def test_retrieve_benefit_not_found(self):
        """GET /api/companies/:id/benefits/9999/ - Không tồn tại"""
        response = self.client.get(benefit_detail(self.company.id, 9999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # --- UPDATE BENEFIT ---
    
    def test_update_benefit_success(self):
        """PUT /api/companies/:id/benefits/:pk/ - Thành công"""
        self.client.force_authenticate(user=self.company_owner)
        data = {
            'benefit_name': 'Updated Benefit',
            'description': 'Updated description'
        }
        response = self.client.put(benefit_detail(self.company.id, self.benefit.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['benefit_name'], 'Updated Benefit')
        
        self.benefit.refresh_from_db()
        self.assertEqual(self.benefit.benefit_name, 'Updated Benefit')
    
    def test_update_benefit_not_owner(self):
        """PUT /api/companies/:id/benefits/:pk/ - Không phải owner -> 403"""
        self.client.force_authenticate(user=self.other_user)
        data = {'benefit_name': 'Hacked'}
        response = self.client.put(benefit_detail(self.company.id, self.benefit.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # --- DELETE BENEFIT ---
    
    def test_delete_benefit_success(self):
        """DELETE /api/companies/:id/benefits/:pk/ - Thành công"""
        self.client.force_authenticate(user=self.company_owner)
        response = self.client.delete(benefit_detail(self.company.id, self.benefit.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CompanyBenefit.objects.count(), 0)
    
    def test_delete_benefit_not_owner(self):
        """DELETE /api/companies/:id/benefits/:pk/ - Không phải owner -> 403"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(benefit_detail(self.company.id, self.benefit.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(CompanyBenefit.objects.count(), 1)
    
    # --- REORDER BENEFITS ---
    
    def test_reorder_benefits_success(self):
        """PATCH /api/companies/:id/benefits/reorder/ - Thành công"""
        self.client.force_authenticate(user=self.company_owner)
        
        # Tạo thêm benefits (b1 already exists as self.benefit with display_order=1)
        # Create b2, b3
        b2 = CompanyBenefit.objects.create(company=self.company, category=self.category, benefit_name="B2", display_order=2)
        b3 = CompanyBenefit.objects.create(company=self.company, category=self.category, benefit_name="B3", display_order=3)
        
        # Current order: benefit(1), b2(2), b3(3)
        # Reorder: b3, benefit, b2
        
        data = {
            'benefit_ids': [b3.id, self.benefit.id, b2.id]
        }
        response = self.client.patch(benefits_reorder(self.company.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify order
        self.benefit.refresh_from_db()
        b2.refresh_from_db()
        b3.refresh_from_db()
        self.assertEqual(b3.display_order, 0)
        self.assertEqual(self.benefit.display_order, 1)
        self.assertEqual(b2.display_order, 2)
    
    def test_reorder_benefits_not_owner(self):
        """PATCH /api/companies/:id/benefits/reorder/ - Không phải owner -> 403"""
        self.client.force_authenticate(user=self.other_user)
        data = {
            'benefit_ids': [self.benefit.id]
        }
        response = self.client.patch(benefits_reorder(self.company.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_reorder_benefits_invalid_ids(self):
        """PATCH /api/companies/:id/benefits/reorder/ - IDs không hợp lệ"""
        self.client.force_authenticate(user=self.company_owner)
        data = {
            'benefit_ids': [self.benefit.id, 9999]  # 9999 không tồn tại
        }
        response = self.client.patch(benefits_reorder(self.company.id), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
