from django.db import transaction
from django.core.exceptions import ValidationError
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
            cv_url = save_raw_file('referrals/cvs', cv_file, 'cv')

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
    def update_status(self, referral: Referral, new_status: str) -> Referral:
        # State machine logic here if needed
        referral.status = new_status
        referral.save()
        return referral
