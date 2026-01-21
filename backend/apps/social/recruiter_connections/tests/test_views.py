"""
API Integration Tests for Recruiter Connections

Tests for 7 Connections API endpoints.
"""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.social.recruiter_connections.models import RecruiterConnection
from apps.candidate.recruiters.models import Recruiter


User = get_user_model()


class ConnectionsAPITestCase(APITestCase):
    """Base test case with common setup."""
    
    @classmethod
    def setUpTestData(cls):
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
        
        cls.third_user = User.objects.create_user(
            email='third@example.com',
            password='thirdpass123',
            full_name='Third User',
            is_active=True
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
        
        cls.third_recruiter = Recruiter.objects.create(
            user=cls.third_user,
            years_of_experience=1,
            job_search_status='active'
        )
    
    def setUp(self):
        self.client.force_authenticate(user=self.user)


class TestRecruiterConnectionsView(ConnectionsAPITestCase):
    """Tests for GET /api/recruiters/:id/connections/"""
    
    def test_list_connections_success(self):
        """Should list accepted connections."""
        RecruiterConnection.objects.create(
            requester=self.recruiter,
            receiver=self.other_recruiter,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/connections/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['connections']), 1)
        self.assertIn('counts', response.data)
    
    def test_list_connections_forbidden(self):
        """Should not see other's connections."""
        response = self.client.get(f'/api/recruiters/{self.other_recruiter.id}/connections/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_connections_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/connections/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_connections_recruiter_not_found(self):
        """Should return 404 for non-existent recruiter."""
        response = self.client.get('/api/recruiters/99999/connections/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_list_connections_filter_by_status(self):
        """Should filter by status parameter."""
        RecruiterConnection.objects.create(
            requester=self.recruiter,
            receiver=self.other_recruiter,
            status=RecruiterConnection.Status.PENDING
        )
        
        response = self.client.get(f'/api/recruiters/{self.recruiter.id}/connections/?status=pending')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['connections']), 1)


