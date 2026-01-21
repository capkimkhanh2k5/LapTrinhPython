"""
Unit Tests for Reviews Services

Tests for reviews services: create, update, delete, helpful, report, approve.
"""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.social.reviews.models import Review
from apps.social.review_reactions.models import ReviewReaction
from apps.company.companies.models import Company
from apps.candidate.recruiters.models import Recruiter
from apps.social.reviews.services.reviews import (
    CreateReviewInput,
    UpdateReviewInput,
    ReportReviewInput,
    create_review,
    update_review,
    delete_review,
    mark_helpful,
    report_review,
    approve_review,
)


User = get_user_model()


class TestCreateReview(TestCase):
    """Tests for create_review function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='reviewer@example.com',
            password='testpass123',
            full_name='Reviewer User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Test Company',
            slug='test-company',
            description="Test"
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=3,
            job_search_status='active'
        )
    
    def test_create_review_success(self):
        """Should create a new review."""
        input_data = CreateReviewInput(
            company_id=self.company.id,
            recruiter_id=self.recruiter.id,
            rating=4,
            title='Great company',
            content='I really enjoyed working here',
            pros='Good culture',
            cons='Long hours',
            is_anonymous=False
        )
        
        review = create_review(input_data)
        
        self.assertIsNotNone(review.id)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.status, Review.Status.PENDING)
    
    def test_create_review_anonymous(self):
        """Should create anonymous review."""
        input_data = CreateReviewInput(
            company_id=self.company.id,
            recruiter_id=self.recruiter.id,
            rating=3,
            content='Average experience',
            is_anonymous=True
        )
        
        review = create_review(input_data)
        
        self.assertTrue(review.is_anonymous)
    
    def test_create_review_company_not_found(self):
        """Should raise error for non-existent company."""
        input_data = CreateReviewInput(
            company_id=99999,
            recruiter_id=self.recruiter.id,
            rating=4,
            content='Test'
        )
        
        with self.assertRaises(Company.DoesNotExist):
            create_review(input_data)
    
    def test_create_review_recruiter_not_found(self):
        """Should raise error for non-existent recruiter."""
        input_data = CreateReviewInput(
            company_id=self.company.id,
            recruiter_id=99999,
            rating=4,
            content='Test'
        )
        
        with self.assertRaises(Recruiter.DoesNotExist):
            create_review(input_data)
    
    def test_create_review_boundary_rating_1(self):
        """Should accept minimum rating of 1."""
        input_data = CreateReviewInput(
            company_id=self.company.id,
            recruiter_id=self.recruiter.id,
            rating=1,
            content='Poor experience'
        )
        
        review = create_review(input_data)
        self.assertEqual(review.rating, 1)
    
    def test_create_review_boundary_rating_5(self):
        """Should accept maximum rating of 5."""
        input_data = CreateReviewInput(
            company_id=self.company.id,
            recruiter_id=self.recruiter.id,
            rating=5,
            content='Excellent!'
        )
        
        review = create_review(input_data)
        self.assertEqual(review.rating, 5)


class TestUpdateReview(TestCase):
    """Tests for update_review function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='update@example.com',
            password='testpass123',
            full_name='Update User',
            is_active=True
        )
        
        cls.other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            full_name='Other User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Update Company',
            slug='update-company',
            description="Test"
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=2,
            job_search_status='active'
        )
        
        cls.other_recruiter = Recruiter.objects.create(
            user=cls.other_user,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_update_review_success(self):
        """Should update own review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='Original',
            status=Review.Status.APPROVED
        )
        
        input_data = UpdateReviewInput(
            review_id=review.id,
            recruiter_id=self.recruiter.id,
            rating=4,
            content='Updated content'
        )
        
        updated = update_review(input_data)
        
        self.assertEqual(updated.rating, 4)
        self.assertEqual(updated.content, 'Updated content')
        self.assertEqual(updated.status, Review.Status.PENDING)  # Reset to pending
    
    def test_update_review_not_owner(self):
        """Should reject update from non-owner."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='Original'
        )
        
        input_data = UpdateReviewInput(
            review_id=review.id,
            recruiter_id=self.other_recruiter.id,  # Wrong owner
            rating=1
        )
        
        with self.assertRaises(PermissionError):
            update_review(input_data)
    
    def test_update_review_partial_fields(self):
        """Should update only provided fields."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='Original',
            title='Original Title'
        )
        
        input_data = UpdateReviewInput(
            review_id=review.id,
            recruiter_id=self.recruiter.id,
            content='New content'  # Only content
        )
        
        updated = update_review(input_data)
        
        self.assertEqual(updated.content, 'New content')
        self.assertEqual(updated.rating, 3)  # Unchanged
    
    def test_update_review_not_found(self):
        """Should raise error for non-existent review."""
        input_data = UpdateReviewInput(
            review_id=99999,
            recruiter_id=self.recruiter.id,
            rating=4
        )
        
        with self.assertRaises(Review.DoesNotExist):
            update_review(input_data)


class TestDeleteReview(TestCase):
    """Tests for delete_review function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='delete@example.com',
            password='testpass123',
            full_name='Delete User',
            is_active=True
        )
        
        cls.other_user = User.objects.create_user(
            email='other_del@example.com',
            password='testpass123',
            full_name='Other Del User',
            is_active=True
        )
        
        cls.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass',
            full_name='Admin',
            is_staff=True
        )
        
        cls.company = Company.objects.create(
            company_name='Delete Company',
            slug='delete-company',
            description="Test"
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=2,
            job_search_status='active'
        )
        
        cls.other_recruiter = Recruiter.objects.create(
            user=cls.other_user,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_delete_review_owner(self):
        """Owner should be able to delete."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='To delete'
        )
        
        result = delete_review(review.id, self.user.id, is_admin=False)
        
        self.assertTrue(result)
        self.assertFalse(Review.objects.filter(id=review.id).exists())
    
    def test_delete_review_admin(self):
        """Admin should be able to delete any review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='Admin delete'
        )
        
        result = delete_review(review.id, self.admin.id, is_admin=True)
        
        self.assertTrue(result)
    
    def test_delete_review_not_owner(self):
        """Non-owner should not delete."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='Not allowed'
        )
        
        with self.assertRaises(PermissionError):
            delete_review(review.id, self.other_user.id, is_admin=False)
    
    def test_delete_review_not_found(self):
        """Should raise error for non-existent review."""
        with self.assertRaises(Review.DoesNotExist):
            delete_review(99999, self.user.id, is_admin=False)


class TestMarkHelpful(TestCase):
    """Tests for mark_helpful function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='helpful@example.com',
            password='testpass123',
            full_name='Helpful User',
            is_active=True
        )
        
        cls.other_user = User.objects.create_user(
            email='helpful2@example.com',
            password='testpass123',
            full_name='Helpful User 2',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Helpful Company',
            slug='helpful-company',
            description="Test"
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_mark_helpful_toggle(self):
        """Should toggle helpful mark."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Helpful test',
            helpful_count=0
        )
        
        # Mark as helpful
        result1 = mark_helpful(review.id, self.user.id)
        self.assertTrue(result1['is_helpful'])
        self.assertEqual(result1['helpful_count'], 1)
        
        # Unmark
        result2 = mark_helpful(review.id, self.user.id)
        self.assertFalse(result2['is_helpful'])
        self.assertEqual(result2['helpful_count'], 0)
    
    def test_mark_helpful_multiple_users(self):
        """Multiple users can mark same review as helpful."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Popular',
            helpful_count=0
        )
        
        result1 = mark_helpful(review.id, self.user.id)
        result2 = mark_helpful(review.id, self.other_user.id)
        
        self.assertEqual(result2['helpful_count'], 2)
    
    def test_mark_helpful_review_not_found(self):
        """Should raise error for non-existent review."""
        with self.assertRaises(Review.DoesNotExist):
            mark_helpful(99999, self.user.id)


