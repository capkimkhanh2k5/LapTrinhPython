from django.db.models import QuerySet
from apps.recruitment.referrals.models import ReferralProgram, Referral

class ReferralSelector:
    @staticmethod
    def list_programs(user, filters=None) -> QuerySet[ReferralProgram]:
        """
        List referral programs.
        - If user is company owner/recruiter: list company's programs.
        - If generic user: list active public programs (not implemented yet, assuming backend usage).
        """
        qs = ReferralProgram.objects.all()
        
        #TODO: Cần kiểm tra lại

        # Filter by company if user is company staff
        if hasattr(user, 'company_profile'): # Assuming related name or check
             qs = qs.filter(company=user.company_profile)
        # Or if user is just querying active programs for jobs (public view)
        # This logic depends on context. For now, let's assume this is for Company Management.
        
        return qs

    @staticmethod
    def list_my_referrals(user) -> QuerySet[Referral]:
        """List referrals made by the current user"""
        return Referral.objects.filter(referrer=user).select_related('program', 'job')

    @staticmethod
    def list_company_referrals(company) -> QuerySet[Referral]:
        """List all referrals for a company's programs"""
        return Referral.objects.filter(program__company=company).select_related('referrer', 'job', 'program')
