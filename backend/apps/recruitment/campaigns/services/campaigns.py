from typing import Optional, List
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator

from django.db import transaction
from django.db.models import Sum, Count, Q
from django.core.exceptions import ValidationError

from apps.recruitment.campaigns.models import Campaign
from apps.recruitment.jobs.models import Job
from apps.company.companies.models import Company

class CampaignCreateInput(BaseModel):
    title: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = 'draft'
    budget: Optional[Decimal] = Field(None, ge=0)
    job_ids: List[int] = Field(default_factory=list)

    @model_validator(mode='after')
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError('End date cannot be before start date')
        return self

class CampaignUpdateInput(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    job_ids: Optional[List[int]] = None

    @model_validator(mode='after')
    def check_dates(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError('End date cannot be before start date')
        return self

class CampaignReviewInput(BaseModel):
    is_approved: bool
    review_notes: Optional[str] = None

class AnalyticsOutput(BaseModel):
    total_views: int
    total_applications: int
    active_jobs: int
    total_jobs: int

class CampaignService:
    @staticmethod
    @transaction.atomic
    def create_campaign(company: Company, data: CampaignCreateInput) -> Campaign:
        # Check slug uniqueness for company
        if Campaign.objects.filter(slug=data.slug, company=company).exists():
            raise ValidationError(f"Campaign with slug '{data.slug}' already exists for this company.")

        campaign = Campaign.objects.create(
            company=company,
            title=data.title,
            slug=data.slug,
            description=data.description,
            start_date=data.start_date,
            end_date=data.end_date,
            status=data.status,
            budget=data.budget
        )
        
        if data.job_ids:
            jobs = Job.objects.filter(id__in=data.job_ids, company=company)
            campaign.jobs.set(jobs)
        
        return campaign

    @staticmethod
    @transaction.atomic
    def update_campaign(campaign: Campaign, data: CampaignUpdateInput) -> Campaign:
        if data.title is not None:
            campaign.title = data.title
        if data.description is not None:
            campaign.description = data.description
        if data.start_date is not None:
            campaign.start_date = data.start_date
        if data.end_date is not None:
            campaign.end_date = data.end_date
        if data.status is not None:
            campaign.status = data.status
        if data.budget is not None:
            campaign.budget = data.budget
            
        campaign.save()

        if data.job_ids is not None:
            jobs = Job.objects.filter(id__in=data.job_ids, company=campaign.company)
            campaign.jobs.set(jobs)
            
        return campaign

    @staticmethod
    def add_jobs(campaign: Campaign, job_ids: List[int]) -> Campaign:
        jobs = Job.objects.filter(id__in=job_ids, company=campaign.company)
        campaign.jobs.add(*jobs)
        return campaign

    @staticmethod
    def remove_job(campaign: Campaign, job_id: int) -> Campaign:
        job = Job.objects.filter(id=job_id, company=campaign.company).first()
        if job:
            campaign.jobs.remove(job)
        return campaign

    @staticmethod
    def get_analytics(campaign: Campaign) -> AnalyticsOutput:
        # Aggregate stats from linked jobs
        # Use existing counter fields in Job model: view_count, application_count
        
        stats = campaign.jobs.aggregate(
            total_views=Sum('view_count'),
            total_applications=Sum('application_count')
        )
        
        total_jobs = campaign.jobs.count()
        active_jobs = campaign.jobs.filter(status='published').count()
        
        return AnalyticsOutput(
            total_views=stats['total_views'] or 0,
            total_applications=stats['total_applications'] or 0,
            active_jobs=active_jobs,
            total_jobs=total_jobs
        )
