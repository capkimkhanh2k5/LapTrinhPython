"""
Unit Tests for Test Results Services

Tests for test_results services: certificate, retake, application results.
"""
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.assessment_categories.models import AssessmentCategory
from apps.assessment.test_results.models import TestResult
from apps.candidate.recruiters.models import Recruiter
from apps.assessment.test_results.services.test_results import (
    get_recruiter_test_results,
    get_result_by_id,
    get_certificate_data,
    request_retake,
    get_application_test_results,
    get_job_required_tests,
)


User = get_user_model()


class TestGetRecruiterTestResults(TestCase):
    """Tests for get_recruiter_test_results function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='recruiter@example.com',
            password='testpass123',
            full_name='Recruiter User',
            is_active=True
        )
        
        cls.category = AssessmentCategory.objects.create(
            name='Technical',
            slug='technical'
        )
        
        cls.test = AssessmentTest.objects.create(
            title='Python Test',
            slug='python-test',
            category=cls.category,
            test_type='technical',
            duration_minutes=30,
            total_questions=5,
            questions_data={'questions': []},
            is_active=True,
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            job_search_status='active'
        )
    
    def test_get_results_success(self):
        """Should return all results for recruiter."""
        TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('80.00'),
            percentage_score=Decimal('80.00'),
            passed=True,
            started_at=timezone.now()
        )
        
        results = get_recruiter_test_results(self.recruiter.id)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].score, Decimal('80.00'))
    
    def test_get_results_empty(self):
        """Should return empty queryset when no results."""
        results = get_recruiter_test_results(self.recruiter.id)
        
        self.assertEqual(len(results), 0)
    
    def test_get_results_ordered_by_date(self):
        """Should order results by completed_at descending."""
        TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('70.00'),
            started_at=timezone.now()
        )
        TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('90.00'),
            started_at=timezone.now()
        )
        
        results = get_recruiter_test_results(self.recruiter.id)
        
        self.assertEqual(len(results), 2)
        # Latest should be first
        self.assertEqual(results[0].score, Decimal('90.00'))


class TestGetCertificateData(TestCase):
    """Tests for get_certificate_data function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='cert@example.com',
            password='testpass123',
            full_name='Cert User',
            is_active=True
        )
        
        cls.category = AssessmentCategory.objects.create(
            name='Language',
            slug='language'
        )
        
        cls.test = AssessmentTest.objects.create(
            title='English Test',
            slug='english-test',
            category=cls.category,
            test_type='language',
            duration_minutes=60,
            total_questions=10,
            passing_score=Decimal('60.00'),
            questions_data={'questions': []},
            is_active=True,
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=2,
            job_search_status='active'
        )
    
    def test_get_certificate_passed(self):
        """Should return valid certificate for passed result."""
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('80.00'),
            percentage_score=Decimal('80.00'),
            passed=True,
            started_at=timezone.now()
        )
        
        certificate = get_certificate_data(result.id)
        
        self.assertIsNotNone(certificate)
        self.assertEqual(certificate['validity_status'], 'valid')
        self.assertEqual(certificate['recruiter_name'], 'Cert User')
        self.assertEqual(certificate['test_title'], 'English Test')
        self.assertTrue(certificate['passed'])
    
    def test_get_certificate_not_passed(self):
        """Should return not_passed status for failed result."""
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('40.00'),
            percentage_score=Decimal('40.00'),
            passed=False,
            started_at=timezone.now()
        )
        
        certificate = get_certificate_data(result.id)
        
        self.assertIsNotNone(certificate)
        self.assertEqual(certificate['validity_status'], 'not_passed')
        self.assertFalse(certificate['passed'])
    
    def test_get_certificate_not_found(self):
        """Should return None for non-existent result."""
        certificate = get_certificate_data(99999)
        
        self.assertIsNone(certificate)


