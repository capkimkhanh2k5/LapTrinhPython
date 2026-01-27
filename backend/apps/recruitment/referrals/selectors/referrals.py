from django.db.models import QuerySet, Q
from django.utils import timezone
from apps.recruitment.referrals.models import ReferralProgram, Referral

class ReferralSelector:
    @staticmethod
    def list_programs(user=None, active_only=False) -> QuerySet[ReferralProgram]:
        """
        List referral programs.
        - active_only=True: Show only ACTIVE programs (for candidates).
        - user: Filter by company if user is staff.
        """
        qs = ReferralProgram.objects.all()
        
        if active_only:
            now = timezone.now().date()
            qs = qs.filter(status=ReferralProgram.Status.ACTIVE)
            # Check dates if set
            qs = qs.filter(
                Q(start_date__isnull=True) | Q(start_date__lte=now)
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now)
            )

        if user and hasattr(user, 'company_profile'):
             qs = qs.filter(company=user.company_profile)
        
        return qs.select_related('company')

    @staticmethod
    def list_my_referrals(user) -> QuerySet[Referral]:
        """List referrals made by the current user"""
        return Referral.objects.filter(referrer=user).select_related('program', 'job')

    @staticmethod
    def list_company_referrals(company) -> QuerySet[Referral]:
        """List all referrals for a company's programs"""
        return Referral.objects.filter(program__company=company).select_related('referrer', 'job', 'program')
