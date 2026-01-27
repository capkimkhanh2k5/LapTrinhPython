from django.test import TestCase
from rest_framework.test import APIRequestFactory
from apps.core.users.models import CustomUser
from apps.company.companies.models import Company
from apps.recruitment.jobs.models import Job
from apps.recruitment.campaigns.serializers import CampaignJobAddSerializer

class CampaignValidationTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        
        # User & Company
        self.user = CustomUser.objects.create(email='recruiter@test.com')
        self.company = Company.objects.create(user=self.user, company_name='My Company', slug='my-co')
        
        # Other User & Company
        self.other_user = CustomUser.objects.create(email='other@test.com')
        self.other_company = Company.objects.create(user=self.other_user, company_name='Other Company', slug='other-co')
        
        # Jobs
        self.job_valid = Job.objects.create(
            company=self.company, 
            title='Valid Job', 
            slug='valid-job',
            status=Job.Status.PUBLISHED,
            created_by=self.user
        )
        self.job_draft = Job.objects.create(
            company=self.company, 
            title='Draft Job', 
            slug='draft-job',
            status=Job.Status.DRAFT,
            created_by=self.user
        )
        self.job_other = Job.objects.create(
            company=self.other_company, 
            title='Other Job', 
            slug='other-job',
            status=Job.Status.PUBLISHED,
            created_by=self.other_user
        )

    def test_valid_jobs(self):
        """Test adding valid published jobs owned by user"""
        data = {'job_ids': [self.job_valid.id]}
        
        # Mock request context
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = CampaignJobAddSerializer(data=data, context={'request': request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_invalid_ownership(self):
        """Test adding job from another company"""
        data = {'job_ids': [self.job_other.id]}
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = CampaignJobAddSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('job_ids', serializer.errors)
        self.assertIn('One or more jobs are invalid', str(serializer.errors['job_ids']))

    def test_invalid_status(self):
        """Test adding draft job"""
        data = {'job_ids': [self.job_draft.id]}
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = CampaignJobAddSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('One or more jobs are invalid', str(serializer.errors['job_ids']))

    def test_mixed_validity(self):
        """Test mix of valid and invalid jobs (Should fail all)"""
        data = {'job_ids': [self.job_valid.id, self.job_other.id]}
        
        request = self.factory.post('/')
        request.user = self.user
        
        serializer = CampaignJobAddSerializer(data=data, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('One or more jobs are invalid', str(serializer.errors['job_ids']))
