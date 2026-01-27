from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.recruitment.referrals.services.referrals import ReferralService, ProgramCreateInput, ReferralCreateInput
from apps.recruitment.referrals.models import ReferralProgram, Referral
from apps.recruitment.referrals.selectors.referrals import ReferralSelector
from apps.company.companies.models import Company
from apps.recruitment.job_categories.models import JobCategory
from apps.recruitment.jobs.models import Job

User = get_user_model()

class TestReferralService(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='company@test.com',
            password='password123',
            full_name='Test Company',
            role='employer'
        )
        self.company = Company.objects.create(
            user=self.user,
            company_name="Test Company",
            slug="test-company"
        )
        self.category = JobCategory.objects.create(name="IT Software", slug="it-software")
        self.job = Job.objects.create(
            company=self.company,
            title="Python Developer",
            category=self.category,
            job_type="full-time",
            level="junior",
            description="Dev python",
            requirements="Python skills",
            status="published",
            created_by=self.user
        )

    def test_create_program_service(self):
        service = ReferralService()
        input_data = ProgramCreateInput(
            title="Referral Program 2024",
            description="Earn huge rewards",
            reward_amount=5000000,
            job_ids=[self.job.id]
        )
        
        program = service.create_program(self.company, input_data)
        
        self.assertEqual(program.title, "Referral Program 2024")
        self.assertEqual(program.reward_amount, 5000000)
        self.assertEqual(program.company, self.company)
        self.assertEqual(program.jobs.count(), 1)
        self.assertEqual(program.jobs.first(), self.job)

    def test_submit_referral_service(self):
        # Setup program
        service = ReferralService()
        program = ReferralProgram.objects.create(
            company=self.company,
            title="Prog 1",
            description="Desc",
            reward_amount=1000
        )
        program.jobs.add(self.job)
        
        # Submit referral
        input_data = ReferralCreateInput(
            program_id=program.id,
            job_id=self.job.id,
            candidate_name="Nguyen Van A",
            candidate_email="nguyenvana@example.com",
            candidate_phone="0909123456",
            notes="Strong candidate"
        )
        
        referral = service.submit_referral(
            referrer=self.user,
            data=input_data,
            cv_file=None 
        )
        
        self.assertEqual(referral.referrer, self.user)
        self.assertEqual(referral.candidate_name, "Nguyen Van A")
        self.assertEqual(referral.status, Referral.Status.PENDING)

    def test_submit_duplicate_referral(self):
        service = ReferralService()
        program = ReferralProgram.objects.create(
            company=self.company,
            title="Prog 1",
            description="Desc",
            reward_amount=1000
        )
        program.jobs.add(self.job)
        
        input_data = ReferralCreateInput(
            program_id=program.id,
            job_id=self.job.id,
            candidate_name="Nguyen Van A",
            candidate_email="unique@example.com",
            candidate_phone="0909123456"
        )
        
        service.submit_referral(self.user, input_data, None)
        
        with self.assertRaises(ValidationError):
            service.submit_referral(self.user, input_data, None)

    def test_referral_update_status(self):
        program = ReferralProgram.objects.create(company=self.company, reward_amount=100, title="T")
        referral = Referral.objects.create(
            program=program,
            job=self.job,
            referrer=self.user,
            candidate_name="B",
            candidate_email="b@e.com",
            candidate_phone="123"
        )
        
        service = ReferralService()
        updated = service.update_status(referral, Referral.Status.HIRED)
        self.assertEqual(updated.status, Referral.Status.HIRED)

    def test_selector_list_programs(self):
        program1 = ReferralProgram.objects.create(company=self.company, title="P1", reward_amount=100)
        ReferralProgram.objects.create(company=self.company, title="P2", reward_amount=100)
        
        qs = ReferralSelector.list_programs(self.user)
        self.assertGreaterEqual(qs.count(), 2)
