import pytest
from apps.communication.job_alerts.models import JobAlert, JobAlertMatch
from apps.communication.job_alerts.services.matching import JobMatchingService
from apps.recruitment.jobs.models import Job
from apps.recruitment.job_categories.models import JobCategory
from apps.geography.provinces.models import Province
from apps.geography.addresses.models import Address
from apps.company.companies.models import Company
from django.contrib.auth import get_user_model
from apps.candidate.recruiters.models import Recruiter

User = get_user_model()

@pytest.fixture
def user():
    return User.objects.create_user(email='user@test.com', password='password', full_name='Test', role='recruiter')

@pytest.fixture
def recruiter_profile(user):
    return Recruiter.objects.create(user=user)

@pytest.fixture
def category():
    return JobCategory.objects.create(name="IT", slug="it")

@pytest.fixture
def province_a():
    return Province.objects.create(province_name="HCM", province_code="79")

@pytest.fixture
def province_b():
    return Province.objects.create(province_name="Hanoi", province_code="01")

@pytest.fixture
def company(user):
    return Company.objects.create(company_name="Test Co")

@pytest.fixture
def address_hcm(province_a):
    return Address.objects.create(address_line="D1", province=province_a)

@pytest.mark.django_db
class TestJobMatchingService:
    
    def test_basic_matching(self, recruiter_profile, category, province_a, company, address_hcm, user):
        # Create Alert
        alert = JobAlert.objects.create(
            recruiter=recruiter_profile,
            alert_name="HCM Job",
            category=category,
            salary_min=10000000
        )
        alert.locations.add(province_a)
        
        # Create Matching Job
        job_match = Job.objects.create(
            title="Match", slug="match",
            company=company,
            category=category,
            address=address_hcm,
            salary_min=10000000,
            salary_max=15000000, # Max >= Alert Min (10tr)
            status=Job.Status.PUBLISHED,
            created_by=user,
            description="desc", requirements="req"
        )
        
        matches = JobMatchingService.find_alerts_for_job(job_match)
        assert len(matches) == 1
        assert matches[0].id == alert.id

    def test_salary_mismatch(self, recruiter_profile, category, province_a, company, address_hcm, user):
        # Alert expects min 20tr
        alert = JobAlert.objects.create(
            recruiter=recruiter_profile, alert_name="High Salary",
            category=category, salary_min=20000000
        )
        
        # Job offers max 15tr
        job_low = Job.objects.create(
            title="Low Salary", slug="low",
            company=company, category=category, address=address_hcm,
            salary_min=10000000, salary_max=15000000,
            status=Job.Status.PUBLISHED, created_by=user,
            description="desc", requirements="req"
        )
        
        matches = JobMatchingService.find_alerts_for_job(job_low)
        assert len(matches) == 0

    def test_location_mismatch(self, recruiter_profile, category, province_b, company, address_hcm, user):
        # Alert expects Hanoi (province_b)
        alert = JobAlert.objects.create(
            recruiter=recruiter_profile, alert_name="Hanoi Job",
            category=category,
        )
        alert.locations.add(province_b)
        
        # Job is in HCM (address_hcm use province_a)
        job_hcm = Job.objects.create(
            title="HCM Job", slug="hcm",
            company=company, category=category, address=address_hcm,
            status=Job.Status.PUBLISHED, created_by=user,
            description="desc", requirements="req"
        )
        
        matches = JobMatchingService.find_alerts_for_job(job_hcm)
        assert len(matches) == 0

    def test_signal_integration(self, recruiter_profile, category, province_a, company, address_hcm, user):
        # Alert setup
        alert = JobAlert.objects.create(
            recruiter=recruiter_profile,
            alert_name="Signal Test",
            category=category
        )
        alert.locations.add(province_a)
        
        # Create Job -> Signal should trigger matching -> Create JobAlertMatch
        job = Job.objects.create(
            title="Signal Job", slug="signal",
            company=company, category=category, address=address_hcm,
            status=Job.Status.PUBLISHED, created_by=user,
            description="desc", requirements="req"
        )
        
        # Check if Match record created
        assert JobAlertMatch.objects.filter(job=job, job_alert=alert).exists()
    def test_level_matching(self, recruiter_profile, category, province_a, company, address_hcm, user):
        alert_senior = JobAlert.objects.create(recruiter=recruiter_profile, alert_name="Senior", category=category, level='senior')
        alert_junior = JobAlert.objects.create(recruiter=recruiter_profile, alert_name="Junior", category=category, level='junior')
        alert_senior.locations.add(province_a)
        alert_junior.locations.add(province_a)

        job_senior = Job.objects.create(
            title="Senior Job", slug="senior", company=company, category=category, address=address_hcm,
            level='senior', status=Job.Status.PUBLISHED, created_by=user, description="d", requirements="r"
        )

        matches = JobMatchingService.find_alerts_for_job(job_senior)
        match_ids = [a.id for a in matches]
        assert alert_senior.id in match_ids
        assert alert_junior.id not in match_ids

    def test_job_type_matching(self, recruiter_profile, category, province_a, company, address_hcm, user):
        alert_ft = JobAlert.objects.create(recruiter=recruiter_profile, alert_name="Fulltime", category=category, job_type='full-time')
        alert_pt = JobAlert.objects.create(recruiter=recruiter_profile, alert_name="Parttime", category=category, job_type='part-time')
        alert_ft.locations.add(province_a)
        alert_pt.locations.add(province_a)

        job_ft = Job.objects.create(
            title="FT Job", slug="ft", company=company, category=category, address=address_hcm,
            job_type='full-time', status=Job.Status.PUBLISHED, created_by=user, description="d", requirements="r"
        )
        
        matches = JobMatchingService.find_alerts_for_job(job_ft)
        match_ids = [a.id for a in matches]
        assert alert_ft.id in match_ids
        assert alert_pt.id not in match_ids

    def test_matching_with_no_location_preference(self, recruiter_profile, category, company, address_hcm, user):
        # Alert with NO specific location (should match anywhere?)
        # Based on logic: filter(Q(locations=job_prov) | Q(locations__isnull=True))
        alert_anywhere = JobAlert.objects.create(recruiter=recruiter_profile, alert_name="Anywhere", category=category)
        
        job_hcm = Job.objects.create(
            title="HCM Job", slug="hcm-any", company=company, category=category, address=address_hcm,
            status=Job.Status.PUBLISHED, created_by=user, description="d", requirements="r"
        )
        
        matches = JobMatchingService.find_alerts_for_job(job_hcm)
        assert alert_anywhere.id in [a.id for a in matches]

    def test_duplicate_match_prevention(self, recruiter_profile, category, province_a, company, address_hcm, user):
        # Ensure record_match doesn't create duplicate DB entries for same pair
        alert = JobAlert.objects.create(recruiter=recruiter_profile, alert_name="Dup Test", category=category)
        alert.locations.add(province_a)
        
        job = Job.objects.create(
            title="Job Dup", slug="dup", company=company, category=category, address=address_hcm,
            status=Job.Status.PUBLISHED, created_by=user, description="abc", requirements="xyz"
        )
        
        # Match 1st time
        match1 = JobMatchingService.record_match(alert, job)
        # Match 2nd time
        match2 = JobMatchingService.record_match(alert, job)
        
        assert match1.id == match2.id
        assert JobAlertMatch.objects.filter(job_alert=alert, job=job).count() == 1
