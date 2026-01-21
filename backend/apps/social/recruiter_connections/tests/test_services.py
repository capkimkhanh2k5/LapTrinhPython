"""
Unit Tests for Recruiter Connections Services

Tests for connection services: send, accept, reject, delete, suggestions.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.social.recruiter_connections.models import RecruiterConnection
from apps.candidate.recruiters.models import Recruiter
from apps.social.recruiter_connections.services.recruiter_connections import (
    SendConnectionInput,
    send_connection_request,
    accept_connection,
    reject_connection,
    delete_connection,
    get_connection_suggestions,
)


User = get_user_model()


class TestSendConnectionRequest(TestCase):
    """Tests for send_connection_request function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            full_name='User One',
            is_active=True
        )
        
        cls.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            full_name='User Two',
            is_active=True
        )
        
        cls.user3 = User.objects.create_user(
            email='user3@example.com',
            password='testpass123',
            full_name='User Three',
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
        
        cls.recruiter3 = Recruiter.objects.create(
            user=cls.user3,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_send_connection_success(self):
        """Should create pending connection request."""
        input_data = SendConnectionInput(
            requester_id=self.recruiter1.id,
            receiver_id=self.recruiter2.id,
            message='Let\'s connect!'
        )
        
        connection = send_connection_request(input_data)
        
        self.assertIsNotNone(connection.id)
        self.assertEqual(connection.status, RecruiterConnection.Status.PENDING)
        self.assertEqual(connection.message, 'Let\'s connect!')
    
    def test_send_connection_to_self_fails(self):
        """Should raise error for self-connection."""
        input_data = SendConnectionInput(
            requester_id=self.recruiter1.id,
            receiver_id=self.recruiter1.id
        )
        
        with self.assertRaises(ValueError) as context:
            send_connection_request(input_data)
        
        self.assertIn('yourself', str(context.exception))
    
    def test_send_duplicate_pending_fails(self):
        """Should raise error for duplicate pending request."""
        RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.PENDING
        )
        
        input_data = SendConnectionInput(
            requester_id=self.recruiter1.id,
            receiver_id=self.recruiter2.id
        )
        
        with self.assertRaises(ValueError) as context:
            send_connection_request(input_data)
        
        self.assertIn('pending', str(context.exception).lower())
    
    def test_send_already_connected_fails(self):
        """Should raise error if already connected."""
        RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        input_data = SendConnectionInput(
            requester_id=self.recruiter1.id,
            receiver_id=self.recruiter2.id
        )
        
        with self.assertRaises(ValueError) as context:
            send_connection_request(input_data)
        
        self.assertIn('connected', str(context.exception).lower())
    
    def test_send_after_rejection_allows_rerequest(self):
        """Should allow re-request after rejection."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.REJECTED
        )
        
        input_data = SendConnectionInput(
            requester_id=self.recruiter1.id,
            receiver_id=self.recruiter2.id,
            message='Please reconsider'
        )
        
        updated = send_connection_request(input_data)
        
        self.assertEqual(updated.id, connection.id)  # Same record updated
        self.assertEqual(updated.status, RecruiterConnection.Status.PENDING)
    
    def test_send_to_blocked_fails(self):
        """Should raise error if blocked."""
        RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.BLOCKED
        )
        
        input_data = SendConnectionInput(
            requester_id=self.recruiter1.id,
            receiver_id=self.recruiter2.id
        )
        
        with self.assertRaises(ValueError) as context:
            send_connection_request(input_data)
        
        self.assertIn('cannot connect', str(context.exception).lower())
    
    def test_send_recruiter_not_found(self):
        """Should raise error for non-existent recruiter."""
        input_data = SendConnectionInput(
            requester_id=self.recruiter1.id,
            receiver_id=99999
        )
        
        with self.assertRaises(Recruiter.DoesNotExist):
            send_connection_request(input_data)


class TestAcceptConnection(TestCase):
    """Tests for accept_connection function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email='accept1@example.com',
            password='testpass123',
            full_name='Accept One',
            is_active=True
        )
        
        cls.user2 = User.objects.create_user(
            email='accept2@example.com',
            password='testpass123',
            full_name='Accept Two',
            is_active=True
        )
        
        cls.recruiter1 = Recruiter.objects.create(
            user=cls.user1,
            years_of_experience=2,
            job_search_status='active'
        )
        
        cls.recruiter2 = Recruiter.objects.create(
            user=cls.user2,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_accept_connection_success(self):
        """Receiver should accept pending connection."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.PENDING
        )
        
        result = accept_connection(connection.id, self.user2.id)
        
        self.assertEqual(result.status, RecruiterConnection.Status.ACCEPTED)
    
    def test_accept_not_receiver_fails(self):
        """Non-receiver should not be able to accept."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.PENDING
        )
        
        with self.assertRaises(PermissionError):
            accept_connection(connection.id, self.user1.id)  # requester trying to accept
    
    def test_accept_already_accepted_fails(self):
        """Should raise error for already accepted connection."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        with self.assertRaises(ValueError) as context:
            accept_connection(connection.id, self.user2.id)
        
        self.assertIn('already', str(context.exception).lower())
    
    def test_accept_not_found_fails(self):
        """Should raise error for non-existent connection."""
        with self.assertRaises(RecruiterConnection.DoesNotExist):
            accept_connection(99999, self.user1.id)


class TestRejectConnection(TestCase):
    """Tests for reject_connection function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email='reject1@example.com',
            password='testpass123',
            full_name='Reject One',
            is_active=True
        )
        
        cls.user2 = User.objects.create_user(
            email='reject2@example.com',
            password='testpass123',
            full_name='Reject Two',
            is_active=True
        )
        
        cls.recruiter1 = Recruiter.objects.create(
            user=cls.user1,
            years_of_experience=2,
            job_search_status='active'
        )
        
        cls.recruiter2 = Recruiter.objects.create(
            user=cls.user2,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_reject_connection_success(self):
        """Receiver should reject pending connection."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.PENDING
        )
        
        result = reject_connection(connection.id, self.user2.id)
        
        self.assertEqual(result.status, RecruiterConnection.Status.REJECTED)
    
    def test_reject_not_receiver_fails(self):
        """Non-receiver should not be able to reject."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.PENDING
        )
        
        with self.assertRaises(PermissionError):
            reject_connection(connection.id, self.user1.id)


