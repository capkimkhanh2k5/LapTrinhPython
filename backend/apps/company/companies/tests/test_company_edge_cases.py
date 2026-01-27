"""
Test cases bổ sung cho Company Management APIs
Bổ sung các edge cases và APIs còn thiếu trong Module 2
"""
import io
from PIL import Image
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.users.models import CustomUser
from apps.company.companies.models import Company


# ============================================================================
# URL HELPERS
# ============================================================================
def company_detail(pk):
    return f'/api/companies/{pk}/'

def company_logo(pk):
    return f'/api/companies/{pk}/logo/'

def company_banner(pk):
    return f'/api/companies/{pk}/banner/'

def company_jobs(pk):
    return f'/api/companies/{pk}/jobs/'

def company_reviews(pk):
    return f'/api/companies/{pk}/reviews/'

def company_followers(pk):
    return f'/api/companies/{pk}/followers/'

def company_claim(pk):
    return f'/api/companies/{pk}/claim/'

def company_stats(pk):
    return f'/api/companies/{pk}/stats/'


# ============================================================================
# BASE TEST CLASS
# ============================================================================
class BaseCompanyTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company_user = CustomUser.objects.create_user(
            email="companyowner@example.com",
            password="password123",
            role='company'
        )
        self.other_user = CustomUser.objects.create_user(
            email="other@example.com",
            password="password123"
        )
        self.company = Company.objects.create(
            user=self.company_user,
            company_name="Test Company",
            slug="test-company"
        )
        self.orphan_company = Company.objects.create(
            user=None,
            company_name="Orphan Company",
            slug="orphan-company"
        )


