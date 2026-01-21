"""
API Integration Tests for Reviews

Tests for all 10 Reviews API endpoints.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.social.reviews.models import Review
from apps.company.companies.models import Company
from apps.candidate.recruiters.models import Recruiter


User = get_user_model()


class ReviewsAPITestCase(APITestCase):
    """Base test case with common setup."""
    
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123',
            full_name='Admin User',
            is_staff=True
        )
        
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
        
        cls.other_recruiter = Recruiter.objects.create(
            user=cls.other_user,
            years_of_experience=2,
            job_search_status='active'
        )
    
    def setUp(self):
        self.client.force_authenticate(user=self.user)


class TestCompanyReviewsListView(ReviewsAPITestCase):
    """Tests for GET /api/companies/:id/reviews/"""
    
    def test_list_reviews_success(self):
        """Should list approved reviews."""
        Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Great',
            status=Review.Status.APPROVED
        )
        
        response = self.client.get(f'/api/companies/{self.company.id}/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['reviews']), 1)
        self.assertIn('stats', response.data)
    
    def test_list_reviews_excludes_pending(self):
        """Should not show pending reviews."""
        Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='Pending',
            status=Review.Status.PENDING
        )
        
        self.client.logout()
        response = self.client.get(f'/api/companies/{self.company.id}/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['reviews']), 0)
    
    def test_list_reviews_company_not_found(self):
        """Should return 404 for non-existent company."""
        response = self.client.get('/api/companies/99999/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestCompanyReviewsCreateView(ReviewsAPITestCase):
    """Tests for POST /api/companies/:id/reviews/"""
    
    def test_create_review_success(self):
        """Should create a new review."""
        data = {
            'rating': 4,
            'title': 'Great place',
            'content': 'I enjoyed working here',
            'pros': 'Good culture',
            'cons': 'Long hours'
        }
        
        response = self.client.post(
            f'/api/companies/{self.company.id}/reviews/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['rating'], 4)
        self.assertEqual(response.data['status'], 'pending')
    
    def test_create_review_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()
        data = {'rating': 4, 'content': 'Test'}
        
        response = self.client.post(
            f'/api/companies/{self.company.id}/reviews/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_review_invalid_rating(self):
        """Should reject invalid rating."""
        data = {'rating': 6, 'content': 'Test'}
        
        response = self.client.post(
            f'/api/companies/{self.company.id}/reviews/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestReviewDetailView(ReviewsAPITestCase):
    """Tests for GET/PUT/DELETE /api/reviews/:id/"""
    
    def test_get_detail_success(self):
        """Should get review detail."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Detail test',
            status=Review.Status.APPROVED
        )
        
        response = self.client.get(f'/api/reviews/{review.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 4)
    
    def test_update_own_review(self):
        """Should update own review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='Original'
        )
        
        data = {'rating': 5, 'content': 'Updated'}
        response = self.client.put(f'/api/reviews/{review.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5)
    
    def test_update_other_review_returns_error(self):
        """Should not update other's review - returns 400 for ownership error."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.other_recruiter,
            rating=3,
            content='Other'
        )
        
        data = {'rating': 1}
        response = self.client.put(f'/api/reviews/{review.id}/', data, format='json')
        
        # View returns 400 for permission errors wrapped in validation
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
    
    def test_delete_own_review(self):
        """Should delete own review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=3,
            content='To delete'
        )
        
        response = self.client.delete(f'/api/reviews/{review.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestReviewHelpfulView(ReviewsAPITestCase):
    """Tests for POST /api/reviews/:id/helpful/"""
    
    def test_mark_helpful_toggle(self):
        """Should toggle helpful mark."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.other_recruiter,
            rating=4,
            content='Helpful',
            helpful_count=0
        )
        
        # Mark as helpful
        response = self.client.post(f'/api/reviews/{review.id}/helpful/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_helpful'])
        
        # Unmark
        response = self.client.post(f'/api/reviews/{review.id}/helpful/')
        self.assertFalse(response.data['is_helpful'])


class TestReviewReportView(ReviewsAPITestCase):
    """Tests for POST /api/reviews/:id/report/"""
    
    def test_report_review_success(self):
        """Should report a review."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.other_recruiter,
            rating=1,
            content='Bad'
        )
        
        data = {'reason': 'Inappropriate content'}
        response = self.client.post(f'/api/reviews/{review.id}/report/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['reported'])


class TestReviewApproveView(ReviewsAPITestCase):
    """Tests for PATCH /api/reviews/:id/approve/"""
    
    def test_approve_review_admin(self):
        """Admin should approve review."""
        self.client.force_authenticate(user=self.admin)
        
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Pending',
            status=Review.Status.PENDING
        )
        
        data = {'action': 'approve'}
        response = self.client.patch(f'/api/reviews/{review.id}/approve/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'approved')
    
    def test_approve_review_non_admin_forbidden(self):
        """Non-admin should not approve."""
        review = Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Pending'
        )
        
        data = {'action': 'approve'}
        response = self.client.patch(f'/api/reviews/{review.id}/approve/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestPendingReviewsView(ReviewsAPITestCase):
    """Tests for GET /api/reviews/pending/"""
    
    def test_list_pending_admin(self):
        """Admin should see pending reviews."""
        self.client.force_authenticate(user=self.admin)
        
        Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='Pending',
            status=Review.Status.PENDING
        )
        
        response = self.client.get('/api/reviews/pending/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['reviews']), 1)
    
    def test_list_pending_non_admin_forbidden(self):
        """Non-admin should not see pending."""
        response = self.client.get('/api/reviews/pending/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestRecruiterReviewsView(ReviewsAPITestCase):
    """Tests for GET /api/recruiters/:id/reviews/"""
    
    def test_get_own_reviews(self):
        """Should get own reviews."""
        Review.objects.create(
            company=self.company,
            recruiter=self.recruiter,
            rating=4,
            content='My review'
        )
        
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['reviews']), 1)
    
    def test_get_other_reviews_forbidden(self):
        """Should not see other's reviews."""
        response = self.client.get(f'/api/recruiters/{self.other_recruiter.id}/reviews/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