class TestDeleteConnection(TestCase):
    """Tests for delete_connection function."""
    
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
        
        cls.user3 = User.objects.create_user(
            email='del3@example.com',
            password='testpass123',
            full_name='Del Three',
            is_active=True
        )
        
        cls.recruiter1 = Recruiter.objects.create(
            user=cls.user1,
            years_of_experience=2,
            job_search_status='active'
        )
        
        cls.recruiter2 = Recruiter.objects.create(
            user=cls.user2,
            years_of_experience=1,
            job_search_status='active'
        )
        
        cls.recruiter3 = Recruiter.objects.create(
            user=cls.user3,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def test_delete_connection_requester(self):
        """Requester should delete connection."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        result = delete_connection(connection.id, self.user1.id)
        
        self.assertTrue(result)
        self.assertFalse(RecruiterConnection.objects.filter(id=connection.id).exists())
    
    def test_delete_connection_receiver(self):
        """Receiver should also be able to delete connection."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        result = delete_connection(connection.id, self.user2.id)
        
        self.assertTrue(result)
    
    def test_delete_connection_not_party_fails(self):
        """Non-party should not delete connection."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        with self.assertRaises(PermissionError):
            delete_connection(connection.id, self.user3.id)


class TestGetConnectionSuggestions(TestCase):
    """Tests for get_connection_suggestions function."""
    
    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email='sug1@example.com',
            password='testpass123',
            full_name='Sug One',
            is_active=True
        )
        
        cls.user2 = User.objects.create_user(
            email='sug2@example.com',
            password='testpass123',
            full_name='Sug Two',
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
    
    def test_get_suggestions_excludes_self(self):
        """Suggestions should not include self."""
        suggestions = get_connection_suggestions(self.recruiter1.id)
        
        recruiter_ids = [s['recruiter'].id for s in suggestions]
        self.assertNotIn(self.recruiter1.id, recruiter_ids)
    
    def test_get_suggestions_excludes_connected(self):
        """Suggestions should not include already connected."""
        RecruiterConnection.objects.create(
            requester=self.recruiter1,
            receiver=self.recruiter2,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        suggestions = get_connection_suggestions(self.recruiter1.id)
        
        recruiter_ids = [s['recruiter'].id for s in suggestions]
        self.assertNotIn(self.recruiter2.id, recruiter_ids)
    
    def test_get_suggestions_respects_limit(self):
        """Should respect limit parameter."""
        suggestions = get_connection_suggestions(self.recruiter1.id, limit=1)
        
        self.assertLessEqual(len(suggestions), 1)