class TestRequestRetake(TestCase):
    """Tests for request_retake function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='retake@example.com',
            password='testpass123',
            full_name='Retake User',
            is_active=True
        )
        
        cls.category = AssessmentCategory.objects.create(
            name='Skills',
            slug='skills'
        )
        
        cls.test = AssessmentTest.objects.create(
            title='Skill Test',
            slug='skill-test',
            category=cls.category,
            test_type='skill',
            duration_minutes=30,
            total_questions=5,
            questions_data={
                'questions': [
                    {'id': 1, 'type': 'multiple_choice', 'question': 'Q1',
                     'options': ['A', 'B'], 'correct_answer': 'A', 'points': 10}
                ]
            },
            is_active=True,
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_request_retake_success(self):
        """Should allow retake when eligible."""
        from datetime import timedelta
        
        # Create result in the past to allow retake
        past_date = timezone.now() - timedelta(days=30)
        
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('50.00'),
            passed=False,
            started_at=past_date
        )
        # Force update completed_at because auto_now_add=True prevents setting it in create
        TestResult.objects.filter(id=result.id).update(completed_at=past_date)
        
        retake = request_retake(result.id, self.recruiter.id)
        
        self.assertTrue(retake['can_retake'])
        self.assertIsNotNone(retake['session'])
        self.assertIn('questions', retake['session'])
    
    def test_request_retake_wrong_user(self):
        """Should reject retake for different user."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            full_name='Other',
            is_active=True
        )
        other_recruiter = Recruiter.objects.create(
            user=other_user,
            years_of_experience=1,
            job_search_status='active'
        )
        
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('50.00'),
            started_at=timezone.now()
        )
        
        with self.assertRaises(ValueError) as context:
            request_retake(result.id, other_recruiter.id)
        
        self.assertIn('does not belong', str(context.exception))
    
    def test_request_retake_not_found(self):
        """Should raise error for non-existent result."""
        with self.assertRaises(TestResult.DoesNotExist):
            request_retake(99999, self.recruiter.id)


class TestGetJobRequiredTests(TestCase):
    """Tests for get_job_required_tests function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        from apps.company.companies.models import Company
        from apps.recruitment.jobs.models import Job
        from apps.assessment.job_assessment_requirements.models import JobAssessmentRequirement
        
        cls.user = User.objects.create_user(
            email='job@example.com',
            password='testpass123',
            full_name='Job User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Test Company',
            slug='test-company',
            description='Test'
        )
        
        cls.job = Job.objects.create(
            company=cls.company,
            title='Python Dev',
            slug='python-dev',
            description='Python developer',
            requirements='Python',
            job_type='full-time',
            level='junior',
            status='published',
            created_by=cls.user
        )
        
        cls.category = AssessmentCategory.objects.create(
            name='Technical',
            slug='tech'
        )
        
        cls.test = AssessmentTest.objects.create(
            title='Python Test',
            slug='python-test-req',
            category=cls.category,
            test_type='technical',
            duration_minutes=30,
            total_questions=5,
            questions_data={'questions': []},
            is_active=True,
            created_by=cls.user
        )
        
        cls.requirement = JobAssessmentRequirement.objects.create(
            job=cls.job,
            assessment_test=cls.test,
            is_mandatory=True,
            minimum_score=Decimal('70.00')
        )
    
    def test_get_required_tests_success(self):
        """Should return required tests for job."""
        tests = get_job_required_tests(self.job.id)
        
        self.assertEqual(len(tests), 1)
        self.assertEqual(tests[0]['test_id'], self.test.id)
        self.assertEqual(tests[0]['test_title'], 'Python Test')
        self.assertTrue(tests[0]['is_required'])
        self.assertEqual(tests[0]['minimum_score'], Decimal('70.00'))
    
    def test_get_required_tests_empty(self):
        """Should return empty list when no requirements."""
        from apps.recruitment.jobs.models import Job
        
        job2 = Job.objects.create(
            company=self.company,
            title='Other Job',
            slug='other-job',
            description='Other',
            requirements='None',
            job_type='full-time',
            level='junior',
            status='published',
            created_by=self.user
        )
        
        tests = get_job_required_tests(job2.id)
        
        self.assertEqual(len(tests), 0)