class TestSendConnectionView(ConnectionsAPITestCase):
    """Tests for POST /api/recruiters/:id/connect/"""
    
    def test_send_connection_success(self):
        """Should send connection request."""
        data = {'message': 'Let\'s connect!'}
        
        response = self.client.post(
            f'/api/recruiters/{self.other_recruiter.id}/connect/', data, format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
    
    def test_send_connection_to_self(self):
        """Should reject self-connection."""
        response = self.client.post(f'/api/recruiters/{self.recruiter.id}/connect/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_send_duplicate_connection(self):
        """Should reject duplicate pending request."""
        RecruiterConnection.objects.create(
            requester=self.recruiter,
            receiver=self.other_recruiter,
            status=RecruiterConnection.Status.PENDING
        )
        
        response = self.client.post(f'/api/recruiters/{self.other_recruiter.id}/connect/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_send_already_connected(self):
        """Should reject if already connected."""
        RecruiterConnection.objects.create(
            requester=self.recruiter,
            receiver=self.other_recruiter,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        response = self.client.post(f'/api/recruiters/{self.other_recruiter.id}/connect/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_send_connection_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()
        response = self.client.post(f'/api/recruiters/{self.other_recruiter.id}/connect/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_send_connection_recruiter_not_found(self):
        """Should return 404 for non-existent receiver."""
        response = self.client.post('/api/recruiters/99999/connect/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestAcceptConnectionView(ConnectionsAPITestCase):
    """Tests for PATCH /api/connections/:id/accept/"""
    
    def test_accept_connection_success(self):
        """Receiver should accept."""
        connection = RecruiterConnection.objects.create(
            requester=self.other_recruiter,
            receiver=self.recruiter,
            status=RecruiterConnection.Status.PENDING
        )
        
        response = self.client.patch(f'/api/connections/{connection.id}/accept/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'accepted')
    
    def test_accept_not_receiver(self):
        """Non-receiver should not accept."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter,
            receiver=self.other_recruiter,
            status=RecruiterConnection.Status.PENDING
        )
        
        response = self.client.patch(f'/api/connections/{connection.id}/accept/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_accept_already_accepted(self):
        """Should reject already accepted connection."""
        connection = RecruiterConnection.objects.create(
            requester=self.other_recruiter,
            receiver=self.recruiter,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        response = self.client.patch(f'/api/connections/{connection.id}/accept/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_accept_not_found(self):
        """Should return 404 for non-existent connection."""
        response = self.client.patch('/api/connections/99999/accept/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRejectConnectionView(ConnectionsAPITestCase):
    """Tests for PATCH /api/connections/:id/reject/"""
    
    def test_reject_connection_success(self):
        """Receiver should reject."""
        connection = RecruiterConnection.objects.create(
            requester=self.other_recruiter,
            receiver=self.recruiter,
            status=RecruiterConnection.Status.PENDING
        )
        
        response = self.client.patch(f'/api/connections/{connection.id}/reject/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')
    
    def test_reject_not_receiver(self):
        """Non-receiver should not reject."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter,
            receiver=self.other_recruiter,
            status=RecruiterConnection.Status.PENDING
        )
        
        response = self.client.patch(f'/api/connections/{connection.id}/reject/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_reject_not_found(self):
        """Should return 404 for non-existent connection."""
        response = self.client.patch('/api/connections/99999/reject/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestDeleteConnectionView(ConnectionsAPITestCase):
    """Tests for DELETE /api/connections/:id/"""
    
    def test_delete_connection_requester(self):
        """Requester can delete."""
        connection = RecruiterConnection.objects.create(
            requester=self.recruiter,
            receiver=self.other_recruiter,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        response = self.client.delete(f'/api/connections/{connection.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_delete_connection_receiver(self):
        """Receiver can also delete."""
        connection = RecruiterConnection.objects.create(
            requester=self.other_recruiter,
            receiver=self.recruiter,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        response = self.client.delete(f'/api/connections/{connection.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_delete_connection_not_party(self):
        """Non-party should not delete."""
        connection = RecruiterConnection.objects.create(
            requester=self.other_recruiter,
            receiver=self.third_recruiter,
            status=RecruiterConnection.Status.ACCEPTED
        )
        
        response = self.client.delete(f'/api/connections/{connection.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_not_found(self):
        """Should return 404 for non-existent connection."""
        response = self.client.delete('/api/connections/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestPendingConnectionsView(ConnectionsAPITestCase):
    """Tests for GET /api/connections/pending/"""
    
    def test_list_pending_received(self):
        """Should list pending requests received."""
        RecruiterConnection.objects.create(
            requester=self.other_recruiter,
            receiver=self.recruiter,
            status=RecruiterConnection.Status.PENDING
        )
        
        response = self.client.get('/api/connections/pending/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['pending_requests']), 1)
    
    def test_list_pending_excludes_sent(self):
        """Should not include sent requests."""
        RecruiterConnection.objects.create(
            requester=self.recruiter,
            receiver=self.other_recruiter,
            status=RecruiterConnection.Status.PENDING
        )
        
        response = self.client.get('/api/connections/pending/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['pending_requests']), 0)
    
    def test_list_pending_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()
        response = self.client.get('/api/connections/pending/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestConnectionSuggestionsView(ConnectionsAPITestCase):
    """Tests for GET /api/connections/suggestions/"""
    
    def test_get_suggestions_success(self):
        """Should get suggestions."""
        response = self.client.get('/api/connections/suggestions/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)
    
    def test_get_suggestions_with_limit(self):
        """Should respect limit parameter."""
        response = self.client.get('/api/connections/suggestions/?limit=5')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['suggestions']), 5)
    
    def test_get_suggestions_unauthenticated(self):
        """Should require authentication."""
        self.client.logout()
        response = self.client.get('/api/connections/suggestions/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

