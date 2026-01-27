from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.core.users.models import CustomUser
from apps.company.companies.models import Company
from apps.blog.models import Post

class CompanyBlogTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # 1. Company Owner
        self.owner = CustomUser.objects.create(email='owner@test.com', full_name='Owner')
        self.company = Company.objects.create(user=self.owner, company_name='Owner Co', slug='owner-co')
        
        # 2. Regular User (Freelancer)
        self.freelancer = CustomUser.objects.create(email='free@test.com', full_name='Free')
        
        # 3. Admin
        self.admin = CustomUser.objects.create_superuser(email='admin@test.com', password='pwd')

    def test_create_post_company_owner(self):
        """Owner's post should be linked to Company and Draft by default"""
        self.client.force_authenticate(user=self.owner)
        data = {
            'title': 'Company Culture',
            'content': 'We are great.',
            'summary': 'Summary'
        }
        response = self.client.post('/api/blog/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        post = Post.objects.get(id=response.data['id'])
        self.assertEqual(post.author, self.owner)
        self.assertEqual(post.company, self.company)
        self.assertEqual(post.status, Post.Status.DRAFT)

    def test_create_post_freelancer(self):
        """Freelancer's post has no company"""
        self.client.force_authenticate(user=self.freelancer)
        data = {
            'title': 'My Freelance Journey',
            'content': 'It is hard.',
            'summary': 'Summary'
        }
        response = self.client.post('/api/blog/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        post = Post.objects.get(id=response.data['id'])
        self.assertEqual(post.author, self.freelancer)
        self.assertIsNone(post.company)
        self.assertEqual(post.status, Post.Status.DRAFT)

    def test_create_post_admin(self):
        """Admin can publish immediately"""
        self.client.force_authenticate(user=self.admin)
        data = {
            'title': 'Official News',
            'content': 'Update available.',
            'status': Post.Status.PUBLISHED
        }
        response = self.client.post('/api/blog/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        post = Post.objects.get(id=response.data['id'])
        self.assertEqual(post.status, Post.Status.PUBLISHED)
