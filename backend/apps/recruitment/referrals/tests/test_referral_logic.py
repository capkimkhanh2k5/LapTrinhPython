from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.users.models import CustomUser
from apps.company.companies.models import Company
from apps.recruitment.jobs.models import Job
from apps.recruitment.referrals.models import ReferralProgram, Referral
from apps.recruitment.referrals.services.referrals import ReferralService, ReferralCreateInput
from decimal import Decimal

class ReferralLogicTest(TestCase):
    def setUp(self):
        # Setup Company and Users
        self.owner_user = CustomUser.objects.create(email='owner@comp.com', role='employer')
        self.company = Company.objects.create(
            company_name='Test Corp', 
            user=self.owner_user,
            slug='test-corp'
        )
        self.owner_user.company_profile = self.company
        self.owner_user.save()

        self.other_user = CustomUser.objects.create(email='other@comp.com', role='employer')
        self.other_company = Company.objects.create(
            company_name='Other Corp', 
            user=self.other_user,
            slug='other-corp'
        )
        self.other_user.company_profile = self.other_company
        self.other_user.save()

        self.referrer = CustomUser.objects.create(email='referrer@gmail.com', role='candidate')

        self.job = Job.objects.create(
            company=self.company, 
            title='Python Dev',
            created_by=self.owner_user
        )
        
        self.program = ReferralProgram.objects.create(
            company=self.company,
            title='Referral Program',
            reward_amount=Decimal('1000000'),
            status=ReferralProgram.Status.ACTIVE
        )
        
        self.service = ReferralService()

    def test_referral_state_machine_valid(self):
        """Test valid state transitions: PENDING -> REVIEWED -> INTERVIEWING -> HIRED -> PAID"""
        referral = Referral.objects.create(
            program=self.program,
            job=self.job,
            referrer=self.referrer,
            candidate_name='Candidate A',
            candidate_email='a@gmail.com',
            status=Referral.Status.PENDING
        )
        
        # 1. PENDING -> REVIEWED
        referral = self.service.update_status(referral, Referral.Status.REVIEWED, actor=self.owner_user)
        self.assertEqual(referral.status, Referral.Status.REVIEWED)
        
        # 2. REVIEWED -> INTERVIEWING
        referral = self.service.update_status(referral, Referral.Status.INTERVIEWING, actor=self.owner_user)
        self.assertEqual(referral.status, Referral.Status.INTERVIEWING)
        
        # 3. INTERVIEWING -> HIRED
        referral = self.service.update_status(referral, Referral.Status.HIRED, actor=self.owner_user)
        self.assertEqual(referral.status, Referral.Status.HIRED)
        
        # 4. HIRED -> PAID
        referral = self.service.update_status(referral, Referral.Status.PAID, actor=self.owner_user)
        self.assertEqual(referral.status, Referral.Status.PAID)
        self.assertIsNotNone(referral.paid_at)

    def test_referral_state_machine_invalid(self):
        """Test invalid state transition: PENDING -> PAID (Skip steps)"""
        referral = Referral.objects.create(
            program=self.program,
            job=self.job,
            referrer=self.referrer,
            candidate_name='Candidate B',
            candidate_email='b@gmail.com',
            status=Referral.Status.PENDING
        )
        
        with self.assertRaises(ValidationError) as cm:
            self.service.update_status(referral, Referral.Status.PAID, actor=self.owner_user)
        self.assertIn("Không thể chuyển trạng thái", str(cm.exception))

    def test_permission_enforcement(self):
        """Test that only the program owner can update status"""
        referral = Referral.objects.create(
            program=self.program,
            job=self.job,
            referrer=self.referrer,
            candidate_name='Candidate C',
            candidate_email='c@gmail.com',
            status=Referral.Status.PENDING
        )
        
        # Another company owner tries to update
        with self.assertRaises(ValidationError) as cm:
            self.service.update_status(referral, Referral.Status.REVIEWED, actor=self.other_user)
        self.assertIn("Bạn không có quyền", str(cm.exception))

    def test_mark_as_paid_helper(self):
        """Test the mark_as_paid specialized helper"""
        referral = Referral.objects.create(
            program=self.program,
            job=self.job,
            referrer=self.referrer,
            candidate_name='Candidate D',
            candidate_email='d@gmail.com',
            status=Referral.Status.HIRED # Already HIRED
        )
        
        referral = self.service.mark_as_paid(referral, actor=self.owner_user)
        self.assertEqual(referral.status, Referral.Status.PAID)
        self.assertIsNotNone(referral.paid_at)
