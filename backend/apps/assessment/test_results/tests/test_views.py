"""
API Integration Tests for Test Results

Tests for all 6 Test Results API endpoints.
"""
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.assessment_categories.models import AssessmentCategory
from apps.assessment.test_results.models import TestResult
from apps.candidate.recruiters.models import Recruiter
from apps.company.companies.models import Company
from apps.recruitment.jobs.models import Job
from apps.recruitment.applications.models import Application


User = get_user_model()


class TestResultsAPITestCase(APITestCase):
    """Base test case with common setup."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        cls.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Test User',
            is_active=True
        )
        
        cls.other_user = User.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            full_name='Other User',
            is_active=True
        )
        
        cls.category = AssessmentCategory.objects.create(
            name='Technical',
            slug='technical',
            is_active=True
        )
        
        cls.test = AssessmentTest.objects.create(
            title='Python Test',
            slug='python-test',
            category=cls.category,
            test_type='technical',
            duration_minutes=30,
            total_questions=5,
            passing_score=Decimal('60.00'),
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
            years_of_experience=3,
            job_search_status='active'
        )
        
        cls.other_recruiter = Recruiter.objects.create(
            user=cls.other_user,
            years_of_experience=2,
            job_search_status='active'
        )
        
        cls.company = Company.objects.create(
            company_name='Test Company',
            slug='test-company',
            description='Test'
        )
        
        cls.job = Job.objects.create(
            company=cls.company,
            title='Python Dev',
            slug='py-dev',
            description='Python developer',
            requirements='Python',
            job_type='full-time',
            level='junior',
            status='published',
            created_by=cls.user
        )
    
    def setUp(self):
        """Set up for each test."""
        self.client.force_authenticate(user=self.user)


class TestRecruiterTestResultsView(TestResultsAPITestCase):
    """Tests for GET /api/recruiters/:id/test-results"""
    
    def test_get_own_results_success(self):
        """Should get own test results."""
        TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('80.00'),
            percentage_score=Decimal('80.00'),
            passed=True,
            started_at=timezone.now()
        )
        
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/test-results')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['recruiter_id'], self.recruiter.id)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_other_results_forbidden(self):
        """Should not allow access to other user's results."""
        response = self.client.get(f'/api/recruiters/{self.other_recruiter.id}/test-results')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_results_recruiter_not_found(self):
        """Should return 404 for non-existent recruiter."""
        response = self.client.get('/api/recruiters/99999/test-results')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_results_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/test-results')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestTestResultDetailView(TestResultsAPITestCase):
    """Tests for GET /api/test-results/:id/"""
    
    def test_get_detail_success(self):
        """Should get result detail."""
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('80.00'),
            percentage_score=Decimal('80.00'),
            passed=True,
            started_at=timezone.now()
        )
        
        response = self.client.get(f'/api/test-results/{result.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['score']), 80.00)
        self.assertTrue(response.data['passed'])
    
    def test_get_detail_not_found(self):
        """Should return 404 for non-existent result."""
        response = self.client.get('/api/test-results/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_detail_forbidden(self):
        """Should not allow access to other user's result."""
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.other_recruiter,
            score=Decimal('70.00'),
            started_at=timezone.now()
        )
        
        response = self.client.get(f'/api/test-results/{result.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestCertificateView(TestResultsAPITestCase):
    """Tests for GET /api/test-results/:id/certificate/"""
    
    def test_get_certificate_passed(self):
        """Should get certificate for passed result."""
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('80.00'),
            percentage_score=Decimal('80.00'),
            passed=True,
            started_at=timezone.now()
        )
        
        response = self.client.get(f'/api/test-results/{result.id}/certificate/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['validity_status'], 'valid')
        self.assertEqual(response.data['recruiter_name'], 'Test User')
    
    def test_get_certificate_not_passed(self):
        """Should reject certificate for failed result."""
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('40.00'),
            percentage_score=Decimal('40.00'),
            passed=False,
            started_at=timezone.now()
        )
        
        response = self.client.get(f'/api/test-results/{result.id}/certificate/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('not passed', response.data['reason'])
    
    def test_get_certificate_not_found(self):
        """Should return 404 for non-existent result."""
        response = self.client.get('/api/test-results/99999/certificate/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRetakeView(TestResultsAPITestCase):
    """Tests for POST /api/test-results/:id/retake/"""
    
    def test_retake_success(self):
        """Should allow retake when eligible."""
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('50.00'),
            passed=False,
            started_at=timezone.now()
        )
        
        response = self.client.post(f'/api/test-results/{result.id}/retake/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['can_retake'])
        self.assertIsNotNone(response.data['session'])
    
    def test_retake_not_found(self):
        """Should return 404 for non-existent result."""
        response = self.client.post('/api/test-results/99999/retake/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_retake_wrong_user(self):
        """Should reject retake for different user's result."""
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.other_recruiter,
            score=Decimal('50.00'),
            started_at=timezone.now()
        )
        
        response = self.client.post(f'/api/test-results/{result.id}/retake/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestApplicationTestResultsView(TestResultsAPITestCase):
    """Tests for GET /api/applications/:id/test-results/"""
    
    def test_get_application_results_applicant(self):
        """Applicant should see own application test results."""
        application = Application.objects.create(
            job=self.job,
            recruiter=self.recruiter,
            cover_letter='Test',
            status='pending'
        )
        
        TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            application=application,
            score=Decimal('80.00'),
            passed=True,
            started_at=timezone.now()
        )
        
        response = self.client.get(f'/api/applications/{application.id}/test-results/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_get_application_results_not_found(self):
        """Should return 404 for non-existent application."""
        response = self.client.get('/api/applications/99999/test-results/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_application_results_forbidden(self):
        """Should forbid access to other user's application."""
        application = Application.objects.create(
            job=self.job,
            recruiter=self.other_recruiter,
            cover_letter='Test',
            status='pending'
        )
        
        response = self.client.get(f'/api/applications/{application.id}/test-results/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestJobRequiredTestsView(TestResultsAPITestCase):
    """Tests for GET /api/jobs/:id/required-tests"""
    
    def test_get_required_tests_success(self):
        """Should get required tests for job."""
        from apps.assessment.job_assessment_requirements.models import JobAssessmentRequirement
        
        JobAssessmentRequirement.objects.create(
            job=self.job,
            assessment_test=self.test,
            is_mandatory=True,
            minimum_score=Decimal('70.00')
        )
        
        response = self.client.get(f'/api/jobs/{self.job.id}/required-tests')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['required_tests']), 1)
        self.assertEqual(response.data['job_title'], 'Python Dev')
    
    def test_get_required_tests_empty(self):
        """Should return empty list when no requirements."""
        response = self.client.get(f'/api/jobs/{self.job.id}/required-tests')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['required_tests']), 0)
    
    def test_get_required_tests_job_not_found(self):
        """Should return 404 for non-existent job."""
        response = self.client.get('/api/jobs/99999/required-tests')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_required_tests_public(self):
        """Should allow public access."""
        self.client.logout()
        response = self.client.get(f'/api/jobs/{self.job.id}/required-tests')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