class TestReportReview(TestCase):
    """Tests for report_review function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='report@example.com',
            password='testpass123',
            full_name='Report User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Report Company',
            slug='report-company',
            description="Test"
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_report_review_success(self):
        """Should report a review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=1,
            content='Bad review'
        )
        
        input_data = ReportReviewInput(
            review_id=review.id,
            reporter_id=self.user.id,
            reason='Inappropriate content'
        )
        
        result = report_review(input_data)
        
        self.assertTrue(result['reported'])
    
    def test_report_review_not_found(self):
        """Should raise error for non-existent review."""
        input_data = ReportReviewInput(
            review_id=99999,
            reporter_id=self.user.id,
            reason='Test'
        )
        
        with self.assertRaises(Review.DoesNotExist):
            report_review(input_data)


class TestApproveReview(TestCase):
    """Tests for approve_review function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email='approve@example.com',
            password='testpass123',
            full_name='Approve User',
            is_active=True
        )
        
        cls.company = Company.objects.create(
            company_name='Approve Company',
            slug='approve-company',
            description="Test"
        )
        
        cls.recruiter = Recruiter.objects.create(
            user=cls.user,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_approve_review(self):
        """Should approve pending review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Pending',
            status=Review.Status.PENDING
        )
        
        result = approve_review(review.id, 'approve')
        
        self.assertEqual(result.status, Review.Status.APPROVED)
    
    def test_reject_review(self):
        """Should reject pending review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Pending',
            status=Review.Status.PENDING
        )
        
        result = approve_review(review.id, 'reject', 'Inappropriate content')
        
        self.assertEqual(result.status, Review.Status.REJECTED)
    
    def test_approve_review_not_found(self):
        """Should raise error for non-existent review."""
        with self.assertRaises(Review.DoesNotExist):
            approve_review(99999, 'approve')
    
    def test_approve_already_approved(self):
        """Should handle already approved review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Already done',
            status=Review.Status.APPROVED
        )
        
        # Approving again should still work
        result = approve_review(review.id, 'approve')
        self.assertEqual(result.status, Review.Status.APPROVED)

