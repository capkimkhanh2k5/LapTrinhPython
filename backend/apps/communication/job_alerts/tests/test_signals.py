from django.test import TestCase
from unittest.mock import patch
from django.utils import timezone
from apps.recruitment.jobs.models import Job
from apps.company.companies.models import Company
from apps.core.users.models import CustomUser

class JobAlertSignalTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='signal_test@example.com', password='password'
        )
        self.company = Company.objects.create(
            user=self.user, company_name='Tech Co', tax_code='123'
        )

    @patch('apps.communication.job_alerts.signals.process_job_matching_task.delay')
    def test_job_publish_triggers_async_task(self, mock_task):
        """Test publishing a job triggers the async celery task via on_commit"""
        
        # Create Job (Draft)
        job = Job.objects.create(
            company=self.company,
            title='Backend Dev',
            status=Job.Status.DRAFT,
            application_deadline=timezone.now().date(),
            job_type=Job.JobType.FULL_TIME,
            level=Job.Level.JUNIOR,
            description='Test Description',
            requirements='Test Requirements',
            created_by=self.user
        )
        
        # Update to Published within captureOnCommitCallbacks
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            job.status = Job.Status.PUBLISHED
            job.save()
        
        # Verify task was called exactly once with job id
        mock_task.assert_called_once_with(job.id)
