from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel

class ReferralProgram(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ACTIVE = 'active', _('Active')
        PAUSED = 'paused', _('Paused')
        ENDED = 'ended', _('Ended')

    class RewardType(models.TextChoices):
        FIXED = 'fixed', _('Fixed Amount')
        PERCENTAGE = 'percentage', _('Percentage of Salary')

    company = models.ForeignKey(
        'company_companies.Company',
        on_delete=models.CASCADE,
        related_name='recruitment_referral_programs'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Reward Configuration
    reward_type = models.CharField(
        max_length=20,
        choices=RewardType.choices,
        default=RewardType.FIXED,
        verbose_name=_('Loại thưởng')
    )
    reward_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        verbose_name=_('Giá trị thưởng (Tiền hoặc %)')
    )
    currency = models.CharField(max_length=10, default='VND')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Jobs eligible for this program
    jobs = models.ManyToManyField(
        'recruitment_jobs.Job',
        related_name='referral_programs',
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Referral(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        REVIEWED = 'reviewed', _('Reviewed')
        INTERVIEWING = 'interviewing', _('Interviewing')
        HIRED = 'hired', _('Hired')
        REJECTED = 'rejected', _('Rejected')
        PAID = 'paid', _('Paid')

    program = models.ForeignKey(
        ReferralProgram,
        on_delete=models.CASCADE,
        related_name='referrals'
    )
    job = models.ForeignKey(
        'recruitment_jobs.Job',
        on_delete=models.CASCADE,
        related_name='recruitment_referrals'
    )
    referrer = models.ForeignKey(
        'core_users.CustomUser',
        on_delete=models.CASCADE,
        related_name='recruitment_referrals_made'
    )
    
    # Candidate Information
    candidate_name = models.CharField(max_length=255)
    candidate_email = models.EmailField()
    candidate_phone = models.CharField(max_length=20)
    cv_file = models.URLField(max_length=500, blank=True, help_text='Cloudinary URL of CV file')
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    referral_date = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Ngày thanh toán'))
    notes = models.TextField(blank=True)

    @property
    def company(self):
        return self.program.company

    class Meta:
        ordering = ['-referral_date']

    def __str__(self):
        return f"{self.referrer} -> {self.candidate_name}"
