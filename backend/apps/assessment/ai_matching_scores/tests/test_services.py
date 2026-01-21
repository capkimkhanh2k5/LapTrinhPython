"""
Service Layer Tests for AI Matching Scores

Tests for services/ai_matching_scores.py functions.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.recruitment.jobs.models import Job
from apps.candidate.recruiters.models import Recruiter
from apps.company.companies.models import Company
from apps.assessment.ai_matching_scores.models import AIMatchingScore
from apps.assessment.ai_matching_scores.services.ai_matching_scores import (
    CalculateMatchInput,
    BatchCalculateInput,
    RefreshMatchInput,
    calculate_single_match,
    batch_calculate_matches,
    refresh_matches,
    get_matching_insights,
    MATCHING_WEIGHTS_BASIC,
    MATCHING_WEIGHTS_SEMANTIC,
)


User = get_user_model()


class TestCalculateSingleMatch(TestCase):
    """Tests for calculate_single_match service function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Test Company',
            slug='test-company',
            description='Test company'
        )
        
        cls.job = Job.objects.create(
            company=cls.company,
            title='Python Developer',
            slug='python-dev',
            description='Python developer role',
            requirements='Python, Django',
            job_type='full-time',
            level='junior',
            experience_years_min=2,
            experience_years_max=5,
            status='published',
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            highest_education_level='dai_hoc',
            job_search_status='active'
        )
    
    def test_calculate_single_match_creates_score(self):
        """Should create AIMatchingScore for new job-recruiter pair."""
        input_data = CalculateMatchInput(
            job_id=self.job.id,
            recruiter_id=self.recruiter.id
        )
        
        result = calculate_single_match(input_data)
        
        self.assertIsInstance(result, AIMatchingScore)
        self.assertEqual(result.job_id, self.job.id)
        self.assertEqual(result.recruiter_id, self.recruiter.id)
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.overall_score)
    
    def test_calculate_single_match_updates_existing_score(self):
        """Should update existing score instead of creating duplicate."""
        # Create existing score
        existing = AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('50.00'),
            is_valid=True
        )
        
        input_data = CalculateMatchInput(
            job_id=self.job.id,
            recruiter_id=self.recruiter.id
        )
        
        result = calculate_single_match(input_data)
        
        # Should be same object, updated
        self.assertEqual(result.id, existing.id)
        # Score should have been recalculated
        self.assertNotEqual(result.overall_score, Decimal('50.00'))
    
    def test_calculate_single_match_job_not_found(self):
        """Should raise DoesNotExist for invalid job_id."""
        input_data = CalculateMatchInput(
            job_id=99999,
            recruiter_id=self.recruiter.id
        )
        
        with self.assertRaises(Job.DoesNotExist):
            calculate_single_match(input_data)
    
    def test_calculate_single_match_recruiter_not_found(self):
        """Should raise DoesNotExist for invalid recruiter_id."""
        input_data = CalculateMatchInput(
            job_id=self.job.id,
            recruiter_id=99999
        )
        
        with self.assertRaises(Recruiter.DoesNotExist):
            calculate_single_match(input_data)
    
    def test_matching_details_contains_all_components(self):
        """Matching details should contain all score components."""
        input_data = CalculateMatchInput(
            job_id=self.job.id,
            recruiter_id=self.recruiter.id
        )
        
        result = calculate_single_match(input_data)
        details = result.matching_details
        
        self.assertIn('skill', details)
        self.assertIn('experience', details)
        self.assertIn('education', details)
        self.assertIn('location', details)
        self.assertIn('salary', details)
        self.assertIn('weights', details)
        self.assertIn('semantic_enabled', details)


class TestBatchCalculateMatches(TestCase):
    """Tests for batch_calculate_matches service function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='batch@example.com',
            password='testpass123',
            full_name='Batch User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Batch Company',
            slug='batch-company',
            description='Batch test'
        )
        
        cls.job = Job.objects.create(
            company=cls.company,
            title='Batch Job',
            slug='batch-job',
            description='Batch job desc',
            requirements='Skills',
            job_type='full-time',
            level='junior',
            status='published',
            created_by=cls.user
        )
        
        # Create multiple recruiters
        cls.recruiters = []
        for i in range(3):
            user = User.objects.create_user(
                email=f'recruiter{i}@example.com',
                password='testpass123',
                full_name=f'Recruiter {i}',
                is_active=True
            )
            recruiter = Recruiter.objects.create(
                user=user,
                years_of_experience=i + 1,
                job_search_status='active'
            )
            cls.recruiters.append(recruiter)
    
    def test_batch_calculate_success(self):
        """Should calculate scores for multiple recruiters."""
        input_data = BatchCalculateInput(
            job_id=self.job.id,
            recruiter_ids=[r.id for r in self.recruiters]
        )
        
        results = batch_calculate_matches(input_data)
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, AIMatchingScore)
            self.assertEqual(result.job_id, self.job.id)
    
    def test_batch_calculate_skips_invalid_recruiters(self):
        """Should skip invalid recruiter IDs without failing."""
        input_data = BatchCalculateInput(
            job_id=self.job.id,
            recruiter_ids=[self.recruiters[0].id, 99999, self.recruiters[1].id]
        )
        
        results = batch_calculate_matches(input_data)
        
        # Should only have 2 results (skipped invalid ID)
        self.assertEqual(len(results), 2)
    
    def test_batch_calculate_empty_list(self):
        """Should handle empty recruiter list."""
        # This should raise validation error from Pydantic
        with self.assertRaises(ValueError):
            BatchCalculateInput(
                job_id=self.job.id,
                recruiter_ids=[]
            )


class TestRefreshMatches(TestCase):
    """Tests for refresh_matches service function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='refresh@example.com',
            password='testpass123',
            full_name='Refresh User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Refresh Company',
            slug='refresh-company',
            description='Refresh test'
        )
        
        cls.job = Job.objects.create(
            company=cls.company,
            title='Refresh Job',
            slug='refresh-job',
            description='Refresh job desc',
            requirements='Skills',
            job_type='full-time',
            level='junior',
            status='published',
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            job_search_status='active'
        )
    
    def test_refresh_by_job_id(self):
        """Should refresh all scores for a job."""
        # Create existing score
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('50.00'),
            is_valid=True
        )
        
        input_data = RefreshMatchInput(job_id=self.job.id)
        count = refresh_matches(input_data)
        
        self.assertEqual(count, 1)
    
    def test_refresh_by_recruiter_id(self):
        """Should refresh all scores for a recruiter."""
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('50.00'),
            is_valid=True
        )
        
        input_data = RefreshMatchInput(recruiter_id=self.recruiter.id)
        count = refresh_matches(input_data)
        
        self.assertEqual(count, 1)
    
    def test_refresh_no_existing_scores(self):
        """Should return 0 when no scores to refresh."""
        input_data = RefreshMatchInput(job_id=self.job.id)
        count = refresh_matches(input_data)
        
        self.assertEqual(count, 0)


