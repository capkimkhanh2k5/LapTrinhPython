"""
Unit Tests for Assessment Tests Services

Tests for assessment_tests services: start_test, submit_test, calculate_score.
"""
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.assessment_categories.models import AssessmentCategory
from apps.assessment.test_results.models import TestResult
from apps.candidate.recruiters.models import Recruiter
from apps.assessment.assessment_tests.services.assessment_tests import (
    StartTestInput,
    SubmitTestInput,
    start_test,
    submit_test,
    calculate_score,
    get_test_results,
    check_retake_eligibility,
)


User = get_user_model()


class TestStartTest(TestCase):
    """Tests for start_test service function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
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
            difficulty_level='intermediate',
            duration_minutes=30,
            total_questions=5,
            passing_score=Decimal('60.00'),
            questions_data={
                'questions': [
                    {
                        'id': 1,
                        'type': 'multiple_choice',
                        'question': 'What is Python?',
                        'options': ['A', 'B', 'C', 'D'],
                        'correct_answer': 'A',
                        'points': 10
                    },
                    {
                        'id': 2,
                        'type': 'true_false',
                        'question': 'Python is compiled',
                        'correct_answer': False,
                        'points': 10
                    }
                ]
            },
            is_active=True,
            is_public=True,
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            job_search_status='active'
        )
    
    def test_start_test_success(self):
        """Should successfully start a test."""
        input_data = StartTestInput(
            test_id=self.test.id,
            recruiter_id=self.recruiter.id
        )
        
        result = start_test(input_data)
        
        self.assertEqual(result['test_id'], self.test.id)
        self.assertEqual(result['test_title'], 'Python Test')
        self.assertEqual(result['duration_minutes'], 30)
        self.assertEqual(result['total_questions'], 5)
        self.assertEqual(len(result['questions']), 2)
        self.assertIn('started_at', result)
        
        # Verify correct answers are stripped
        for q in result['questions']:
            self.assertNotIn('correct_answer', q)
    
    def test_start_test_not_found(self):
        """Should raise error for non-existent test."""
        input_data = StartTestInput(
            test_id=99999,
            recruiter_id=self.recruiter.id
        )
        
        with self.assertRaises(AssessmentTest.DoesNotExist):
            start_test(input_data)
    
    def test_start_test_inactive(self):
        """Should raise error for inactive test."""
        self.test.is_active = False
        self.test.save()
        
        input_data = StartTestInput(
            test_id=self.test.id,
            recruiter_id=self.recruiter.id
        )
        
        with self.assertRaises(ValueError) as context:
            start_test(input_data)
        
        self.assertIn('not currently active', str(context.exception))
        
        # Reset
        self.test.is_active = True
        self.test.save()
    
    def test_start_test_max_retakes_exceeded(self):
        """Should raise error when max retakes exceeded."""
        # Create 2 results (Original + 1 Retake). Default max_retakes is 1, so total allowed is 2.
        for i in range(2):
            res = TestResult.objects.create(
                assessment_test=self.test,
                recruiter=self.recruiter,
                score=Decimal('50.00'),
                percentage_score=Decimal('50.00'),
                started_at=timezone.now() - timezone.timedelta(days=10+i)
            )
            TestResult.objects.filter(id=res.id).update(completed_at=timezone.now() - timezone.timedelta(days=10+i, minutes=-30))
        
        input_data = StartTestInput(
            test_id=self.test.id,
            recruiter_id=self.recruiter.id
        )
        
        with self.assertRaises(ValueError) as context:
            start_test(input_data)
        
        self.assertIn('Đạt tới giới hạn' if 'Đạt tới giới hạn' in str(context.exception) else 'giới hạn tối đa', str(context.exception))


class TestSubmitTest(TestCase):
    """Tests for submit_test service function."""
    
    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = User.objects.create_user(
            email='submit@example.com',
            password='testpass123',
            full_name='Submit User',
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
            total_questions=3,
            passing_score=Decimal('60.00'),
            questions_data={
                'questions': [
                    {'id': 1, 'type': 'multiple_choice', 'question': 'Q1', 
                     'options': ['A', 'B', 'C'], 'correct_answer': 'A', 'points': 10},
                    {'id': 2, 'type': 'true_false', 'question': 'Q2',
                     'correct_answer': True, 'points': 10},
                    {'id': 3, 'type': 'multiple_choice', 'question': 'Q3',
                     'options': ['A', 'B', 'C'], 'correct_answer': 'B', 'points': 10}
                ]
            },
            is_active=True,
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=2,
            job_search_status='active'
        )
    
    def test_submit_test_all_correct(self):
        """Should return 100% for all correct answers."""
        input_data = SubmitTestInput(
            test_id=self.test.id,
            recruiter_id=self.recruiter.id,
            answers=[
                {'question_id': 1, 'answer': 'A'},
                {'question_id': 2, 'answer': True},
                {'question_id': 3, 'answer': 'B'}
            ],
            started_at=timezone.now()
        )
        
        result = submit_test(input_data)
        
        self.assertIsInstance(result, TestResult)
        self.assertEqual(result.score, Decimal('30.00'))
        self.assertEqual(result.percentage_score, Decimal('100.00'))
        self.assertTrue(result.passed)
    
    def test_submit_test_partial_correct(self):
        """Should calculate correct percentage for partial answers."""
        input_data = SubmitTestInput(
            test_id=self.test.id,
            recruiter_id=self.recruiter.id,
            answers=[
                {'question_id': 1, 'answer': 'A'},  # Correct
                {'question_id': 2, 'answer': False},  # Wrong
                {'question_id': 3, 'answer': 'C'}  # Wrong
            ],
            started_at=timezone.now()
        )
        
        result = submit_test(input_data)
        
        self.assertEqual(result.score, Decimal('10.00'))
        self.assertAlmostEqual(float(result.percentage_score), 33.33, places=1)
        self.assertFalse(result.passed)
    
    def test_submit_test_all_wrong(self):
        """Should return 0% for all wrong answers."""
        input_data = SubmitTestInput(
            test_id=self.test.id,
            recruiter_id=self.recruiter.id,
            answers=[
                {'question_id': 1, 'answer': 'C'},
                {'question_id': 2, 'answer': False},
                {'question_id': 3, 'answer': 'A'}
            ],
            started_at=timezone.now()
        )
        
        result = submit_test(input_data)
        
        self.assertEqual(result.score, Decimal('0.00'))
        self.assertEqual(result.percentage_score, Decimal('0.00'))
        self.assertFalse(result.passed)


class TestCalculateScore(TestCase):
    """Tests for calculate_score function."""
    
    def setUp(self):
        """Set up mock test."""
        self.test = MagicMock()
        self.test.questions_data = {
            'questions': [
                {'id': 1, 'type': 'multiple_choice', 'correct_answer': 'A', 'points': 10},
                {'id': 2, 'type': 'true_false', 'correct_answer': True, 'points': 5},
                {'id': 3, 'type': 'text', 'correct_answer': 'Python', 'points': 15}
            ]
        }
    
    def test_calculate_multiple_choice(self):
        """Should correctly score multiple choice."""
        answers = [{'question_id': 1, 'answer': 'A'}]
        result = calculate_score(self.test, answers)
        
        self.assertEqual(result['correct_count'], 1)
        self.assertEqual(result['earned_points'], 10)
    
    def test_calculate_true_false(self):
        """Should correctly score true/false."""
        answers = [{'question_id': 2, 'answer': True}]
        result = calculate_score(self.test, answers)
        
        # Only question 2 answered correctly
        self.assertEqual(result['earned_points'], 5)
    
    def test_calculate_text_case_insensitive(self):
        """Should match text answers case-insensitively."""
        answers = [{'question_id': 3, 'answer': 'PYTHON'}]
        result = calculate_score(self.test, answers)
        
        self.assertEqual(result['earned_points'], 15)
    
    def test_calculate_missing_answer(self):
        """Should handle missing answers."""
        answers = [{'question_id': 1, 'answer': 'A'}]  # Missing 2 and 3
        result = calculate_score(self.test, answers)
        
        self.assertEqual(result['correct_count'], 1)
        self.assertEqual(result['total_questions'], 3)
    
    def test_calculate_empty_answers(self):
        """Should handle empty answers."""
        result = calculate_score(self.test, [])
        
        self.assertEqual(result['correct_count'], 0)
        self.assertEqual(result['score'], Decimal('0.00'))


class TestRetakeEligibility(TestCase):
    """Tests for check_retake_eligibility function."""
    
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
            questions_data={'questions': []},
            is_active=True,
            created_by=cls.user
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_eligibility_no_attempts(self):
        """Should be eligible with no attempts."""
        eligibility = check_retake_eligibility(self.test.id, self.recruiter.id)
        self.assertTrue(eligibility['can_retake'])
        self.assertEqual(eligibility['attempts_used'], 0)
        self.assertEqual(eligibility['attempts_remaining'], self.test.max_retakes + 1)
    
    def test_eligibility_wait_period(self):
        """Should not be eligible during wait period."""
        # Setup: One attempt recently (wait days is 7)
        res = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('50.00'),
            started_at=timezone.now() - timezone.timedelta(hours=1)
        )
        TestResult.objects.filter(id=res.id).update(completed_at=timezone.now() - timezone.timedelta(minutes=30))
        
        eligibility = check_retake_eligibility(self.test.id, self.recruiter.id)
        self.assertFalse(eligibility['can_retake'])
        self.assertEqual(eligibility['wait_days_remaining'], 7)
    
    def test_eligibility_after_one_attempt_old(self):
        """Should be eligible after one attempt if it's old enough."""
        # Setup: One attempt 10 days ago
        res = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=Decimal('50.00'),
            started_at=timezone.now() - timezone.timedelta(days=10)
        )
        TestResult.objects.filter(id=res.id).update(completed_at=timezone.now() - timezone.timedelta(days=10, minutes=-30))
        
        eligibility = check_retake_eligibility(self.test.id, self.recruiter.id)
        
        self.assertTrue(eligibility['can_retake'])
        self.assertEqual(eligibility['attempts_used'], 1)
        self.assertEqual(eligibility['attempts_remaining'], self.test.max_retakes)
    
    def test_eligibility_max_reached(self):
        """Should not be eligible after max attempts reached (even if wait period passed)."""
        max_total = self.test.max_retakes + 1
        for i in range(max_total):
            res = TestResult.objects.create(
                assessment_test=self.test,
                recruiter=self.recruiter,
                score=Decimal('50.00'),
                started_at=timezone.now() - timezone.timedelta(days=100+i)
            )
            TestResult.objects.filter(id=res.id).update(completed_at=timezone.now() - timezone.timedelta(days=100+i, minutes=-30))
        
        eligibility = check_retake_eligibility(self.test.id, self.recruiter.id)
        
        self.assertFalse(eligibility['can_retake'])
        self.assertEqual(eligibility['attempts_used'], max_total)
        self.assertEqual(eligibility['attempts_remaining'], 0)
        self.assertIn("đạt giới hạn tối đa", eligibility['message'])
