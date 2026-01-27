from django.test import TestCase
from apps.analytics.selectors import DashboardSelector
from apps.core.users.models import CustomUser
from apps.recruitment.jobs.models import Job
from apps.billing.models import Transaction
from apps.company.companies.models import Company

class TestAnalyticsServices(TestCase):
    def setUp(self):
        # Create Users
        CustomUser.objects.create_user(email='u1@test.com', password='pwd')
        CustomUser.objects.create_user(email='u2@test.com', password='pwd')
        
        # Create Company for jobs
        self.company = Company.objects.create(company_name="Test Corp", slug="test-corp")
        
        # Create Jobs
        user = CustomUser.objects.first()
        Job.objects.create(title='J1', slug='j1', created_by=user, company=self.company, status=Job.Status.PUBLISHED)
        Job.objects.create(title='J2', slug='j2', created_by=user, company=self.company, status=Job.Status.DRAFT)
        
        # Create Transactions
        Transaction.objects.create(company=self.company, amount=100.00, status='completed') 
        Transaction.objects.create(company=self.company, amount=50.00, status='pending')

    def test_admin_dashboard_stats(self):
        stats = DashboardSelector.get_admin_overview()
        
        self.assertEqual(stats['users']['total'], 2)
        self.assertEqual(stats['jobs']['total'], 2)
        self.assertEqual(stats['jobs']['active'], 1)
        self.assertEqual(float(stats['revenue']['total']), 100.00)
