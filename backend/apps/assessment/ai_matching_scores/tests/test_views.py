"""
API Integration Tests for AI Matching Scores

Tests for all 8 AI Matching API endpoints.
"""
from decimal import Decimal

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter
from apps.company.companies.models import Company
from apps.assessment.ai_matching_scores.models import AIMatchingScore


User = get_user_model()


class AIMatchingAPITestCase(APITestCase):
    """Base test case with common setup for AI Matching tests."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        # Create test user
        cls.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            is_active=True
        )
        
        # Create company
        cls.company = Company.objects.create(
            company_name='Test Company',
            slug='test-company',
            description='Test company description'
        )
        
        # Create job
        cls.job = Job.objects.create(
            company=cls.company,
            title='Python Developer',
            slug='python-developer',
            description='Python developer job',
            requirements='Python, Django',
            job_type='full-time',
            level='junior',
            experience_years_min=2,
            experience_years_max=5,
            status='published',
            created_by=cls.user
        )
        
        # Create recruiter
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            highest_education_level='dai_hoc',
            job_search_status='active'
        )
    
    def setUp(self):
        """Set up for each test."""
        self.client.force_authenticate(user=self.user)


class TestMatchingCandidatesView(AIMatchingAPITestCase):
    """Tests for GET /api/jobs/:id/matching-candidates"""
    
    def test_matching_candidates_success(self):
        """Get matching candidates for a job successfully."""
        # Create a matching score
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('85.50'),
            skill_match_score=Decimal('90.00'),
            experience_match_score=Decimal('80.00'),
            education_match_score=Decimal('85.00'),
            location_match_score=Decimal('75.00'),
            salary_match_score=Decimal('80.00'),
            is_valid=True
        )
        
        url = f'/api/jobs/{self.job.id}/matching-candidates'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['job_id'], self.job.id)
        self.assertEqual(len(response.data['candidates']), 1)
    
    def test_matching_candidates_job_not_found(self):
        """Return 404 for non-existent job."""
        url = '/api/jobs/99999/matching-candidates'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_matching_candidates_unauthorized(self):
        """Return 401 for unauthenticated request."""
        self.client.logout()
        url = f'/api/jobs/{self.job.id}/matching-candidates'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestMatchingJobsView(AIMatchingAPITestCase):
    """Tests for GET /api/recruiters/:id/matching-jobs"""
    
    def test_matching_jobs_success(self):
        """Get matching jobs for a recruiter successfully."""
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('85.50'),
            is_valid=True
        )
        
        url = f'/api/recruiters/{self.recruiter.id}/matching-jobs'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['recruiter_id'], self.recruiter.id)
    
    def test_matching_jobs_recruiter_not_found(self):
        """Return 404 for non-existent recruiter."""
        url = '/api/recruiters/99999/matching-jobs'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestCalculateMatchView(AIMatchingAPITestCase):
    """Tests for POST /api/ai-matching/calculate"""
    
    def test_calculate_match_success(self):
        """Calculate match score successfully."""
        url = '/api/ai-matching/calculate/'
        data = {
            'job_id': self.job.id,
            'recruiter_id': self.recruiter.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('overall_score', response.data)
        
        # Verify score saved to database
        self.assertTrue(
            AIMatchingScore.objects.filter(
                job=self.job,
                recruiter=self.recruiter
            ).exists()
        )
    
    def test_calculate_match_job_not_found(self):
        """Return 404 for non-existent job."""
        url = '/api/ai-matching/calculate/'
        data = {
            'job_id': 99999,
            'recruiter_id': self.recruiter.id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_calculate_match_invalid_data(self):
        """Return 400 for invalid data."""
        url = '/api/ai-matching/calculate/'
        data = {}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestMatchDetailView(AIMatchingAPITestCase):
    """Tests for GET /api/ai-matching/:jobId/:recruiterId"""
    
    def test_match_detail_success(self):
        """Get match detail successfully."""
        score = AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('85.50'),
            matching_details={'test': 'data'},
            is_valid=True
        )
        
        url = f'/api/ai-matching/{self.job.id}/{self.recruiter.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['overall_score']), 85.50)
    
    def test_match_detail_not_found(self):
        """Return 404 when no match exists."""
        url = f'/api/ai-matching/{self.job.id}/99999/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestBatchCalculateView(AIMatchingAPITestCase):
    """Tests for POST /api/ai-matching/batch-calculate"""
    
    def test_batch_calculate_success(self):
        """Batch calculate matches successfully."""
        url = '/api/ai-matching/batch-calculate/'
        data = {
            'job_id': self.job.id,
            'recruiter_ids': [self.recruiter.id]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['total_requested'], 1)
        self.assertEqual(response.data['total_calculated'], 1)
    
    def test_batch_calculate_limit_exceeded(self):
        """Return 400 when batch limit exceeded."""
        url = '/api/ai-matching/batch-calculate/'
        data = {
            'job_id': self.job.id,
            'recruiter_ids': list(range(1, 102))  # 101 items
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestTopMatchesView(AIMatchingAPITestCase):
    """Tests for GET /api/ai-matching/top-matches"""
    
    def test_top_matches_success(self):
        """Get top matches successfully."""
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('90.00'),
            is_valid=True
        )
        
        url = '/api/ai-matching/top-matches/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('top_matches', response.data)
    
    def test_top_matches_with_filters(self):
        """Get top matches with custom filters."""
        url = '/api/ai-matching/top-matches/?limit=5&min_score=80'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestRefreshMatchView(AIMatchingAPITestCase):
    """Tests for POST /api/ai-matching/refresh"""
    
    def test_refresh_match_success(self):
        """Refresh matches successfully."""
        # Create existing score
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('50.00'),
            is_valid=True
        )
        
        url = '/api/ai-matching/refresh/'
        data = {'job_id': self.job.id}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_refreshed', response.data)
    
    def test_refresh_match_no_params(self):
        """Return 400 when no job_id or recruiter_id provided."""
        url = '/api/ai-matching/refresh/'
        data = {}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestMatchingInsightsView(AIMatchingAPITestCase):
    """Tests for GET /api/ai-matching/insights"""
    
    def test_insights_success(self):
        """Get insights successfully."""
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('85.50'),
            skill_match_score=Decimal('90.00'),
            experience_match_score=Decimal('80.00'),
            education_match_score=Decimal('85.00'),
            location_match_score=Decimal('75.00'),
            salary_match_score=Decimal('80.00'),
            is_valid=True
        )
        
        url = '/api/ai-matching/insights/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('summary', response.data)
        self.assertIn('score_distribution', response.data)
        self.assertIn('component_averages', response.data)
    
    def test_insights_with_job_filter(self):
        """Get insights filtered by job."""
        url = f'/api/ai-matching/insights/?job_id={self.job.id}'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['filters_applied']['job_id'], self.job.id)