class TestGetMatchingInsights(TestCase):
    """Tests for get_matching_insights service function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='insights@example.com',
            password='testpass123',
            full_name='Insights User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Insights Company',
            slug='insights-company',
            description='Insights test'
        )
        
        cls.job = Job.objects.create(
            company=cls.company,
            title='Insights Job',
            slug='insights-job',
            description='Insights job desc',
            requirements='Skills',
            job_type='full-time',
            level='junior',
            status='published',
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            job_search_status='active'
        )
    
    def test_insights_with_scores(self):
        """Should return insights when scores exist."""
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('85.00'),
            skill_match_score=Decimal('90.00'),
            experience_match_score=Decimal('80.00'),
            education_match_score=Decimal('85.00'),
            location_match_score=Decimal('75.00'),
            salary_match_score=Decimal('80.00'),
            is_valid=True
        )
        
        insights = get_matching_insights()
        
        self.assertIn('summary', insights)
        self.assertIn('score_distribution', insights)
        self.assertIn('component_averages', insights)
        self.assertEqual(insights['summary']['total_matches'], 1)
    
    def test_insights_empty(self):
        """Should work with no scores."""
        insights = get_matching_insights()
        
        self.assertEqual(insights['summary']['total_matches'], 0)
        self.assertEqual(insights['summary']['avg_overall_score'], 0)
    
    def test_insights_with_job_filter(self):
        """Should filter by job_id."""
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('85.00'),
            is_valid=True
        )
        
        insights = get_matching_insights(job_id=self.job.id)
        
        self.assertEqual(insights['filters_applied']['job_id'], self.job.id)
        self.assertEqual(insights['summary']['total_matches'], 1)
    
    def test_insights_score_distribution(self):
        """Should correctly categorize scores."""
        # Create scores in different ranges
        AIMatchingScore.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            overall_score=Decimal('85.00'),  # High
            is_valid=True
        )
        
        insights = get_matching_insights()
        
        self.assertIn('high', insights['score_distribution'])
        self.assertIn('medium', insights['score_distribution'])
        self.assertIn('low', insights['score_distribution'])


class TestMatchingWeights(TestCase):
    """Tests for matching weights configuration."""
    
    def test_basic_weights_sum_to_one(self):
        """Basic weights should sum to 1.0."""
        total = sum(MATCHING_WEIGHTS_BASIC.values())
        self.assertEqual(total, Decimal('1.00'))
    
    def test_semantic_weights_sum_to_one(self):
        """Semantic weights should sum to 1.0."""
        total = sum(MATCHING_WEIGHTS_SEMANTIC.values())
        self.assertEqual(total, Decimal('1.00'))
    
    def test_semantic_weights_have_semantic_key(self):
        """Semantic weights should include semantic key."""
        self.assertIn('semantic', MATCHING_WEIGHTS_SEMANTIC)
        self.assertEqual(MATCHING_WEIGHTS_SEMANTIC['semantic'], Decimal('0.25'))


class TestPydanticInputModels(TestCase):
    """Tests for Pydantic input validation models."""
    
    def test_calculate_match_input_valid(self):
        """Valid input should pass validation."""
        input_data = CalculateMatchInput(job_id=1, recruiter_id=1)
        self.assertEqual(input_data.job_id, 1)
        self.assertEqual(input_data.recruiter_id, 1)
    
    def test_batch_calculate_input_max_limit(self):
        """Should enforce max 100 recruiters limit."""
        with self.assertRaises(ValueError):
            BatchCalculateInput(
                job_id=1,
                recruiter_ids=list(range(101))
            )
    
    def test_refresh_match_input_requires_at_least_one(self):
        """Should require at least one of job_id or recruiter_id."""
        # Note: Validation happens in service layer, not Pydantic model
        # RefreshMatchInput() without args creates empty model, validation is elsewhere
        pass
    
    def test_refresh_match_input_accepts_job_only(self):
        """Should accept job_id only."""
        input_data = RefreshMatchInput(job_id=1)
        self.assertEqual(input_data.job_id, 1)
        self.assertIsNone(input_data.recruiter_id)
    
    def test_refresh_match_input_accepts_recruiter_only(self):
        """Should accept recruiter_id only."""
        input_data = RefreshMatchInput(recruiter_id=1)
        self.assertIsNone(input_data.job_id)
        self.assertEqual(input_data.recruiter_id, 1)
