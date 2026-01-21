import pytest
from apps.analytics.selectors import DashboardSelector
from apps.core.users.models import CustomUser
from apps.recruitment.jobs.models import Job
from apps.billing.models import Transaction

@pytest.fixture
def sample_data(db):
    # Create Users
    CustomUser.objects.create_user(email='u1@test.com', password='pwd')
    CustomUser.objects.create_user(email='u2@test.com', password='pwd')
    
    # Create Company for jobs
    from apps.company.companies.models import Company
    company = Company.objects.create(company_name="Test Corp", slug="test-corp")
    
    # Create Jobs
    user = CustomUser.objects.first()
    Job.objects.create(title='J1', slug='j1', created_by=user, company=company, status=Job.Status.PUBLISHED)
    Job.objects.create(title='J2', slug='j2', created_by=user, company=company, status=Job.Status.DRAFT)
    
    # Create Transactions
    Transaction.objects.create(company=company, amount=100.00, status='completed') 
    Transaction.objects.create(company=company, amount=50.00, status='pending')

@pytest.mark.django_db
def test_admin_dashboard_stats(sample_data):
    stats = DashboardSelector.get_admin_overview()
    
    assert stats['users']['total'] == 2
    assert stats['jobs']['total'] == 2
    assert stats['jobs']['active'] == 1
    assert float(stats['revenue']['total']) == 100.00
