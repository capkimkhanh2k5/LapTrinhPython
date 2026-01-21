"""
Unit Tests for Recommendations Services

Tests for recommendation services: create, update, delete, toggle_visibility.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.social.recommendations.models import Recommendation
from apps.candidate.recruiters.models import Recruiter
from apps.social.recommendations.services.recommendations import (
    CreateRecommendationInput,
    UpdateRecommendationInput,
    create_recommendation,
    update_recommendation,
    delete_recommendation,
    toggle_visibility,
)


User = get_user_model()


class TestCreateRecommendation(TestCase):
    """Tests for create_recommendation function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email='rec1@example.com',
            password='testpass123',
            full_name='Rec One',
            is_active=True
        )
        
        cls.user2 = User.objects.create_user(
            email='rec2@example.com',
            password='testpass123',
            full_name='Rec Two',
            is_active=True
        )
        
        cls.recruiter1 = Recruiter.objects.create(
            user=cls.user1,
            years_of_experience=3,
            job_search_status='active'
        )
        
        cls.recruiter2 = Recruiter.objects.create(
            user=cls.user2,
            years_of_experience=2,
            job_search_status='active'
        )
    
    def test_create_recommendation_success(self):
        """Should create a new recommendation."""
        input_data = CreateRecommendationInput(
            recruiter_id=self.recruiter2.id,
            recommender_id=self.user1.id,
            relationship='Former colleague',
            content='Excellent developer!'
        )
        
        recommendation = create_recommendation(input_data)
        
        self.assertIsNotNone(recommendation.id)
        self.assertEqual(recommendation.content, 'Excellent developer!')
        self.assertEqual(recommendation.relationship, 'Former colleague')
        self.assertTrue(recommendation.is_visible)
    
    def test_create_self_recommendation_fails(self):
        """Should raise error for self-recommendation."""
        input_data = CreateRecommendationInput(
            recruiter_id=self.recruiter1.id,
            recommender_id=self.user1.id,  # Same user
            content='I am great!'
        )
        
        with self.assertRaises(ValueError) as context:
            create_recommendation(input_data)
        
        self.assertIn('yourself', str(context.exception).lower())
    
    def test_create_duplicate_recommendation_fails(self):
        """Should raise error for duplicate recommendation."""
        Recommendation.objects.create(
            recruiter=self.recruiter2,
            recommender=self.user1,
            content='Already written'
        )
        
        input_data = CreateRecommendationInput(
            recruiter_id=self.recruiter2.id,
            recommender_id=self.user1.id,
            content='Another one'
        )
        
        with self.assertRaises(ValueError) as context:
            create_recommendation(input_data)
        
        self.assertIn('already', str(context.exception).lower())
    
    def test_create_recruiter_not_found_fails(self):
        """Should raise error for non-existent recruiter."""
        input_data = CreateRecommendationInput(
            recruiter_id=99999,
            recommender_id=self.user1.id,
            content='Test'
        )
        
        with self.assertRaises(Recruiter.DoesNotExist):
            create_recommendation(input_data)
    
    def test_create_recommender_not_found_fails(self):
        """Should raise error for non-existent recommender."""
        input_data = CreateRecommendationInput(
            recruiter_id=self.recruiter2.id,
            recommender_id=99999,
            content='Test'
        )
        
        with self.assertRaises(User.DoesNotExist):
            create_recommendation(input_data)


class TestUpdateRecommendation(TestCase):
    """Tests for update_recommendation function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email='upd1@example.com',
            password='testpass123',
            full_name='Upd One',
            is_active=True
        )
        
        cls.user2 = User.objects.create_user(
            email='upd2@example.com',
            password='testpass123',
            full_name='Upd Two',
            is_active=True
        )
        
        cls.recruiter1 = Recruiter.objects.create(
            user=cls.user1,
            years_of_experience=3,
            job_search_status='active'
        )
        
        cls.recruiter2 = Recruiter.objects.create(
            user=cls.user2,
            years_of_experience=2,
            job_search_status='active'
        )
    
    def test_update_recommendation_success(self):
        """Should update own recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter2,
            recommender=self.user1,
            content='Original',
            relationship='Colleague'
        )
        
        input_data = UpdateRecommendationInput(
            recommendation_id=recommendation.id,
            user_id=self.user1.id,
            content='Updated content',
            relationship='Former manager'
        )
        
        updated = update_recommendation(input_data)
        
        self.assertEqual(updated.content, 'Updated content')
        self.assertEqual(updated.relationship, 'Former manager')
    
    def test_update_not_owner_fails(self):
        """Should raise error when updating other's recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter1,
            recommender=self.user2,
            content='Original'
        )
        
        input_data = UpdateRecommendationInput(
            recommendation_id=recommendation.id,
            user_id=self.user1.id,  # Not the recommender
            content='Hacked!'
        )
        
        with self.assertRaises(PermissionError):
            update_recommendation(input_data)
    
    def test_update_partial_fields(self):
        """Should update only provided fields."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter2,
            recommender=self.user1,
            content='Original',
            relationship='Colleague'
        )
        
        input_data = UpdateRecommendationInput(
            recommendation_id=recommendation.id,
            user_id=self.user1.id,
            content='New content'  # Only content updated
        )
        
        updated = update_recommendation(input_data)
        
        self.assertEqual(updated.content, 'New content')
        self.assertEqual(updated.relationship, 'Colleague')  # Unchanged
    
    def test_update_not_found_fails(self):
        """Should raise error for non-existent recommendation."""
        input_data = UpdateRecommendationInput(
            recommendation_id=99999,
            user_id=self.user1.id,
            content='Test'
        )
        
        with self.assertRaises(Recommendation.DoesNotExist):
            update_recommendation(input_data)


