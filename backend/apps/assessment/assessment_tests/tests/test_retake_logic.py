from django.test import TestCase
from django.utils import timezone
from apps.core.users.models import CustomUser
from apps.assessment.assessment_tests.models import AssessmentTest
from apps.assessment.assessment_categories.models import AssessmentCategory
from apps.assessment.test_results.models import TestResult
from apps.assessment.assessment_tests.services.assessment_tests import check_retake_eligibility
from apps.candidate.recruiters.models import Recruiter
from decimal import Decimal

class AssessmentRetakeLogicTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(email='tester@example.com', full_name='Tester')
        self.recruiter = Recruiter.objects.create(user=self.user)
        self.category = AssessmentCategory.objects.create(name='Tech', slug='tech')
        
        self.test = AssessmentTest.objects.create(
            title='Python Expert',
            slug='python-expert',
            category=self.category,
            test_type='technical',
            duration_minutes=60,
            total_questions=10,
            questions_data={'questions': []},
            max_retakes=2,       # Total 3 attempts (1 original + 2 retakes)
            retake_wait_days=7
        )

    def test_initial_eligibility(self):
        """Test that a user can take the test for the first time."""
        eligibility = check_retake_eligibility(self.test.id, self.recruiter.id)
        self.assertTrue(eligibility['can_retake'])
        self.assertEqual(eligibility['attempts_used'], 0)
        self.assertEqual(eligibility['max_attempts'], 3)

    def test_wait_period_enforcement(self):
        """Test that user must wait before retaking."""
        # Simulate first attempt
        TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=50,
            percentage_score=50,
            passed=False,
            started_at=timezone.now() - timezone.timedelta(hours=1),
            completed_at=timezone.now() - timezone.timedelta(minutes=50) # 50 mins ago
        )
        
        eligibility = check_retake_eligibility(self.test.id, self.recruiter.id)
        self.assertFalse(eligibility['can_retake'])
        self.assertEqual(eligibility['wait_days_remaining'], 7)
        self.assertIn("Bạn cần chờ thêm 7 ngày", eligibility['message'])

    def test_eligible_after_wait_period(self):
        """Test that user can retake after wait period expires."""
        # Simulate attempt 8 days ago
        old_time = timezone.now() - timezone.timedelta(days=8)
        result = TestResult.objects.create(
            assessment_test=self.test,
            recruiter=self.recruiter,
            score=50,
            percentage_score=50,
            passed=False,
            started_at=old_time
        )
        TestResult.objects.filter(id=result.id).update(completed_at=old_time + timezone.timedelta(minutes=30))
        
        eligibility = check_retake_eligibility(self.test.id, self.recruiter.id)
        self.assertTrue(eligibility['can_retake'], f"Should be eligible. Eligibility: {eligibility}")
        self.assertEqual(eligibility['attempts_used'], 1)

    def test_max_retakes_enforcement(self):
        """Test that max retakes limit is respected."""
        # Setup: 3 previous results (all older than wait period)
        for i in range(3):
            TestResult.objects.create(
                assessment_test=self.test,
                recruiter=self.recruiter,
                score=50,
                percentage_score=50,
                passed=False,
                started_at=timezone.now() - timezone.timedelta(days=30 + i),
                completed_at=timezone.now() - timezone.timedelta(days=29 + i)
            )
            
        eligibility = check_retake_eligibility(self.test.id, self.recruiter.id)
        self.assertFalse(eligibility['can_retake'])
        self.assertEqual(eligibility['attempts_used'], 3)
        self.assertIn("đạt giới hạn tối đa 3 lần thi", eligibility['message'])