# ============================================================================
# TESTS: GET /api/companies/:id - Chi tiết công ty
# ============================================================================
class TestRetrieveCompanyById(BaseCompanyTestCase):
    """Tests cho GET /api/companies/:id"""
    
    def test_retrieve_company_success(self):
        """Lấy chi tiết công ty theo ID thành công"""
        response = self.client.get(company_detail(self.company.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.company.id)
        self.assertEqual(response.data['company_name'], 'Test Company')
        self.assertEqual(response.data['slug'], 'test-company')
    
    def test_retrieve_company_not_found(self):
        """Company không tồn tại → 404"""
        response = self.client.get(company_detail(99999))
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retrieve_company_public(self):
        """Truy cập chi tiết công ty không cần authentication"""
        response = self.client.get(company_detail(self.company.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================================================
# TESTS: POST /api/companies/:id/logo - Upload logo
# ============================================================================
class TestUploadLogo(BaseCompanyTestCase):
    """Tests cho POST /api/companies/:id/logo"""
    
    @patch('apps.company.companies.services.companies.upload_company_logo')
    def test_upload_logo_success(self, mock_upload):
        """Upload logo thành công"""
        mock_upload.return_value = "http://cloudinary.com/logo.jpg"
        self.client.force_authenticate(user=self.company_user)
        
        # Tạo file ảnh giả
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'jpeg')
        file.seek(0)
        logo = SimpleUploadedFile("logo.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(company_logo(self.company.id), {'logo': logo}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('logo_url', response.data)
    
    def test_upload_logo_not_owner(self):
        """Không phải owner → 403"""
        self.client.force_authenticate(user=self.other_user)
        
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'jpeg')
        file.seek(0)
        logo = SimpleUploadedFile("logo.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(company_logo(self.company.id), {'logo': logo}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_upload_logo_no_file(self):
        """Không có file → 400"""
        self.client.force_authenticate(user=self.company_user)
        
        response = self.client.post(company_logo(self.company.id), {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('File not provided', response.data['detail'])
    
    def test_upload_logo_unauthenticated(self):
        """Chưa đăng nhập → 401"""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'jpeg')
        file.seek(0)
        logo = SimpleUploadedFile("logo.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(company_logo(self.company.id), {'logo': logo}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_upload_logo_company_not_found(self):
        """Company không tồn tại → 404"""
        self.client.force_authenticate(user=self.company_user)
        
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), 'red')
        image.save(file, 'jpeg')
        file.seek(0)
        logo = SimpleUploadedFile("logo.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(company_logo(99999), {'logo': logo}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================================
# TESTS: POST /api/companies/:id/banner - Upload banner
# ============================================================================
class TestUploadBanner(BaseCompanyTestCase):
    """Tests cho POST /api/companies/:id/banner"""
    
    @patch('apps.company.companies.services.companies.upload_company_banner')
    def test_upload_banner_success(self, mock_upload):
        """Upload banner thành công"""
        mock_upload.return_value = "http://cloudinary.com/banner.jpg"
        self.client.force_authenticate(user=self.company_user)
        
        file = io.BytesIO()
        image = Image.new('RGB', (1200, 400), 'blue')
        image.save(file, 'jpeg')
        file.seek(0)
        banner = SimpleUploadedFile("banner.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(company_banner(self.company.id), {'banner': banner}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('banner_url', response.data)

    def test_upload_banner_not_owner(self):
        """Không phải owner → 403"""
        self.client.force_authenticate(user=self.other_user)
        
        file = io.BytesIO()
        image = Image.new('RGB', (1200, 400), 'blue')
        image.save(file, 'jpeg')
        file.seek(0)
        banner = SimpleUploadedFile("banner.jpg", file.read(), content_type="image/jpeg")
        
        response = self.client.post(company_banner(self.company.id), {'banner': banner}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ============================================================================
# TESTS: GET /api/companies/:id/jobs - Danh sách việc làm
# ============================================================================
class TestCompanyJobs(BaseCompanyTestCase):
    """Tests cho GET /api/companies/:id/jobs"""
    
    def test_list_company_jobs_success(self):
        """Danh sách jobs của công ty thành công"""
        response = self.client.get(company_jobs(self.company.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_list_company_jobs_not_found(self):
        """Company không tồn tại → 404"""
        response = self.client.get(company_jobs(99999))
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================================
# TESTS: POST /api/companies/:id/claim - Nhận quyền quản lý
# ============================================================================
class TestClaimCompany(BaseCompanyTestCase):
    """Tests cho POST /api/companies/:id/claim"""
    
    def test_claim_company_success(self):
        """Claim company chưa có owner thành công"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.post(company_claim(self.orphan_company.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('claimed successfully', response.data['detail'])
        
        # Verify DB
        self.orphan_company.refresh_from_db()
        self.assertEqual(self.orphan_company.user, self.other_user)
    
    def test_claim_company_already_claimed(self):
        """Company đã có owner → 400"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.post(company_claim(self.company.id))
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already claimed', response.data['detail'])


# ============================================================================
# TESTS: GET /api/companies/suggestions - Gợi ý công ty (Personalization)
# ============================================================================
class TestCompanySuggestions(TestCase):
    """Tests cho GET /api/companies/suggestions"""
    
    def setUp(self):
        self.client = APIClient()
        from apps.company.companies.models import Company
        from apps.core.users.models import CustomUser
        from apps.candidate.recruiters.models import Recruiter
        
        # Setup company owner
        self.company_user = CustomUser.objects.create_user(email="company@example.com", password="password", role='company')
        
        # Setup base company
        self.company = Company.objects.create(
            user=self.company_user,
            company_name="Test Company",
            slug="test-company",
            verification_status='verified',
            follower_count=100
        )
        self.user = CustomUser.objects.create_user(email="candidate@example.com", password="password")
        self.recruiter = Recruiter.objects.create(user=self.user)
        
    def _setup_skill_matching(self):
        """Helper to setup skill matching data"""
        from apps.recruitment.jobs.models import Job
        from apps.candidate.skills.models import Skill
        from apps.candidate.skill_categories.models import SkillCategory
        from apps.recruitment.job_skills.models import JobSkill
        from apps.candidate.recruiter_skills.models import RecruiterSkill
        
        # 0. Tạo Skill Category
        category = SkillCategory.objects.create(name="IT", slug="it")
        
        # 1. Tạo Skill "Python"
        python_skill = Skill.objects.create(
            name="Python", 
            slug="python",
            category=category
        )
        
        # 2. Gán skill cho Recruiter
        RecruiterSkill.objects.create(recruiter=self.recruiter, skill=python_skill)
        
        # 3. Tạo Job requires Python của Company
        job = Job.objects.create(
            company=self.company, 
            title="Python Dev", 
            slug="python-dev",
            status=Job.Status.PUBLISHED,
            created_by=self.company.user  # Required field
        )
        JobSkill.objects.create(job=job, skill=python_skill)
        
        return self.user, self.company
        
    def test_suggestions_anonymous(self):
        """Anonymous user -> Trả về top trending (verified)"""
        response = self.client.get('/api/companies/suggestions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain at least our verified company
        self.assertTrue(len(response.data) > 0)
        found_ids = [c['id'] for c in response.data]
        self.assertIn(self.company.id, found_ids)

    def test_suggestions_by_skills(self):
        """Logged in user -> Gợi ý theo skill match"""
        self._setup_skill_matching()
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/companies/suggestions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find the company because user has Python skill and company hires for Python
        found_ids = [c['id'] for c in response.data]
        self.assertIn(self.company.id, found_ids)

    def test_suggestions_fallback(self):
        """Logged in user NO matching -> Fallback to top trending"""
        # Create user with no skills
        no_skill_user = CustomUser.objects.create_user(email="no_skill@example.com", password="password")
        from apps.candidate.recruiters.models import Recruiter
        Recruiter.objects.create(user=no_skill_user)
        
        self.client.force_authenticate(user=no_skill_user)
        response = self.client.get('/api/companies/suggestions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should still return list (fallback)
        self.assertIsInstance(response.data, list)
        # And should include our popular company (fallback logic)
        found_ids = [c['id'] for c in response.data]
        self.assertIn(self.company.id, found_ids)


# ============================================================================
# TESTS: Job Status Filtering (Edge Cases)
# ============================================================================
class TestJobStatusFiltering(TestCase):
    """Tests filtering draft/closed jobs"""
    
    def setUp(self):
        self.client = APIClient()
        from apps.company.companies.models import Company
        from apps.core.users.models import CustomUser
        
        self.user = CustomUser.objects.create_user(email="owner@example.com", password="password")
        self.company = Company.objects.create(
            company_name="My Company",
            slug="my-company",
            user=self.user
        )
    
    def test_list_company_jobs_excludes_draft(self):
        """Public API không hiển thị job nháp"""
        from apps.recruitment.jobs.models import Job
        
        # Create Draft Job
        Job.objects.create(
            company=self.company, 
            title="Draft Job", 
            slug="draft-job",
            status=Job.Status.DRAFT,
            created_by=self.user  # Required field
        )
        # Create Published Job
        Job.objects.create(
            company=self.company, 
            title="Public Job", 
            slug="public-job",
            status=Job.Status.PUBLISHED,
            created_by=self.user  # Required field
        )
        
        response = self.client.get(company_jobs(self.company.id))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Public Job")
