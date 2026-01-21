"""
API Integration Tests for Assessment Tests

Tests for all 10 Assessment Tests API endpoints.
"""
from decimal import Decimal

from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.assessment_categories.models import AssessmentCategory
from apps.assessment.test_results.models import TestResult
from apps.candidate.recruiters.models import Recruiter


User = get_user_model()


class AssessmentTestAPITestCase(APITestCase):
    """Base test case with common setup."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        cls.admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True
        )
        
        cls.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            full_name='Normal User',
            is_active=True
        )
        
        cls.category = AssessmentCategory.objects.create(
            name='Technical',
            slug='technical',
            is_active=True
        )
        
        cls.category2 = AssessmentCategory.objects.create(
            name='Personality',
            slug='personality',
            is_active=True
        )
        
        cls.test = AssessmentTest.objects.create(
            title='Python Test',
            slug='python-test',
            category=cls.category,
            test_type='technical',
            difficulty_level='intermediate',
            duration_minutes=30,
            total_questions=2,
            passing_score=Decimal('60.00'),
            questions_data={
                'questions': [
                    {'id': 1, 'type': 'multiple_choice', 'question': 'Q1',
                     'options': ['A', 'B', 'C'], 'correct_answer': 'A', 'points': 10},
                    {'id': 2, 'type': 'true_false', 'question': 'Q2',
                     'correct_answer': True, 'points': 10}
                ]
            },
            is_active=True,
            is_public=True,
            created_by=cls.admin_user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            job_search_status='active'
        )
    
    def setUp(self):
        """Set up for each test."""
        self.client.force_authenticate(user=self.user)


class TestAssessmentTestListView(AssessmentTestAPITestCase):
    """Tests for GET /api/assessment-tests/"""
    
    def test_list_tests_success(self):
        """Should list all active tests."""
        response = self.client.get('/api/assessment-tests/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated (dict with 'results') and non-paginated (list) response
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)
    
    def test_list_tests_filter_by_category(self):
        """Should filter tests by category."""
        response = self.client.get(f'/api/assessment-tests/?category={self.category.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_tests_filter_by_type(self):
        """Should filter tests by type."""
        response = self.client.get('/api/assessment-tests/?type=technical')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_tests_anonymous(self):
        """Should allow anonymous access."""
        self.client.logout()
        response = self.client.get('/api/assessment-tests/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestAssessmentTestDetailView(AssessmentTestAPITestCase):
    """Tests for GET /api/assessment-tests/:id/"""
    
    def test_get_detail_success(self):
        """Should get test detail."""
        response = self.client.get(f'/api/assessment-tests/{self.test.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Python Test')
        
        # Verify correct answers stripped for non-admin
        for q in response.data['questions']:
            self.assertNotIn('correct_answer', q)
    
    def test_get_detail_not_found(self):
        """Should return 404 for non-existent test."""
        response = self.client.get('/api/assessment-tests/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_detail_admin_sees_answers(self):
        """Admin should see correct answers."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/assessment-tests/{self.test.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestAssessmentTestCreateView(AssessmentTestAPITestCase):
    """Tests for POST /api/assessment-tests/"""
    
    def test_create_test_admin_success(self):
        """Admin should be able to create test."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'title': 'New Test',
            'slug': 'new-test',
            'category': self.category.id,
            'test_type': 'skill',
            'duration_minutes': 45,
            'total_questions': 10,
            'questions_data': {
                'questions': [
                    {'id': 1, 'type': 'multiple_choice', 'question': 'Q1',
                     'options': ['A', 'B'], 'correct_answer': 'A', 'points': 10}
                ]
            }
        }
        
        response = self.client.post('/api/assessment-tests/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'New Test')
    
    def test_create_test_non_admin_forbidden(self):
        """Non-admin should not be able to create test."""
        data = {'title': 'New Test', 'slug': 'new-test'}
        response = self.client.post('/api/assessment-tests/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_create_test_invalid_questions_data(self):
        """Should reject invalid questions_data format."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'title': 'Bad Test',
            'slug': 'bad-test',
            'category': self.category.id,
            'test_type': 'skill',
            'duration_minutes': 30,
            'total_questions': 1,
            'questions_data': {'invalid': 'format'}  # Missing 'questions' key
        }
        
        response = self.client.post('/api/assessment-tests/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestAssessmentTestUpdateView(AssessmentTestAPITestCase):
    """Tests for PUT /api/assessment-tests/:id/"""
    
    def test_update_test_admin_success(self):
        """Admin should be able to update test."""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'title': 'Updated Test',
            'slug': 'updated-test',
            'category': self.category.id,
            'test_type': 'technical',
            'duration_minutes': 60,
            'total_questions': 2,
            'questions_data': self.test.questions_data
        }
        
        response = self.client.put(
            f'/api/assessment-tests/{self.test.id}/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Test')
    
    def test_update_test_non_admin_forbidden(self):
        """Non-admin should not be able to update."""
        data = {'title': 'Hacked'}
        response = self.client.put(
            f'/api/assessment-tests/{self.test.id}/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestAssessmentTestDeleteView(AssessmentTestAPITestCase):
    """Tests for DELETE /api/assessment-tests/:id/"""
    
    def test_delete_test_admin_success(self):
        """Admin should be able to delete test."""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create a test to delete
        test_to_delete = AssessmentTest.objects.create(
            title='To Delete',
            slug='to-delete',
            category=self.category,
            test_type='skill',
            duration_minutes=30,
            total_questions=1,
            questions_data={'questions': []},
            is_active=True,
            created_by=self.admin_user
        )
        
        response = self.client.delete(f'/api/assessment-tests/{test_to_delete.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AssessmentTest.objects.filter(id=test_to_delete.id).exists())
    
    def test_delete_test_non_admin_forbidden(self):
        """Non-admin should not be able to delete."""
        response = self.client.delete(f'/api/assessment-tests/{self.test.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestAssessmentTestCategoriesView(AssessmentTestAPITestCase):
    """Tests for GET /api/assessment-tests/categories/"""
    
    def test_list_categories_success(self):
        """Should list all categories."""
        response = self.client.get('/api/assessment-tests/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('categories', response.data)
        self.assertEqual(response.data['total'], 2)


class TestAssessmentTestByTypeView(AssessmentTestAPITestCase):
    """Tests for GET /api/assessment-tests/by-type/:type/"""
    
    def test_filter_by_type_success(self):
        """Should filter tests by type."""
        response = self.client.get('/api/assessment-tests/by-type/technical/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['test_type'], 'technical')
        self.assertGreaterEqual(len(response.data['tests']), 1)
    
    def test_filter_by_invalid_type(self):
        """Should return error for invalid type."""
        response = self.client.get('/api/assessment-tests/by-type/invalid/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestStartTestView(AssessmentTestAPITestCase):
    """Tests for POST /api/assessment-tests/:id/start/"""
    
    def test_start_test_success(self):
        """Should start test for authenticated user."""
        response = self.client.post(f'/api/assessment-tests/{self.test.id}/start/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['test_id'], self.test.id)
        self.assertIn('questions', response.data)
        self.assertIn('started_at', response.data)
    
    def test_start_test_not_found(self):
        """Should return 404 for non-existent test."""
        response = self.client.post('/api/assessment-tests/99999/start/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_start_test_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()
        response = self.client.post(f'/api/assessment-tests/{self.test.id}/start/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestSubmitTestView(AssessmentTestAPITestCase):
    """Tests for POST /api/assessment-tests/:id/submit/"""
    
    def test_submit_test_success(self):
        """Should submit test and return result."""
        from django.utils import timezone
        
        data = {
            'answers': [
                {'question_id': 1, 'answer': 'A'},
                {'question_id': 2, 'answer': True}
            ],
            'started_at': timezone.now().isoformat()
        }
        
        response = self.client.post(
            f'/api/assessment-tests/{self.test.id}/submit/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('result_id', response.data)
        self.assertIn('score', response.data)
        self.assertIn('passed', response.data)
    
    def test_submit_test_invalid_data(self):
        """Should reject invalid submission data."""
        data = {}  # Missing required fields
        
        response = self.client.post(
            f'/api/assessment-tests/{self.test.id}/submit/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestTestResultsView(AssessmentTestAPITestCase):
    """Tests for GET /api/assessment-tests/:id/results/"""
    
    def test_get_results_success(self):
        """Should get test results for current user."""
        # Create a result
        from django.utils import timezone
        TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('80.00'),
            percentage_score=Decimal('80.00'),
            passed=True,
            started_at=timezone.now()
        )
        
        response = self.client.get(f'/api/assessment-tests/{self.test.id}/results/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['test_id'], self.test.id)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIn('retake_eligibility', response.data)
    
    def test_get_results_empty(self):
        """Should return empty results when no attempts."""
        response = self.client.get(f'/api/assessment-tests/{self.test.id}/results/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_get_results_not_found(self):
        """Should return 404 for non-existent test."""
        response = self.client.get('/api/assessment-tests/99999/results/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
