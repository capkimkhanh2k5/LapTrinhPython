from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.recruitment.referrals.models import ReferralProgram, Referral
from apps.company.companies.utils.cloudinary import save_raw_file
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date
from decimal import Decimal

class ProgramCreateInput(BaseModel):
    title: str
    description: str
    reward_amount: Decimal = Field(ge=0)
    currency: str = 'VND'
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    job_ids: List[int] = []

class ReferralCreateInput(BaseModel):
    program_id: int
    job_id: int
    candidate_name: str
    candidate_email: EmailStr
    candidate_phone: str
    notes: Optional[str] = ''

class ReferralService:
    @transaction.atomic
    def create_program(self, company, data: ProgramCreateInput) -> ReferralProgram:
        program = ReferralProgram.objects.create(
            company=company,
            title=data.title,
            description=data.description,
            reward_amount=data.reward_amount,
            currency=data.currency,
            start_date=data.start_date,
            end_date=data.end_date,
            status=ReferralProgram.Status.DRAFT
        )
        if data.job_ids:
            program.jobs.set(data.job_ids)
        return program

    @transaction.atomic
    def submit_referral(self, referrer, data: ReferralCreateInput, cv_file) -> Referral:
        # Check duplicate referral
        if Referral.objects.filter(
            job_id=data.job_id,
            candidate_email=data.candidate_email
        ).exists():
            raise ValidationError("This candidate has already been referred for this job.")

        # Upload CV to Cloudinary if file provided
        cv_url = ''
        if cv_file:
            # save_raw_file will verify 'Jobio/' prefix
            cv_url = save_raw_file('Referrals/CVs', cv_file, 'cv')

        referral = Referral.objects.create(
            program_id=data.program_id,
            job_id=data.job_id,
            referrer=referrer,
            candidate_name=data.candidate_name,
            candidate_email=data.candidate_email,
            candidate_phone=data.candidate_phone,
            cv_file=cv_url,
            notes=data.notes
        )
        return referral

    @transaction.atomic
    def update_status(self, referral: Referral, new_status: str, actor=None) -> Referral:
        """
        Update referral status with State Machine logic.
        
        Transitions: 
        PENDING -> REVIEWED/REJECTED
        REVIEWED -> INTERVIEWING/REJECTED
        INTERVIEWING -> HIRED/REJECTED
        HIRED -> PAID
        """
        # Actor validation - only company staff can change status
        if actor and not hasattr(actor, 'company_profile'):
            raise ValidationError("Chỉ nhân viên công ty mới có quyền cập nhật trạng thái giới thiệu.")
        
        if actor and actor.company_profile != referral.program.company:
            raise ValidationError("Bạn không có quyền cập nhật trạng thái cho chương trình này.")

        old_status = referral.status
        
        # Prevent same-status update
        if old_status == new_status:
            return referral

        # Simple state machine validation
        allowed_transitions = {
            Referral.Status.PENDING: [Referral.Status.REVIEWED, Referral.Status.REJECTED],
            Referral.Status.REVIEWED: [Referral.Status.INTERVIEWING, Referral.Status.REJECTED],
            Referral.Status.INTERVIEWING: [Referral.Status.HIRED, Referral.Status.REJECTED],
            Referral.Status.HIRED: [Referral.Status.PAID],
            Referral.Status.REJECTED: [], # Final state
            Referral.Status.PAID: [],     # Final state
        }
        
        if new_status not in allowed_transitions.get(old_status, []):
            raise ValidationError(f"Không thể chuyển trạng thái từ {old_status} sang {new_status}.")

        # Handle specific logic for PAID
        if new_status == Referral.Status.PAID:
            referral.paid_at = timezone.now()

        referral.status = new_status
        referral.save()
        return referral

    @transaction.atomic
    def mark_as_paid(self, referral: Referral, actor) -> Referral:
        """Helper for marking as paid directly with specific HIRED check."""
        if referral.status != Referral.Status.HIRED:
             raise ValidationError("Ứng viên phải ở trạng thái HIRED trước khi đánh dấu đã thanh toán.")
        
        return self.update_status(referral, Referral.Status.PAID, actor)