class TestDeleteRecommendation(TestCase):
    """Tests for delete_recommendation function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email='del1@example.com',
            password='testpass123',
            full_name='Del One',
            is_active=True
        )
        
        cls.user2 = User.objects.create_user(
            email='del2@example.com',
            password='testpass123',
            full_name='Del Two',
            is_active=True
        )
        
        cls.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass',
            full_name='Admin'
        )
        
        cls.recruiter1 = Recruiter.objects.create(
            user=cls.user1,
            years_of_experience=3,
            job_search_status='active'
        )
        
        cls.recruiter2 = Recruiter.objects.create(
            user=cls.user2,
            years_of_experience=2,
            job_search_status='active'
        )
    
    def test_delete_own_recommendation(self):
        """Owner (recommender) should delete."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter2,
            recommender=self.user1,
            content='To delete'
        )
        
        result = delete_recommendation(recommendation.id, self.user1.id, is_admin=False)
        
        self.assertTrue(result)
        self.assertFalse(Recommendation.objects.filter(id=recommendation.id).exists())
    
    def test_delete_admin(self):
        """Admin should delete any recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter2,
            recommender=self.user1,
            content='Admin delete'
        )
        
        result = delete_recommendation(recommendation.id, self.admin.id, is_admin=True)
        
        self.assertTrue(result)
    
    def test_delete_not_owner_fails(self):
        """Non-owner should not delete."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter1,
            recommender=self.user2,
            content='Not mine'
        )
        
        with self.assertRaises(PermissionError):
            delete_recommendation(recommendation.id, self.user1.id, is_admin=False)


class TestToggleVisibility(TestCase):
    """Tests for toggle_visibility function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email='vis1@example.com',
            password='testpass123',
            full_name='Vis One',
            is_active=True
        )
        
        cls.user2 = User.objects.create_user(
            email='vis2@example.com',
            password='testpass123',
            full_name='Vis Two',
            is_active=True
        )
        
        cls.recruiter1 = Recruiter.objects.create(
            user=cls.user1,
            years_of_experience=3,
            job_search_status='active'
        )
        
        cls.recruiter2 = Recruiter.objects.create(
            user=cls.user2,
            years_of_experience=2,
            job_search_status='active'
        )
    
    def test_toggle_visibility_hide(self):
        """Recipient should hide recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter1,
            recommender=self.user2,
            content='Visible',
            is_visible=True
        )
        
        result = toggle_visibility(recommendation.id, self.recruiter1.id, False)
        
        self.assertFalse(result.is_visible)
    
    def test_toggle_visibility_show(self):
        """Recipient should show hidden recommendation."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter1,
            recommender=self.user2,
            content='Hidden',
            is_visible=False
        )
        
        result = toggle_visibility(recommendation.id, self.recruiter1.id, True)
        
        self.assertTrue(result.is_visible)
    
    def test_toggle_visibility_not_recipient_fails(self):
        """Non-recipient should not toggle visibility."""
        recommendation = Recommendation.objects.create(
            recruiter=self.recruiter1,
            recommender=self.user2,
            content='Not mine'
        )
        
        with self.assertRaises(PermissionError):
            toggle_visibility(recommendation.id, self.recruiter2.id, False)
    
    def test_toggle_visibility_not_found_fails(self):
        """Should raise error for non-existent recommendation."""
        with self.assertRaises(Recommendation.DoesNotExist):
            toggle_visibility(99999, self.recruiter1.id, False)
