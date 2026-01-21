from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from ..models import JobSearchHistory

User = get_user_model()

class JobSearchHistoryViewSetTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            password='password123',
            first_name='Searcher',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='password123'
        )
        
        # Create history for user
        self.item1 = JobSearchHistory.objects.create(
            user=self.user,
            search_query='Python Developer',
            results_count=10
        )
        self.item2 = JobSearchHistory.objects.create(
            user=self.user,
            search_query='Django',
            results_count=5
        )
        
        # Create history for other user
        JobSearchHistory.objects.create(
            user=self.other_user,
            search_query='Java',
            results_count=2
        )
        
        self.list_url = reverse('search-history-list')
        self.clear_url = reverse('search-history-clear')

    def test_list_history(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should see 2 items
        self.assertEqual(len(response.data), 2)
        # Should not see other user's history
        queries = [item['search_query'] for item in response.data]
        self.assertIn('Python Developer', queries)
        self.assertNotIn('Java', queries)

    def test_delete_item(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('search-history-detail', args=[self.item1.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(JobSearchHistory.objects.filter(user=self.user).count(), 1)

    def test_clear_history(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.clear_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(JobSearchHistory.objects.filter(user=self.user).count(), 0)
