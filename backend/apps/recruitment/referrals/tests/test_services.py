import pytest
from django.core.exceptions import ValidationError
from apps.recruitment.referrals.services.referrals import ReferralService, ProgramCreateInput, ReferralCreateInput
from apps.recruitment.referrals.models import ReferralProgram, Referral
from apps.recruitment.referrals.selectors.referrals import ReferralSelector

@pytest.mark.django_db
class TestReferralService:
    def test_create_program_service(self, company, job):
        service = ReferralService()
        input_data = ProgramCreateInput(
            title="Referral Program 2024",
            description="Earn huge rewards",
            reward_amount=5000000,
            job_ids=[job.id]
        )
        
        program = service.create_program(company, input_data)
        
        assert program.title == "Referral Program 2024"
        assert program.reward_amount == 5000000
        assert program.company == company
        assert program.jobs.count() == 1
        assert program.jobs.first() == job

    def test_submit_referral_service(self, user, job, company):
        # Setup program
        service = ReferralService()
        program = ReferralProgram.objects.create(
            company=company,
            title="Prog 1",
            description="Desc",
            reward_amount=1000
        )
        program.jobs.add(job)
        
        # Submit referral
        input_data = ReferralCreateInput(
            program_id=program.id,
            job_id=job.id,
            candidate_name="Nguyen Van A",
            candidate_email="nguyenvana@example.com",
            candidate_phone="0909123456",
            notes="Strong candidate"
        )
        
        referral = service.submit_referral(
            referrer=user,
            data=input_data,
            cv_file=None # Mocking file not strictly needed for service logic if handled
        )
        
        assert referral.referrer == user
        assert referral.candidate_name == "Nguyen Van A"
        assert referral.status == Referral.Status.PENDING

    def test_submit_duplicate_referral(self, user, job, company):
        service = ReferralService()
        program = ReferralProgram.objects.create(
            company=company,
            title="Prog 1",
            description="Desc",
            reward_amount=1000
        )
        program.jobs.add(job)
        
        input_data = ReferralCreateInput(
            program_id=program.id,
            job_id=job.id,
            candidate_name="Nguyen Van A",
            candidate_email="unique@example.com",
            candidate_phone="0909123456"
        )
        
        service.submit_referral(user, input_data, None)
        
        with pytest.raises(ValidationError):
            service.submit_referral(user, input_data, None)

    def test_referral_update_status(self, user, job, company):
        program = ReferralProgram.objects.create(company=company, reward_amount=100, title="T")
        referral = Referral.objects.create(
            program=program,
            job=job,
            referrer=user,
            candidate_name="B",
            candidate_email="b@e.com",
            candidate_phone="123"
        )
        
        service = ReferralService()
        updated = service.update_status(referral, Referral.Status.HIRED)
        assert updated.status == Referral.Status.HIRED

    def test_selector_list_programs(self, company, user):
        program1 = ReferralProgram.objects.create(company=company, title="P1", reward_amount=100)
        ReferralProgram.objects.create(company=company, title="P2", reward_amount=100)
        
        # selector logic depends on user context in implementation
        # For now, selector is simple wrapper
        qs = ReferralSelector.list_programs(user) # If generic user, implementation might return all?
        # Let's verify the implementation: currently returns all
        assert qs.count() >= 2
